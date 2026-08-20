"""
Etapa 03 — monta o dataset processado (features + lags + targets).

Separacao explicita exigida pela secao 3 do CLAUDE.md:
    FEATURES  -> colunas listadas em features.ALL_ENGINEERED + lags
    TARGET    -> colunas y_*, y3_*, fwd_*
    META      -> Date, BarIndex, OHLC cru, flags de diagnostico
"""
from __future__ import annotations

import json

import pandas as pd

import features as F
import targets as T
from config import (DATA_PROCESSED, DEFAULT_LAGS, MA_PERIOD, REPORTS_DIR,
                    RESULTS_DIR)
from load_data import load_chronological
from validate_data import validate, write_report

META_COLS = [
    "Date", "BarIndex", "FileOrder", "Open", "High", "Low", "Close",
    "AggBuy", "AggSell", "Duration", "Quantity", "Trades",
    "IsSyntheticBrick", "IsSessionFirstBar", "Session",
]


def build(n_lags: int = DEFAULT_LAGS, ma_period: int = MA_PERIOD,
          write: bool = True) -> pd.DataFrame:
    raw = load_chronological()

    # ---- exclusao explicita e registrada: ultima barra incompleta -------
    body_abs = (raw["Close"] - raw["Open"]).abs()
    brick = body_abs.mode().iloc[0]
    partial = body_abs != brick
    excluded = raw.loc[partial, ["BarIndex", "Date"]].copy()
    excluded["reason"] = f"|Close-Open| != brick ({brick})"
    if partial.any():
        raw = raw.loc[~partial].reset_index(drop=True)
        raw["BarIndex"] = range(len(raw))

    rep = validate(raw)
    rep["detected_brick_size"] = float(brick)
    rep["explicit_exclusions"] = [
        {"BarIndex": int(r.BarIndex), "Date": str(r.Date), "reason": r.reason}
        for r in excluded.itertuples()
    ]
    if write:
        write_report(rep)

    f = F.build_features(raw, ma_period=ma_period)
    f = F.add_prev_comparisons(f)
    f = F.add_lags(f, n_lags=n_lags)
    y = T.build_all_targets(raw)
    exc = T.forward_excursions(raw, horizon=12)

    ds = pd.concat([f, y, exc], axis=1)
    ds["Session"] = ds["Date"].dt.normalize()

    if write:
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        ds.to_parquet(DATA_PROCESSED / "dataset.parquet", index=False)
        manifest = {
            "n_rows": len(ds),
            "n_lags": n_lags,
            "ma_period": ma_period,
            "brick_size": float(brick),
            "date_min": str(ds["Date"].min()),
            "date_max": str(ds["Date"].max()),
            "feature_columns_contemporaneous": F.ALL_ENGINEERED,
            "prev_comparison_columns": F.prev_comparison_names(),
            "lag_columns": F.lag_names(n_lags=n_lags),
            "target_columns": [c for c in ds.columns
                               if c.startswith(T.TARGET_PREFIXES)],
            "meta_columns": META_COLS,
            "excluded_rows": rep["explicit_exclusions"],
        }
        (RESULTS_DIR / "03_dataset_manifest.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return ds


def load_dataset() -> pd.DataFrame:
    return pd.read_parquet(DATA_PROCESSED / "dataset.parquet")


def split_columns(ds: pd.DataFrame) -> dict:
    """Classifica colunas em FEATURES / TARGET / META (guarda-corpo)."""
    tgt = [c for c in ds.columns if c.startswith(T.TARGET_PREFIXES)]
    meta = [c for c in META_COLS if c in ds.columns]
    feat = [c for c in ds.columns if c not in tgt and c not in meta]
    return {"features": feat, "targets": tgt, "meta": meta}


if __name__ == "__main__":
    ds = build()
    cols = split_columns(ds)
    print(f"dataset: {ds.shape[0]} linhas x {ds.shape[1]} colunas")
    print(f"  features candidatas : {len(cols['features'])}")
    print(f"  targets             : {len(cols['targets'])}")
    print(f"  meta                : {len(cols['meta'])}")
    print(f"salvo em {DATA_PROCESSED / 'dataset.parquet'}")
