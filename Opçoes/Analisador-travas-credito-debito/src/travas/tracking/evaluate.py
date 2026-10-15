"""Avaliação das estruturas acompanhadas com cotações atuais. Funções puras (sem MT5).

Convenções (iguais às do motor de payoff):
- fluxo de entrada > 0 = crédito recebido; < 0 = débito pago (R$ totais);
- valor atual da posição = Σ sinal × unidades × preço (comprado +, vendido −);
- P&L não realizado = valor atual + fluxo de entrada − custos de entrada.
- "Zerar pelo natural": vende as compradas no bid e recompra as vendidas no ask (pior preço
  visível). "Pelo mid": referência, sem garantia de execução.
"""

from __future__ import annotations

import datetime as dt
import math

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.options.models import Flow, Leg, OptionType, Side, Structure
from travas.options.payoff import net_premium
from travas.options.simulation import business_days_until, leg_terms, profile_summary, simulate
from travas.options.validation import structural_kind
from travas.options.valuation import structure_greeks, structure_value
from travas.settings import EarlyExerciseSettings
from travas.tracking.models import ExitIn, PositionIn

NEAR_EXPIRY_BUSINESS_DAYS = 2
NET_MISMATCH_TOLERANCE = 0.005  # R$ por unidade


class PositionError(ValueError):
    """Dados da estrutura inválidos (ticker inexistente, ativo errado…)."""


def _f(value: object) -> float | None:
    try:
        x = float(value)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None
    return x if math.isfinite(x) else None


# ---------- cadastro ----------------------------------------------------------------------------
def build_record(pos: PositionIn, catalog: pd.DataFrame) -> dict:
    """Resolve cada ticker no catálogo real do MT5 (nada é presumido pelo nome)."""
    by_symbol = catalog.set_index("symbol")
    legs = []
    for leg in pos.legs:
        if leg.symbol not in by_symbol.index:
            raise PositionError(f"{leg.symbol}: ticker não encontrado no MT5")
        info = by_symbol.loc[leg.symbol]
        if info["underlying"] != pos.underlying:
            raise PositionError(
                f"{leg.symbol} é opção de {info['underlying']}, não de {pos.underlying}"
            )
        legs.append(
            {
                "symbol": leg.symbol,
                "side": leg.side.value,
                "quantity": leg.quantity,
                "entry_price": leg.entry_price,
                "option_type": info["option_type"],
                "strike": float(info["strike"]),
                "expiration": pd.Timestamp(info["expiration_date"]).date().isoformat(),
                "exercise_style": info["exercise_style"],
                "multiplier": float(info.get("contract_size", 1.0) or 1.0),
            }
        )
    record = pos.model_dump(mode="json")
    record["legs"] = legs
    record["kind_label"] = describe(to_structure(record, prices=None))
    return record


def to_structure(record: dict, prices: list[float | None] | None) -> Structure:
    legs = tuple(
        Leg(
            option_type=OptionType(lg["option_type"]),
            side=Side(lg["side"]),
            strike=float(lg["strike"]),
            expiration=dt.date.fromisoformat(lg["expiration"]),
            quantity=int(lg["quantity"]),
            multiplier=float(lg["multiplier"]),
            price=None if prices is None else prices[i],
            symbol=lg["symbol"],
            exercise_style=lg["exercise_style"],
        )
        for i, lg in enumerate(record["legs"])
    )
    return Structure(record["underlying"], legs)


def describe(structure: Structure) -> str:
    kind, _ = structural_kind(structure)
    if kind is not None:
        return kind.label
    legs = structure.legs
    if len(legs) == 1:
        leg = legs[0]
        return f"{'Compra' if leg.side is Side.LONG else 'Venda'} de {leg.option_type.value}"
    if (
        len(legs) == 2
        and legs[0].option_type is legs[1].option_type
        and legs[0].side is not legs[1].side
        and legs[0].expiration != legs[1].expiration
    ):
        return "Calendário" if legs[0].strike == legs[1].strike else "Diagonal"
    return f"Estrutura personalizada ({len(legs)} pernas)"


def entry_prices(record: dict) -> tuple[list[float], str, list[str]]:
    """Preços de entrada por perna. Com só o preço líquido, ele é alocado na 1ª perna
    (o payoff depende apenas da soma; o P&L por perna fica indisponível)."""
    warnings: list[str] = []
    legs = record["legs"]
    units = [lg["quantity"] * lg["multiplier"] for lg in legs]
    given = [lg.get("entry_price") for lg in legs]
    net = record.get("entry_net")
    flow = record.get("entry_flow")
    signed_net = None if net is None else (net if flow == Flow.CREDIT.value else -net)
    if all(p is not None for p in given):
        prices = [float(p) for p in given]
        if signed_net is not None and len(set(units)) == 1:
            implied = -sum(Side(lg["side"]).sign * p for lg, p in zip(legs, prices, strict=True))
            if abs(implied - signed_net) > NET_MISMATCH_TOLERANCE:
                warnings.append(
                    f"preço líquido informado ({net:.2f}) difere do calculado pelas pernas "
                    f"({abs(implied):.2f}); usando os preços das pernas"
                )
        return prices, "pernas", warnings
    if signed_net is None:
        raise PositionError("sem preço de entrada")
    # −Σ sinal·preço·unid = líquido·unid  →  só a 1ª perna recebe preço.
    first_sign = Side(legs[0]["side"]).sign
    prices = [0.0] * len(legs)
    prices[0] = -signed_net / first_sign
    return prices, "liquido", warnings


def exit_cash(record: dict) -> float | None:
    """Fluxo de caixa ao zerar (R$ totais, + recebido), a partir do registro de saída."""
    ex = record.get("exit")
    if not ex:
        return None
    legs = record["legs"]
    if ex.get("leg_prices") and all(p is not None for p in ex["leg_prices"]):
        return sum(
            Side(lg["side"]).sign * float(p) * lg["quantity"] * lg["multiplier"]
            for lg, p in zip(legs, ex["leg_prices"], strict=True)
        )
    units = legs[0]["quantity"] * legs[0]["multiplier"]
    return (ex["exit_net"] if ex["exit_flow"] == Flow.CREDIT.value else -ex["exit_net"]) * units


def close_record(record: dict, exit_in: ExitIn) -> dict:
    if exit_in.leg_prices is not None and len(exit_in.leg_prices) != len(record["legs"]):
        raise PositionError("um preço de saída por perna")
    return {"status": "encerrada", "exit": exit_in.model_dump(mode="json")}


# ---------- avaliação ---------------------------------------------------------------------------
def evaluate_position(
    record: dict,
    quotes: pd.DataFrame,
    spot: float | None,
    today: dt.date,
    calendar: B3Calendar,
    rate: float,
    rate_annual: float,
    early_exercise: EarlyExerciseSettings,
    vol_override: float | None = None,
    with_simulation: bool = False,
) -> dict:
    """`quotes`: cadeia normalizada + IV + liquidez, indexada por símbolo (pode faltar série)."""
    prices, entry_mode, warnings = entry_prices(record)
    if record.get("aggregated"):
        entry_mode = "agregado"  # preços alocados entre estruturas: P&L por perna não se aplica
    structure = to_structure(record, prices)
    costs_entry = float(record.get("costs_entry") or 0.0)
    entry_cash = net_premium(structure)
    units0 = structure.legs[0].units
    alerts: list[str] = []

    legs_out = []
    natural_value = mid_value = 0.0
    natural_ok = mid_ok = True
    sigmas: list[float | None] = []
    for leg, lg, price in zip(structure.legs, record["legs"], prices, strict=True):
        q = quotes.loc[leg.symbol] if leg.symbol in quotes.index else None
        bid, ask, mid, last = (
            (_f(q["bid"]), _f(q["ask"]), _f(q["mid"]), _f(q["last"]))
            if q is not None
            else (None,) * 4
        )
        close_px = bid if leg.side is Side.LONG else ask
        if close_px is None:
            natural_ok = False
        else:
            natural_value += leg.side.sign * leg.units * close_px
        if mid is None:
            mid_ok = False
        else:
            mid_value += leg.side.sign * leg.units * mid
        iv = _f(q["iv"]) if q is not None and q.get("iv_status") == "ok" else None
        sigma = vol_override if vol_override is not None else iv
        sigmas.append(sigma)
        flags = list(q["quote_flags"]) if q is not None else ["sem cotação no MT5"]
        source = q.get("source", "mt5") if q is not None else None
        if source == "mt5_fora_pregao":
            flags.append("lida fora do pregão")
        captured = q.get("captured_at") if q is not None else None
        current_strike = _f(q["strike"]) if q is not None else None
        if current_strike is not None and abs(current_strike - leg.strike) > 1e-6:
            alerts.append(
                f"{leg.symbol}: strike mudou de {leg.strike:.2f} para {current_strike:.2f} "
                "(ajuste por provento?) — confira e edite a estrutura"
            )
        leg_pnl = (
            leg.side.sign * leg.units * (close_px - price)
            if entry_mode == "pernas" and close_px is not None
            else None
        )
        legs_out.append(
            {
                **lg,
                "entry_price_used": price if entry_mode == "pernas" else None,
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "last": last,
                "close_price_natural": close_px,
                "quote_time": q["quote_time"].isoformat()
                if q is not None and pd.notna(q["quote_time"])
                else None,
                "quote_age_seconds": _f(q["quote_age_seconds"]) if q is not None else None,
                "source": source,
                "captured_at": pd.Timestamp(captured).isoformat()
                if captured is not None and pd.notna(captured)
                else None,
                "iv": iv,
                "flags": flags,
                "pnl_natural": leg_pnl,
                "dte_business_days": business_days_until(calendar, today, leg.expiration),
            }
        )

    pnl_natural = natural_value + entry_cash - costs_entry if natural_ok else None
    pnl_mid = mid_value + entry_cash - costs_entry if mid_ok else None

    sim = simulate(
        structure, today, calendar, rate, rate_annual, sigmas, costs_entry, extra_prices=(spot,)
    )
    profile = profile_summary(structure, sim, costs_entry)
    max_profit, max_loss = profile["max_profit"], profile["max_loss"]

    model_ok = spot is not None and all(s is not None and s > 0 for s in sigmas)
    terms = leg_terms(structure, calendar, today)
    theo_pnl = greeks = None
    if model_ok and all(t > 0 for t in terms):
        theo_value = float(structure_value(structure, [spot], terms, rate, sigmas)[0])
        theo_pnl = theo_value + entry_cash - costs_entry
        greeks = structure_greeks(structure, spot, terms, rate, sigmas)

    first_exp = min(structure.expirations)
    dte = business_days_until(calendar, today, first_exp)
    status = record.get("status", "aberta")
    if status == "aberta":
        if today > first_exp:
            alerts.append("vencimento passado: registre o encerramento/exercício")
        elif dte <= NEAR_EXPIRY_BUSINESS_DAYS:
            alerts.append(f"vence em {dte} dia(s) útil(eis): avaliar zerar ou rolar")
        stale = [lg["symbol"] for lg in legs_out if lg["flags"]]
        if stale:
            alerts.append(f"cotação com problema em {', '.join(stale)}: P&L pode não ser real")
        tp, sl = record.get("take_profit_pct"), record.get("stop_loss_brl")
        target_hit = (
            tp
            and pnl_natural is not None
            and max_profit
            and math.isfinite(max_profit)
            and pnl_natural >= tp / 100 * max_profit
        )
        if target_hit:
            alerts.append(f"ALVO atingido: P&L ≥ {tp:.0f}% do lucro máximo (pelo natural)")
        if sl and pnl_natural is not None and pnl_natural <= -sl:
            stop = f"{sl:.2f}".replace(".", ",")
            alerts.append(f"STOP atingido: prejuízo ≥ R$ {stop} (pelo natural)")
        alerts.extend(_early_exercise(structure, legs_out, spot, early_exercise))

    realized = None
    if status == "encerrada":
        cash_out = exit_cash(record)
        costs_exit = float(record["exit"].get("costs_exit") or 0.0)
        realized = cash_out + entry_cash - costs_entry - costs_exit

    result = {
        "id": record["id"],
        "name": record.get("name") or record["kind_label"],
        "group": record.get("group") or "Sem grupo",
        "underlying": record["underlying"],
        "kind_label": record["kind_label"],
        "status": status,
        "entry_date": record.get("entry_date"),
        "entry_mode": entry_mode,
        "entry_cash_total": entry_cash,
        "entry_net_per_unit": abs(entry_cash) / units0 if units0 else None,
        "entry_flow": "credito" if entry_cash > 0 else "debito",
        "costs_entry": costs_entry,
        "units": units0,
        "spot": spot,
        "legs": legs_out,
        "value_natural": natural_value if natural_ok else None,
        "value_mid": mid_value if mid_ok else None,
        "close_net_natural_per_unit": abs(natural_value) / units0 if natural_ok else None,
        "pnl_natural": pnl_natural,
        "pnl_mid": pnl_mid,
        "pnl_theoretical": theo_pnl,
        "pnl_pct_of_risk": (
            pnl_natural / max_loss
            if pnl_natural is not None and max_loss and math.isfinite(max_loss) and max_loss > 0
            else None
        ),
        "pnl_pct_of_max_profit": (
            pnl_natural / max_profit
            if pnl_natural is not None
            and max_profit
            and math.isfinite(max_profit)
            and max_profit > 0
            else None
        ),
        **profile,
        "dte_business_days": dte,
        "first_expiration": first_exp.isoformat(),
        "greeks": greeks,
        "realized_pnl": realized,
        "exit": record.get("exit"),
        "take_profit_pct": record.get("take_profit_pct"),
        "stop_loss_brl": record.get("stop_loss_brl"),
        "notes": record.get("notes", ""),
        "alerts": alerts,
        "warnings": warnings,
        "vol_source": "volatilidade informada" if vol_override else "IV de cada perna (mid)",
    }
    if with_simulation:
        result["simulation"] = sim
    return result


def _early_exercise(
    structure: Structure, legs_out: list[dict], spot: float | None, s: EarlyExerciseSettings
) -> list[str]:
    out = []
    if spot is None:
        return out
    for leg, lo in zip(structure.legs, legs_out, strict=True):
        if leg.side is not Side.SHORT or leg.exercise_style != "american":
            continue
        is_call = leg.option_type is OptionType.CALL
        intrinsic = max(spot - leg.strike, 0.0) if is_call else max(leg.strike - spot, 0.0)
        premium = lo["ask"] or lo["mid"] or lo["last"]
        if intrinsic <= 0 or premium is None:
            continue
        extrinsic = premium - intrinsic
        if extrinsic < max(s.min_extrinsic_brl, s.min_extrinsic_pct_premium * premium):
            out.append(
                f"RISCO de exercício antecipado em {leg.symbol} (vendida americana ITM, "
                f"extrínseco R$ {extrinsic:.2f})"
            )
    return out


def group_summaries(evaluated: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for e in evaluated:
        groups.setdefault(e["group"], []).append(e)
    out = []
    for name, items in sorted(groups.items()):
        open_items = [e for e in items if e["status"] == "aberta"]

        def total(key: str, rows: list[dict]) -> float | None:
            vals = [r[key] for r in rows]
            if any(v is None for v in vals):
                return None
            return float(sum(vals))

        losses = [e["max_loss"] for e in open_items]
        out.append(
            {
                "group": name,
                "count": len(items),
                "open": len(open_items),
                "underlyings": sorted({e["underlying"] for e in items}),
                "entry_cash_total": total("entry_cash_total", open_items),
                "pnl_natural": total("pnl_natural", open_items),
                "pnl_mid": total("pnl_mid", open_items),
                "realized_pnl": float(
                    sum(e["realized_pnl"] for e in items if e["realized_pnl"] is not None)
                ),
                "max_loss_sum": (
                    float(sum(losses))
                    if losses and all(v is not None and math.isfinite(v) for v in losses)
                    else None
                ),
                "alerts": sum(len(e["alerts"]) for e in open_items),
                "combinable": len({e["underlying"] for e in open_items}) == 1 and bool(open_items),
            }
        )
    return out


def combined_record(records: list[dict]) -> dict:
    """Junta as estruturas abertas de um grupo (mesmo ativo) numa só, para o payoff agregado.
    Cada perna recebe o preço de entrada efetivo, de modo que o fluxo total é preservado."""
    legs, costs = [], 0.0
    for rec in records:
        prices, _, _ = entry_prices(rec)
        for lg, p in zip(rec["legs"], prices, strict=True):
            legs.append({**lg, "entry_price": p})
        costs += float(rec.get("costs_entry") or 0.0)
    return {
        "id": "grupo",
        "name": "Grupo",
        "group": records[0].get("group"),
        "underlying": records[0]["underlying"],
        "legs": legs,
        "entry_net": None,
        "entry_flow": None,
        "costs_entry": costs,
        "status": "aberta",
        "kind_label": f"Grupo ({len(records)} estruturas, {len(legs)} pernas)",
        "aggregated": True,
    }
