"""Rotas da aba Ativo protegido: varredura de collar e collar + borboleta (ativo + put + calls)."""

from __future__ import annotations

import logging
import math
import uuid
from collections import OrderedDict
from collections.abc import Callable

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from travas.data.market_data import ChainScope
from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.options.liquidity import LiquidityRules
from travas.options.protected import (
    ProtectedChain,
    ProtectedKind,
    ProtectedParams,
    StockQuote,
    assumptions,
    evaluate,
    find_rows,
    prepare,
    scan_prepared,
    simulation,
)
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)
MAX_CONTEXTS = 8
ATM_MARGIN = 0.06  # a coleta sempre inclui strikes a ±6% do spot (IV ATM)


class LiquidityOverrides(BaseModel):
    max_spread_pct_mid: float | None = None
    min_mid_price_brl: float | None = None
    min_turnover_brl: float | None = None
    min_deals: int | None = None
    max_quote_age_seconds: float | None = None


class ProtectedIn(BaseModel):
    underlying: str
    kinds: list[ProtectedKind] | None = None
    dte_min: int | None = Field(default=None, ge=0)
    dte_max: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, gt=0)
    rate_annual: float | None = None
    costs_brl: float = Field(default=0.0, ge=0)
    min_floor_return: float | None = None  # fração (0,01 = piso ≥ custo + 1%)
    european_short: bool = False
    include_illiquid: bool = False
    limit_aggressiveness: float | None = Field(default=None, ge=0, le=1)
    liquidity: LiquidityOverrides = LiquidityOverrides()
    weights: dict[str, float] | None = None
    refresh: bool = False


def protected_router(
    settings: Settings,
    service: MarketDataService,
    clean: Callable,
    require_options: Callable[[MarketDataService, str], None],
) -> APIRouter:
    router = APIRouter(prefix="/api/protected")
    contexts: OrderedDict[str, tuple[ProtectedChain, dict]] = OrderedDict()

    @router.post("/scan")
    def scan(body: ProtectedIn) -> dict:
        underlying = body.underlying.strip().upper()
        require_options(service, underlying)
        quote = service.quote(underlying)
        if quote.price is None:
            raise MarketDataUnavailable(f"{underlying} sem cotação no terminal")
        params = _params(body, settings)
        spot = quote.price
        chain, meta = service.chain(underlying, _scope(params, spot), force=body.refresh)
        if chain.empty:
            raise HTTPException(404, f"nenhuma opção de {underlying} encontrada no escopo")
        if chain["underlying_price"].notna().any():
            spot = float(chain["underlying_price"].dropna().iloc[-1])
        stock = StockQuote(
            symbol=underlying,
            bid=quote.bid,
            ask=quote.ask,
            last=quote.last,
            price=quote.price,
            quote_time=quote.quote_time.isoformat() if quote.quote_time is not None else None,
            source=quote.source,
        )
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        prep = prepare(chain, stock, spot, today, service.calendar, params)
        result = scan_prepared(prep)
        scan_id = uuid.uuid4().hex[:12]
        contexts[scan_id] = (prep, meta)
        while len(contexts) > MAX_CONTEXTS:
            contexts.popitem(last=False)
        result.update({"scan_id": scan_id, "underlying": underlying, "collection": meta})
        return clean(result)

    @router.get("/detail/{scan_id}/{structure_id}")
    def detail(scan_id: str, structure_id: str) -> dict:
        if scan_id not in contexts:
            raise HTTPException(404, "varredura expirada; escaneie de novo")
        prep, meta = contexts[scan_id]
        try:
            kind, rows = find_rows(prep, structure_id)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        row = evaluate(prep, kind, rows)
        row["simulation"] = simulation(prep, kind, rows)
        row["collection"] = meta
        row["spot"] = prep.spot
        row["assumptions"] = assumptions(prep)
        return clean(row)

    return router


def _params(body: ProtectedIn, settings: Settings) -> ProtectedParams:
    s = settings.protected
    liq = settings.liquidity.model_dump()
    liq.update({k: v for k, v in body.liquidity.model_dump().items() if v is not None})
    weights = s.weights.model_dump()
    if body.weights:
        weights.update({k: max(0.0, float(v)) for k, v in body.weights.items() if k in weights})
        total = sum(weights.values())
        if total <= 0:
            raise HTTPException(422, "pelo menos um peso do ranking deve ser positivo")
        weights = {k: v / total for k, v in weights.items()}
    return ProtectedParams(
        quantity=body.quantity or s.quantity,
        rate_annual=body.rate_annual
        if body.rate_annual is not None
        else settings.pricing.risk_free_rate_annual,
        liquidity=LiquidityRules(**liq),
        weights=weights,
        pricing=settings.pricing,
        early_exercise=settings.early_exercise,
        kinds=tuple(body.kinds) if body.kinds else tuple(ProtectedKind),
        dte_min=body.dte_min if body.dte_min is not None else s.dte_min_business_days,
        dte_max=body.dte_max or s.dte_max_business_days,
        put_min_pct_spot=s.put_min_pct_spot,
        put_max_pct_spot=s.put_max_pct_spot,
        call_max_pct_spot=s.call_max_pct_spot,
        max_wing_pct_spot=s.max_wing_pct_spot,
        min_floor_return=body.min_floor_return
        if body.min_floor_return is not None
        else s.min_floor_return,
        costs_brl=body.costs_brl,
        european_short=body.european_short,
        include_illiquid=body.include_illiquid,
        illiquid_score_cap=s.illiquid_score_cap,
        limit_aggressiveness=body.limit_aggressiveness
        if body.limit_aggressiveness is not None
        else s.limit_aggressiveness,
        max_results=s.max_results,
        max_candidates=s.max_candidates,
    )


def _scope(params: ProtectedParams, spot: float) -> ChainScope:
    low = min(spot * params.put_min_pct_spot, spot * (1 - ATM_MARGIN))
    high = max(spot * params.call_max_pct_spot, spot * (1 + ATM_MARGIN))
    # Arredonda para reaproveitar o cache entre varreduras com spot quase igual.
    return ChainScope(
        ("call", "put"), params.dte_max, math.floor(low * 2) / 2, math.ceil(high * 2) / 2
    )
