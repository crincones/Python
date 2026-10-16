"""API local (FastAPI) e arquivos da interface. Nenhuma rota envia ordens."""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from travas.api.heatmap_routes import heatmap_router
from travas.api.tracking_routes import tracking_router
from travas.data.icons import IconCache
from travas.data.market_data import ChainScope
from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.options.analysis import (
    AnalysisParams,
    PreparedChain,
    analyze_prepared,
    evaluate_pair,
    find_pair,
    prepare_chain,
    simulation_grid,
)
from travas.options.liquidity import LiquidityRules
from travas.options.models import Direction, Flow
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE
from travas.tracking.store import TrackingStore

log = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parents[1] / "web" / "static"
MAX_CONTEXTS = 8
ATM_MARGIN = 0.06  # a coleta sempre inclui strikes a ±6% do spot (IV ATM)


class LiquidityIn(BaseModel):
    max_spread_pct_mid: float | None = None
    min_mid_price_brl: float | None = None
    min_turnover_brl: float | None = None
    min_deals: int | None = None
    max_quote_age_seconds: float | None = None


class AnalyzeIn(BaseModel):
    underlying: str
    direction: Direction
    flow: Flow
    target_price: float | None = Field(default=None, gt=0)
    target_pct: float | None = None  # variação % esperada (usada se não houver preço-alvo)
    horizon_date: dt.date | None = None
    conservative_price: float | None = Field(default=None, gt=0)
    optimistic_price: float | None = Field(default=None, gt=0)
    expirations: list[dt.date] | None = None
    dte_min: int | None = Field(default=None, ge=0)
    dte_max: int | None = Field(default=None, gt=0)
    strike_min: float | None = None
    strike_max: float | None = None
    max_width: float | None = Field(default=None, gt=0)
    max_loss_total: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, gt=0)
    rate_annual: float | None = None
    vol_override: float | None = Field(default=None, gt=0)
    liquidity: LiquidityIn = LiquidityIn()
    weights: dict[str, float] | None = None
    include_illiquid: bool = False
    limit_aggressiveness: float | None = Field(default=None, ge=0, le=1)
    min_reward_risk: float | None = Field(default=None, gt=0)
    nobre_filter: bool = False
    nobre_target_required: bool = False
    nobre_max_cost_fraction: float = 0.25
    nobre_prefer_close: bool = True
    european_short: bool = False

    @field_validator("nobre_max_cost_fraction")
    @classmethod
    def _nobre_fraction(cls, v: float) -> float:
        # Só os tetos do método: 1/4 (padrão) ou 1/3 (mais permissivo).
        for allowed in (0.25, 1 / 3):
            if abs(v - allowed) < 1e-3:
                return allowed
        raise ValueError("teto do filtro Rafael Nobre deve ser 1/4 ou 1/3")

    costs_brl: float = Field(default=0.0, ge=0)
    refresh: bool = False


def clean(value: Any) -> Any:
    """JSON sem NaN/inf (viram null) e com datas em ISO."""
    if isinstance(value, float):
        # 10 casas eliminam ruído de ponto flutuante sem afetar preços (tick de R$ 0,01).
        return round(value, 10) if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [clean(v) for v in value]
    if isinstance(value, dt.date | pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):  # escalares numpy
        return clean(value.item())
    return value


def create_app(
    settings: Settings,
    service: MarketDataService | None = None,
    store: TrackingStore | None = None,
) -> FastAPI:
    service = service or MarketDataService(settings)
    store = store or TrackingStore(settings.paths.tracking_file)
    contexts: OrderedDict[str, tuple[PreparedChain, dict]] = OrderedDict()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        service.connect_in_background()
        yield
        service.close()

    app = FastAPI(title="Analisador de Travas B3", lifespan=lifespan)

    @app.middleware("http")
    async def _no_stale_assets(request, call_next):
        # Sem isso o Chrome pode reutilizar JS/CSS antigos depois de uma atualização do app.
        response = await call_next(request)
        path = request.url.path
        if path == "/" or (path.startswith("/static/") and "/vendor/" not in path):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.exception_handler(MarketDataUnavailable)
    async def _unavailable(_, exc: MarketDataUnavailable):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.get("/api/status")
    def status() -> dict:
        return clean(service.status())

    @app.get("/api/defaults")
    def defaults() -> dict:
        a = settings.analysis
        return clean(
            {
                "analysis": a.model_dump(),
                "liquidity": settings.liquidity.model_dump(),
                "rate_annual": settings.pricing.risk_free_rate_annual,
                "candles": settings.candles.model_dump(),
            }
        )

    @app.get("/api/underlyings")
    def underlyings() -> list[dict]:
        return clean(service.underlyings().to_dict(orient="records"))

    icons = IconCache(
        settings.paths.icons_dir,
        settings.icons.source_url,
        settings.icons.timeout_seconds,
        settings.icons.enabled,
    )

    @app.get("/api/icon/{ticker}")
    def icon(ticker: str) -> FileResponse:
        path = icons.path(ticker)
        if path is None:
            raise HTTPException(404, "sem ícone")
        return FileResponse(
            path, media_type="image/png", headers={"Cache-Control": "max-age=86400"}
        )

    @app.get("/api/options/{underlying}")
    def options(underlying: str) -> list[dict]:
        """Opções vigentes do ativo (catálogo real do MT5), para montar estruturas."""
        _require_mt5_options(service, underlying.upper())
        catalog = service.catalog()
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        rows = catalog[
            (catalog["underlying"] == underlying.upper()) & (catalog["expiration_date"] >= today)
        ].sort_values(["expiration_date", "option_type", "strike"])
        return clean(rows.to_dict(orient="records"))

    app.include_router(tracking_router(settings, service, store, clean))
    app.include_router(heatmap_router(settings, service, clean))

    @app.get("/api/quote/{underlying}")
    def quote(underlying: str) -> dict:
        return clean(service.quote(underlying.upper()).to_dict())

    @app.get("/api/candles/{underlying}")
    def candles(underlying: str, tf: Literal["d1", "w1", "h4"] = "d1") -> dict:
        bars, meta = service.candles(underlying.upper(), tf)
        records = [
            {
                "timestamp": int(row.time.timestamp() * 1000),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.real_volume,
                "ema_fast": row.ema_fast,
                "ema_slow": row.ema_slow,
                "forming": bool(row.forming),
            }
            for row in bars.itertuples()
        ]
        return clean({"meta": meta, "bars": records})

    @app.post("/api/analyze")
    def run_analysis(body: AnalyzeIn) -> dict:
        underlying = body.underlying.upper()
        _require_mt5_options(service, underlying)
        quote = service.quote(underlying)
        if quote.price is None:
            raise MarketDataUnavailable(f"{underlying} sem cotação no terminal")
        spot = quote.price
        params = _params(body, spot, settings)
        scope = _scope(params, spot, settings)
        chain, meta = service.chain(underlying, scope, force=body.refresh)
        if chain.empty:
            raise HTTPException(404, f"nenhuma opção de {underlying} encontrada no escopo")
        spot = (
            float(chain["underlying_price"].dropna().iloc[-1])
            if chain["underlying_price"].notna().any()
            else spot
        )
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        prep = prepare_chain(chain, spot, today, service.calendar, params)
        result = analyze_prepared(prep)
        analysis_id = uuid.uuid4().hex[:12]
        contexts[analysis_id] = (prep, meta)
        while len(contexts) > MAX_CONTEXTS:
            contexts.popitem(last=False)
        result.update(
            {
                "analysis_id": analysis_id,
                "underlying": underlying,
                "collection": meta,
                "target_price": params.target_price,
            }
        )
        return clean(result)

    @app.get("/api/detail/{analysis_id}/{pair_id}")
    def detail(analysis_id: str, pair_id: str) -> dict:
        if analysis_id not in contexts:
            raise HTTPException(404, "análise expirada; refaça a análise")
        prep, meta = contexts[analysis_id]
        long_symbol, _, short_symbol = pair_id.partition("|")
        try:
            long_row, short_row = find_pair(prep, long_symbol, short_symbol)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        row = evaluate_pair(prep, long_row, short_row)
        row["simulation"] = simulation_grid(prep, long_row, short_row)
        row["collection"] = meta
        row["spot"] = prep.spot
        row["target_price"] = prep.params.target_price
        return clean(row)

    @app.get("/api/preferences")
    def get_preferences() -> dict:
        path = settings.paths.preferences_file
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("Preferências corrompidas em %s; ignoradas", path)
            return {}

    @app.put("/api/preferences")
    def put_preferences(prefs: dict) -> dict:
        # Só preferências de interface/análise; nada de credenciais.
        text = json.dumps(prefs, ensure_ascii=False, indent=2)
        if len(text) > 100_000:
            raise HTTPException(413, "preferências grandes demais")
        settings.paths.preferences_file.write_text(text, encoding="utf-8")
        return {"ok": True}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _require_mt5_options(service: MarketDataService, underlying: str) -> None:
    """Ativo com opções na B3 mas sem elas no MT5 da corretora: explica em vez de "nada
    encontrado"."""
    u = service.underlyings().set_index("underlying")
    if underlying in u.index and not u.loc[underlying, "has_mt5_options"]:
        n = int(u.loc[underlying, "listed_series"])
        raise HTTPException(
            422,
            f"A {service.broker_name()} não disponibiliza no MT5 as opções de {underlying} "
            f"({n:,} séries listadas na "
            "B3). Sem cotações das opções não é possível analisar travas deste ativo.",
        )


def _params(body: AnalyzeIn, spot: float, settings: Settings) -> AnalysisParams:
    a = settings.analysis
    liq = settings.liquidity.model_dump()
    liq.update({k: v for k, v in body.liquidity.model_dump().items() if v is not None})
    weights = a.weights.model_dump()
    if body.weights:
        weights.update({k: max(0.0, float(v)) for k, v in body.weights.items() if k in weights})
        total = sum(weights.values())
        if total <= 0:
            raise HTTPException(422, "pelo menos um peso do ranking deve ser positivo")
        weights = {k: v / total for k, v in weights.items()}
    target = body.target_price
    if target is None and body.target_pct is not None:
        target = spot * (1 + body.target_pct / 100)
    scenarios = tuple(
        (name, price)
        for name, price in (
            ("conservador", body.conservative_price),
            ("otimista", body.optimistic_price),
        )
        if price
    )
    return AnalysisParams(
        direction=body.direction,
        flow=body.flow,
        quantity=body.quantity or a.quantity,
        rate_annual=body.rate_annual
        if body.rate_annual is not None
        else settings.pricing.risk_free_rate_annual,
        liquidity=LiquidityRules(**liq),
        weights=weights,
        pricing=settings.pricing,
        early_exercise=settings.early_exercise,
        dte_min=body.dte_min if body.dte_min is not None else a.dte_min_business_days,
        dte_max=body.dte_max or a.dte_max_business_days,
        expirations=tuple(body.expirations) if body.expirations else None,
        strike_min=body.strike_min,
        strike_max=body.strike_max,
        max_width=body.max_width or spot * a.max_width_pct_spot,
        max_loss_total=body.max_loss_total,
        target_price=target,
        horizon_date=body.horizon_date,
        scenarios=scenarios,
        vol_override=body.vol_override,
        include_illiquid=body.include_illiquid,
        illiquid_score_cap=a.illiquid_score_cap,
        limit_aggressiveness=(
            body.limit_aggressiveness
            if body.limit_aggressiveness is not None
            else a.limit_aggressiveness
        ),
        min_reward_risk=body.min_reward_risk,
        nobre_filter=body.nobre_filter,
        nobre_target_required=body.nobre_target_required,
        nobre_max_cost_fraction=body.nobre_max_cost_fraction,
        nobre_prefer_close=body.nobre_prefer_close,
        european_short=body.european_short,
        costs_brl=body.costs_brl,
        max_results=a.max_results,
    )


def _scope(params: AnalysisParams, spot: float, settings: Settings) -> ChainScope:
    pct = settings.collection.strike_range_pct_spot
    low = params.strike_min if params.strike_min is not None else spot * (1 - pct)
    high = params.strike_max if params.strike_max is not None else spot * (1 + pct)
    low, high = min(low, spot * (1 - ATM_MARGIN)), max(high, spot * (1 + ATM_MARGIN))
    # Arredonda para reaproveitar o cache entre análises com spot quase igual.
    return ChainScope(
        (params.kind.option_type.value,),
        params.dte_max,
        math.floor(low * 2) / 2,
        math.ceil(high * 2) / 2,
    )
