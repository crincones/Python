"""Relatório HTML estático: arquivo único, CSS/JS inline, Plotly embutido uma vez, offline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.offline
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from screener.data import store
from screener.data.schema import (
    ANALYSIS_META_FILE,
    BIAS_TABLE,
    SPREADS_TABLE,
    UNDERLYINGS_TABLE,
)
from screener.spreads.builder import BEAR_PUT, BULL_CALL

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "relatorio.html.j2"
REPORT_NAME_FORMAT = "relatorio_%Y%m%d_%H%M.html"

# Colunas das travas enviadas ao navegador (tabelas, detalhe e payoff).
SPREAD_FIELDS = [
    "underlying",
    "strategy",
    "direction",
    "expiration_date",
    "dte_business_days",
    "spot",
    "long_symbol",
    "short_symbol",
    "long_strike",
    "short_strike",
    "long_exercise_style",
    "short_exercise_style",
    "long_bid",
    "long_ask",
    "long_mid",
    "short_bid",
    "short_ask",
    "short_mid",
    "long_iv",
    "short_iv",
    "atm_iv",
    "width",
    "debit",
    "debit_mid",
    "execution_cost_pct_width",
    "debit_to_width",
    "reward_risk",
    "breakeven",
    "breakeven_distance_pct",
    "breakeven_distance_sigma",
    "pop",
    "debit_per_lot",
    "max_gain_per_lot",
    "max_loss_per_lot",
    "long_liquidity_score",
    "short_liquidity_score",
    "liquidity_score",
    "worst_spread_pct_mid",
    "min_turnover_brl",
    "min_deals",
    "short_extrinsic",
    "early_exercise_alert",
    "early_exercise_reason",
    "score",
    "bias",
    "bias_source",
    "ranked",
    "rank",
]
BIAS_FIELDS = [
    "underlying",
    "bias",
    "bias_source",
    "auto_bias",
    "manual_bias",
    "d1_trend",
    "h4_trend",
]


def _clean(value: Any) -> Any:
    """Converte para tipos JSON: NaN/NaT/NA → null, datas → ISO, numpy → Python."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _records(frame: pd.DataFrame, fields: list[str]) -> list[dict[str, Any]]:
    present = [f for f in fields if f in frame.columns]
    return [{k: _clean(v) for k, v in row.items()} for row in frame[present].to_dict("records")]


def build_report_data(
    spreads: pd.DataFrame,
    bias: pd.DataFrame,
    underlyings: pd.DataFrame,
    analysis_meta: dict[str, Any],
    snapshot_time: pd.Timestamp,
) -> dict[str, Any]:
    """Dados do relatório. Envia só travas dentro da faixa de POP (ranqueadas e, para consulta,
    as que não batem com o viés)."""
    in_band = spreads[spreads["in_pop_band"]].copy()
    in_band["expiration_date"] = pd.to_datetime(in_band["expiration_date"]).dt.strftime("%Y-%m-%d")
    in_band = in_band.sort_values(["strategy", "ranked", "score"], ascending=[True, False, False])

    spots = underlyings.loc[underlyings["passed_filter"], ["underlying", "price", "quote_time"]]
    bias_view = bias.reindex(columns=BIAS_FIELDS).merge(spots, on="underlying", how="left")

    settings = analysis_meta.get("settings", {})
    return {
        "snapshot": analysis_meta.get("snapshot"),
        "snapshot_time": _clean(snapshot_time),
        "analyzed_at": analysis_meta.get("analyzed_at"),
        "risk_free_rate_annual": analysis_meta.get("risk_free_rate_annual"),
        "risk_free_rate": analysis_meta.get("risk_free_rate"),
        "lot_size": settings.get("spreads", {}).get("lot_size"),
        "pop_band": [
            settings.get("scoring", {}).get("pop_min"),
            settings.get("scoring", {}).get("pop_max"),
        ],
        "score_weights": settings.get("scoring", {}).get("weights", {}),
        "signals": settings.get("signals", {}),
        "counts": {
            "series_total": analysis_meta.get("series_total"),
            "series_eligible": analysis_meta.get("series_eligible"),
            "spreads_valid": analysis_meta.get("spreads_valid"),
            "spreads_in_pop_band": analysis_meta.get("spreads_in_pop_band"),
            "ranked": {
                strategy: int(((spreads["strategy"] == strategy) & spreads["ranked"]).sum())
                for strategy in (BULL_CALL, BEAR_PUT)
            },
        },
        "bias": _records(bias_view, [*BIAS_FIELDS, "price", "quote_time"]),
        "spreads": _records(in_band, SPREAD_FIELDS),
    }


def to_script_json(data: dict[str, Any]) -> str:
    """JSON seguro para <script>: sem NaN e sem fechar a tag por acidente."""
    return json.dumps(data, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")


def render_html(data: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(TEMPLATE_NAME)
    return template.render(
        data_json=to_script_json(data),
        plotly_js=plotly.offline.get_plotlyjs(),
    )


def report_path(snapshot: Path, output_dir: Path) -> Path:
    """Caminho do relatório do snapshot (nome = horário do snapshot), gerado ou não."""
    snapshot_time = pd.Timestamp(store.read_meta(snapshot)["snapshot_time"])
    return output_dir / snapshot_time.strftime(REPORT_NAME_FORMAT)


def write_report(snapshot: Path, output_dir: Path) -> Path:
    """Gera o relatório de um snapshot já analisado. Nome do arquivo = horário do snapshot."""
    spreads = store.read_table(snapshot, SPREADS_TABLE)
    bias = store.read_table(snapshot, BIAS_TABLE)
    underlyings = store.read_table(snapshot, UNDERLYINGS_TABLE)
    meta = store.read_meta(snapshot, ANALYSIS_META_FILE)
    snapshot_time = pd.Timestamp(store.read_meta(snapshot)["snapshot_time"])
    data = build_report_data(spreads, bias, underlyings, meta, snapshot_time)

    output_dir.mkdir(parents=True, exist_ok=True)
    target = report_path(snapshot, output_dir)
    temporary = target.with_name(target.name + ".partial")
    temporary.write_text(render_html(data), encoding="utf-8")
    temporary.replace(target)
    return target
