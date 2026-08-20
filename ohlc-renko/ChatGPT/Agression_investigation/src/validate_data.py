"""
Relatorio de integridade dos dados (secao 2 do CLAUDE.md).

Nada e removido silenciosamente. Toda exclusao proposta e registrada
no relatorio e aplicada apenas por ``apply_exclusions`` de forma explicita.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import BRICK_SIZE, REPORTS_DIR, RESULTS_DIR


def validate(df: pd.DataFrame) -> dict:
    """Produz o dicionario de diagnostico da base em ordem cronologica."""
    n = len(df)
    d = df["Date"]
    rng = df["High"] - df["Low"]
    body = df["Close"] - df["Open"]
    agg_total = df["AggBuy"] + df["AggSell"]

    dt = d.diff().dt.total_seconds()

    rep: dict = {}
    rep["n_rows"] = n
    rep["encoding"] = df.attrs.get("encoding")
    rep["source"] = df.attrs.get("source")
    rep["file_was_reversed"] = df.attrs.get("file_was_reversed")
    rep["steps_forward_in_file"] = df.attrs.get("steps_forward_in_file")
    rep["steps_backward_in_file"] = df.attrs.get("steps_backward_in_file")

    rep["date_min"] = str(d.min())
    rep["date_max"] = str(d.max())
    rep["n_days"] = int(d.dt.normalize().nunique())

    rep["n_unparsed_dates"] = int(d.isna().sum())
    rep["n_duplicate_timestamps"] = int(d.duplicated(keep=False).sum())
    rep["n_distinct_timestamps"] = int(d.nunique())
    rep["n_out_of_order_after_sort"] = int((dt < 0).sum())
    rep["n_zero_delta_t"] = int((dt == 0).sum())

    rep["nulls_per_column"] = {
        c: int(df[c].isna().sum())
        for c in ("Date", "Open", "High", "Low", "Close", "AggBuy",
                  "AggSell", "Duration", "Quantity", "Trades")
    }

    # --- valores impossiveis -------------------------------------------
    rep["n_high_lt_low"] = int((df["High"] < df["Low"]).sum())
    rep["n_open_outside_hl"] = int(
        ((df["Open"] > df["High"]) | (df["Open"] < df["Low"])).sum()
    )
    rep["n_close_outside_hl"] = int(
        ((df["Close"] > df["High"]) | (df["Close"] < df["Low"])).sum()
    )
    rep["n_negative_agg_buy"] = int((df["AggBuy"] < 0).sum())
    rep["n_negative_agg_sell"] = int((df["AggSell"] < 0).sum())
    rep["n_negative_duration"] = int((df["Duration"] < 0).sum())
    rep["n_negative_quantity"] = int((df["Quantity"] < 0).sum())
    rep["n_negative_trades"] = int((df["Trades"] < 0).sum())

    # --- degeneracoes ---------------------------------------------------
    rep["n_zero_range"] = int((rng == 0).sum())
    rep["n_zero_body"] = int((body == 0).sum())
    rep["n_zero_duration"] = int((df["Duration"] == 0).sum())
    rep["n_zero_agg_total"] = int((agg_total == 0).sum())
    rep["n_zero_agg_buy"] = int((df["AggBuy"] == 0).sum())
    rep["n_zero_agg_sell"] = int((df["AggSell"] == 0).sum())
    rep["n_zero_quantity"] = int((df["Quantity"] == 0).sum())
    rep["n_zero_trades"] = int((df["Trades"] == 0).sum())

    # --- coerencia Renko ------------------------------------------------
    rep["brick_size_nominal"] = BRICK_SIZE
    rep["body_abs_stats"] = _stats(body.abs())
    rep["range_stats"] = _stats(rng)
    rep["body_abs_value_counts_top"] = {
        str(k): int(v) for k, v in body.abs().value_counts().head(10).items()
    }
    rep["n_body_equal_brick"] = int((body.abs() == BRICK_SIZE).sum())
    rep["n_body_gt_brick"] = int((body.abs() > BRICK_SIZE).sum())
    rep["n_body_lt_brick"] = int((body.abs() < BRICK_SIZE).sum())

    # continuidade entre barras: em Renko puro Open[t] deveria colar em
    # Close[t-1] (ou distar exatamente 1 brick nas viradas).
    open_gap = (df["Open"] - df["Close"].shift(1)).dropna()
    rep["open_vs_prev_close_value_counts_top"] = {
        str(k): int(v) for k, v in open_gap.value_counts().head(10).items()
    }
    rep["n_open_ne_prev_close"] = int((open_gap != 0).sum())

    # --- gaps temporais ---------------------------------------------------
    rep["delta_t_seconds_stats"] = _stats(dt.dropna())
    same_day = d.dt.normalize().diff().dt.days.fillna(0) == 0
    intraday_dt = dt.where(same_day)
    rep["n_intraday_gaps_gt_1h"] = int((intraday_dt > 3600).sum())
    rep["n_session_breaks"] = int((~same_day).sum() - 1)

    # --- duracao vs delta de timestamp -----------------------------------
    # BarDurationF deve ser consistente com o tempo decorrido.
    rep["duration_stats"] = _stats(df["Duration"])
    corr = np.corrcoef(
        df["Duration"].iloc[1:].to_numpy(float),
        np.nan_to_num(dt.iloc[1:].to_numpy(float), nan=0.0),
    )[0, 1]
    rep["corr_duration_vs_delta_t"] = float(corr)

    # --- exclusoes propostas (registradas, nao aplicadas aqui) ----------
    bad = (
        df["Date"].isna()
        | df[["Open", "High", "Low", "Close"]].isna().any(axis=1)
        | (df["High"] < df["Low"])
        | (df["AggBuy"] < 0) | (df["AggSell"] < 0)
        | (df["Quantity"] < 0) | (df["Trades"] < 0)
        | (df["Duration"] < 0)
    )
    rep["n_rows_flagged_for_exclusion"] = int(bad.sum())
    rep["excluded_bar_indexes"] = df.loc[bad, "BarIndex"].tolist()[:200]

    return rep


def _stats(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) == 0:
        return {}
    q = s.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return {
        "count": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p01": float(q.loc[0.01]), "p05": float(q.loc[0.05]),
        "p25": float(q.loc[0.25]), "p50": float(q.loc[0.5]),
        "p75": float(q.loc[0.75]), "p95": float(q.loc[0.95]),
        "p99": float(q.loc[0.99]),
        "max": float(s.max()),
    }


def apply_exclusions(df: pd.DataFrame, rep: dict) -> pd.DataFrame:
    """Remove APENAS as linhas explicitamente sinalizadas no relatorio."""
    if rep["n_rows_flagged_for_exclusion"] == 0:
        return df
    bad_idx = set(rep["excluded_bar_indexes"])
    out = df[~df["BarIndex"].isin(bad_idx)].reset_index(drop=True)
    out["BarIndex"] = range(len(out))
    out.attrs.update(df.attrs)
    return out


def write_report(rep: dict) -> None:
    (RESULTS_DIR / "01_data_validation.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = ["# 01 — Relatorio de validacao dos dados", ""]
    for k, v in rep.items():
        if isinstance(v, dict):
            lines.append(f"## {k}")
            lines.append("")
            lines.append("| chave | valor |")
            lines.append("|---|---|")
            for kk, vv in v.items():
                lines.append(f"| `{kk}` | {vv} |")
            lines.append("")
        elif isinstance(v, list):
            lines.append(f"- **{k}**: {len(v)} itens (ver JSON)")
        else:
            lines.append(f"- **{k}**: `{v}`")
    (REPORTS_DIR / "01_data_validation.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
