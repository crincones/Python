"""Pipeline mínimo (CLAUDE.md, seção 43): dados → setups → backtest → estatísticas → relatório.

Cada execução grava em results/AAAAMMDD_HHMMSS/ (nunca sobrescreve) e atualiza reports/.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from mtf.backtest.engine import run_backtest, trades_frame
from mtf.config import PROJECT_ROOT, Settings, Variant, config_hash, data_dir
from mtf.data.quality import quality_report
from mtf.data.store import available_symbols, load_market_data
from mtf.data.timeutils import now_local
from mtf.models import MarketData
from mtf.signals.setups import build_features, build_setups
from mtf.statistics.metrics import (
    distance_buckets,
    filter_increment,
    overfitting_warnings,
    robustness_across_assets,
    summarize,
    summarize_by,
)
from mtf.universe.selection import history_summary

log = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    run_dir: Path
    meta: dict
    universe: pd.DataFrame
    quality: pd.DataFrame
    trades: pd.DataFrame
    comparison: pd.DataFrame
    by_asset: pd.DataFrame
    by_year: pd.DataFrame
    buckets: pd.DataFrame
    liquidity: pd.DataFrame
    increments: pd.DataFrame
    warnings: dict[str, list[str]]
    market: dict[str, MarketData] = field(default_factory=dict)
    features: dict[str, pd.DataFrame] = field(default_factory=dict)


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "desconhecido"


def backtest_variant(
    market: dict[str, MarketData],
    features: dict[str, pd.DataFrame],
    variant: Variant,
    settings: Settings,
) -> tuple[pd.DataFrame, int]:
    frames, setup_count = [], 0
    for symbol, data in market.items():
        setups = build_setups(features[symbol], variant, settings, symbol)
        setup_count += len(setups)
        trades = run_backtest(data.h1, setups, variant, settings)
        frame = trades_frame(trades, setups, settings.forward_bars)
        if not frame.empty:
            frames.append(frame)
    trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return trades, setup_count


def liquidity_robustness(
    market: dict[str, MarketData],
    features: dict[str, pd.DataFrame],
    variant: Variant,
    settings: Settings,
) -> pd.DataFrame:
    """Refaz a variante com cada mínimo de liquidez da seção 2."""
    rows = []
    for threshold in settings.universe.robustness_thresholds:
        universe = settings.universe.model_copy(update={"min_average_daily_value": threshold})
        adjusted = settings.model_copy(update={"universe": universe})
        trades, _ = backtest_variant(market, features, variant, adjusted)
        rows.append(
            {
                "min_average_daily_value": threshold,
                **summarize(trades, settings.forward_bars),
                **(robustness_across_assets(trades) if not trades.empty else {}),
            }
        )
    return pd.DataFrame(rows)


def run_research(settings: Settings, raw_dir: Path | None = None) -> ResearchResult:
    raw_dir = raw_dir or data_dir() / "raw"
    started = now_local()
    run_dir = PROJECT_ROOT / "results" / started.strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=False)

    symbols = available_symbols(raw_dir)
    if not symbols:
        raise FileNotFoundError(f"nenhum ativo com D1/H4/H1 em {raw_dir}; rode `mtf download`")
    market = {symbol: load_market_data(raw_dir, symbol) for symbol in symbols}

    universe_path = data_dir() / "metadata" / "universe.parquet"
    listed = pd.read_parquet(universe_path) if universe_path.exists() else pd.DataFrame()
    history = pd.DataFrame(
        history_summary(s, {"D1": m.d1, "H4": m.h4, "H1": m.h1}, settings.data.min_history_years)
        for s, m in market.items()
    )
    if not listed.empty:
        history = history.merge(
            listed[
                [
                    "symbol",
                    "description",
                    "listed_options",
                    "options_available",
                    "average_daily_value",
                ]
            ],
            on="symbol",
            how="left",
        )
    quality = pd.DataFrame(
        quality_report(m, settings.quality.max_overnight_gap_pct) for m in market.values()
    )
    features = {symbol: build_features(data, settings) for symbol, data in market.items()}

    all_trades, rows, warnings = [], [], {}
    for variant in settings.variants:
        trades, setup_count = backtest_variant(market, features, variant, settings)
        log.info("%s: %d setups, %d trades", variant.name, setup_count, len(trades))
        rows.append(
            {
                "variant": variant.name,
                "filter": variant.filter,
                "trigger": variant.trigger,
                "max_distance_atr": variant.max_distance_atr,
                "touch": variant.touch,
                "setups": setup_count,
                **summarize(trades, settings.forward_bars, settings.bootstrap_samples),
                **(robustness_across_assets(trades) if not trades.empty else {}),
            }
        )
        warnings[variant.name] = overfitting_warnings(trades, settings.warnings)
        if not trades.empty:
            all_trades.append(trades)
    trades = pd.concat(all_trades, ignore_index=True)
    trades["year"] = trades["exit_time"].dt.year
    comparison = pd.DataFrame(rows)
    by_asset = summarize_by(trades, ["variant", "symbol"], settings.forward_bars)
    by_year = summarize_by(trades, ["variant", "year"], settings.forward_bars)
    baseline = settings.variant(settings.baseline_variant)
    pullback = trades[trades["variant"] == baseline.name]
    buckets = distance_buckets(pullback, settings.distance_buckets_atr, settings.forward_bars)
    liquidity = liquidity_robustness(market, features, baseline, settings)
    increments = pd.DataFrame(
        {
            "label": inc.label,
            **filter_increment(
                trades, inc.base, inc.test, settings.bootstrap_samples, settings.warnings.min_trades
            ),
        }
        for inc in settings.increments
    )

    first = min(m.h1["time"].iloc[0] for m in market.values())
    last = max(m.h1["time"].iloc[-1] for m in market.values())
    meta = {
        "timestamp": started.isoformat(),
        "git_commit": git_commit(),
        "config_hash": config_hash(),
        "data_range": {"first_bar": first.isoformat(), "last_bar": last.isoformat()},
        "test_start_date": settings.data.test_start_date.isoformat(),
        "number_of_assets": len(market),
        "symbols": symbols,
        "number_of_trades": int(len(trades)),
        "parameters": settings.model_dump(mode="json"),
    }
    download_meta = data_dir() / "metadata" / "download.json"
    if download_meta.exists():
        meta["download"] = json.loads(download_meta.read_text(encoding="utf-8"))

    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    trades.to_parquet(run_dir / "trades.parquet", index=False)
    trades.to_csv(run_dir / "trades.csv", index=False)
    for name, frame in (
        ("comparison", comparison),
        ("by_asset", by_asset),
        ("by_year", by_year),
        ("distance_buckets", buckets),
        ("liquidity_robustness", liquidity),
        ("increments", increments),
        ("universe", history),
        ("quality", quality),
    ):
        frame.to_csv(run_dir / f"{name}.csv", index=False)
    (run_dir / "warnings.json").write_text(
        json.dumps(warnings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return ResearchResult(
        run_dir=run_dir,
        meta=meta,
        universe=history,
        quality=quality,
        trades=trades,
        comparison=comparison,
        by_asset=by_asset,
        by_year=by_year,
        buckets=buckets,
        liquidity=liquidity,
        increments=increments,
        warnings=warnings,
        market=market,
        features=features,
    )


def publish_reports(run_reports: Path) -> Path:
    """Copia os relatórios da execução para reports/ (visão mais recente)."""
    target = PROJECT_ROOT / "reports"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(run_reports, target)
    return target
