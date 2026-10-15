"""Rotas da aba Acompanhamento. Nenhuma rota envia ordens: só registra e avalia estruturas."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.options import pricing
from travas.options.implied_vol import options_implied_vol
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE
from travas.tracking.evaluate import (
    PositionError,
    build_record,
    close_record,
    combined_record,
    evaluate_position,
    group_summaries,
)
from travas.tracking.models import ExitIn, PositionIn
from travas.tracking.store import TrackingStore

log = logging.getLogger(__name__)
QUOTES_REUSE_SECONDS = 120


class EvaluateIn(BaseModel):
    vol_override: float | None = Field(default=None, gt=0)
    rate_annual: float | None = None


def tracking_router(
    settings: Settings, service: MarketDataService, store: TrackingStore, clean: Callable
) -> APIRouter:
    router = APIRouter(prefix="/api/tracking")
    cache: dict[str, tuple[float, float | None, pd.DataFrame]] = {}  # ativo → (t, spot, cotações)

    def _quotes(underlying: str, symbols: list[str], rate_annual: float, fresh: bool):
        cached = cache.get(underlying)
        if (
            cached
            and not fresh
            and time.monotonic() - cached[0] <= QUOTES_REUSE_SECONDS
            and set(symbols) <= set(cached[2].index)
        ):
            return cached[1], cached[2]
        spot = service.quote(underlying).price
        chain = service.leg_quotes(underlying, symbols)
        if not chain.empty:
            rules = LiquidityRules(**settings.liquidity.model_dump())
            chain = chain.join(evaluate_liquidity(chain, rules))
            chain = chain.join(options_implied_vol(chain, rate_annual, settings.pricing))
            chain = chain.set_index("symbol", drop=False)
        cache[underlying] = (time.monotonic(), spot, chain)
        return spot, chain

    def _evaluate(records: list[dict], body: EvaluateIn, fresh: bool, simulate: bool = False):
        rate_annual = (
            body.rate_annual
            if body.rate_annual is not None
            else settings.pricing.risk_free_rate_annual
        )
        rate = float(pricing.continuous_rate(rate_annual))
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        by_underlying: dict[str, set[str]] = {}
        for rec in records:
            if rec.get("status") == "aberta":
                by_underlying.setdefault(rec["underlying"], set()).update(
                    lg["symbol"] for lg in rec["legs"]
                )
        market: dict[str, tuple[float | None, pd.DataFrame]] = {}
        errors: list[str] = []
        for underlying, symbols in by_underlying.items():
            try:
                market[underlying] = _quotes(underlying, sorted(symbols), rate_annual, fresh)
            except MarketDataUnavailable as exc:
                errors.append(f"{underlying}: {exc}")
                market[underlying] = (None, pd.DataFrame())
        out = []
        for rec in records:
            spot, quotes = market.get(rec["underlying"], (None, pd.DataFrame()))
            try:
                out.append(
                    evaluate_position(
                        rec,
                        quotes,
                        spot,
                        today,
                        service.calendar,
                        rate,
                        rate_annual,
                        settings.early_exercise,
                        body.vol_override,
                        with_simulation=simulate,
                    )
                )
            except PositionError as exc:
                errors.append(f"{rec.get('name') or rec['id']}: {exc}")
        return out, errors

    @router.get("/positions")
    def list_positions() -> list[dict]:
        return clean(store.list())

    @router.post("/positions")
    def create(body: PositionIn) -> dict:
        try:
            record = build_record(body, service.catalog())
        except PositionError as exc:
            raise HTTPException(422, str(exc)) from exc
        return clean(store.add(record))

    @router.put("/positions/{position_id}")
    def update(position_id: str, body: PositionIn) -> dict:
        if store.get(position_id) is None:
            raise HTTPException(404, "estrutura não encontrada")
        try:
            record = build_record(body, service.catalog())
        except PositionError as exc:
            raise HTTPException(422, str(exc)) from exc
        return clean(store.update(position_id, record))

    @router.post("/positions/{position_id}/close")
    def close(position_id: str, body: ExitIn) -> dict:
        record = store.get(position_id)
        if record is None:
            raise HTTPException(404, "estrutura não encontrada")
        try:
            changes = close_record(record, body)
        except PositionError as exc:
            raise HTTPException(422, str(exc)) from exc
        return clean(store.update(position_id, changes))

    @router.post("/positions/{position_id}/reopen")
    def reopen(position_id: str) -> dict:
        if store.get(position_id) is None:
            raise HTTPException(404, "estrutura não encontrada")
        return clean(store.update(position_id, {"status": "aberta", "exit": None}))

    @router.delete("/positions/{position_id}")
    def delete(position_id: str) -> dict:
        try:
            store.delete(position_id)
        except KeyError as exc:
            raise HTTPException(404, "estrutura não encontrada") from exc
        return {"ok": True}

    @router.post("/evaluate")
    def evaluate(body: EvaluateIn) -> dict:
        evaluated, errors = _evaluate(store.list(), body, fresh=True)
        market = service.market()
        legs = [leg for e in evaluated if e["status"] == "aberta" for leg in e["legs"]]
        captured = [
            leg["captured_at"]
            for leg in legs
            if leg.get("source") == "ultimo_pregao" and leg.get("captured_at")
        ]
        outside = sorted({leg["symbol"] for leg in legs if leg.get("source") == "mt5_fora_pregao"})
        quotes_note = None
        if not market.is_open:
            parts = [market.label]
            if captured:
                when = max(captured)[:16].replace("T", " ")
                parts.append(f"usando as últimas cotações capturadas no pregão (até {when})")
            if outside:
                parts.append(
                    "sem cotações salvas do pregão para "
                    + ", ".join(outside)
                    + ": lidas do MT5 fora do pregão, podem estar distorcidas ou zeradas "
                    "(serão salvas na próxima atualização com o mercado aberto)"
                )
            quotes_note = "; ".join(parts) + ". Não são cotações atuais."
        return clean(
            {
                "market": market.to_dict(),
                "quotes_note": quotes_note,
                "evaluated_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
                "positions": evaluated,
                "groups": group_summaries(evaluated),
                "errors": errors,
            }
        )

    @router.post("/positions/{position_id}/detail")
    def detail(position_id: str, body: EvaluateIn) -> dict:
        record = store.get(position_id)
        if record is None:
            raise HTTPException(404, "estrutura não encontrada")
        evaluated, errors = _evaluate([record], body, fresh=False, simulate=True)
        if not evaluated:
            raise HTTPException(422, "; ".join(errors))
        return clean({**evaluated[0], "errors": errors})

    @router.post("/groups/{group}/detail")
    def group_detail(group: str, body: EvaluateIn) -> dict:
        records = [
            r for r in store.list() if r.get("group") == group and r.get("status") == "aberta"
        ]
        if not records:
            raise HTTPException(404, "grupo sem estruturas abertas")
        if len({r["underlying"] for r in records}) > 1:
            raise HTTPException(
                422, "grupo com ativos diferentes: payoff agregado só para um mesmo ativo"
            )
        evaluated, errors = _evaluate([combined_record(records)], body, False, simulate=True)
        return clean({**evaluated[0], "group": group, "errors": errors})

    return router
