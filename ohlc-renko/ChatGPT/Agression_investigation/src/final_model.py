"""
Etapas 08-10 — selecao FINAL de features, escolha de threshold e
TESTE FINAL OUT-OF-SAMPLE (secoes 21, 25, 20 e 41 do CLAUDE.md).

Protocolo, na ordem exata:

  1. a serie e cortada em DEV (primeiros 80% das barras) e HOLDOUT
     (ultimos 20%), com embargo de 3 barras entre os dois;
  2. o conjunto FINAL de features e escolhido a partir da estabilidade da
     importancia medida SOMENTE no walk-forward de DEV;
  3. o threshold e escolhido a partir das predicoes out-of-fold de DEV;
  4. o modelo e retreinado em todo o DEV;
  5. so entao o HOLDOUT e avaliado, uma unica vez.

O holdout nunca influencia (2), (3) nem (4).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_dataset import load_dataset
from config import (BRICK_SIZE, DEFAULT_LAGS, EMBARGO_BARS, FIGURES_DIR,
                    MODELS_DIR, REPORTS_DIR, RESULTS_DIR, THRESHOLD_GRID)
from evaluate import (bootstrap_ci, classification_metrics, metrics_by_group,
                      threshold_curve)
from train_catboost import feature_columns
from walk_forward import fit_predict, holdout_split, run_walk_forward

MIN_SIGNALS_PER_DAY = 1.0     # utilidade operacional minima (secao 41.6)


# --------------------------------------------------------- selecao FINAL
def select_final_features(ds, target_suffix, feature_set, params, n_lags,
                          min_topk_fraction=0.8, top_k=15) -> dict:
    """Conjunto FINAL = features estaveis no walk-forward de DEV (secao 21)."""
    dev, _ = holdout_split(np.arange(len(ds)))
    cols = feature_columns(ds, feature_set, n_lags)
    r = run_walk_forward(ds, cols, f"y_{target_suffix}",
                         f"cand_{target_suffix}", "catboost", params,
                         bar_pool=dev, collect_importance=True)
    imp = r.importances
    if imp is None or imp.empty:
        return {"final_features": cols, "note": "sem importancias"}
    imp["rank"] = imp.groupby("fold")["importance"].rank(ascending=False)
    n_folds = imp["fold"].nunique()
    frac = imp.assign(intop=imp["rank"] <= top_k).groupby("feature")["intop"].mean()
    final = frac[frac >= min_topk_fraction].index.tolist()
    if len(final) < 4:      # nada e estavel: cai para o top-8 medio
        final = (imp.groupby("feature")["importance"].mean()
                    .sort_values(ascending=False).head(8).index.tolist())
    return {"final_features": final, "n_folds": n_folds,
            "candidate_pool": cols,
            "stability_fraction": frac.sort_values(ascending=False)
                                      .head(30).to_dict()}


# ------------------------------------------------------------- threshold
def choose_threshold(oof: pd.DataFrame, n_days_dev: int,
                     grid=THRESHOLD_GRID,
                     min_signals_per_day=MIN_SIGNALS_PER_DAY) -> dict:
    """Escolhe o threshold usando SOMENTE as predicoes OOF de DEV."""
    curve = threshold_curve(oof["y"], oof["prob"], grid, n_days=n_days_dev)
    curve["signals_per_day"] = curve["n_signals"] / n_days_dev
    ok = curve[curve["signals_per_day"] >= min_signals_per_day]
    pick = (ok.sort_values("precision", ascending=False).iloc[0]
            if len(ok) else curve.sort_values("precision", ascending=False).iloc[0])
    return {"threshold": float(pick["threshold"]),
            "dev_precision": float(pick["precision"]),
            "dev_signals_per_day": float(pick["signals_per_day"]),
            "dev_base_rate": float(curve["base_rate"].iloc[0]),
            "curve": curve.to_dict("records")}


# ------------------------------------------------- simulacao economica
def economic_summary(ds: pd.DataFrame, idx: np.ndarray,
                     selected: np.ndarray) -> dict:
    """Secao 20: MFE/MAE, +2/+3 bricks e tempo ate o alvo."""
    sub = ds.iloc[idx]
    sel = sub[selected]
    if len(sel) == 0:
        return {"n": 0}
    def s(col):
        v = pd.to_numeric(sel[col], errors="coerce").dropna()
        return {} if v.empty else {
            "mean": float(v.mean()), "median": float(v.median()),
            "p25": float(v.quantile(.25)), "p75": float(v.quantile(.75))}
    return {
        "n": int(len(sel)),
        "hit_2_bricks_rate": float(sel["fwd_hit2"].mean()),
        "hit_3_bricks_rate": float(sel["fwd_hit3"].mean()),
        "mfe_bricks": s("fwd_mfe_bricks"),
        "mae_bricks": s("fwd_mae_bricks"),
        "bars_to_2_bricks": s("fwd_bars_to_2bricks"),
        "bars_to_3_bricks": s("fwd_bars_to_3bricks"),
        "mae_before_2_bricks_pts": s("fwd_mae_before_2bricks"),
        "mean_move_12_bars_pts": float(
            pd.to_numeric(sel["fwd_close_move_12b"], errors="coerce").mean()),
        "expectancy_bricks_12b": float(
            pd.to_numeric(sel["fwd_close_move_12b"], errors="coerce").mean()
            / BRICK_SIZE),
    }


# ------------------------------------------------------------------ run
def run(target_suffix="p2c2", feature_set="BASE", params=None,
        n_lags=DEFAULT_LAGS) -> dict:
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    ds = load_dataset()
    bars = np.arange(len(ds))
    dev, test = holdout_split(bars)

    tcol, ccol, scol = (f"y_{target_suffix}", f"cand_{target_suffix}",
                        f"side_{target_suffix}")
    usable = ((ds[ccol] == 1) & ds[tcol].notna()).to_numpy()

    dev_days = ds.iloc[dev]["Session"].nunique()
    test_days = ds.iloc[test]["Session"].nunique()

    # ---- (2) features FINAIS a partir de DEV ---------------------------
    sel = select_final_features(ds, target_suffix, feature_set, params, n_lags)
    final_cols = sel["final_features"]

    # ---- (3) threshold a partir das predicoes OOF de DEV ---------------
    wf = run_walk_forward(ds, final_cols, tcol, ccol, "catboost", params,
                          bar_pool=dev, collect_importance=False)
    dev_metrics = classification_metrics(wf.oof["y"], wf.oof["prob"], 0.5)
    lo, hi = bootstrap_ci(wf.oof["y"], wf.oof["prob"], "roc_auc")
    th = choose_threshold(wf.oof, dev_days)

    # ---- (4) retreino em TODO o DEV ------------------------------------
    tr = np.intersect1d(dev, np.where(usable)[0])
    te = np.intersect1d(test, np.where(usable)[0])
    ytr = ds[tcol].to_numpy()[tr].astype(int)
    yte = ds[tcol].to_numpy()[te].astype(int)

    prob_te, model = fit_predict("catboost", params, ds.iloc[tr][final_cols],
                                 ytr, ds.iloc[te][final_cols])
    model.save_model(str(MODELS_DIR / f"catboost_{target_suffix}.cbm"))

    # ---- (5) HOLDOUT — avaliacao unica ---------------------------------
    t = th["threshold"]
    test_metrics = classification_metrics(yte, prob_te, t, n_days=test_days)
    test_metrics_05 = classification_metrics(yte, prob_te, 0.5, n_days=test_days)
    lo_t, hi_t = bootstrap_ci(yte, prob_te, "roc_auc")

    preds = pd.DataFrame({
        "timestamp": ds["Date"].to_numpy()[te],
        "BarIndex": ds["BarIndex"].to_numpy()[te],
        "side": ds[scol].to_numpy()[te],
        "probability": prob_te,
        "prediction": (prob_te >= t).astype(int),
        "target": yte,
        "fold": "HOLDOUT",
    })
    oof_out = wf.oof.rename(columns={"Date": "timestamp", "prob": "probability",
                                     "y": "target"})
    oof_out["prediction"] = (oof_out["probability"] >= t).astype(int)
    all_preds = pd.concat([oof_out, preds], ignore_index=True)
    all_preds.to_csv(RESULTS_DIR / f"08_predictions_{target_suffix}.csv",
                     index=False)

    # ---- metricas por direcao e por horario no holdout ------------------
    dfte = pd.DataFrame({"y": yte, "prob": prob_te,
                         "side": ds[scol].to_numpy()[te],
                         "hour": pd.to_datetime(ds["Date"].to_numpy()[te]).hour})
    by_side = metrics_by_group(dfte, "side", t)
    by_hour = metrics_by_group(dfte, "hour", t)

    # ---- economia -------------------------------------------------------
    econ_sig = economic_summary(ds, te, prob_te >= t)
    econ_all = economic_summary(ds, te, np.ones(len(te), bool))

    out = {
        "target": target_suffix, "feature_set": feature_set,
        "params": params, "n_lags": n_lags,
        "final_features": final_cols,
        "n_final_features": len(final_cols),
        "feature_stability": sel.get("stability_fraction", {}),
        "dev": {"n_days": dev_days, "n_events": int(len(tr)),
                "walkforward": dev_metrics,
                "auc_ci95": [lo, hi],
                "fold_metrics": wf.fold_metrics},
        "threshold_selection": th,
        "holdout": {
            "n_days": test_days, "n_events": int(len(te)),
            "bar_range": [int(ds['BarIndex'].to_numpy()[te].min()),
                          int(ds['BarIndex'].to_numpy()[te].max())],
            "date_range": [str(ds['Date'].to_numpy()[te].min()),
                           str(ds['Date'].to_numpy()[te].max())],
            "metrics_at_selected_threshold": test_metrics,
            "metrics_at_0.5": test_metrics_05,
            "auc_ci95": [lo_t, hi_t],
            "by_side": by_side.to_dict("records") if len(by_side) else [],
            "by_hour": by_hour.to_dict("records") if len(by_hour) else [],
        },
        "economics": {"signals": econ_sig, "all_candidates": econ_all},
    }
    _plot(th["curve"], target_suffix, yte, prob_te, t)
    (RESULTS_DIR / f"08_final_{target_suffix}.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    return out


def _plot(curve, suf, yte, prob_te, chosen):
    c = pd.DataFrame(curve)
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
    axes[0].plot(c["threshold"], c["precision"], "o-", color="#4C78A8")
    axes[0].axhline(c["base_rate"].iloc[0], ls="--", color="grey",
                    label="taxa-base")
    axes[0].axvline(chosen, ls=":", color="#E45756", label="escolhido")
    axes[0].set_xlabel("threshold"); axes[0].set_ylabel("precision (DEV OOF)")
    axes[0].legend(fontsize=8); axes[0].set_title("Threshold x precision")

    axes[1].plot(c["threshold"], c["n_signals"], "o-", color="#72B7B2")
    axes[1].set_xlabel("threshold"); axes[1].set_ylabel("n sinais (DEV OOF)")
    axes[1].set_title("Threshold x quantidade de sinais")

    axes[2].hist(prob_te[yte == 1], bins=30, alpha=.6, density=True,
                 label="y=1", color="#2E8B57")
    axes[2].hist(prob_te[yte == 0], bins=30, alpha=.6, density=True,
                 label="y=0", color="#C0392B")
    axes[2].axvline(chosen, ls=":", color="black")
    axes[2].set_title("Probabilidades no HOLDOUT"); axes[2].legend(fontsize=8)
    fig.suptitle(f"Selecao de threshold e holdout — {suf}")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"08_threshold_{suf}.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    res = run()
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("feature_stability",)}, indent=2,
                     default=float)[:5000])
