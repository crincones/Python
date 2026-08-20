"""
Etapa 06 — busca de hiperparametros do CatBoost e sensibilidade a lags
(secoes 17 e 24 do CLAUDE.md).

TODA a selecao acontece no conjunto de DESENVOLVIMENTO, via walk-forward.
O holdout final nunca e tocado aqui.

Criterio de selecao: NAO usamos o AUC agregado out-of-fold. Usamos
    score = media(AUC por fold) - 0.5 * desvio(AUC por fold)
para penalizar configuracoes instaveis, e reportamos tambem quantos folds
ficaram acima de 0.5. Isso implementa a exigencia da secao 41 (estabilidade
em walk-forward, nao apenas AUC > 0.5).
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

import features as F
from baselines import INFO_GROUPS, _cols
from build_dataset import build, load_dataset
from config import (CATBOOST_GRID, DEFAULT_LAGS, LAG_GRID, REPORTS_DIR,
                    RESULTS_DIR)
from evaluate import classification_metrics
from walk_forward import holdout_split, run_walk_forward


def feature_columns(ds: pd.DataFrame, fs: str, n_lags: int) -> list[str]:
    S = INFO_GROUPS["structural_only"]
    if fs == "BASE":
        return _cols(F.GROUP_BASE_CORE, ds, n_lags, F.LAGGED_FEATURES)
    if fs == "EXTENDED":
        return _cols(F.ALL_ENGINEERED, ds, n_lags, F.LAGGED_FEATURES)
    if fs == "PREVCMP":
        return _cols(F.prev_comparison_names(), ds)
    if fs == "EXTENDED+PREVCMP":
        return (_cols(F.ALL_ENGINEERED, ds, n_lags, F.LAGGED_FEATURES)
                + _cols(F.prev_comparison_names(), ds))
    if fs == "STRUCT+AGG":
        return _cols(S + INFO_GROUPS["aggression"], ds, n_lags,
                     ["AggBalanceNorm", "AggTotalNorm", "AggBuyNorm",
                      "AggSellNorm"])
    if fs == "STRUCT+VOL":
        return _cols(S + INFO_GROUPS["volume"], ds, n_lags,
                     ["QuantityNorm", "TradesNorm"])
    raise ValueError(fs)


def _score(fold_metrics) -> dict:
    fm = pd.DataFrame(fold_metrics)
    mean = float(fm["roc_auc"].mean())
    std = float(fm["roc_auc"].std())
    return {
        "auc_fold_mean": mean, "auc_fold_std": std,
        "auc_fold_min": float(fm["roc_auc"].min()),
        "folds_above_05": int((fm["roc_auc"] > 0.5).sum()),
        "n_folds": len(fm),
        "stability_score": mean - 0.5 * (std if np.isfinite(std) else 1.0),
    }


def grid_search(target_suffix: str = "p2c2",
                feature_sets=("BASE", "EXTENDED", "STRUCT+AGG", "STRUCT+VOL"),
                n_lags: int = DEFAULT_LAGS,
                grid=CATBOOST_GRID) -> pd.DataFrame:
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)))
    tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"

    rows = []
    t0 = time.time()
    for fs in feature_sets:
        cols = feature_columns(ds, fs, n_lags)
        for gi, params in enumerate(grid):
            r = run_walk_forward(ds, cols, tcol, ccol, "catboost", params,
                                 bar_pool=dev, feature_set=fs,
                                 collect_importance=False)
            if r.oof.empty:
                continue
            m = classification_metrics(r.oof["y"], r.oof["prob"], 0.5)
            row = {"target": target_suffix, "feature_set": fs,
                   "n_features": len(cols), "n_lags": n_lags, **params,
                   "oof_auc": m["roc_auc"], "oof_pr_auc": m["pr_auc"],
                   "base_rate": m["base_rate"], **_score(r.fold_metrics)}
            rows.append(row)
        print(f"  [{fs}] {len(grid)} configs em {time.time() - t0:.0f}s")

    res = pd.DataFrame(rows).sort_values("stability_score", ascending=False)
    res.to_csv(RESULTS_DIR / f"06_catboost_grid_{target_suffix}.csv",
               index=False)
    return res


def lag_sensitivity(target_suffix: str = "p2c2",
                    feature_sets=("BASE", "EXTENDED"),
                    params=None, lag_grid=LAG_GRID) -> pd.DataFrame:
    """Secao 6 / 24: 3, 5, 8, 10 lags. Cada n_lags exige reconstruir o
    dataset, porque as colunas de lag mudam."""
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    rows = []
    for n_lags in lag_grid:
        ds = build(n_lags=n_lags, write=False)
        dev, _ = holdout_split(np.arange(len(ds)))
        tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"
        for fs in feature_sets:
            cols = feature_columns(ds, fs, n_lags)
            r = run_walk_forward(ds, cols, tcol, ccol, "catboost", params,
                                 bar_pool=dev, feature_set=fs,
                                 collect_importance=False)
            if r.oof.empty:
                continue
            m = classification_metrics(r.oof["y"], r.oof["prob"], 0.5)
            rows.append({"target": target_suffix, "feature_set": fs,
                         "n_lags": n_lags, "n_features": len(cols),
                         "oof_auc": m["roc_auc"], "pr_auc": m["pr_auc"],
                         **_score(r.fold_metrics)})
            print(f"  lags={n_lags:2d} {fs:10s} AUC={m['roc_auc']:.4f} "
                  f"stab={rows[-1]['stability_score']:.4f} "
                  f"folds>0.5={rows[-1]['folds_above_05']}/{rows[-1]['n_folds']}")
    res = pd.DataFrame(rows)
    res.to_csv(RESULTS_DIR / f"06_lag_sensitivity_{target_suffix}.csv",
               index=False)
    return res


def ma_period_sensitivity(target_suffix: str = "p2c2",
                          periods=(10, 20, 40), params=None) -> pd.DataFrame:
    """Secao 24: variar o periodo da media movel de duracao."""
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    rows = []
    for p in periods:
        ds = build(n_lags=DEFAULT_LAGS, ma_period=p, write=False)
        dev, _ = holdout_split(np.arange(len(ds)))
        cols = feature_columns(ds, "BASE", DEFAULT_LAGS)
        r = run_walk_forward(ds, cols, f"y_{target_suffix}",
                             f"cand_{target_suffix}", "catboost", params,
                             bar_pool=dev, collect_importance=False)
        if r.oof.empty:
            continue
        m = classification_metrics(r.oof["y"], r.oof["prob"], 0.5)
        rows.append({"ma_period": p, "oof_auc": m["roc_auc"],
                     **_score(r.fold_metrics)})
        print(f"  ma_period={p:3d} AUC={m['roc_auc']:.4f} "
              f"stab={rows[-1]['stability_score']:.4f}")
    res = pd.DataFrame(rows)
    res.to_csv(RESULTS_DIR / f"06_ma_sensitivity_{target_suffix}.csv",
               index=False)
    return res


def _write_md(grid_res: dict, lag_res: pd.DataFrame, ma_res: pd.DataFrame,
              best: dict) -> None:
    L = ["# 06 — CatBoost: busca de hiperparametros e estabilidade", "",
         "Selecao feita **apenas** no conjunto de desenvolvimento, via "
         "walk-forward expansivo com embargo. O holdout final nao foi usado.",
         "", "## Melhor configuracao por target (criterio de estabilidade)", "",
         "| target | feature set | depth | lr | l2 | AUC OOF | AUC medio/fold |"
         " desvio | folds>0.5 | score |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in best.items():
        L.append(f"| `{t}` | {r['feature_set']} | {r['depth']} | "
                 f"{r['learning_rate']} | {r['l2_leaf_reg']} | "
                 f"{r['oof_auc']:.4f} | {r['auc_fold_mean']:.4f} | "
                 f"{r['auc_fold_std']:.4f} | "
                 f"{r['folds_above_05']}/{r['n_folds']} | "
                 f"{r['stability_score']:.4f} |")
    for t, df in grid_res.items():
        L += ["", f"### Top 10 configuracoes — `{t}`", "",
              "| feature set | depth | lr | l2 | AUC OOF | AUC/fold | desvio | folds>0.5 |",
              "|---|---|---|---|---|---|---|---|"]
        for _, r in df.head(10).iterrows():
            L.append(f"| {r['feature_set']} | {r['depth']} | "
                     f"{r['learning_rate']} | {r['l2_leaf_reg']} | "
                     f"{r['oof_auc']:.4f} | {r['auc_fold_mean']:.4f} | "
                     f"{r['auc_fold_std']:.4f} | "
                     f"{r['folds_above_05']}/{r['n_folds']} |")
        L += ["", f"Dispersao do AUC OOF em `{t}`: "
              f"min={df['oof_auc'].min():.4f}, max={df['oof_auc'].max():.4f}, "
              f"desvio={df['oof_auc'].std():.4f} sobre {len(df)} configuracoes."]
    L += ["", "## Sensibilidade ao numero de lags", "",
          "| target | feature set | lags | n feat | AUC OOF | AUC/fold | desvio | folds>0.5 |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in lag_res.iterrows():
        L.append(f"| `{r['target']}` | {r['feature_set']} | {r['n_lags']} | "
                 f"{r['n_features']} | {r['oof_auc']:.4f} | "
                 f"{r['auc_fold_mean']:.4f} | {r['auc_fold_std']:.4f} | "
                 f"{r['folds_above_05']}/{r['n_folds']} |")
    L += ["", "## Sensibilidade ao periodo da media movel", "",
          "| periodo | AUC OOF | AUC/fold | desvio | folds>0.5 |",
          "|---|---|---|---|---|"]
    for _, r in ma_res.iterrows():
        L.append(f"| {r['ma_period']} | {r['oof_auc']:.4f} | "
                 f"{r['auc_fold_mean']:.4f} | {r['auc_fold_std']:.4f} | "
                 f"{r['folds_above_05']}/{r['n_folds']} |")
    (REPORTS_DIR / "06_catboost_tuning.md").write_text("\n".join(L),
                                                       encoding="utf-8")


if __name__ == "__main__":
    grid_res, best = {}, {}
    for t in ("p2c2", "p3c2"):
        print(f"\n=== grid search {t} ===")
        g = grid_search(t)
        grid_res[t] = g
        best[t] = g.iloc[0].to_dict()
        print(g.head(5).to_string(index=False))

    print("\n=== sensibilidade a lags ===")
    lag_res = lag_sensitivity("p2c2")
    print("\n=== sensibilidade ao periodo da media ===")
    ma_res = ma_period_sensitivity("p2c2")

    _write_md(grid_res, lag_res, ma_res, best)
    (RESULTS_DIR / "06_best_config.json").write_text(
        json.dumps(best, indent=2, default=float), encoding="utf-8")
    print("\nmelhor config:", json.dumps(best, indent=2, default=float))
