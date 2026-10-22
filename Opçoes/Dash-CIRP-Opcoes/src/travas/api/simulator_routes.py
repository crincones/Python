"""Rotas da aba Simulador: grade de opções de um vencimento e avaliação de pernas livres.
Nenhuma rota envia ordens."""

from __future__ import annotations

import datetime as dt
import logging
import time
from collections.abc import Callable
from typing import Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.options import pricing
from travas.options.implied_vol import options_implied_vol
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.options.models import Side
from travas.options.simulator import (
    MAX_LEGS,
    SimulationError,
    evaluate_simulation,
    resolve_legs,
)
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)
QUOTES_REUSE_SECONDS = 60
CHAIN_STRIKE_RANGE = 0.30  # grade: strikes a ±30% do spot


class SimLegIn(BaseModel):
    kind: Literal["opcao", "ativo"] = "opcao"
    symbol: str | None = Field(default=None, max_length=32)
    side: Side
    quantity: int = Field(gt=0)
    price: float | None = Field(default=None, ge=0)
    sigma: float | None = Field(default=None, gt=0)


class SimulateIn(BaseModel):
    underlying: str = Field(min_length=1, max_length=16)
    legs: list[SimLegIn] = Field(min_length=1, max_length=MAX_LEGS)
    rate_annual: float | None = None
    vol_override: float | None = Field(default=None, gt=0)
    costs_brl: float = Field(default=0.0, ge=0)
    target_price: float | None = Field(default=None, gt=0)
    refresh: bool = False


def simulator_router(
    settings: Settings,
    service: MarketDataService,
    clean: Callable,
    require_options: Callable[[MarketDataService, str], None],
) -> APIRouter:
    router = APIRouter(prefix="/api/simulator")
    cache: dict[str, tuple[float, pd.DataFrame]] = {}  # ativo → (t, cotações por símbolo)

    def _rules() -> LiquidityRules:
        return LiquidityRules(**settings.liquidity.model_dump())

    def _quotes(underlying: str, symbols: list[str], rate_annual: float, fresh: bool):
        """Cotações das séries (mesma origem da Carteira: pregão aberto = MT5 e salva;
        fechado = últimas do pregão, com a idade medida contra a captura mais recente)."""
        cached = cache.get(underlying)
        if (
            cached
            and not fresh
            and time.monotonic() - cached[0] <= QUOTES_REUSE_SECONDS
            and set(symbols) <= set(cached[1].index)
        ):
            return cached[1]
        chain = service.leg_quotes(underlying, symbols)
        if not chain.empty:
            chain = chain.join(evaluate_liquidity(chain, _rules()))
            chain = chain.join(options_implied_vol(chain, rate_annual, settings.pricing))
            chain = chain.drop_duplicates("symbol", keep="last").set_index("symbol", drop=False)
        merged = chain
        recent = cached and time.monotonic() - cached[0] <= QUOTES_REUSE_SECONDS
        if recent and not fresh and not cached[1].empty:
            # Mantém as séries lidas há pouco (outras pernas/vencimentos) junto das novas.
            merged = pd.concat([cached[1].drop(index=chain.index, errors="ignore"), chain])
        cache[underlying] = (time.monotonic(), merged)
        return merged

    def _rate(value: float | None) -> float:
        return value if value is not None else settings.pricing.risk_free_rate_annual

    @router.get("/chain/{underlying}")
    def chain(underlying: str, expiration: dt.date, refresh: bool = False) -> dict:
        """Calls e puts de um vencimento (strikes a ±30% do spot), para montar pernas rápido."""
        underlying = underlying.strip().upper()
        require_options(service, underlying)
        quote = service.quote(underlying)
        if quote.price is None:
            raise MarketDataUnavailable(f"{underlying} sem cotação no terminal")
        catalog = service.catalog()
        rows = catalog[
            (catalog["underlying"] == underlying)
            & (catalog["expiration_date"] == expiration)
            & catalog["strike"].between(
                quote.price * (1 - CHAIN_STRIKE_RANGE), quote.price * (1 + CHAIN_STRIKE_RANGE)
            )
        ]
        if rows.empty:
            raise HTTPException(404, f"nenhuma opção de {underlying} em {expiration:%d/%m/%Y}")
        quotes = _quotes(underlying, sorted(rows["symbol"]), _rate(None), fresh=refresh).reindex(
            rows["symbol"]
        )
        out = []
        for _, info in rows.sort_values(["strike", "option_type"]).iterrows():
            q = quotes.loc[info["symbol"]] if info["symbol"] in quotes.index else None
            has = q is not None and pd.notna(q.get("symbol"))
            out.append(
                {
                    "symbol": info["symbol"],
                    "option_type": info["option_type"],
                    "strike": float(info["strike"]),
                    "exercise_style": info["exercise_style"],
                    "bid": q["bid"] if has else None,
                    "ask": q["ask"] if has else None,
                    "mid": q["mid"] if has else None,
                    "last": q["last"] if has else None,
                    "iv": q["iv"] if has and q.get("iv_status") == "ok" else None,
                    "deals": q["deals"] if has else None,
                    "flags": list(q["quote_flags"]) if has else ["sem cotação"],
                    "price_basis": q.get("price_basis")
                    if has and isinstance(q.get("price_basis"), str)
                    else "book",
                }
            )
        market = service.market()
        return clean(
            {
                "underlying": underlying,
                "expiration": expiration,
                "spot": quote.price,
                "spot_source": quote.source,
                "market": market.to_dict(),
                "read_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
                "rows": out,
            }
        )

    @router.post("/evaluate")
    def evaluate(body: SimulateIn) -> dict:
        underlying = body.underlying.strip().upper()
        require_options(service, underlying)
        try:
            legs = resolve_legs(
                [leg.model_dump(mode="json") for leg in body.legs], underlying, service.catalog()
            )
        except SimulationError as exc:
            raise HTTPException(422, str(exc)) from exc
        rate_annual = _rate(body.rate_annual)
        quote = service.quote(underlying)
        symbols = sorted({leg.symbol for leg in legs if leg.kind == "opcao"})
        quotes = _quotes(underlying, symbols, rate_annual, fresh=body.refresh)
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        stock = {
            "symbol": underlying,
            "bid": quote.bid,
            "ask": quote.ask,
            "last": quote.last,
            "price": quote.price,
            "quote_time": quote.quote_time.isoformat() if quote.quote_time is not None else None,
            "source": quote.source,
        }
        try:
            result = evaluate_simulation(
                legs,
                quotes,
                stock,
                quote.price,
                today,
                service.calendar,
                float(pricing.continuous_rate(rate_annual)),
                rate_annual,
                settings.early_exercise,
                body.vol_override,
                body.costs_brl,
                body.target_price,
                settings.liquidity.max_quote_age_seconds,
            )
        except SimulationError as exc:
            raise HTTPException(422, str(exc)) from exc
        market = service.market()
        note = None
        if not market.is_open:
            note = (
                f"{market.label}: usando as últimas cotações capturadas no pregão (ativo e "
                "opções); não são cotações atuais"
            )
        result.update(
            {
                "market": market.to_dict(),
                "quotes_note": note,
                "evaluated_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
                "rate_annual": rate_annual,
                "vol_override": body.vol_override,
            }
        )
        return clean(result)

    return router
