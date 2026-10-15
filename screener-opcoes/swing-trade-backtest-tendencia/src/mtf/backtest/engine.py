"""Simulação de execução sobre as barras H1 (separada da descoberta de sinais).

Regras (conservadoras onde o OHLC não diz a ordem dos eventos):
- Uma posição por ativo; um novo setup só é considerado depois da barra de saída.
- Gatilho `break`: ordem stop no preço do gatilho válida nas `valid_bars` barras seguintes ao
  sinal. Gap além do gatilho → preenchida na abertura. `immediate`: abertura da barra seguinte.
- Setup cujo preço de entrada já está além do stop é descartado.
- Na barra de entrada: se a barra atinge o stop, sai no stop (não se sabe se veio antes ou
  depois da entrada; assume o pior). O alvo só conta se o fechamento passou dele.
- Barras seguintes: gap além do stop/alvo sai na abertura; stop e alvo na mesma barra → stop.
- Sem saída em `max_holding_bars` barras: sai no fechamento. Fim dos dados: último fechamento.
- Custos: slippage em ticks contra a operação em cada lado; taxa em bps por lado.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mtf.config import CostSettings, Settings, Variant
from mtf.models import Trade


def _fill_entry(
    direction: int, trigger: str, trigger_price: float, bar_open: float, high: float, low: float
) -> float | None:
    if trigger == "immediate":
        return bar_open
    if direction > 0:
        return max(bar_open, trigger_price) if high >= trigger_price else None
    return min(bar_open, trigger_price) if low <= trigger_price else None


def _simulate_exit(
    direction: int,
    entry_bar: int,
    stop: float,
    target: float,
    o: np.ndarray,
    h: np.ndarray,
    lo: np.ndarray,
    c: np.ndarray,
    max_bars: int,
) -> tuple[int, float, str]:
    last = len(c) - 1
    # Barra de entrada.
    stop_hit = lo[entry_bar] <= stop if direction > 0 else h[entry_bar] >= stop
    if stop_hit:
        return entry_bar, stop, "stop"
    target_closed = c[entry_bar] >= target if direction > 0 else c[entry_bar] <= target
    if target_closed:
        return entry_bar, target, "target"
    end = min(entry_bar + max_bars, last)
    for k in range(entry_bar + 1, end + 1):
        if direction > 0:
            if o[k] <= stop:
                return k, o[k], "stop"
            if o[k] >= target:
                return k, o[k], "target"
            if lo[k] <= stop:
                return k, stop, "stop"
            if h[k] >= target:
                return k, target, "target"
        else:
            if o[k] >= stop:
                return k, o[k], "stop"
            if o[k] <= target:
                return k, o[k], "target"
            if h[k] >= stop:
                return k, stop, "stop"
            if lo[k] <= target:
                return k, target, "target"
    reason = "time" if entry_bar + max_bars <= last else "end_of_data"
    return end, c[end], reason


def _excursions(
    direction: int,
    entry: float,
    entry_bar: int,
    exit_bar: int,
    exit_price: float,
    reason: str,
    h: np.ndarray,
    lo: np.ndarray,
) -> tuple[float, float]:
    """(MFE, MAE) em preço. Na barra de saída só conta o que é compatível com a saída
    assumida: no stop, nada a favor; no alvo, o favorável para no alvo."""
    best, worst = (h, lo) if direction > 0 else (-lo, -h)
    signed_entry, signed_exit = direction * entry, direction * exit_price
    fav = max([signed_entry, *best[entry_bar:exit_bar]])
    adv = min([signed_entry, *worst[entry_bar:exit_bar]])
    if reason == "stop":
        adv = min(adv, signed_exit)
    elif reason == "target":
        fav = max(fav, signed_exit)
        adv = min(adv, worst[exit_bar])
    else:
        fav, adv = max(fav, best[exit_bar]), min(adv, worst[exit_bar])
    return fav - signed_entry, signed_entry - adv


def _net_result(
    direction: int, entry: float, exit_price: float, stop: float, costs: CostSettings
) -> tuple[float, float]:
    """(R líquido, retorno % líquido). Risco = distância da entrada efetiva ao stop."""
    slip = costs.slippage_ticks * costs.tick_size
    entry_eff = entry + direction * slip
    exit_eff = exit_price - direction * slip
    fees = costs.fees_bps_per_side / 10_000 * (entry_eff + exit_eff)
    pnl = direction * (exit_eff - entry_eff) - fees
    risk = abs(entry_eff - stop)
    return pnl / risk, pnl / entry_eff


def run_backtest(
    h1: pd.DataFrame, setups: pd.DataFrame, variant: Variant, settings: Settings
) -> list[Trade]:
    risk_cfg = settings.risk
    o, h, lo, c = (h1[col].to_numpy(dtype=float) for col in ("open", "high", "low", "close"))
    times = h1["time"]
    last = len(c) - 1
    trades: list[Trade] = []
    next_free = 0
    for setup in setups.itertuples(index=False):
        signal = int(setup.bar)
        if signal < next_free or signal >= last:
            continue
        direction = int(setup.direction)
        entry_bar, entry = None, None
        for j in range(signal + 1, min(signal + settings.entry.valid_bars, last) + 1):
            entry = _fill_entry(direction, variant.trigger, setup.trigger_price, o[j], h[j], lo[j])
            if entry is not None:
                entry_bar = j
                break
        if entry_bar is None or entry is None:
            continue
        stop = float(setup.stop_price)
        if direction * (entry - stop) <= 0:
            continue
        target = entry + direction * risk_cfg.target_r * abs(entry - stop)
        exit_bar, exit_price, reason = _simulate_exit(
            direction, entry_bar, stop, target, o, h, lo, c, risk_cfg.max_holding_bars
        )
        r_multiple, return_pct = _net_result(direction, entry, exit_price, stop, settings.costs)
        risk = abs(entry - stop)
        mfe, mae = _excursions(direction, entry, entry_bar, exit_bar, exit_price, reason, h, lo)
        forward = {
            n: direction * (c[entry_bar + n] - entry) / risk
            for n in settings.forward_bars
            if entry_bar + n <= last
        }
        trades.append(
            Trade(
                symbol=setup.symbol,
                variant=variant.name,
                direction=direction,
                signal_bar=signal,
                entry_bar=entry_bar,
                exit_bar=exit_bar,
                signal_time=setup.time,
                entry_time=times.iloc[entry_bar],
                exit_time=times.iloc[exit_bar],
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                exit_price=float(exit_price),
                exit_reason=reason,
                r_multiple=r_multiple,
                return_pct=return_pct,
                mfe_r=float(mfe / risk),
                mae_r=float(mae / risk),
                bars_held=exit_bar - entry_bar,
                forward_r=forward,
            )
        )
        next_free = exit_bar + 1
    return trades


TRADE_CONTEXT_COLUMNS = [
    "bar",
    "d1_trend",
    "h4_trend",
    "pullback_bars",
    "pullback_low",
    "pullback_high",
    "pullback_start",
    "impulse_size_atr_d1",
    "pullback_depth_atr_d1",
    "d1_ma",
    "h4_ma",
    "atr_d1",
    "atr_h4",
    "atr_h1",
    "dist_d1_ma_atr",
    "signed_dist_d1_ma_atr",
    "dist_h4_ma_atr",
    "touch_d1_ma",
    "adv",
]


def trades_frame(
    trades: list[Trade], setups: pd.DataFrame, forward_bars: list[int]
) -> pd.DataFrame:
    """Trades + contexto do setup (log da seção 30)."""
    if not trades:
        return pd.DataFrame()
    rows = []
    for trade in trades:
        row = {k: v for k, v in trade.__dict__.items() if k != "forward_r"}
        for n in forward_bars:
            row[f"r_after_{n}_bars"] = trade.forward_r.get(n, np.nan)
        rows.append(row)
    frame = pd.DataFrame(rows)
    context = setups[TRADE_CONTEXT_COLUMNS].rename(columns={"bar": "signal_bar"})
    return frame.merge(context, on="signal_bar", how="left")
