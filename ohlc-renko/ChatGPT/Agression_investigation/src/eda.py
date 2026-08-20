"""
Etapa 04 — analise exploratoria obrigatoria (secoes 36, 37 e 38).

Produz:
  results/04_eda.json
  reports/04_eda.md
  reports/figures/*.png
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import features as F
import targets as T
from build_dataset import load_dataset
from config import FIGURES_DIR, REPORTS_DIR, RESULTS_DIR

DIST_COLS = [
    "Range", "Duration", "AggBuy", "AggSell", "AggBalance", "AggTotal",
    "Quantity", "Trades",
    "AggBuyNorm", "AggSellNorm", "AggBalanceNorm", "AggTotalNorm",
    "QuantityNorm", "TradesNorm", "DurationResidual",
    "BodyNorm", "UpperWickNorm", "LowerWickNorm", "CloseLocation",
    "AggImbalance", "QuantityPerTrade",
]


def describe(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {}
    q = s.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return {
        "n": int(len(s)), "mean": float(s.mean()), "std": float(s.std()),
        "min": float(s.min()), "p01": float(q.loc[.01]), "p05": float(q.loc[.05]),
        "p25": float(q.loc[.25]), "p50": float(q.loc[.5]), "p75": float(q.loc[.75]),
        "p95": float(q.loc[.95]), "p99": float(q.loc[.99]), "max": float(s.max()),
        "skew": float(s.skew()), "n_zero": int((s == 0).sum()),
    }


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    a = a.replace([np.inf, -np.inf], np.nan).dropna()
    b = b.replace([np.inf, -np.inf], np.nan).dropna()
    if len(a) < 5 or len(b) < 5:
        return float("nan")
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var() + (nb - 1) * b.var()) / max(na + nb - 2, 1))
    if sp == 0 or np.isnan(sp):
        return float("nan")
    return float((a.mean() - b.mean()) / sp)


def auc_single(x: pd.Series, y: pd.Series) -> float:
    """AUC de uma unica feature (Mann-Whitney), robusto a NaN."""
    m = x.replace([np.inf, -np.inf], np.nan).notna() & y.notna()
    x, y = x[m], y[m].astype(int)
    if y.nunique() < 2:
        return float("nan")
    r = x.rank()
    n1 = int(y.sum())
    n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def run() -> dict:
    ds = load_dataset()
    out: dict = {}

    # ---------------------------------------------- 37.1-37.9 distribuicoes
    out["distributions"] = {c: describe(ds[c]) for c in DIST_COLS if c in ds}

    # ---------------------------------------------- 37.10 taxa-base
    base_rates = {}
    for v in T.TARGET_VARIANTS:
        suf = T.target_suffix(v["pre_seq"], v["cont"], v.get("exact", False))
        cand = ds[f"cand_{suf}"] == 1
        y = ds.loc[cand, f"y_{suf}"]
        side = ds.loc[cand, f"side_{suf}"]
        n_days = ds["Session"].nunique()
        base_rates[suf] = {
            "pre_seq": v["pre_seq"], "cont": v["cont"],
            "exact": bool(v.get("exact", False)),
            "n_candidates": int(cand.sum()),
            "candidates_per_day": round(float(cand.sum()) / n_days, 2),
            "n_labeled": int(y.notna().sum()),
            "base_rate": float(y.mean()),
            "n_positive": int(y.sum()),
            "positives_per_day": round(float(y.sum()) / n_days, 2),
            "base_rate_up": float(y[side == 1].mean()),
            "base_rate_down": float(y[side == -1].mean()),
            "n_up": int((side == 1).sum()), "n_down": int((side == -1).sum()),
        }
    out["base_rates"] = base_rates

    # baseline de referencia: probabilidade incondicional de N barras
    # consecutivas na mesma direcao a partir de uma barra qualquer
    d = ds["Direction"]
    out["unconditional"] = {
        "p_direction_change": float((d != d.shift(1)).iloc[1:].mean()),
        "p_next_same_dir": float((d.shift(-1) == d).iloc[:-1].mean()),
        "p_next2_same_dir": float(
            ((d.shift(-1) == d) & (d.shift(-2) == d)).iloc[:-2].mean()),
        "p_next3_same_dir": float(
            ((d.shift(-1) == d) & (d.shift(-2) == d)
             & (d.shift(-3) == d)).iloc[:-3].mean()),
        "mean_run_length": float(
            d.groupby((d != d.shift()).cumsum()).size().mean()),
    }

    # ---------------------------------------------- secao 36: Renko stats
    cont_mask = ds["Direction"] == ds["Direction"].shift(1)
    rev_mask = (ds["Direction"] != ds["Direction"].shift(1)) & ds["Direction"].shift(1).notna()
    suf_main = "p2c2"
    cand = ds[f"cand_{suf_main}"] == 1
    win = cand & (ds[f"y_{suf_main}"] == 1)
    fail = cand & (ds[f"y_{suf_main}"] == 0)
    groups = {"continuidade": cont_mask, "reversao": rev_mask,
              "reversao_vencedora": win, "reversao_falsa": fail}
    out["renko_structure"] = {
        g: {c: describe(ds.loc[m, c])
            for c in ("Range", "BodyNorm", "UpperWickNorm", "LowerWickNorm",
                      "AggTotalNorm", "AggBalanceNorm", "DurationResidual")}
        for g, m in groups.items()
    }

    # ---------------------------------------------- secao 38: condicional
    cond = {}
    for suf in ("p2c2", "p2c3", "p3c2", "p3c3"):
        cand = ds[f"cand_{suf}"] == 1
        y = ds[f"y_{suf}"]
        sub = ds[cand & y.notna()]
        ysub = y[cand & y.notna()].astype(int)
        rows = []
        for col in F.ALL_ENGINEERED:
            if col not in sub.columns:
                continue
            for lag in (0, 1, 2):
                x = sub[col] if lag == 0 else ds[col].shift(lag)[sub.index]
                rows.append({
                    "feature": col, "lag": lag,
                    "mean_pos": float(pd.to_numeric(x[ysub == 1], errors="coerce")
                                      .replace([np.inf, -np.inf], np.nan).mean()),
                    "mean_neg": float(pd.to_numeric(x[ysub == 0], errors="coerce")
                                      .replace([np.inf, -np.inf], np.nan).mean()),
                    "cohens_d": cohens_d(x[ysub == 1], x[ysub == 0]),
                    "auc": auc_single(x, ysub),
                })
        r = pd.DataFrame(rows)
        r["abs_auc_gap"] = (r["auc"] - 0.5).abs()
        r = r.sort_values("abs_auc_gap", ascending=False)
        r.to_csv(RESULTS_DIR / f"04_conditional_{suf}.csv", index=False)
        cond[suf] = r.head(30).to_dict("records")
    out["conditional_top"] = cond

    # ---------------------------------------------- correlacao
    corr_cols = [c for c in F.ALL_ENGINEERED if c in ds.columns]
    corr = ds[corr_cols].replace([np.inf, -np.inf], np.nan).corr()
    corr.to_csv(RESULTS_DIR / "04_feature_correlation.csv")
    hi = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool)).stack()
    out["highly_correlated_pairs"] = [
        {"a": a, "b": b, "r": float(v)}
        for (a, b), v in hi[hi.abs() > 0.95].sort_values(key=abs, ascending=False
                                                         ).head(40).items()
    ]

    _figures(ds)
    _write_md(out)
    (RESULTS_DIR / "04_eda.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    return out


def _figures(ds: pd.DataFrame) -> None:
    cols = ["Range", "Duration", "AggBuy", "AggSell", "AggBalance",
            "Quantity", "Trades", "AggBalanceNorm", "AggTotalNorm",
            "QuantityNorm", "TradesNorm", "DurationResidual",
            "BodyNorm", "UpperWickNorm", "LowerWickNorm", "CloseLocation"]
    fig, axes = plt.subplots(4, 4, figsize=(18, 13))
    for ax, c in zip(axes.ravel(), cols):
        s = pd.to_numeric(ds[c], errors="coerce").replace(
            [np.inf, -np.inf], np.nan).dropna()
        lo, hi = s.quantile([0.005, 0.995])
        ax.hist(s.clip(lo, hi), bins=60, color="#4C78A8")
        ax.set_title(c, fontsize=10)
        ax.tick_params(labelsize=8)
    fig.suptitle("Distribuicoes — Renko WIN (bricks fechados)", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_distributions.png", dpi=110)
    plt.close(fig)

    # reversao vencedora vs falsa
    suf = "p2c2"
    cand = ds[f"cand_{suf}"] == 1
    y = ds[f"y_{suf}"]
    comp = ["UpperWickNorm", "LowerWickNorm", "BodyNorm", "CloseLocation",
            "AggBalanceNorm", "AggImbalance", "AggTotalNorm", "TradesNorm",
            "DurationResidual", "QuantityPerTrade", "RunLength", "RangeRatio20"]
    fig, axes = plt.subplots(3, 4, figsize=(18, 10))
    for ax, c in zip(axes.ravel(), comp):
        for lab, m, col in ((f"y=1", cand & (y == 1), "#2E8B57"),
                            (f"y=0", cand & (y == 0), "#C0392B")):
            s = pd.to_numeric(ds.loc[m, c], errors="coerce").replace(
                [np.inf, -np.inf], np.nan).dropna()
            lo, hi = s.quantile([0.01, 0.99])
            ax.hist(s.clip(lo, hi), bins=40, alpha=0.55, density=True,
                    label=lab, color=col)
        ax.set_title(c, fontsize=10); ax.tick_params(labelsize=8)
        ax.legend(fontsize=7)
    fig.suptitle("Reversao vencedora (y=1) vs falsa (y=0) — target p2c2",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_win_vs_fail.png", dpi=110)
    plt.close(fig)


def _write_md(out: dict) -> None:
    L = ["# 04 — Analise exploratoria", ""]
    L.append("## Taxa-base dos eventos de reversao")
    L.append("")
    L.append("| target | pre | cont | exato | candidatos | cand/dia | taxa-base | up | down |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for suf, r in out["base_rates"].items():
        L.append(f"| `{suf}` | {r['pre_seq']} | {r['cont']} | {r['exact']} | "
                 f"{r['n_candidates']} | {r['candidates_per_day']} | "
                 f"{r['base_rate']:.4f} | {r['base_rate_up']:.4f} | "
                 f"{r['base_rate_down']:.4f} |")
    L += ["", "## Probabilidades incondicionais", ""]
    for k, v in out["unconditional"].items():
        L.append(f"- `{k}`: {v:.4f}")
    L += ["", "## Estrutura Renko por grupo (medias)", ""]
    keys = ["Range", "BodyNorm", "UpperWickNorm", "LowerWickNorm",
            "AggTotalNorm", "AggBalanceNorm", "DurationResidual"]
    L.append("| grupo | " + " | ".join(keys) + " |")
    L.append("|" + "---|" * (len(keys) + 1))
    for g, d in out["renko_structure"].items():
        L.append(f"| {g} | " + " | ".join(
            f"{d[k].get('mean', float('nan')):.4f}" for k in keys) + " |")
    L += ["", "## Top features condicionais (target p2c2, |AUC-0.5|)", ""]
    L.append("| feature | lag | AUC | Cohen d | media y=1 | media y=0 |")
    L.append("|---|---|---|---|---|---|")
    for r in out["conditional_top"]["p2c2"][:25]:
        L.append(f"| `{r['feature']}` | {r['lag']} | {r['auc']:.4f} | "
                 f"{r['cohens_d']:.4f} | {r['mean_pos']:.4f} | {r['mean_neg']:.4f} |")
    L += ["", "## Pares altamente correlacionados (|r| > 0.95)", ""]
    for p in out["highly_correlated_pairs"]:
        L.append(f"- `{p['a']}` ~ `{p['b']}` : r = {p['r']:.4f}")
    L += ["", "![distribuicoes](figures/04_distributions.png)",
          "", "![win vs fail](figures/04_win_vs_fail.png)"]
    (REPORTS_DIR / "04_eda.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    o = run()
    print(json.dumps(o["base_rates"], indent=2))
    print(json.dumps(o["unconditional"], indent=2))
