"""
Metricas (secao 19) e utilidades de avaliacao.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, confusion_matrix,
                             roc_auc_score)


def classification_metrics(y_true, y_prob, threshold: float = 0.5,
                           n_days: int | None = None) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    n = len(y_true)
    base = float(y_true.mean()) if n else float("nan")

    if len(np.unique(y_true)) > 1:
        roc = float(roc_auc_score(y_true, y_prob))
        pr = float(average_precision_score(y_true, y_prob))
    else:
        roc = pr = float("nan")

    tn, fp, fn, tp = (confusion_matrix(y_true, y_pred, labels=[0, 1])
                      .ravel().astype(int))
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec and rec and
                                           not np.isnan(prec) and
                                           not np.isnan(rec) and
                                           (prec + rec) > 0) else float("nan")
    out = {
        "n": int(n), "base_rate": base, "threshold": float(threshold),
        "roc_auc": roc, "pr_auc": pr,
        "precision": float(prec), "recall": float(rec), "f1": float(f1),
        "accuracy": float((y_pred == y_true).mean()) if n else float("nan"),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "fpr": float(fp / (fp + tn)) if (fp + tn) else float("nan"),
        "fnr": float(fn / (fn + tp)) if (fn + tp) else float("nan"),
        "n_signals": int(y_pred.sum()),
        "signal_rate": float(y_pred.mean()) if n else float("nan"),
        "lift": float(prec / base) if base else float("nan"),
        "edge_vs_base": float(prec - base),
    }
    if n_days:
        out["signals_per_day"] = round(out["n_signals"] / n_days, 3)
    return out


def threshold_curve(y_true, y_prob, grid, excursion=None,
                    n_days: int | None = None) -> pd.DataFrame:
    """Curva threshold x precision x n_sinais x excursao esperada (secao 25)."""
    rows = []
    for th in grid:
        m = classification_metrics(y_true, y_prob, th, n_days)
        if excursion is not None:
            sel = np.asarray(y_prob) >= th
            e = np.asarray(excursion, dtype=float)[sel]
            e = e[~np.isnan(e)]
            m["mean_excursion_bricks"] = float(e.mean()) if len(e) else float("nan")
            m["median_excursion_bricks"] = float(np.median(e)) if len(e) else float("nan")
        rows.append(m)
    return pd.DataFrame(rows)


def bootstrap_ci(y_true, y_prob, stat="roc_auc", n_boot: int = 1000,
                 seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, int)
    y_prob = np.asarray(y_prob, float)
    n = len(y_true)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt, yp = y_true[idx], y_prob[idx]
        if len(np.unique(yt)) < 2:
            continue
        vals.append(roc_auc_score(yt, yp) if stat == "roc_auc"
                    else average_precision_score(yt, yp))
    if not vals:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def delong_like_pvalue(y_true, prob_a, prob_b, n_boot: int = 2000,
                       seed: int = 42) -> float:
    """p-valor bilateral bootstrap para AUC(a) - AUC(b) == 0 (pareado)."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, int)
    a, b = np.asarray(prob_a, float), np.asarray(prob_b, float)
    n = len(y_true)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        diffs.append(roc_auc_score(yt, a[idx]) - roc_auc_score(yt, b[idx]))
    if not diffs:
        return float("nan")
    diffs = np.asarray(diffs)
    p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return float(min(p, 1.0))


def metrics_by_group(df: pd.DataFrame, group_col: str, threshold: float,
                     y_col: str = "y", p_col: str = "prob") -> pd.DataFrame:
    rows = []
    for g, sub in df.groupby(group_col, observed=True):
        if len(sub) < 30:
            continue
        m = classification_metrics(sub[y_col], sub[p_col], threshold)
        m[group_col] = g
        rows.append(m)
    if not rows:
        return pd.DataFrame()
    cols = [group_col] + [c for c in rows[0] if c != group_col]
    return pd.DataFrame(rows)[cols]
