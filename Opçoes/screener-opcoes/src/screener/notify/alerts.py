"""Seleção das travas com score alto e montagem do aviso para o Telegram.

Uma mensagem de resumo (ou "nenhuma trava acima do limite") e, para as melhores, uma foto do
payoff com a legenda da trava. Para não repetir variações da mesma trava, agrupa como a visão
padrão do relatório: melhor por estratégia, ativo e vencimento.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from html import escape
from typing import Any

import pandas as pd

from screener.notify.format import brl, num, pct
from screener.notify.payoff_chart import payoff_png
from screener.notify.telegram import TelegramApi
from screener.settings import NotifySettings
from screener.spreads.builder import BEAR_PUT, BULL_CALL

log = logging.getLogger("screener")

GROUP_KEYS = ["strategy", "underlying", "expiration_date"]
STRATEGY_LABEL = {BULL_CALL: "Trava de alta", BEAR_PUT: "Trava de baixa"}
STRATEGY_ICON = {BULL_CALL: "🟢", BEAR_PUT: "🔴"}
STRATEGY_ORDER = [BULL_CALL, BEAR_PUT]
DATE_FORMAT = "%d/%m/%Y"
TEST_PREFIX = "🧪 <b>[TESTE]</b> "


@dataclass(frozen=True)
class Highlight:
    """Melhor trava de um grupo (estratégia, ativo, vencimento) acima do limite."""

    spread: dict[str, Any]
    variations: int  # outras travas do mesmo grupo também acima do limite


def select_highlights(spreads: pd.DataFrame, settings: NotifySettings) -> list[Highlight]:
    """Travas com score > min_score (só ranqueadas, se configurado), melhor por grupo."""
    mask = spreads["score"] > settings.min_score
    if settings.only_ranked:
        mask &= spreads["ranked"].fillna(False).astype(bool)
    hits = spreads[mask].sort_values("score", ascending=False)
    if not settings.best_per_group:
        return [Highlight(row, 0) for row in hits.to_dict("records")]
    sizes = hits.groupby(GROUP_KEYS).size()
    best = hits.drop_duplicates(GROUP_KEYS)
    return [
        Highlight(row, int(sizes[tuple(row[k] for k in GROUP_KEYS)]) - 1)
        for row in best.to_dict("records")
    ]


def _date(value: Any) -> str:
    return pd.Timestamp(value).strftime(DATE_FORMAT)


def spread_caption(h: Highlight, lot_size: int) -> str:
    """Legenda (HTML do Telegram, < 1024 caracteres) com os números principais da trava."""
    s = h.spread
    rank = f" · #{int(s['rank'])}" if pd.notna(s.get("rank")) else ""
    lines = [
        f"{STRATEGY_ICON[s['strategy']]} <b>{STRATEGY_LABEL[s['strategy']]} · "
        f"{escape(s['underlying'])}</b> · venc. {_date(s['expiration_date'])} "
        f"({int(s['dte_business_days'])} DU)",
        f"Compra <b>{escape(s['long_symbol'])}</b> (K {num(s['long_strike'])}) · "
        f"vende <b>{escape(s['short_symbol'])}</b> (K {num(s['short_strike'])})",
        f"Spot {num(s['spot'])} · largura {num(s['width'])}",
        f"Débito {num(s['debit'])} ({brl(s['debit_per_lot'])}/lote de {lot_size}) · "
        f"mid {num(s['debit_mid'])}",
        f"Ganho máx. {brl(s['max_gain_per_lot'])} · perda máx. {brl(s['max_loss_per_lot'])} · "
        f"R/R {num(s['reward_risk'])}",
        f"Breakeven {num(s['breakeven'])} ({pct(s['breakeven_distance_pct'], signed=True)} · "
        f"{num(s['breakeven_distance_sigma'])} σ) · POP {pct(s['pop'])}",
        f"IV compra/venda {pct(s['long_iv'])} / {pct(s['short_iv'])} · "
        f"liquidez {num(s['liquidity_score'])}",
        f"<b>Score {num(s['score'], 1)}</b>{rank} · viés {escape(str(s['bias']))} "
        f"({escape(str(s['bias_source']))})",
    ]
    if s.get("early_exercise_alert"):
        lines.append(f"⚠ Exercício antecipado: {escape(str(s['early_exercise_reason']))}")
    if h.variations:
        lines.append(f"+{h.variations} variação(ões) do mesmo vencimento também acima do limite")
    return "\n".join(lines)


def summary_message(
    highlights: list[Highlight],
    settings: NotifySettings,
    snapshot_time: pd.Timestamp,
    report_url: str | None,
    test: bool,
) -> str:
    """Resumo do snapshot: contagem por estratégia e lista curta, ou aviso de que não há."""
    limit = num(settings.min_score, 0)
    header = f"📊 <b>Screener de travas</b> · {snapshot_time.strftime('%d/%m/%Y %H:%M')}"
    lines = [(TEST_PREFIX if test else "") + header]
    if not highlights:
        lines.append(f"Nenhuma trava de alta ou de baixa com score acima de {limit}.")
    else:
        counts = {k: sum(h.spread["strategy"] == k for h in highlights) for k in STRATEGY_ORDER}
        lines.append(
            f"Travas com score acima de {limit} (melhor por ativo e vencimento): "
            f"alta {counts[BULL_CALL]} · baixa {counts[BEAR_PUT]}"
        )
        for h in highlights[: settings.max_listed]:
            s = h.spread
            lines.append(
                f"{STRATEGY_ICON[s['strategy']]} {escape(s['underlying'])} "
                f"{escape(s['long_symbol'])}/{escape(s['short_symbol'])} · "
                f"venc. {_date(s['expiration_date'])} · score {num(s['score'], 1)} · "
                f"POP {pct(s['pop'])} · R/R {num(s['reward_risk'])}"
            )
        hidden = len(highlights) - settings.max_listed
        if hidden > 0:
            lines.append(f"… e mais {hidden} no relatório")
    if report_url:
        lines.append(f'<a href="{escape(report_url)}">Relatório completo</a>')
    return "\n".join(lines)


def send_alerts(
    api: TelegramApi,
    spreads: pd.DataFrame,
    settings: NotifySettings,
    lot_size: int,
    snapshot_time: pd.Timestamp,
    report_url: str | None = None,
    test: bool = False,
) -> list[Highlight]:
    """Envia o resumo e as fotos de payoff das melhores travas. Devolve as selecionadas."""
    highlights = select_highlights(spreads, settings)
    api.send_message(summary_message(highlights, settings, snapshot_time, report_url, test))
    for h in highlights[: settings.max_charts]:
        s = h.spread
        title = (
            f"{STRATEGY_LABEL[s['strategy']]} {s['underlying']} "
            f"{s['long_symbol']}/{s['short_symbol']} · venc. {_date(s['expiration_date'])}"
        )
        api.send_photo(payoff_png(s, lot_size, title), spread_caption(h, lot_size))
    log.info(
        "Telegram: %d trava(s) com score > %s, %d gráfico(s) enviados",
        len(highlights),
        settings.min_score,
        min(len(highlights), settings.max_charts),
    )
    return highlights
