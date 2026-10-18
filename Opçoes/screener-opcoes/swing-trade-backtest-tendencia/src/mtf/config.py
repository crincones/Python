"""Configuração (config/*.yaml) validada por pydantic."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILES = ("universe.yaml", "strategy.yaml", "backtest.yaml")


class MT5Settings(BaseModel):
    terminal_path: Path
    portable: bool = True
    launch_if_closed: bool = True
    close_if_launched: bool = True
    startup_timeout_seconds: float = 180
    startup_stable_seconds: float = 5
    shutdown_timeout_seconds: float = 60
    init_retries: int = 3
    retry_wait_seconds: float = 2.0
    history_retries: int = 3
    server_timezone: str = "America/Sao_Paulo"


class DataSettings(BaseModel):
    start_date: dt.date
    end_date: dt.date | None = None
    test_start_date: dt.date
    timeframes: list[Literal["D1", "H4", "H1"]]
    min_history_years: float = 2.0


class UniverseSettings(BaseModel):
    stock_path: str
    options_path: str
    excluded: list[str] = Field(default_factory=list)
    liquidity_window: int = 60
    min_average_daily_value: float = 5_000_000
    robustness_thresholds: list[float] = Field(default_factory=list)
    pilot_assets: int = 5


class QualitySettings(BaseModel):
    max_overnight_gap_pct: float = 0.20


class MASettings(BaseModel):
    ma_type: Literal["SMA", "EMA"] = "SMA"
    ma_period: int = 21
    slope_period: int = 5


class TrendSettings(BaseModel):
    d1: MASettings
    h4: MASettings


class PullbackSettings(BaseModel):
    min_bars: int = 2
    max_bars: int = 5


class ReferenceSettings(BaseModel):
    ma_type: Literal["SMA", "EMA"] = "SMA"
    ma_period: int = 21
    atr_period: int = 14
    h4_ma_period: int = 21
    impulse_lookback: int = 20


class EntrySettings(BaseModel):
    valid_bars: int = 1


class RiskSettings(BaseModel):
    stop: Literal["structural"] = "structural"
    stop_buffer_atr_h1: float = 0.0
    atr_period_h1: int = 14
    target_r: float = 2.0
    max_holding_bars: int = 70
    benchmark_stop_lookback: int = 3


class Variant(BaseModel):
    name: str
    filter: Literal["random", "trend", "pullback"]
    trigger: Literal["break", "immediate"] = "break"
    max_distance_atr: float | None = None
    touch: bool = False


class CostSettings(BaseModel):
    fees_bps_per_side: float = 0.0
    slippage_ticks: int = 0
    tick_size: float = 0.01


class RandomBenchmarkSettings(BaseModel):
    seed: int = 42
    probability: float = 0.10


class WarningSettings(BaseModel):
    min_trades: int = 30
    max_asset_profit_share: float = 0.5
    max_year_profit_share: float = 0.5
    max_top5_trades_profit_share: float = 0.5


class ExampleSettings(BaseModel):
    per_category: int = 10
    bars_before: int = 80
    bars_after: int = 20
    context_bars: int = 120


class Increment(BaseModel):
    label: str
    base: str
    test: str


class KLineSettings(BaseModel):
    version: str = "9.8.12"
    cache: Path = Path("data/cache/klinecharts.min.js")


class Settings(BaseModel):
    mt5: MT5Settings
    data: DataSettings
    universe: UniverseSettings
    quality: QualitySettings
    trend: TrendSettings
    pullback: PullbackSettings
    reference: ReferenceSettings
    entry: EntrySettings
    risk: RiskSettings
    variants: list[Variant]
    costs: CostSettings
    random_benchmark: RandomBenchmarkSettings
    forward_bars: list[int]
    bootstrap_samples: int = 2000
    warnings: WarningSettings
    distance_buckets_atr: list[float]
    baseline_variant: str
    examples: ExampleSettings
    increments: list[Increment]
    klinecharts: KLineSettings

    def variant(self, name: str) -> Variant:
        for variant in self.variants:
            if variant.name == name:
                return variant
        raise KeyError(f"variante inexistente: {name}")


def load_settings(config_dir: Path = CONFIG_DIR) -> Settings:
    merged: dict = {}
    for name in CONFIG_FILES:
        with (config_dir / name).open(encoding="utf-8") as file:
            merged.update(yaml.safe_load(file) or {})
    return Settings.model_validate(merged)


def config_hash(config_dir: Path = CONFIG_DIR) -> str:
    digest = hashlib.sha256()
    for name in CONFIG_FILES:
        digest.update((config_dir / name).read_bytes())
    return digest.hexdigest()[:16]


def data_dir() -> Path:
    return PROJECT_ROOT / "data"
