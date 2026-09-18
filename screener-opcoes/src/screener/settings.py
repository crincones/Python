"""Leitura e validação de config/settings.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    model_validator,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
WEIGHT_SUM_TOLERANCE = 1e-9


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _check_weight_sum(weights: BaseModel) -> None:
    total = sum(weights.model_dump().values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"pesos devem somar 1, somam {total}")


class MT5Settings(_Strict):
    terminal_path: Path
    portable: bool
    launch_if_closed: bool
    close_if_launched: bool
    startup_timeout_seconds: PositiveFloat
    startup_stable_seconds: NonNegativeFloat
    shutdown_timeout_seconds: PositiveFloat
    init_retries: PositiveInt
    retry_wait_seconds: NonNegativeFloat
    select_batch_size: PositiveInt
    quote_poll_seconds: PositiveFloat
    quote_min_wait_seconds: NonNegativeFloat
    quote_wait_timeout_seconds: PositiveFloat
    feed_cooldown_seconds: NonNegativeFloat
    server_timezone: str


class PathSettings(_Strict):
    snapshots_dir: Path
    output_dir: Path
    logs_dir: Path
    holidays_file: Path
    dividends_file: Path

    def resolved(self, root: Path) -> PathSettings:
        return PathSettings(**{k: root / v for k, v in self.model_dump().items()})


class PublishSettings(_Strict):
    """Envio do relatório para o servidor que o serve na tailnet (SSH/SFTP + nginx)."""

    enabled: bool
    host: str
    port: PositiveInt
    user: str
    private_key: Path | None  # None = chaves padrão do ~/.ssh e agente SSH
    known_hosts: Path
    strict_host_key: bool
    remote_dir: str  # raiz servida pelo nginx, caminho absoluto no servidor
    history_subdir: str  # subpasta dos relatórios datados
    latest_name: str  # nome público (link para o relatório desta execução)
    keep_reports: PositiveInt
    timeout_seconds: PositiveFloat
    public_url: str

    @model_validator(mode="after")
    def _remote_paths(self) -> PublishSettings:
        if not self.remote_dir.startswith("/") or self.remote_dir.endswith("/"):
            raise ValueError("remote_dir deve ser um caminho absoluto sem barra no fim")
        for field in ("history_subdir", "latest_name"):
            value: str = getattr(self, field)
            if not value or "/" in value:
                raise ValueError(f"{field} deve ser um nome simples, sem barras")
        return self


class LoggingSettings(_Strict):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    max_bytes: PositiveInt
    backup_count: NonNegativeInt


class CollectorSettings(_Strict):
    strike_range_pct_spot: PositiveFloat
    history_retries: PositiveInt
    feed_retries: PositiveInt
    min_quoted_series_fraction: NonNegativeFloat


class UnderlyingFilterSettings(_Strict):
    excluded_underlyings: list[str]
    lookback_sessions: PositiveInt
    min_avg_daily_turnover_brl: NonNegativeFloat
    max_underlyings: PositiveInt
    min_listed_series: NonNegativeInt


class LiquidityWeights(_Strict):
    spread: NonNegativeFloat
    turnover: NonNegativeFloat
    deals: NonNegativeFloat
    open_interest: NonNegativeFloat

    @model_validator(mode="after")
    def _sum_to_one(self) -> LiquidityWeights:
        _check_weight_sum(self)
        return self


class SeriesLiquiditySettings(_Strict):
    max_spread_pct_mid: PositiveFloat
    min_mid_price_brl: NonNegativeFloat
    min_turnover_brl: NonNegativeFloat
    min_deals: NonNegativeInt
    min_open_interest: NonNegativeInt | None
    max_quote_age_seconds: PositiveFloat
    weights: LiquidityWeights


class SpreadSettings(_Strict):
    lot_size: PositiveInt
    dte_min_business_days: NonNegativeInt
    dte_max_business_days: PositiveInt
    max_width_pct_spot: PositiveFloat

    @model_validator(mode="after")
    def _dte_window(self) -> SpreadSettings:
        if self.dte_min_business_days > self.dte_max_business_days:
            raise ValueError("dte_min_business_days maior que dte_max_business_days")
        return self


class MarketSettings(_Strict):
    risk_free_rate_source: Literal["b3", "yaml"]
    risk_free_rate_annual: NonNegativeFloat
    b3_indicators_url: str
    b3_cdi_description: str
    b3_timeout_seconds: PositiveFloat
    max_rate_age_days: PositiveInt


class PricingSettings(_Strict):
    iv_lower_bound: PositiveFloat
    iv_upper_bound: PositiveFloat
    iv_tolerance: PositiveFloat
    iv_max_iterations: PositiveInt
    atm_max_spread_pct_mid: PositiveFloat
    atm_max_strike_distance_pct: PositiveFloat

    @model_validator(mode="after")
    def _bounds(self) -> PricingSettings:
        if self.iv_lower_bound >= self.iv_upper_bound:
            raise ValueError("iv_lower_bound deve ser menor que iv_upper_bound")
        return self


class ScoringWeights(_Strict):
    execution_cost: NonNegativeFloat
    liquidity: NonNegativeFloat
    reward_risk: NonNegativeFloat

    @model_validator(mode="after")
    def _sum_to_one(self) -> ScoringWeights:
        _check_weight_sum(self)
        return self


class ScoringSettings(_Strict):
    pop_min: float
    pop_max: float
    weights: ScoringWeights

    @model_validator(mode="after")
    def _pop_band(self) -> ScoringSettings:
        if not 0 <= self.pop_min < self.pop_max <= 1:
            raise ValueError("faixa de POP inválida: exige 0 ≤ pop_min < pop_max ≤ 1")
        return self


Timeframe = Literal["d1", "h4"]
BiasValue = Literal["alta", "baixa", "neutro"]


class TrendSettings(_Strict):
    ema_fast: PositiveInt
    ema_slow: PositiveInt

    @model_validator(mode="after")
    def _order(self) -> TrendSettings:
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast deve ser menor que ema_slow")
        return self


class SignalSettings(_Strict):
    enabled: bool
    bars: PositiveInt
    min_bars: PositiveInt
    timeframes: dict[Timeframe, TrendSettings]

    @model_validator(mode="after")
    def _bars(self) -> SignalSettings:
        if self.min_bars > self.bars:
            raise ValueError("min_bars maior que bars")
        return self


class EarlyExerciseAlertSettings(_Strict):
    min_extrinsic_pct_premium: NonNegativeFloat
    min_extrinsic_brl: NonNegativeFloat


class CheckSettings(_Strict):
    sample_underlyings: PositiveInt
    sample_series_per_underlying: PositiveInt


class Settings(_Strict):
    mt5: MT5Settings
    paths: PathSettings
    publish: PublishSettings
    logging: LoggingSettings
    collector: CollectorSettings
    underlying_filter: UnderlyingFilterSettings
    series_liquidity: SeriesLiquiditySettings
    spreads: SpreadSettings
    market: MarketSettings
    pricing: PricingSettings
    bias: dict[str, BiasValue]
    signals: SignalSettings
    scoring: ScoringSettings
    early_exercise_alert: EarlyExerciseAlertSettings
    check: CheckSettings


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    """Carrega o YAML, valida e resolve caminhos relativos à raiz do projeto."""
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    settings = Settings.model_validate(raw)
    root = path.resolve().parent.parent
    return settings.model_copy(update={"paths": settings.paths.resolved(root)})
