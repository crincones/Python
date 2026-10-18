"""Totais da carteira e relatório das operações encerradas (funções puras).

Entrada: estruturas já avaliadas por `evaluate_position` (P&L realizado = caixa de entrada +
caixa de saída − custos de entrada e de saída). Nada aqui consulta o MT5.

Definições usadas no relatório (por operação encerrada):
- **R (retorno sobre o risco)** = P&L realizado ÷ perda máxima da estrutura na entrada (com
  custos de entrada). Sem perda máxima finita (ex.: venda descoberta), R fica indisponível.
- **Vencedora / perdedora / empate**: P&L realizado > 0 / < 0 / = 0 (após custos).
- **Fator de lucro** = soma dos ganhos ÷ |soma das perdas|.
- **Payoff** = ganho médio ÷ |perda média|.
- **Expectativa** = P&L médio por operação = acerto × ganho médio + erro × perda média.
- **Drawdown máximo**: maior queda do P&L acumulado (ordenado pela data de saída) a partir de um
  pico anterior, partindo de zero.
- **SQN** (System Quality Number, Van Tharp) = √n × média(R) ÷ desvio-padrão(R), com n ≥ 2.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from collections.abc import Iterable

REASON_LABELS = {"zerada": "Zerada", "vencida": "Vencida (virou pó)", "exercida": "Exercida"}


def _finite(v: object) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None
    return x if math.isfinite(x) else None


def _date(v: object) -> dt.date | None:
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and v:
        try:
            return dt.date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


# ---------- totais (abertas + encerradas) --------------------------------------------------------
def portfolio_totals(evaluated: list[dict]) -> dict:
    """Soma do P&L das abertas (natural e mid) e do realizado das encerradas. Se alguma aberta não
    tiver cotação, o total aberto vem só das que têm e `open_missing` diz quantas ficaram fora."""
    open_items = [e for e in evaluated if e["status"] == "aberta"]
    closed = [e for e in evaluated if e["status"] == "encerrada"]

    def partial(key: str) -> tuple[float | None, int]:
        vals = [_finite(e.get(key)) for e in open_items]
        known = [v for v in vals if v is not None]
        return (float(sum(known)) if known else None), len(vals) - len(known)

    open_nat, missing_nat = partial("pnl_natural")
    open_mid, missing_mid = partial("pnl_mid")
    realized = float(sum(_finite(e.get("realized_pnl")) or 0.0 for e in closed))
    losses = [_finite(e.get("max_loss")) for e in open_items]
    entry_cash = [_finite(e.get("entry_cash_total")) or 0.0 for e in open_items]
    costs = sum(_finite(e.get("costs_entry")) or 0.0 for e in evaluated) + sum(
        _finite((e.get("exit") or {}).get("costs_exit")) or 0.0 for e in closed
    )
    return {
        "open_count": len(open_items),
        "closed_count": len(closed),
        "open_pnl_natural": open_nat,
        "open_pnl_mid": open_mid,
        "open_missing_natural": missing_nat,
        "open_missing_mid": missing_mid,
        "realized_pnl": realized,
        "total_natural": (open_nat or 0.0) + realized,
        "total_mid": (open_mid or 0.0) + realized,
        "open_entry_cash": float(sum(entry_cash)),
        "open_max_loss": (
            float(sum(losses)) if losses and all(v is not None for v in losses) else None
        ),
        "costs_total": float(costs),
    }


# ---------- relatório das encerradas -------------------------------------------------------------
def trade_rows(evaluated: Iterable[dict]) -> list[dict]:
    """Uma linha por estrutura encerrada, ordenada pela data de saída."""
    rows = []
    for e in evaluated:
        if e.get("status") != "encerrada":
            continue
        ex = e.get("exit") or {}
        entry, exit_ = _date(e.get("entry_date")), _date(ex.get("exit_date"))
        pnl = _finite(e.get("realized_pnl"))
        risk = _finite(e.get("max_loss"))
        rows.append(
            {
                "id": e["id"],
                "name": e.get("name"),
                "group": e.get("group") or "Sem grupo",
                "underlying": e.get("underlying"),
                "kind_label": e.get("kind_label"),
                "flow": e.get("entry_flow"),
                "entry_date": entry.isoformat() if entry else None,
                "exit_date": exit_.isoformat() if exit_ else None,
                "days_held": (exit_ - entry).days if entry and exit_ else None,
                "reason": ex.get("reason"),
                "entry_cash": _finite(e.get("entry_cash_total")),
                "costs": (_finite(e.get("costs_entry")) or 0.0)
                + (_finite(ex.get("costs_exit")) or 0.0),
                "max_loss": risk,
                "max_profit": _finite(e.get("max_profit")),
                "pnl": pnl,
                "r_multiple": pnl / risk if pnl is not None and risk and risk > 0 else None,
            }
        )
    rows.sort(key=lambda r: (r["exit_date"] or "9999", r["entry_date"] or "9999"))
    return rows


def _streaks(pnls: list[float]) -> tuple[int, int]:
    best_w = best_l = cur_w = cur_l = 0
    for p in pnls:
        cur_w, cur_l = (cur_w + 1, 0) if p > 0 else (0, cur_l + 1) if p < 0 else (0, 0)
        best_w, best_l = max(best_w, cur_w), max(best_l, cur_l)
    return best_w, best_l


def _mean(values: list[float]) -> float | None:
    return float(statistics.fmean(values)) if values else None


def summary_stats(trades: list[dict]) -> dict:
    pnls = [t["pnl"] for t in trades if t["pnl"] is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    n = len(pnls)
    gross_profit, gross_loss = float(sum(wins)), float(sum(losses))
    avg_win, avg_loss = _mean(wins), _mean(losses)
    rs = [t["r_multiple"] for t in trades if t["r_multiple"] is not None]
    risks = [t["max_loss"] for t in trades if t["max_loss"] is not None and t["max_loss"] > 0]

    # Curva de P&L acumulado e drawdown (partindo de zero, na ordem das saídas)
    equity, peak, max_dd, dd_peak, dd_trough = 0.0, 0.0, 0.0, None, None
    peak_date = None
    for t in trades:
        if t["pnl"] is None:
            continue
        equity += t["pnl"]
        if equity > peak:
            peak, peak_date = equity, t["exit_date"]
        if peak - equity > max_dd:
            max_dd, dd_peak, dd_trough = peak - equity, peak_date, t["exit_date"]

    held = [t["days_held"] for t in trades if t["days_held"] is not None]
    held_w = [t["days_held"] for t in trades if t["days_held"] is not None and (t["pnl"] or 0) > 0]
    held_l = [t["days_held"] for t in trades if t["days_held"] is not None and (t["pnl"] or 0) < 0]
    best_w, best_l = _streaks(pnls)
    sqn = None
    if len(rs) >= 2 and statistics.stdev(rs) > 0:
        sqn = math.sqrt(len(rs)) * statistics.fmean(rs) / statistics.stdev(rs)
    exits = [t["exit_date"] for t in trades if t["exit_date"]]
    return {
        "trades": n,
        "without_pnl": len(trades) - n,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": n - len(wins) - len(losses),
        "win_rate": len(wins) / n if n else None,
        "net_pnl": float(sum(pnls)),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": gross_profit / -gross_loss if gross_loss < 0 else None,
        "avg_trade": _mean(pnls),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": avg_win / -avg_loss if avg_win is not None and avg_loss else None,
        "largest_win": max(wins) if wins else None,
        "largest_loss": min(losses) if losses else None,
        "max_consecutive_wins": best_w,
        "max_consecutive_losses": best_l,
        "max_drawdown": max_dd,
        "max_drawdown_from": dd_peak,
        "max_drawdown_to": dd_trough,
        "recovery_factor": float(sum(pnls)) / max_dd if max_dd > 0 else None,
        "total_risk": float(sum(risks)) if risks else None,
        "return_on_risk": float(sum(pnls)) / float(sum(risks))
        if risks and sum(risks) > 0
        else None,
        "avg_r": _mean(rs),
        "sqn": sqn,
        "avg_days_held": _mean([float(h) for h in held]),
        "avg_days_held_wins": _mean([float(h) for h in held_w]),
        "avg_days_held_losses": _mean([float(h) for h in held_l]),
        "costs_total": float(sum(t["costs"] for t in trades)),
        "first_exit": min(exits) if exits else None,
        "last_exit": max(exits) if exits else None,
    }


def _breakdown(trades: list[dict], key, label=lambda k: k) -> list[dict]:
    buckets: dict[str, list[dict]] = {}
    for t in trades:
        buckets.setdefault(key(t) or "—", []).append(t)
    out = []
    for k, items in buckets.items():
        pnls = [t["pnl"] for t in items if t["pnl"] is not None]
        wins = [p for p in pnls if p > 0]
        out.append(
            {
                "key": k,
                "label": label(k),
                "trades": len(items),
                "wins": len(wins),
                "win_rate": len(wins) / len(pnls) if pnls else None,
                "net_pnl": float(sum(pnls)),
                "avg_pnl": _mean(pnls),
            }
        )
    return sorted(out, key=lambda r: r["net_pnl"], reverse=True)


def closed_report(
    evaluated: list[dict],
    start: dt.date | None = None,
    end: dt.date | None = None,
    group: str | None = None,
) -> dict:
    """Encerradas com saída em [start, end] (datas inclusivas) e, se dado, do grupo."""
    trades = trade_rows(evaluated)
    if start:
        trades = [t for t in trades if t["exit_date"] and t["exit_date"] >= start.isoformat()]
    if end:
        trades = [t for t in trades if t["exit_date"] and t["exit_date"] <= end.isoformat()]
    if group:
        trades = [t for t in trades if t["group"] == group]

    equity, cum, peak = [], 0.0, 0.0
    for t in trades:
        if t["pnl"] is None:
            continue
        cum += t["pnl"]
        peak = max(peak, cum)
        equity.append(
            {
                "date": t["exit_date"],
                "name": t["name"],
                "pnl": t["pnl"],
                "cum": cum,
                "dd": cum - peak,
            }
        )
    monthly = sorted(
        _breakdown(trades, lambda t: (t["exit_date"] or "")[:7] or None),
        key=lambda r: r["key"],
    )
    return {
        "filters": {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "group": group,
        },
        "stats": summary_stats(trades),
        "trades": trades,
        "equity": equity,
        "monthly": monthly,
        "by_underlying": _breakdown(trades, lambda t: t["underlying"]),
        "by_kind": _breakdown(trades, lambda t: t["kind_label"]),
        "by_group": _breakdown(trades, lambda t: t["group"]),
        "by_flow": _breakdown(
            trades,
            lambda t: t["flow"],
            lambda k: {"debito": "Débito", "credito": "Crédito"}.get(k, k),
        ),
        "by_reason": _breakdown(trades, lambda t: t["reason"], lambda k: REASON_LABELS.get(k, k)),
        "groups": sorted({t["group"] for t in trade_rows(evaluated)}),
        "methodology": (
            "P&L realizado = caixa de entrada + caixa de saída − custos de entrada e de saída "
            "informados. R = P&L ÷ perda máxima da estrutura na entrada. Fator de lucro = ganhos ÷ "
            "|perdas|. Payoff = ganho médio ÷ |perda média|. Expectativa = P&L médio por "
            "operação. Drawdown = maior queda do P&L acumulado (ordem das saídas) desde um pico. "
            "SQN = √n × média(R) ÷ desvio-padrão(R). "
            "Resultado passado não garante resultado futuro."
        ),
    }
