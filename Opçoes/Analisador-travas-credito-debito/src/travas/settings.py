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
WEIGHT_SUM_TOLERANCE = 1e-6


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


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
    holidays_file: Path
    logs_dir: Path
    preferences_file: Path
    tracking_file: Path
    quotes_dir: Path
    icons_dir: Path

    def resolved(self, root: Path) -> PathSettings:
        return PathSettings(**{k: root / v for k, v in self.model_dump().items()})


class ServerSettings(_Strict):
    host: str
    port: PositiveInt
    open_browser: bool


class MarketHoursSettings(_Strict):
    session_open: str  # HH:MM, horário de Brasília
    session_close: str


class IconSettings(_Strict):
    enabled: bool
    source_url: str  # {name} = ticker completo ou raiz (ex.: BOVA11, PETR)
    timeout_seconds: PositiveFloat


class LoggingSettings(_Strict):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    max_bytes: PositiveInt
    backup_count: NonNegativeInt


class CollectionSettings(_Strict):
    strike_range_pct_spot: PositiveFloat  # séries coletadas: strikes a até X% do spot
    max_dte_business_days: PositiveInt  # vencimentos coletados
    catalog_cache_minutes: PositiveFloat
    chain_cache_seconds: NonNegativeFloat
    stale_feed_minutes: PositiveFloat  # tick do ativo mais velho que isso (relógio do PC) = aviso


class LiquiditySettings(_Strict):
    max_spread_pct_mid: PositiveFloat
    min_mid_price_brl: NonNegativeFloat
    min_turnover_brl: NonNegativeFloat
    min_deals: NonNegativeInt
    max_quote_age_seconds: PositiveFloat


class PricingSettings(_Strict):
    risk_free_rate_annual: float
    iv_lower_bound: PositiveFloat
    iv_upper_bound: PositiveFloat
    iv_tolerance: PositiveFloat
    iv_max_iterations: PositiveInt
    atm_max_spread_pct_mid: PositiveFloat
    atm_max_strike_distance_pct: PositiveFloat


class RankingWeights(_Strict):
    scenario: NonNegativeFloat  # resultado no cenário-alvo / perda máxima
    reward_risk: NonNegativeFloat  # lucro máximo / perda máxima
    pop: NonNegativeFloat  # probabilidade de lucro no vencimento
    liquidity: NonNegativeFloat  # pior perna
    execution_cost: NonNegativeFloat  # (natural − mid) / largura, menor é melhor

    @model_validator(mode="after")
    def _sum(self) -> RankingWeights:
        total = sum(self.model_dump().values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"pesos do ranking devem somar 1, somam {total}")
        return self


class AnalysisSettings(_Strict):
    dte_min_business_days: NonNegativeInt
    dte_max_business_days: PositiveInt
    max_width_pct_spot: PositiveFloat
    quantity: PositiveInt
    limit_aggressiveness: float  # 0 = mid, 1 = preço natural (cruzar o book)
    illiquid_score_cap: float  # teto do score de estruturas com liquidez/cotação reprovada
    weights: RankingWeights
    max_results: PositiveInt


class EarlyExerciseSettings(_Strict):
    min_extrinsic_brl: NonNegativeFloat
    min_extrinsic_pct_premium: NonNegativeFloat


class CandleSettings(_Strict):
    bars: PositiveInt
    ema_fast: PositiveInt
    ema_slow: PositiveInt


class Settings(_Strict):
    mt5: MT5Settings
    paths: PathSettings
    server: ServerSettings
    logging: LoggingSettings
    collection: CollectionSettings
    liquidity: LiquiditySettings
    pricing: PricingSettings
    analysis: AnalysisSettings
    early_exercise: EarlyExerciseSettings
    candles: CandleSettings
    market_hours: MarketHoursSettings
    icons: IconSettings


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    settings = Settings.model_validate(raw)
    return settings.model_copy(update={"paths": settings.paths.resolved(PROJECT_ROOT)})
