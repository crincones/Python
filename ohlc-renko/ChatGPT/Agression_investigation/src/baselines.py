"""
Etapa 05 — baselines e comparacao por grupo de informacao
(secoes 16 e 39 do CLAUDE.md).

Comparacoes obrigatorias:
    Baseline estrutural puro
    vs Baseline + agressao
    vs Baseline + volume
    vs Baseline + tempo
    vs Baseline + todas as features
    vs CatBoost

Tudo em walk-forward, no conjunto de DESENVOLVIMENTO apenas
(o holdout final permanece intocado).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import features as F
from build_dataset import load_dataset
from config import DEFAULT_LAGS, REPORTS_DIR, RESULTS_DIR
from evaluate import bootstrap_ci, classification_metrics, delong_like_pvalue
from walk_forward import holdout_split, run_walk_forward

# Grupos de informacao (secao 39)
INFO_GROUPS = {
    "structural_only": ["RunLength", "SignedRunLength", "ConsecutiveUpCount",
                        "ConsecutiveDownCount", "Direction"],
    "aggression": ["AggBuyNorm", "AggSellNorm", "AggBalanceNorm",
                   "AggTotalNorm", "AggImbalance", "BuyShare", "SellShare",
                   "AggBalanceChange", "AggBalanceAcceleration",
                   "AggImbalanceChange", "DirVsAggDivergence",
                   "AggBalanceNormMean3", "AggBalanceNormMean5",
                   "AggTotalNormMean3", "AggTotalNormMean5",
                   "AggBalanceRunSum"],
    "volume": ["QuantityNorm", "TradesNorm", "QuantityPerTrade",
               "TradesPerQuantity", "AggTotalPerQuantity", "AggTotalPerTrade",
               "QuantityResidual20", "TradesResidual20", "AggTotalResidual20",
               "QuantityRatio20", "TradesRatio20", "AggTotalRatio20",
               "QuantityPerTradeRatio20"],
    "time": ["DurationResidual", "DurationRatio20", "DurationResidualPct",
             "LogDuration", "LogDurationResidual20", "DeltaTLog",
             "SecondsSinceSessionOpen", "HourOfDay"],
    "candle_structure": ["Range", "BodyNorm", "UpperWickNorm",
                         "LowerWickNorm", "WickTotalNorm", "WickAsym",
                         "RangeMean5", "RangeRatio20",
                         "BodyNormMean3", "BodyNormMean5",
                         "CloseChange1Bricks", "CloseChange2Bricks",
                         "CloseChange3Bricks"],
}


def _cols(names, ds, n_lags=DEFAULT_LAGS, with_lags=()):
    out = [c for c in names if c in ds.columns]
    for c in with_lags:
        out += [f"{c}_lag{k}" for k in range(1, n_lags + 1)
                if f"{c}_lag{k}" in ds.columns]
    return list(dict.fromkeys(out))


def build_experiments(ds: pd.DataFrame, n_lags: int = DEFAULT_LAGS) -> list[dict]:
    S = INFO_GROUPS["structural_only"]
    lag_base = F.LAGGED_FEATURES

    combos = {
        "STRUCT": _cols(S, ds),
        "STRUCT+AGG": _cols(S + INFO_GROUPS["aggression"], ds, n_lags,
                            ["AggBalanceNorm", "AggTotalNorm", "AggBuyNorm",
                             "AggSellNorm"]),
        "STRUCT+VOL": _cols(S + INFO_GROUPS["volume"], ds, n_lags,
                            ["QuantityNorm", "TradesNorm"]),
        "STRUCT+TIME": _cols(S + INFO_GROUPS["time"], ds, n_lags,
                             ["DurationResidual"]),
        "STRUCT+CANDLE": _cols(S + INFO_GROUPS["candle_structure"], ds),
        "BASE": _cols(F.GROUP_BASE_CORE, ds, n_lags, lag_base),
        "EXTENDED": _cols(F.ALL_ENGINEERED, ds, n_lags, lag_base),
    }

    exps = []
    # baselines estruturais degenerados
    exps.append(dict(exp="EXP000_ALWAYS_SIGNAL", model="always_signal",
                     fs="STRUCT", cols=combos["STRUCT"], params={}))
    exps.append(dict(exp="EXP001_STRUCT_LOGISTIC", model="logistic",
                     fs="STRUCT", cols=combos["STRUCT"], params={}))
    # um modelo por grupo de informacao
    for i, (fs, cols) in enumerate(combos.items(), start=2):
        exps.append(dict(exp=f"EXP{i:03d}_{fs}_LOGISTIC", model="logistic",
                         fs=fs, cols=cols, params={}))
    n = len(exps)
    for j, (fs, cols) in enumerate(combos.items()):
        exps.append(dict(exp=f"EXP{n + j:03d}_{fs}_CATBOOST", model="catboost",
                         fs=fs, cols=cols,
                         params=dict(depth=4, learning_rate=0.05,
                                     l2_leaf_reg=10.0)))
    # arvore simples e random forest no conjunto EXTENDED
    exps.append(dict(exp="EXP100_EXTENDED_TREE", model="tree", fs="EXTENDED",
                     cols=combos["EXTENDED"], params={}))
    exps.append(dict(exp="EXP101_EXTENDED_RF", model="random_forest",
                     fs="EXTENDED", cols=combos["EXTENDED"], params={}))
    return exps


def run(target_suffix: str = "p2c2", n_lags: int = DEFAULT_LAGS) -> pd.DataFrame:
    ds = load_dataset()
    bars = np.arange(len(ds))
    dev, _test = holdout_split(bars)

    tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"
    exps = build_experiments(ds, n_lags)

    rows, oofs = [], {}
    for e in exps:
        if not e["cols"]:
            continue
        r = run_walk_forward(ds, e["cols"], tcol, ccol, e["model"],
                             e["params"], bar_pool=dev, experiment=e["exp"],
                             feature_set=e["fs"], collect_importance=False)
        if r.oof.empty:
            continue
        m = classification_metrics(r.oof["y"], r.oof["prob"], 0.5)
        lo, hi = bootstrap_ci(r.oof["y"], r.oof["prob"], "roc_auc")
        fm = pd.DataFrame(r.fold_metrics)
        rows.append({
            "experiment": e["exp"], "model": e["model"],
            "feature_set": e["fs"], "n_features": len(e["cols"]),
            "n_oof": m["n"], "base_rate": m["base_rate"],
            "roc_auc": m["roc_auc"], "auc_ci_lo": lo, "auc_ci_hi": hi,
            "pr_auc": m["pr_auc"],
            "precision@0.5": m["precision"], "recall@0.5": m["recall"],
            "f1@0.5": m["f1"], "n_signals@0.5": m["n_signals"],
            "edge_vs_base": m["edge_vs_base"],
            "auc_fold_mean": float(fm["roc_auc"].mean()),
            "auc_fold_std": float(fm["roc_auc"].std()),
            "auc_fold_min": float(fm["roc_auc"].min()),
            "auc_folds_above_0.5": int((fm["roc_auc"] > 0.5).sum()),
            "n_folds": len(fm),
        })
        oofs[e["exp"]] = r.oof
        print(f"  {e['exp']:34s} AUC={m['roc_auc']:.4f} "
              f"[{lo:.4f},{hi:.4f}]  prec={m['precision']:.4f} "
              f"(base {m['base_rate']:.4f})  folds>0.5: "
              f"{int((fm['roc_auc'] > 0.5).sum())}/{len(fm)}")

    res = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    res.to_csv(RESULTS_DIR / f"05_baselines_{target_suffix}.csv", index=False)

    # ---- teste de significancia contra o baseline estrutural ------------
    ref_key = "EXP001_STRUCT_LOGISTIC"
    pvals = {}
    if ref_key in oofs:
        ref = oofs[ref_key].set_index("BarIndex")
        for k, o in oofs.items():
            if k == ref_key:
                continue
            j = o.set_index("BarIndex").join(ref[["prob"]], rsuffix="_ref",
                                             how="inner")
            if len(j) > 100 and j["y"].nunique() > 1:
                pvals[k] = delong_like_pvalue(j["y"], j["prob"], j["prob_ref"])
    (RESULTS_DIR / f"05_significance_{target_suffix}.json").write_text(
        json.dumps(pvals, indent=2), encoding="utf-8")

    _write_md(res, pvals, target_suffix)
    for k, o in oofs.items():
        o.to_csv(RESULTS_DIR / f"oof_{target_suffix}_{k}.csv", index=False)
    return res


def _write_md(res: pd.DataFrame, pvals: dict, suf: str) -> None:
    L = [f"# 05 — Baselines e grupos de informacao (target `{suf}`)", "",
         "Walk-forward expansivo no conjunto de desenvolvimento "
         "(holdout final excluido).", "",
         "| experimento | modelo | features | n | AUC | IC95 | PR-AUC | "
         "prec@0.5 | base | edge | folds AUC>0.5 |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in res.iterrows():
        L.append(
            f"| `{r['experiment']}` | {r['model']} | {r['feature_set']} "
            f"({r['n_features']}) | {r['n_oof']} | {r['roc_auc']:.4f} | "
            f"[{r['auc_ci_lo']:.3f}, {r['auc_ci_hi']:.3f}] | "
            f"{r['pr_auc']:.4f} | {r['precision@0.5']:.4f} | "
            f"{r['base_rate']:.4f} | {r['edge_vs_base']:+.4f} | "
            f"{r['auc_folds_above_0.5']}/{r['n_folds']} |")
    L += ["", "## p-valor bootstrap vs baseline estrutural (AUC pareado)", ""]
    for k, v in sorted(pvals.items(), key=lambda kv: kv[1]):
        L.append(f"- `{k}`: p = {v:.4f}")
    (REPORTS_DIR / f"05_baselines_{suf}.md").write_text("\n".join(L),
                                                        encoding="utf-8")


if __name__ == "__main__":
    for suf in ("p2c2", "p3c2", "p2c3", "p3c3"):
        print(f"\n=== target {suf} ===")
        run(suf)
