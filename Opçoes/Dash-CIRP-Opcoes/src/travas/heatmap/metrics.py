"""Métricas do heatmap e resumo técnico a partir das barras diárias do MT5. Funções puras.

Convenções (exibidas na interface):
- Variações em PREGÕES, janela móvel: dia = 1, semana = 5, mês = 21, ano = 252 pregões. O preço
  final é o fechamento da última barra (em formação durante o pregão = preço atual).
- Volume financeiro do dia = real_volume (quantidade) × fechamento da barra; média de 20 pregões
  exclui a barra do dia. Durante o pregão o volume do dia é PARCIAL.
- Negócios: só o da sessão (session_deals do MT5); o MT5 não fornece histórico de negócios.
- Volatilidade histórica: desvio-padrão dos log-retornos diários × √252, só com barras fechadas.
- RSI de Wilder (14); EMA α = 2/(n+1) (mesma do gráfico); SMA simples.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

PERIODS = {"1d": 1, "1w": 5, "1m": 21, "1y": 252}
HV_WINDOWS = (20, 60, 252)
TURNOVER_AVG_WINDOW = 20
TRADING_DAYS = 252


def _f(x: object) -> float | None:
    try:
        v = float(x)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None
    return v if math.isfinite(v) else None


def change(closes: pd.Series, sessions: int) -> dict:
    """Variação do último fechamento contra o de `sessions` pregões antes."""
    if len(closes) <= sessions:
        return {"abs": None, "pct": None, "ref": None}
    last, ref = float(closes.iloc[-1]), float(closes.iloc[-1 - sessions])
    if ref <= 0:
        return {"abs": None, "pct": None, "ref": None}
    return {"abs": last - ref, "pct": last / ref - 1, "ref": ref}


def historical_vol(closes: pd.Series, window: int) -> float | None:
    rets = np.log(closes / closes.shift(1)).dropna()
    if len(rets) < window:
        return None
    return _f(rets.iloc[-window:].std(ddof=1) * math.sqrt(TRADING_DAYS))


def rsi_wilder(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) <= period:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    last_loss = float(loss.iloc[-1])
    if last_loss == 0:
        return 100.0
    return 100 - 100 / (1 + float(gain.iloc[-1]) / last_loss)


def compute(
    bars: pd.DataFrame,
    session_deals: float | None = None,
    ema_periods: tuple[int, int] = (17, 34),
) -> dict:
    """`bars`: colunas time, open, high, low, close, real_volume, forming (ordem cronológica).
    `ema_periods`: (rápida, lenta), os mesmos do gráfico (config/settings.yaml → candles)."""
    if bars.empty:
        return {"available": False, "reason": "sem barras diárias no MT5"}
    bars = bars.reset_index(drop=True)
    closes = bars["close"].astype("float64")
    last = bars.iloc[-1]
    closed = bars[~bars["forming"]] if "forming" in bars else bars
    closed_closes = closed["close"].astype("float64")

    turnover = bars["real_volume"].astype("float64") * closes
    prior = turnover.iloc[-1 - TURNOVER_AVG_WINDOW : -1]
    avg20 = _f(prior.mean()) if len(prior) else None
    today = _f(turnover.iloc[-1])

    out: dict = {
        "available": True,
        "price": _f(last["close"]),
        "last_bar_date": pd.Timestamp(last["time"]).date().isoformat(),
        "last_bar_forming": bool(last.get("forming", False)),
        "changes": {key: change(closes, n) for key, n in PERIODS.items()},
        "turnover_today": today,
        "turnover_avg20": avg20,
        "turnover_ratio": today / avg20 if today is not None and avg20 else None,
        "deals_session": _f(session_deals) if session_deals else None,
        "hv": {str(w): historical_vol(closed_closes, w) for w in HV_WINDOWS},
    }

    window = bars.iloc[-TRADING_DAYS:]
    high52, low52 = _f(window["high"].max()), _f(window["low"].min())
    price = out["price"]
    n_fast, n_slow = ema_periods
    ema_fast = (
        closes.ewm(span=n_fast, adjust=False).mean().iloc[-1] if len(closes) >= n_fast else None
    )
    ema_slow = (
        closes.ewm(span=n_slow, adjust=False).mean().iloc[-1] if len(closes) >= n_slow else None
    )
    sma50 = closes.iloc[-50:].mean() if len(closes) >= 50 else None
    sma200 = closes.iloc[-200:].mean() if len(closes) >= 200 else None
    rsi = rsi_wilder(closes)
    out["technical"] = {
        "rsi14": rsi,
        "rsi_label": None
        if rsi is None
        else ("sobrecomprado" if rsi >= 70 else "sobrevendido" if rsi <= 30 else "neutro"),
        "ema_fast_period": n_fast,
        "ema_slow_period": n_slow,
        "ema_fast": _f(ema_fast),
        "ema_slow": _f(ema_slow),
        "ema_trend": None
        if ema_fast is None or ema_slow is None
        else ("alta" if ema_fast > ema_slow else "baixa"),
        "sma50": _f(sma50),
        "sma200": _f(sma200),
        "above_sma50": None if sma50 is None else bool(price > sma50),
        "above_sma200": None if sma200 is None else bool(price > sma200),
        "high52": high52,
        "low52": low52,
        "from_high52_pct": price / high52 - 1 if price and high52 else None,
        "from_low52_pct": price / low52 - 1 if price and low52 else None,
        "bars_used": len(bars),
    }
    return out
