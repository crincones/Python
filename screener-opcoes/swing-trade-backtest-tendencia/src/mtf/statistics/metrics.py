"""Métricas dos trades (CLAUDE.md, seções 18, 19, 21, 22 e 23). Unidade principal: R."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mtf.config import WarningSettings


def max_drawdown_r(r: pd.Series) -> float:
    """Maior queda da curva acumulada em R (trades em ordem de saída)."""
    if r.empty:
        return 0.0
    equity = np.concatenate([[0.0], r.cumsum().to_numpy()])
    return float((np.maximum.accumulate(equity) - equity).max())


def bootstrap_ci(r: pd.Series, samples: int, seed: int = 0) -> tuple[float, float]:
    """IC 95% da média de R por bootstrap."""
    if len(r) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    values = r.to_numpy()
    means = rng.choice(values, (samples, len(values))).mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)


def summarize(trades: pd.DataFrame, forward_bars: list[int], bootstrap: int = 0) -> dict:
    if trades.empty:
        return {"number_of_trades": 0}
    ordered = trades.sort_values("exit_time")
    r = ordered["r_multiple"]
    wins, losses = r[r > 0], r[r <= 0]
    gross_profit, gross_loss = float(wins.sum()), float(-losses.sum())
    summary = {
        "number_of_trades": len(r),
        "win_rate": float((r > 0).mean()),
        "loss_rate": float((r <= 0).mean()),
        "average_R": float(r.mean()),
        "median_R": float(r.median()),
        "expectancy": float(r.mean()),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else np.inf,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "max_drawdown": max_drawdown_r(r),
        "best_trade": float(r.max()),
        "worst_trade": float(r.min()),
        "average_return": float(ordered["return_pct"].mean()),
        "median_return": float(ordered["return_pct"].median()),
        "average_trade_duration": float(ordered["bars_held"].mean()),
        "MFE": float(ordered["mfe_r"].mean()),
        "MAE": float(ordered["mae_r"].mean()),
        "target_rate": float((ordered["exit_reason"] == "target").mean()),
        "stop_rate": float((ordered["exit_reason"] == "stop").mean()),
    }
    for n in forward_bars:
        column = f"r_after_{n}_bars"
        if column in ordered:
            summary[f"return_after_{n}_bars"] = float(ordered[column].mean())
    if bootstrap:
        summary["expectancy_ci_low"], summary["expectancy_ci_high"] = bootstrap_ci(r, bootstrap)
    return summary


def summarize_by(trades: pd.DataFrame, keys: list[str], forward_bars: list[int]) -> pd.DataFrame:
    rows = [
        {
            **dict(zip(keys, key if isinstance(key, tuple) else (key,), strict=True)),
            **summarize(group, forward_bars),
        }
        for key, group in trades.groupby(keys, observed=True)
    ]
    return pd.DataFrame(rows)


def robustness_across_assets(trades: pd.DataFrame) -> dict:
    per_asset = trades.groupby("symbol")["r_multiple"].mean()
    return {
        "assets_traded": len(per_asset),
        "median_expectancy_across_assets": float(per_asset.median()) if len(per_asset) else np.nan,
        "percentage_of_assets_profitable": float((per_asset > 0).mean())
        if len(per_asset)
        else np.nan,
    }


def _concentration(who: str, part: float, total: float) -> str:
    text = f"{who}: {part:.1f}R de um resultado total de {total:.1f}R ({part / total:.0%})"
    return text.replace(".", ",")


def overfitting_warnings(trades: pd.DataFrame, cfg: WarningSettings) -> list[str]:
    """Alertas da seção 23 (concentração e amostra pequena)."""
    alerts: list[str] = []
    n = len(trades)
    if n < cfg.min_trades:
        alerts.append(f"poucas operações ({n} < {cfg.min_trades})")
    if n == 0:
        return alerts
    r = trades["r_multiple"]
    total = r.sum()
    if total > 0:
        by_asset = trades.groupby("symbol")["r_multiple"].sum()
        if by_asset.max() / total > cfg.max_asset_profit_share:
            alerts.append(_concentration(str(by_asset.idxmax()), by_asset.max(), total))
        by_year = trades.groupby(trades["exit_time"].dt.year)["r_multiple"].sum()
        if by_year.max() / total > cfg.max_year_profit_share:
            alerts.append(_concentration(str(by_year.idxmax()), by_year.max(), total))
        top5 = r.nlargest(5).sum()
        if top5 / total > cfg.max_top5_trades_profit_share:
            alerts.append(_concentration("os 5 melhores trades", top5, total))
    return alerts


def distance_buckets(
    trades: pd.DataFrame, edges: list[float], forward_bars: list[int]
) -> pd.DataFrame:
    """Resultado em função da distância à MM D1 (buckets em ATR D1, seção 19)."""
    bins = [*edges, np.inf]
    labels = [
        (f"{lo:.2f}–{hi:.2f}" if np.isfinite(hi) else f"{lo:.2f}+").replace(".", ",")
        for lo, hi in zip(bins[:-1], bins[1:], strict=True)
    ]
    bucketed = trades.assign(
        bucket=pd.cut(trades["dist_d1_ma_atr"], bins=bins, labels=labels, right=False)
    )
    return summarize_by(bucketed, ["bucket"], forward_bars)


def bootstrap_diff_ci(
    a: pd.Series, b: pd.Series, samples: int, seed: int = 0
) -> tuple[float, float]:
    """IC 95% de mean(b) − mean(a) por bootstrap independente das duas amostras."""
    if len(a) < 2 or len(b) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    mean_a = rng.choice(a.to_numpy(), (samples, len(a))).mean(axis=1)
    mean_b = rng.choice(b.to_numpy(), (samples, len(b))).mean(axis=1)
    low, high = np.percentile(mean_b - mean_a, [2.5, 97.5])
    return float(low), float(high)


def filter_increment(
    trades: pd.DataFrame, base: str, test: str, samples: int, min_trades: int
) -> dict:
    """Quanto a variante `test` muda a expectativa em relação à `base` (seções 17 e 41)."""
    a = trades.loc[trades["variant"] == base, "r_multiple"]
    b = trades.loc[trades["variant"] == test, "r_multiple"]
    low, high = bootstrap_diff_ci(a, b, samples)
    if min(len(a), len(b)) < min_trades:
        verdict = "amostra pequena"
    elif low > 0:
        verdict = "melhora"
    elif high < 0:
        verdict = "piora"
    else:
        verdict = "sem diferença estatística"
    return {
        "base": base,
        "test": test,
        "trades_base": len(a),
        "trades_test": len(b),
        "expectancy_base": float(a.mean()) if len(a) else np.nan,
        "expectancy_test": float(b.mean()) if len(b) else np.nan,
        "delta_expectancy": float(b.mean() - a.mean()) if len(a) and len(b) else np.nan,
        "delta_ci_low": low,
        "delta_ci_high": high,
        "verdict": verdict,
    }
