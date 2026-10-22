"""Rotas da aba Carteira. Nenhuma rota envia ordens: só registra e avalia estruturas."""

from __future__ import annotations

import datetime as dt
import logging
import time
from collections.abc import Callable
from typing import Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from travas.alerts.service import StopAlerts
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
from travas.tracking.export import legs_csv, structures_csv
from travas.tracking.models import ExitIn, PositionIn
from travas.tracking.report import closed_report, portfolio_totals
from travas.tracking.store import TrackingStore

log = logging.getLogger(__name__)
QUOTES_REUSE_SECONDS = 120


class StopAlertIn(BaseModel):
    enabled: bool


class EvaluateIn(BaseModel):
    vol_override: float | None = Field(default=None, gt=0)
    rate_annual: float | None = None


def tracking_router(
    settings: Settings,
    service: MarketDataService,
    store: TrackingStore,
    clean: Callable,
    alerts: StopAlerts | None = None,
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

    def _alert_state(evaluated: list[dict]) -> None:
        """Alertas de stop: lista vigiada + envio se o ativo alcançou o stop (só com o mercado
        aberto e cotações recebidas agora); marca no resultado o que já foi enviado."""
        if alerts is None:
            return
        alerts.process(evaluated, service.market().is_open)
        for e in evaluated:
            armed = (e.get("stop_alert") or {}).get("armed_at")
            e["stop_alert_sent"] = alerts.sent_info(e["id"], armed) if armed else None

    @router.put("/positions/{position_id}/stop-alert")
    def stop_alert(position_id: str, body: StopAlertIn) -> dict:
        """Checkbox do alerta de stop 1:1. Marcar de novo rearma (novo alerta possível)."""
        record = store.get(position_id)
        if record is None:
            raise HTTPException(404, "estrutura não encontrada")
        now = pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(timespec="seconds")
        flag = {"enabled": body.enabled, "armed_at": now if body.enabled else None}
        record = store.update(position_id, {"stop_alert": flag})
        if body.enabled and alerts is not None:  # já monta a tabela do stop para o servidor
            evaluated, _ = _evaluate([record], EvaluateIn(), fresh=False)
            _alert_state(evaluated)
        return clean(record)

    @router.post("/evaluate")
    def evaluate(body: EvaluateIn) -> dict:
        evaluated, errors = _evaluate(store.list(), body, fresh=True)
        _alert_state(evaluated)
        market = service.market()
        legs = [leg for e in evaluated if e["status"] == "aberta" for leg in e["legs"]]
        captured = [
            leg["captured_at"]
            for leg in legs
            if leg.get("source") == "ultimo_pregao" and leg.get("captured_at")
        ]
        outside = sorted({leg["symbol"] for leg in legs if leg.get("source") == "mt5_fora_pregao"})
        closing = any(leg.get("source") == "fechamento_b3" for leg in legs)
        snapshot = [
            leg["captured_at"]
            for leg in legs
            if leg.get("source") == "snapshot_servidor" and leg.get("captured_at")
        ]
        quotes_note = None
        if not market.is_open:
            parts = [market.label]
            if closing:
                parts.append(
                    "pernas pelo fechamento oficial da B3 (último negócio do pregão, indicativo, "
                    "sem bid/ask)"
                )
            if snapshot:
                when = min(snapshot)[:16].replace("T", " ")
                parts.append(
                    f"pernas pelo snapshot do servidor de {when} (bid/ask daquele horário)"
                )
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
                "totals": portfolio_totals(evaluated),
                "errors": errors,
            }
        )

    @router.get("/report")
    def report(
        start: dt.date | None = None, end: dt.date | None = None, group: str | None = None
    ) -> dict:
        """Relatório das encerradas: só usa os registros (P&L realizado), sem consultar o MT5."""
        closed = [r for r in store.list() if r.get("status") == "encerrada"]
        evaluated, errors = _evaluate(closed, EvaluateIn(), fresh=False)
        return clean({**closed_report(evaluated, start, end, group or None), "errors": errors})

    @router.get("/export.csv")
    def export_csv(
        scope: Literal["todas", "abertas", "encerradas"] = "todas",
        detail: Literal["estruturas", "pernas"] = "estruturas",
        start: dt.date | None = None,
        end: dt.date | None = None,
    ) -> Response:
        records = store.list()
        if scope == "abertas":
            records = [r for r in records if r.get("status") == "aberta"]
        elif scope == "encerradas":
            records = [r for r in records if r.get("status") == "encerrada"]
        if start or end:

            def in_period(r: dict) -> bool:
                if r.get("status") != "encerrada":
                    return True
                when = (r.get("exit") or {}).get("exit_date") or ""
                return (not start or when >= start.isoformat()) and (
                    not end or when <= end.isoformat()
                )

            records = [r for r in records if in_period(r)]
        # Abertas: P&L com as cotações do MT5 (cache de até 2 min); sem cotação, campo vazio.
        evaluated, _ = _evaluate(records, EvaluateIn(), fresh=False)
        text = structures_csv(evaluated) if detail == "estruturas" else legs_csv(evaluated)
        stamp = pd.Timestamp.now(tz=LOCAL_TIMEZONE).strftime("%Y%m%d_%H%M")
        name = f"carteira_{detail}_{scope}_{stamp}.csv"
        return Response(
            content=text.encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
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
