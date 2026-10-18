"""Estruturas centrais (CLAUDE.md, seção 29): dados de mercado, estados, setups e trades.

Descoberta de sinais (trend/, pullback/, signals/) produz a tabela de setups; a simulação de
execução (backtest/) consome essa tabela. As duas etapas não se misturam.

Barras: DataFrame com colunas BAR_COLUMNS, ordenado por `time` (abertura da barra, tz
America/Sao_Paulo) e `close_time` (instante a partir do qual a barra está fechada e pode ser
usada numa decisão).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

import pandas as pd

LOCAL_TIMEZONE = "America/Sao_Paulo"
TIMEFRAMES = ("D1", "H4", "H1")
TIMEFRAME_DELTA = {
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    # A barra D1 tem timestamp 00:00 do pregão; só é considerada fechada à meia-noite seguinte.
    "D1": pd.Timedelta(days=1),
}
BAR_COLUMNS = (
    "time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "real_volume",
)


class TrendState(IntEnum):
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1


@dataclass
class MarketData:
    symbol: str
    d1: pd.DataFrame
    h4: pd.DataFrame
    h1: pd.DataFrame


# Colunas da tabela de setups (uma linha por barra H1 candidata, decidida no fechamento dela):
SETUP_COLUMNS = {
    "symbol": "ativo",
    "bar": "índice da barra H1 do sinal (a entrada só pode ocorrer a partir de bar + 1)",
    "time": "abertura da barra do sinal",
    "direction": "+1 compra, -1 venda",
    "trigger_price": "máxima (compra) ou mínima (venda) da barra do sinal",
    "stop_price": "stop estrutural",
    "d1_trend": "estado D1 com a última barra D1 fechada",
    "h4_trend": "estado H4 com a última barra H4 fechada",
    "pullback_bars": "candles H1 consecutivos contra a tendência até o sinal (0 = sem retração)",
    "pullback_low": "mínima da retração",
    "pullback_high": "máxima da retração",
    "pullback_start": "índice da primeira barra da retração",
    "impulse_size_atr_d1": "amplitude (máx − mín) das barras H1 antes da retração, em ATR D1",
    "pullback_depth_atr_d1": "extremo do impulso até o extremo da retração, em ATR D1",
    "d1_ma": "MM de referência D1 (última barra D1 fechada)",
    "h4_ma": "MM H4 (última barra H4 fechada)",
    "atr_d1": "ATR D1",
    "atr_h4": "ATR H4",
    "atr_h1": "ATR H1",
    "dist_d1_ma_atr": "|fechamento − MM D1| / ATR D1",
    "signed_dist_d1_ma_atr": "(fechamento − MM D1) / ATR D1 × direção (> 0 = lado da tendência)",
    "dist_h4_ma_atr": "|fechamento − MM H4| / ATR H4",
    "touch_d1_ma": "a retração tocou a MM D1",
    "adv": "volume financeiro médio do ativo (última barra D1 fechada)",
}


@dataclass
class Trade:
    symbol: str
    variant: str
    direction: int
    signal_bar: int
    entry_bar: int
    exit_bar: int
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    stop_price: float
    target_price: float
    exit_price: float
    exit_reason: str
    r_multiple: float
    return_pct: float
    mfe_r: float
    mae_r: float
    bars_held: int
    forward_r: dict[int, float] = field(default_factory=dict)


@dataclass
class BacktestResult:
    variant: str
    trades: pd.DataFrame
    setups: int
