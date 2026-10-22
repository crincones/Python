"""Rotas da aba "Liquidez de Opções": ranking dos ativos pela liquidez das opções, indicador
IV/HV (opções baratas ou caras) e CSV."""

from __future__ import annotations

import logging
import time

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import Response

from travas.data.options_liquidity import (
    MAX_SESSIONS,
    SORT_KEYS,
    OptionsLiquidity,
    book_quality,
    csv_filename,
    ranking_csv,
    sort_rows,
)
from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.options.vol_premium import atm_iv_table, monthly_listings, vol_premium
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)

CACHE_SECONDS = 30 * 60
VOL_CACHE_SECONDS = 15 * 60
EMPTY_BOOK = {"book_series": None, "book_with_quotes": None, "book_spread": None}


def liquidity_router(
    settings: Settings, service: MarketDataService, liquidity: OptionsLiquidity, clean
) -> APIRouter:
    router = APIRouter(prefix="/api/liquidity")
    cache: dict[tuple, tuple[float, dict]] = {}
    vol_cache: dict[tuple, tuple[float, dict]] = {}
    min_mid = settings.liquidity.min_mid_price_brl
    rate = settings.pricing.risk_free_rate_annual

    def _closes(tickers: list[str]) -> tuple[dict[str, pd.Series], str | None]:
        """Fechamentos diários (só barras fechadas) para a vol histórica."""
        try:
            daily, _ = service.daily_set(tickers)
        except MarketDataUnavailable as exc:
            return {}, f"sem candles diários do MT5 para a vol histórica ({exc})"
        out = {}
        for ticker, (bars, _info) in daily.items():
            closed = bars[~bars["forming"]] if "forming" in bars else bars
            out[ticker] = closed["close"].astype("float64").reset_index(drop=True)
        return out, None

    def _vol(snap, books: dict[str, dict]) -> dict[str, dict]:
        """IV/HV por ativo do snapshot (cache de 15 min por snapshot)."""
        key = (snap.day, snap.slot)
        hit = vol_cache.get(key)
        if hit and time.monotonic() - hit[0] <= VOL_CACHE_SECONDS:
            return hit[1]
        try:
            atm = atm_iv_table(snap.frame, rate, settings.pricing, service.calendar)
            listed = monthly_listings(snap.frame, service.calendar)
            closes, problem = _closes(sorted(listed["underlying"].unique()))
            result = vol_premium(atm, listed, closes, books, settings.vol_premium, problem)
        except Exception:  # o indicador é acessório: a tabela continua sem ele
            log.exception("IV/HV da liquidez não calculado")
            return {}
        vol_cache.clear()
        vol_cache[key] = (time.monotonic(), result)
        return result

    def _mt5_underlyings() -> set[str] | None:
        """Ativos com opções no MT5 da conta logada (None se o MT5 não estiver conectado)."""
        try:
            catalog = service.catalog()
        except MarketDataUnavailable:
            return None
        return set(catalog["underlying"])

    def _result(sessions: int) -> dict:
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        key = (today, sessions)
        hit = cache.get(key)
        if hit and time.monotonic() - hit[0] <= CACHE_SECONDS:
            result = hit[1]
        else:
            result = liquidity.ranking(today, sessions)
            cache.clear()
            cache[key] = (time.monotonic(), result)
        mt5 = _mt5_underlyings()
        snap = service.latest_snapshot()
        book = book_quality(snap.frame, min_mid) if snap is not None else {}
        vol = _vol(snap, book) if snap is not None else {}
        no_vol = {
            "ivhv": None,
            "ivhv_label": None,
            "ivhv_expiration": None,
            "ivhv_weak": None,
            "ivhv_items": [],
            "ivhv_reason": "ativo fora do snapshot do servidor"
            if snap is not None
            else "snapshot do servidor indisponível",
        }
        rows = [
            {
                **r,
                "has_mt5_options": None if mt5 is None else r["underlying"] in mt5,
                **book.get(r["underlying"], EMPTY_BOOK),
                **vol.get(r["underlying"], no_vol),
            }
            for r in result["rows"]
        ]
        return {
            **result,
            "rows": rows,
            "mt5_checked": mt5 is not None,
            "book_source": snap.label if snap is not None else None,
            "book_band": 0.10,
            "vol_premium": {
                **settings.vol_premium.model_dump(),
                "method": (
                    "IV ATM (Black-Scholes europeu sobre o mid do snapshot, média call/put do "
                    "strike mais próximo do spot, spread ≤ "
                    f"{settings.pricing.atm_max_spread_pct_mid:.0%}) dividida pela vol "
                    "histórica (log-retornos diários × √252, janela = pregões até o vencimento, "
                    f"mínimo {settings.vol_premium.min_hv_window})."
                ),
            },
        }

    def _rows(result: dict, top: int, sort: str, desc: bool | None) -> list[dict]:
        ordered = sort_rows(result["rows"], sort, desc)
        return ordered[:top] if top else ordered

    @router.get("/progress")
    def progress() -> dict:
        return liquidity.progress()

    @router.get("")
    def ranking(
        sessions: int = Query(5, ge=1, le=MAX_SESSIONS),
        top: int = Query(20, ge=0),
        sort: str = Query("rank", pattern="|".join(SORT_KEYS)),
        desc: bool | None = None,
    ) -> dict:
        result = _result(sessions)
        rows = _rows(result, top, sort, desc)
        return clean({**result, "rows": rows, "total": len(result["rows"]), "top": top})

    @router.get(".csv")
    def ranking_file(
        sessions: int = Query(5, ge=1, le=MAX_SESSIONS),
        top: int = Query(20, ge=0),
        sort: str = Query("rank", pattern="|".join(SORT_KEYS)),
        desc: bool | None = None,
    ) -> Response:
        result = _result(sessions)
        rows = _rows(result, top, sort, desc)
        return Response(
            content=ranking_csv(result, rows).encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{csv_filename(result, top)}"'},
        )

    return router
