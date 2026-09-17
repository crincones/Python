"""Viés direcional por ativo-objeto: sinal automático por tendência em D1/H4 + viés manual do YAML.

O sinal automático é uma sugestão transparente; o viés manual sempre prevalece.
"""

from __future__ import annotations

import pandas as pd

from screener.settings import BiasValue, SignalSettings, TrendSettings

BULLISH: BiasValue = "alta"
BEARISH: BiasValue = "baixa"
NEUTRAL: BiasValue = "neutro"

SOURCE_MANUAL = "manual"
SOURCE_AUTO = "automático"
SOURCE_NONE = "sem sinal"


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def timeframe_trend(bars: pd.DataFrame, trend: TrendSettings, min_bars: int) -> dict:
    """Tendência de um timeframe a partir das barras ordenadas por tempo (coluna close).

    alta: close > EMA lenta e EMA rápida > EMA lenta; baixa: o espelho; senão neutro.
    Com menos de min_bars barras, neutro (EMA sem aquecimento).
    """
    if len(bars) < min_bars:
        return {
            "trend": NEUTRAL,
            "close": float("nan"),
            "ema_fast": float("nan"),
            "ema_slow": float("nan"),
            "bars": len(bars),
        }
    close = bars["close"].astype("float64").reset_index(drop=True)
    fast = float(ema(close, trend.ema_fast).iloc[-1])
    slow = float(ema(close, trend.ema_slow).iloc[-1])
    last = float(close.iloc[-1])
    if last > slow and fast > slow:
        direction = BULLISH
    elif last < slow and fast < slow:
        direction = BEARISH
    else:
        direction = NEUTRAL
    return {
        "trend": direction,
        "close": last,
        "ema_fast": fast,
        "ema_slow": slow,
        "bars": len(bars),
    }


def automatic_bias(bars: pd.DataFrame, settings: SignalSettings) -> pd.DataFrame:
    """Uma linha por ativo: tendência de cada timeframe e viés automático.

    `bars`: underlying, timeframe, time, close (demais colunas ignoradas).
    Viés automático = tendência comum a todos os timeframes configurados; senão neutro.
    """
    rows = []
    for underlying, group in bars.groupby("underlying", sort=True):
        row: dict = {"underlying": underlying}
        trends = []
        for name, trend in settings.timeframes.items():
            tf_bars = group[group["timeframe"] == name].sort_values("time")
            result = timeframe_trend(tf_bars, trend, settings.min_bars)
            trends.append(result["trend"])
            row.update({f"{name}_{key}": value for key, value in result.items()})
        row["auto_bias"] = trends[0] if len(set(trends)) == 1 else NEUTRAL
        rows.append(row)
    return pd.DataFrame(rows)


def resolve_bias(
    underlyings: list[str],
    auto: pd.DataFrame,
    manual: dict[str, BiasValue],
    settings: SignalSettings,
) -> pd.DataFrame:
    """Viés final por ativo: manual (YAML) > automático (se habilitado) > neutro."""
    frame = pd.DataFrame({"underlying": sorted(set(underlyings) | set(manual))})
    if settings.enabled and not auto.empty:
        frame = frame.merge(auto, on="underlying", how="left")
    else:
        frame["auto_bias"] = pd.NA
    frame["manual_bias"] = frame["underlying"].map(manual)

    has_manual = frame["manual_bias"].notna()
    has_auto = frame["auto_bias"].notna()
    frame["bias"] = frame["manual_bias"].where(has_manual, frame["auto_bias"]).fillna(NEUTRAL)
    frame["bias_source"] = SOURCE_NONE
    frame.loc[has_auto & ~has_manual, "bias_source"] = SOURCE_AUTO
    frame.loc[has_manual, "bias_source"] = SOURCE_MANUAL
    return frame
