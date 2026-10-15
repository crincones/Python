"""Rotas da aba Heatmap: ativos com opções listadas, métricas, cadastro/eventos (B3) e vol."""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from fastapi import APIRouter, HTTPException

from travas.data.market_data import ChainScope
from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.heatmap.b3_company import B3Companies
from travas.heatmap.build import EXCLUDED, build_items
from travas.heatmap.metrics import compute
from travas.options import pricing
from travas.options.implied_vol import atm_implied_vol, options_implied_vol
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)
IV_MAX_DTE = 60  # vencimentos considerados na IV ATM (dias úteis)
IV_STRIKE_BAND = 0.06  # strikes coletados a ±6% do spot


def heatmap_router(settings: Settings, service: MarketDataService, clean: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/heatmap")
    b3 = B3Companies(settings.paths.quotes_dir.parent / "b3")

    def _tickers() -> list[str]:
        return [t for t in service.underlyings()["underlying"].tolist() if t not in EXCLUDED]

    @router.get("")
    def heatmap() -> dict:
        tickers = _tickers()
        daily, meta = service.daily_set(tickers)
        profiles = b3.prefetch(tickers)
        companies = [t for t in tickers if profiles.get(t, {}).get("is_company")]
        with ThreadPoolExecutor(max_workers=6) as pool:
            events = dict(zip(companies, pool.map(b3.events, companies), strict=True))
        shares = {t: e.get("total_shares") for t, e in events.items() if e.get("available")}
        items = build_items(daily, profiles, shares)
        b3_errors = sorted(t for t, p in profiles.items() if p.get("error"))
        return clean(
            {
                **meta,
                "items": items,
                "excluded": sorted(EXCLUDED),
                "b3_errors": b3_errors,
                "notes": [
                    "Variações em pregões (janela móvel): dia 1, semana 5, mês 21, ano 252.",
                    "Volume financeiro = quantidade × fechamento da barra diária; durante o "
                    "pregão o volume do dia é parcial.",
                    "Negócios: só os da sessão atual (o MT5 não fornece histórico de negócios).",
                    "Valor de mercado aproximado = preço deste ticker × total de ações (B3).",
                    "Setor: classificação setorial da B3.",
                ],
            }
        )

    @router.get("/{ticker}")
    def details(ticker: str) -> dict:
        ticker = ticker.upper()
        daily, meta = service.daily_set(_tickers())
        if ticker not in daily:
            raise HTTPException(404, f"{ticker} fora do universo com opções")
        bars, info = daily[ticker]
        metrics = compute(bars, info.get("session_deals"))
        profile = b3.profile(ticker)
        events = b3.events(ticker)
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date().isoformat()
        cap = (
            metrics["price"] * events["total_shares"]
            if events.get("available") and events.get("total_shares") and metrics.get("price")
            else None
        )
        if events.get("available"):
            last12 = (pd.Timestamp(today) - pd.DateOffset(years=1)).date().isoformat()
            paid12 = sum(
                e["value"] or 0
                for e in events["cash"]
                if e["ex_date"] and last12 < e["ex_date"] <= today
            )
            events["upcoming"] = [
                e for e in events["cash"] if e["ex_date"] and e["ex_date"] >= today
            ]
            events["sum_last12m"] = paid12
            events["yield_last12m"] = paid12 / metrics["price"] if metrics.get("price") else None
        return clean(
            {
                "ticker": ticker,
                "description": info.get("description"),
                "metrics": metrics,
                "profile": profile,
                "events": events,
                "market_cap_approx": cap,
                "collected_at": meta["collected_at"],
                "market": meta["market"],
                "mergers_note": (
                    "Fusões e aquisições não constam da API de empresas da B3; consulte os fatos "
                    "relevantes da companhia (RI/CVM)."
                ),
            }
        )

    @router.get("/{ticker}/iv")
    def implied_vol(ticker: str) -> dict:
        """IV ATM por vencimento (mesma metodologia da análise) contra a vol histórica."""
        ticker = ticker.upper()
        quote = service.quote(ticker)
        if quote.price is None:
            raise MarketDataUnavailable(f"{ticker} sem cotação")
        spot = quote.price
        scope = ChainScope(
            ("call", "put"), IV_MAX_DTE, spot * (1 - IV_STRIKE_BAND), spot * (1 + IV_STRIKE_BAND)
        )
        chain, meta = service.chain(ticker, scope)
        rate = settings.pricing.risk_free_rate_annual
        rows = []
        if not chain.empty:
            chain = chain.join(options_implied_vol(chain, rate, settings.pricing))
            atm = atm_implied_vol(chain, settings.pricing)
            dte = chain.groupby("expiration_date")["dte_business_days"].first()
            for r in atm.sort_values("expiration_date").itertuples():
                rows.append(
                    {
                        "expiration": r.expiration_date.isoformat(),
                        "dte_business_days": int(dte.get(r.expiration_date, 0)),
                        "atm_iv": float(r.atm_iv),
                    }
                )
        daily, _ = service.daily_set(_tickers())
        hv = compute(daily[ticker][0])["hv"] if ticker in daily else {}
        return clean(
            {
                "ticker": ticker,
                "spot": spot,
                "atm_iv": rows,
                "hv": hv,
                "rate_annual": rate,
                "rate_continuous": float(pricing.continuous_rate(rate)),
                "source": meta.get("source"),
                "warning": meta.get("realtime_warning"),
                "series": meta.get("series"),
                "method": (
                    "IV ATM: Black-Scholes europeu sobre o mid, média call/put do strike mais "
                    f"próximo do spot (spread ≤ {settings.pricing.atm_max_spread_pct_mid:.0%}, "
                    f"strike a até {settings.pricing.atm_max_strike_distance_pct:.0%}). "
                    "Vol histórica: log-retornos diários × √252."
                ),
            }
        )

    return router
