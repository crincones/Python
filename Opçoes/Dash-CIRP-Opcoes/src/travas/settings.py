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
    watchlist_file: Path = Path("data/favoritos.json")
    quotes_dir: Path
    icons_dir: Path
    snapshots_dir: Path = Path("data/snapshots")
    google_calendar_file: Path = Path("data/google_agenda.json")  # id da agenda + token cifrado
    google_drive_file: Path = Path("data/google_drive.json")  # ids da pasta/arquivos no Drive
    alert_contacts_file: Path = Path("telegram-token.txt")  # bot, chat id e e-mail (fora do git)
    alerts_sent_file: Path = Path("data/alertas_stop.json")  # alertas já enviados pelo app

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
    # Mercado fechado: fechamento oficial da B3 (último negócio), capturas do pregão (bid/ask)
    # ou snapshots gravados pelo coletor do servidor (bid/ask em horários fixos).
    off_hours_source: Literal["b3", "capturas", "servidor"] = "b3"


class SnapshotSettings(_Strict):
    """Snapshots da cadeia gravados no servidor (`travas snapshot`) e lidos pelo app."""

    server_url: str  # onde o app busca index.json e os arquivos (ex.: via Tailscale)
    timeout_seconds: PositiveFloat
    expirations: PositiveInt  # coletor: próximos N vencimentos MENSAIS de cada ativo
    weekly_max_business_days: NonNegativeInt  # + semanais com até isto de prazo (0 = nenhum)
    max_underlyings: PositiveInt  # coletor: só os N ativos com opções mais líquidas
    liquidity_sessions: PositiveInt  # pregões (arquivo da B3) na média da liquidez


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
    lot_size: PositiveInt = 100  # múltiplo usado ao converter valor a investir em quantidade
    limit_aggressiveness: float  # 0 = mid, 1 = preço natural (cruzar o book)
    illiquid_score_cap: float  # teto do score de estruturas com liquidez/cotação reprovada
    weights: RankingWeights
    max_results: PositiveInt


class CreditStopWeights(_Strict):
    expected: NonNegativeFloat  # resultado esperado com o stop ÷ perda no stop
    no_stop: NonNegativeFloat  # probabilidade de não acionar o stop
    capital: NonNegativeFloat  # crédito ÷ garantia (largura − crédito)
    liquidity: NonNegativeFloat  # pior perna (a saída no stop exige liquidez)
    exit_cost: NonNegativeFloat  # (natural − mid) ÷ crédito, menor é melhor

    @model_validator(mode="after")
    def _sum(self) -> CreditStopWeights:
        total = sum(self.model_dump().values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"pesos do stop 1:1 devem somar 1, somam {total}")
        return self


class CreditStopSettings(_Strict):
    """Travas de crédito com stop quando o prejuízo iguala o lucro máximo (Credit Spread
    Investing): fronteira do stop pelo modelo e Monte Carlo do manejo."""

    loss_multiple: PositiveFloat  # stop quando a perda = isto × crédito (1 = 1:1)
    paths: PositiveInt  # caminhos do Monte Carlo (pares antitéticos)
    weights: CreditStopWeights


class CalendarReminder(_Strict):
    business_days_before: NonNegativeInt  # 0 = no dia do vencimento
    time: str  # HH:MM (Brasília)


class AlertSettings(_Strict):
    """Alertas de stop 1:1 (Telegram + e-mail) das estruturas marcadas na Carteira."""

    enabled: bool = True
    server_url: str | None = "http://100.113.24.44:8767"  # redundância no servidor (Tailscale)
    timeout_seconds: PositiveFloat = 5


class VolPremiumSettings(_Strict):
    """Indicador IV/HV da aba Liquidez de Opções (ver options/vol_premium.py)."""

    expirations: PositiveInt = 3  # próximos vencimentos mensais no tooltip
    cheap_below: PositiveFloat = 0.90  # IV/HV abaixo disto = barata
    expensive_above: PositiveFloat = 1.20  # IV/HV acima disto = cara
    min_hv_window: PositiveInt = 10  # janela mínima da vol histórica (pregões)
    weak_book_spread: PositiveFloat = 0.15  # spread mediano ATM acima disto = pouco confiável
    min_book_quotes: NonNegativeInt = 4  # séries ATM com bid e ask abaixo disto = pouco confiável

    @model_validator(mode="after")
    def _ordered(self) -> VolPremiumSettings:
        if self.cheap_below >= self.expensive_above:
            raise ValueError("vol_premium: cheap_below deve ser menor que expensive_above")
        return self


class GoogleCalendarSettings(_Strict):
    """Eventos de vencimento das estruturas abertas no Google Agenda (ver tracking/gcal.py)."""

    enabled: bool = True
    client_secret_glob: str = "client_secret*.json"  # credencial OAuth na raiz do projeto
    calendar_name: str = "Dash CIRP – Vencimentos"
    event_time: str = "10:15"  # início do evento no dia do vencimento
    event_minutes: PositiveInt = 30
    reminders: list[CalendarReminder] = []
    sync_minutes: PositiveFloat = 30


class GoogleDriveSettings(_Strict):
    """Cópia da Carteira e dos favoritos no Google Drive (ver tracking/gdrive.py)."""

    enabled: bool = True
    folder_name: str = "Dash CIRP – Carteira"
    daily_history: bool = True  # também uma cópia por dia na subpasta "Histórico"
    sync_minutes: PositiveFloat = 60
    debounce_seconds: NonNegativeFloat = 5


class ProtectedWeights(_Strict):
    floor: NonNegativeFloat  # retorno mínimo (piso) ÷ CDI do período
    unchanged: NonNegativeFloat  # retorno com o ativo parado ÷ CDI
    max: NonNegativeFloat  # retorno máximo ÷ CDI
    prob_cdi: NonNegativeFloat  # probabilidade de superar o CDI no vencimento
    liquidity: NonNegativeFloat  # pior perna
    execution_cost: NonNegativeFloat  # (natural − mid) ÷ lucro máximo, menor é melhor

    @model_validator(mode="after")
    def _sum(self) -> ProtectedWeights:
        total = sum(self.model_dump().values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"pesos do ativo protegido devem somar 1, somam {total}")
        return self


class ProtectedSettings(_Strict):
    """Aba Ativo protegido: ativo + put + calls vendidas (collar e collar + borboleta)."""

    dte_min_business_days: NonNegativeInt
    dte_max_business_days: PositiveInt
    put_min_pct_spot: PositiveFloat  # faixa de strikes da put (fração do spot)
    put_max_pct_spot: PositiveFloat
    call_max_pct_spot: PositiveFloat  # strike máximo das calls
    max_wing_pct_spot: PositiveFloat  # borboleta: K2 − K1 ≤ isto × spot
    min_floor_return: float  # piso ≥ custo × (1 + isto); 0 = "risco zero"
    quantity: PositiveInt  # ações (lote)
    lot_size: PositiveInt  # múltiplo usado ao converter valor a investir em quantidade
    limit_aggressiveness: float
    illiquid_score_cap: float
    max_results: PositiveInt
    max_candidates: PositiveInt
    weights: ProtectedWeights


class EarlyExerciseSettings(_Strict):
    min_extrinsic_brl: NonNegativeFloat
    min_extrinsic_pct_premium: NonNegativeFloat


class CandleSettings(_Strict):
    bars: PositiveInt
    monthly_bars: PositiveInt = 100  # mensal: histórico do MT5 costuma ser curto
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
    protected: ProtectedSettings
    snapshots: SnapshotSettings
    credit_stop: CreditStopSettings
    google_calendar: GoogleCalendarSettings = GoogleCalendarSettings()
    google_drive: GoogleDriveSettings = GoogleDriveSettings()
    alerts: AlertSettings = AlertSettings()
    vol_premium: VolPremiumSettings = VolPremiumSettings()


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    settings = Settings.model_validate(raw)
    return settings.model_copy(update={"paths": settings.paths.resolved(PROJECT_ROOT)})
