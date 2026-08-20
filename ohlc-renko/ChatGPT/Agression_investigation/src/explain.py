"""
Etapa 07 — feature importance, SHAP e ESTABILIDADE da importancia
(secao 22 do CLAUDE.md).

A pergunta nao e "qual feature e importante", e sim "qual feature e
importante em TODOS os folds". Uma feature que aparece em um unico periodo
e tratada como suspeita.
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_dataset import load_dataset
from config import DEFAULT_LAGS, FIGURES_DIR, REPORTS_DIR, RESULTS_DIR
from train_catboost import feature_columns
from walk_forward import holdout_split, run_walk_forward


def importance_stability(target_suffix: str = "p2c2",
                         feature_set: str = "BASE",
                         params: dict | None = None,
                         n_lags: int = DEFAULT_LAGS,
                         top_k: int = 15) -> dict:
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)))
    cols = feature_columns(ds, feature_set, n_lags)

    r = run_walk_forward(ds, cols, f"y_{target_suffix}",
                         f"cand_{target_suffix}", "catboost", params,
                         bar_pool=dev, feature_set=feature_set,
                         collect_importance=True)
    imp = r.importances
    if imp is None or imp.empty:
        return {}

    # normaliza por fold para que os folds sejam comparaveis
    imp["imp_norm"] = imp.groupby("fold")["importance"].transform(
        lambda s: s / max(s.sum(), 1e-12))
    imp["rank"] = imp.groupby("fold")["importance"].rank(ascending=False)

    agg = (imp.groupby("feature")
              .agg(imp_mean=("imp_norm", "mean"),
                   imp_std=("imp_norm", "std"),
                   rank_mean=("rank", "mean"),
                   rank_std=("rank", "std"),
                   rank_worst=("rank", "max"),
                   times_in_topk=("rank", lambda s: int((s <= top_k).sum())))
              .reset_index())
    n_folds = imp["fold"].nunique()
    agg["n_folds"] = n_folds
    agg["topk_fraction"] = agg["times_in_topk"] / n_folds
    # coeficiente de variacao: baixo = estavel
    agg["imp_cv"] = agg["imp_std"] / agg["imp_mean"].replace(0, np.nan)
    agg = agg.sort_values(["topk_fraction", "imp_mean"], ascending=False)
    agg.to_csv(RESULTS_DIR / f"07_importance_{target_suffix}_{feature_set}.csv",
               index=False)

    stable = agg[(agg["topk_fraction"] >= 0.8)]["feature"].tolist()
    unstable = agg[(agg["times_in_topk"] > 0) &
                   (agg["topk_fraction"] < 0.5)]["feature"].tolist()

    _plot(imp, agg, target_suffix, feature_set, top_k)

    return {
        "target": target_suffix, "feature_set": feature_set,
        "n_folds": n_folds, "top_k": top_k,
        "stable_features": stable,
        "unstable_but_sometimes_top": unstable[:40],
        "top20_by_mean_importance": agg.head(20).to_dict("records"),
    }


def _plot(imp, agg, suf, fs, top_k):
    top = agg.head(20)["feature"].tolist()
    piv = (imp[imp["feature"].isin(top)]
           .pivot(index="feature", columns="fold", values="rank")
           .reindex(top))
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    a = axes[0]
    y = np.arange(len(top))
    a.barh(y, agg.head(20)["imp_mean"], xerr=agg.head(20)["imp_std"].fillna(0),
           color="#4C78A8")
    a.set_yticks(y); a.set_yticklabels(top, fontsize=8); a.invert_yaxis()
    a.set_xlabel("importancia normalizada (media +/- desvio entre folds)")
    a.set_title(f"Importancia media — {fs} / {suf}")

    b = axes[1]
    im = b.imshow(piv.to_numpy(), aspect="auto", cmap="viridis_r")
    b.set_yticks(np.arange(len(top))); b.set_yticklabels(top, fontsize=8)
    b.set_xticks(np.arange(piv.shape[1])); b.set_xticklabels(piv.columns)
    b.set_xlabel("fold"); b.set_title("Rank da feature por fold (claro = mais importante)")
    fig.colorbar(im, ax=b, label="rank")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"07_importance_{suf}_{fs}.png", dpi=110)
    plt.close(fig)


def shap_summary(target_suffix: str = "p2c2", feature_set: str = "BASE",
                 params: dict | None = None, n_lags: int = DEFAULT_LAGS
                 ) -> dict:
    """SHAP no ultimo fold de desenvolvimento (secao 22)."""
    try:
        import shap  # noqa: F401
    except ImportError:
        return {"available": False}

    from catboost import Pool

    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)))
    cols = feature_columns(ds, feature_set, n_lags)
    tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"

    usable = (ds[ccol] == 1) & ds[tcol].notna()
    pool_idx = np.intersect1d(dev, np.where(usable)[0])
    cut = int(len(pool_idx) * 0.8)
    tr, va = pool_idx[:cut], pool_idx[cut:]

    from walk_forward import fit_predict
    _, model = fit_predict("catboost", params, ds.iloc[tr][cols],
                           ds[tcol].to_numpy()[tr].astype(int),
                           ds.iloc[va][cols])

    X = ds.iloc[va][cols].replace([np.inf, -np.inf], np.nan)
    sv = model.get_feature_importance(Pool(X), type="ShapValues")[:, :-1]
    mean_abs = np.abs(sv).mean(axis=0)
    order = np.argsort(mean_abs)[::-1][:20]

    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(np.arange(len(order)), mean_abs[order][::-1], color="#E45756")
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([cols[i] for i in order][::-1], fontsize=8)
    ax.set_xlabel("|SHAP| medio")
    ax.set_title(f"SHAP — {feature_set} / {target_suffix} (ultimo fold dev)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"07_shap_{target_suffix}_{feature_set}.png",
                dpi=110)
    plt.close(fig)

    return {"available": True,
            "top20": [{"feature": cols[i], "mean_abs_shap": float(mean_abs[i])}
                      for i in order]}


def run(targets=("p2c2", "p3c2"), feature_sets=("BASE", "EXTENDED")) -> dict:
    out = {}
    for t in targets:
        for fs in feature_sets:
            k = f"{t}|{fs}"
            out[k] = importance_stability(t, fs)
            out[k]["shap"] = shap_summary(t, fs)
            print(f"{k}: estaveis (>=80% dos folds no top-15) = "
                  f"{out[k].get('stable_features')}")
    (RESULTS_DIR / "07_importance_stability.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    _write_md(out)
    return out


def _write_md(out: dict) -> None:
    L = ["# 07 — Importancia e estabilidade das features", "",
         "Uma feature so e considerada util se estiver no top-15 em pelo "
         "menos 80% dos folds do walk-forward (secao 22).", ""]
    for k, v in out.items():
        if not v:
            continue
        L += [f"## {k}", "",
              f"- folds: {v['n_folds']}",
              f"- **features estaveis**: "
              f"{', '.join(f'`{s}`' for s in v['stable_features']) or '_nenhuma_'}",
              f"- importantes em <50% dos folds (suspeitas): "
              f"{', '.join(f'`{s}`' for s in v['unstable_but_sometimes_top'][:15]) or '_nenhuma_'}",
              "", "| feature | imp. media | desvio | CV | rank medio | top-15 em |",
              "|---|---|---|---|---|---|"]
        for r in v["top20_by_mean_importance"][:15]:
            cv = r.get("imp_cv")
            cv_s = f"{cv:.2f}" if cv == cv else "—"
            L.append(f"| `{r['feature']}` | {r['imp_mean']:.4f} | "
                     f"{r.get('imp_std', float('nan')):.4f} | {cv_s} | "
                     f"{r['rank_mean']:.1f} | {r['times_in_topk']}/{v['n_folds']} |")
        sh = v.get("shap", {})
        if sh.get("available"):
            L += ["", "SHAP (top 8): " + ", ".join(
                f"`{d['feature']}` ({d['mean_abs_shap']:.4f})"
                for d in sh["top20"][:8])]
        L += ["", f"![importancia](figures/07_importance_{k.replace('|', '_')}.png)", ""]
    (REPORTS_DIR / "07_feature_importance.md").write_text("\n".join(L),
                                                          encoding="utf-8")


if __name__ == "__main__":
    run()
