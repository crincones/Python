"""Relatório de viabilidade dos dados: o que o terminal MT5 realmente entrega (comando `check`)."""

from __future__ import annotations

import pandas as pd

from travas.data.mt5_client import MT5Error
from travas.data.service import MarketDataService, MarketDataUnavailable
from travas.timeutils import LOCAL_TIMEZONE

# Campos da cadeia normalizada cuja presença é auditada (NaN = ausente).
AUDITED = {
    "bid": "bid",
    "ask": "ask",
    "last": "último",
    "mid": "mid (bid e ask válidos)",
    "quote_time": "horário do último tick",
    "vwap": "preço médio da sessão",
    "open_interest": "open interest",
}


def _pct(series: pd.Series) -> str:
    return f"{series.notna().mean():.0%}" if len(series) else "—"


def build_report(service: MarketDataService, underlying: str) -> str:
    now = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
    status = service.status()
    lines = [
        "# Relatório de viabilidade dos dados (MT5)",
        "",
        f"Gerado em {now:%d/%m/%Y %H:%M:%S} (America/Sao_Paulo) pelo comando `travas check`.",
        "",
        "## Terminal",
        "",
        f"- Estado: {status['phase']}; servidor conectado: {status['server_connected']}",
        f"- Build: {status['terminal'].get('build')}; servidor: {status['terminal'].get('server')}"
        f"; corretora: {status['terminal'].get('company')}",
        f"- Hoje é pregão (calendário local): {status['is_session_today']}",
        "",
    ]
    catalog = service.catalog()
    underlyings = service.underlyings()
    lines += [
        "## Catálogo de opções",
        "",
        f"- Opções listadas (option_strike > 0): {len(catalog):,}".replace(",", "."),
        f"- Ativos-objeto com opções vigentes: {len(underlyings)}",
        "- Tipos: "
        + ", ".join(
            f"{k}: {v:,}".replace(",", ".")
            for k, v in catalog["option_type"].value_counts().items()
        ),
        "- Estilo: "
        + ", ".join(
            f"{t}/{e}: {v:,}".replace(",", ".")
            for (t, e), v in catalog.groupby(["option_type", "exercise_style"]).size().items()
        ),
        "- Maiores ativos (séries vigentes): "
        + ", ".join(
            f"{r.underlying} ({r.listed_series})" for r in underlyings.head(15).itertuples()
        ),
        "",
    ]

    lines += [f"## Cadeia de {underlying}", ""]
    try:
        chain, meta = service.chain(underlying, force=True)
    except MarketDataUnavailable as exc:
        lines += [f"Falha na coleta: {exc}", ""]
        return "\n".join(lines)
    u = meta["underlying"]
    lines += [
        f"- Spot {u['price']} (bid {u['bid']}, ask {u['ask']}, último {u['last']}), "
        f"tick {u['quote_time']}; relógio do PC − tick: {u['pc_lag_seconds']:.0f} s"
        if u["pc_lag_seconds"] is not None
        else f"- Spot {u['price']}, sem horário de tick",
        f"- Aviso de tempo real: {meta['realtime_warning'] or 'nenhum'}",
        f"- Séries coletadas: {meta['series']} em {meta['duration_seconds']} s; "
        f"com book (bid e ask): {meta['series_with_book']}",
        f"- Vencimentos: {', '.join(str(d) for d in sorted(chain['expiration_date'].unique()))}",
        f"- contract_size distintos: {sorted(chain['contract_size'].unique().tolist())}; "
        f"tick_size: {sorted(chain['tick_size'].unique().tolist())}",
        f"- Idade da cotação (s, contra o tick mais recente do lote): mediana "
        f"{chain['quote_age_seconds'].median():.0f}, "
        f"p90 {chain['quote_age_seconds'].quantile(0.9):.0f}",
        f"- Séries com session_deals > 0: {int((chain['deals'] > 0).sum())} "
        f"(tick de hoje: {int((chain['quote_time'].dt.date == now.date()).sum())})",
        "",
        "| Campo | Preenchido |",
        "|---|---|",
        *(f"| {label} | {_pct(chain[col])} |" for col, label in AUDITED.items()),
        "",
    ]

    lines += [
        "## Candles do ativo-objeto",
        "",
        "| Timeframe | Barras | Primeira | Última | Em formação |",
        "|---|---|---|---|---|",
    ]
    for tf in ("d1", "w1", "h4"):
        try:
            bars, bmeta = service.candles(underlying, tf)
        except (MarketDataUnavailable, MT5Error) as exc:
            lines.append(f"| {tf} | falha: {exc} | | | |")
            continue
        if bars.empty:
            lines.append(f"| {tf} | 0 | | | |")
            continue
        lines.append(
            f"| {tf} | {len(bars)} | {bars['time'].iloc[0]:%d/%m/%Y %H:%M} | "
            f"{bars['time'].iloc[-1]:%d/%m/%Y %H:%M} | {bmeta['last_bar_forming']} |"
        )
        if tf == "h4":
            hours = sorted(bars["time"].dt.strftime("%H:%M").unique().tolist())
            lines.append(f"| h4: horários de abertura das barras | {', '.join(hours)} | | | |")
    lines.append("")
    return "\n".join(lines)
