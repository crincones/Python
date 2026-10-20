"""Simulador geral: qualquer combinação de opções (e do próprio ativo) de um mesmo ativo-objeto.

Funções puras (sem MT5): recebem as pernas já resolvidas no catálogo, as cotações normalizadas
(com IV e liquidez) e o spot; devolvem um dicionário pronto para a API.

Convenções (iguais às do motor de payoff):
- preço de entrada por perna: o informado pelo usuário ou, sem ele, o natural do book atual
  (compra no ask, venda no bid); sem book, o último negócio, sinalizado como indicativo;
- σ por perna: a informada na perna > a volatilidade geral informada > a IV da própria série;
- fluxo de entrada > 0 = crédito; valor para zerar na data simulada = P&L − entrada + custos.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.options import pricing
from travas.options.margin import exit_spread_cost, margin_estimate
from travas.options.models import Leg, OptionType, Side, Structure
from travas.options.payoff import net_premium
from travas.options.probability import pop_at_expiry
from travas.options.simulation import business_days_until, leg_terms, profile_summary, simulate
from travas.options.valuation import model_sigmas_ok, structure_greeks, structure_value
from travas.settings import EarlyExerciseSettings
from travas.tracking.evaluate import _early_exercise, describe

MAX_LEGS = 12
STOCK_KIND = "ativo"
OPTION_KIND = "opcao"


class SimulationError(ValueError):
    """Pernas inválidas (ticker inexistente, ativo errado, nenhuma opção…)."""


@dataclass(frozen=True)
class SimLeg:
    """Perna pedida pelo usuário, já resolvida no catálogo (`info`) quando é opção."""

    kind: str  # "opcao" ou "ativo"
    side: Side
    quantity: int
    price: float | None = None  # por unidade; None = natural do book
    sigma: float | None = None  # fração; None = vol geral ou IV da série
    symbol: str | None = None
    info: dict | None = None  # option_type, strike, expiration_date, exercise_style, contract_size


def _f(value: object) -> float | None:
    try:
        x = float(value)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None
    return x if math.isfinite(x) else None


def resolve_legs(raw_legs: list[dict], underlying: str, catalog: pd.DataFrame) -> list[SimLeg]:
    """Confere cada ticker no catálogo real do MT5 (nada é presumido pelo nome)."""
    if not raw_legs:
        raise SimulationError("adicione pelo menos uma perna")
    if len(raw_legs) > MAX_LEGS:
        raise SimulationError(f"no máximo {MAX_LEGS} pernas")
    by_symbol = catalog.set_index("symbol")
    out: list[SimLeg] = []
    for raw in raw_legs:
        side = Side(raw["side"])
        quantity = int(raw["quantity"])
        if quantity <= 0:
            raise SimulationError("quantidade deve ser positiva")
        price = _f(raw.get("price"))
        if price is not None and price < 0:
            raise SimulationError("preço não pode ser negativo")
        sigma = _f(raw.get("sigma"))
        if sigma is not None and sigma <= 0:
            raise SimulationError("volatilidade deve ser positiva")
        if raw.get("kind") == STOCK_KIND:
            out.append(SimLeg(STOCK_KIND, side, quantity, price, None, underlying, None))
            continue
        symbol = str(raw.get("symbol") or "").strip().upper()
        if symbol not in by_symbol.index:
            raise SimulationError(f"{symbol or '(vazio)'}: ticker não encontrado no MT5")
        info = by_symbol.loc[symbol].to_dict()
        if info["underlying"] != underlying:
            raise SimulationError(f"{symbol} é opção de {info['underlying']}, não de {underlying}")
        out.append(SimLeg(OPTION_KIND, side, quantity, price, sigma, symbol, info))
    if not any(leg.kind == OPTION_KIND for leg in out):
        raise SimulationError("inclua pelo menos uma opção (só o ativo não tem o que simular)")
    return out


def _natural(side: Side, bid: float | None, ask: float | None) -> float | None:
    return ask if side is Side.LONG else bid


def _entry_price(
    leg: SimLeg, bid: float | None, ask: float | None, last: float | None, closing: bool = False
) -> tuple[float | None, str]:
    if leg.price is not None:
        return leg.price, "informado"
    if closing:
        return (
            (last, "último negócio do pregão (fechamento B3, indicativo)")
            if last
            else (
                None,
                "sem negócio no dia (B3)",
            )
        )
    natural = _natural(leg.side, bid, ask)
    if natural is not None:
        return natural, "natural (ask)" if leg.side is Side.LONG else "natural (bid)"
    if last is not None:
        return last, "último negócio (sem book, indicativo)"
    return None, "sem preço"


def describe_simulation(structure: Structure) -> str:
    """Nome da estrutura pelas pernas (com o ativo, os casos clássicos; senão o rótulo genérico)."""
    stock = [leg for leg in structure.legs if leg.option_type is OptionType.STOCK]
    options = structure.option_legs
    if not stock:
        return describe(structure)
    long_stock = len(stock) == 1 and stock[0].side is Side.LONG
    kinds = sorted((leg.option_type.value, leg.side.value) for leg in options)
    if long_stock and kinds == [("call", "venda")]:
        return "Venda coberta (ativo + call vendida)"
    if long_stock and kinds == [("put", "compra")]:
        return "Ativo protegido por put"
    if long_stock and kinds == [("call", "venda"), ("put", "compra")]:
        return "Collar (ativo + put comprada + call vendida)"
    return f"Estrutura personalizada com o ativo ({len(structure.legs)} pernas)"


def evaluate_simulation(
    legs: list[SimLeg],
    quotes: pd.DataFrame,
    stock: dict,
    spot: float | None,
    today: dt.date,
    calendar: B3Calendar,
    rate: float,
    rate_annual: float,
    early_exercise: EarlyExerciseSettings,
    vol_override: float | None = None,
    costs: float = 0.0,
    target_price: float | None = None,
    max_quote_age_seconds: float | None = None,
) -> dict:
    """`quotes`: cadeia normalizada + IV + liquidez, indexada por símbolo (pode faltar série).
    `stock`: bid/ask/last/price/quote_time/source do ativo-objeto."""
    if spot is None:
        raise SimulationError("ativo sem cotação: não há preço atual para simular")
    first_exp = min(leg.info["expiration_date"] for leg in legs if leg.info)
    warnings: list[str] = []
    legs_out: list[dict] = []
    model_legs: list[Leg] = []
    sigmas: list[float | None] = []
    for i, leg in enumerate(legs):
        if leg.kind == STOCK_KIND:
            bid, ask, last = _f(stock.get("bid")), _f(stock.get("ask")), _f(stock.get("last"))
            price, price_source = _entry_price(leg, bid, ask, last if last is not None else spot)
            flags = [] if stock.get("source") == "mt5" else ["cotação fora do pregão"]
            legs_out.append(
                {
                    "index": i,
                    "kind": STOCK_KIND,
                    "symbol": leg.symbol,
                    "side": leg.side.value,
                    "quantity": leg.quantity,
                    "option_type": OptionType.STOCK.value,
                    "multiplier": 1.0,
                    "bid": bid,
                    "ask": ask,
                    "mid": (bid + ask) / 2 if bid is not None and ask is not None else None,
                    "last": last,
                    "quote_time": stock.get("quote_time"),
                    "price_used": price,
                    "price_source": price_source,
                    "price_given": leg.price,
                    "flags": flags,
                }
            )
            model_legs.append(
                Leg(
                    OptionType.STOCK,
                    leg.side,
                    0.0,
                    first_exp,
                    leg.quantity,
                    1.0,
                    price,
                    leg.symbol,
                    None,
                )
            )
            sigmas.append(None)
            continue
        info = leg.info or {}
        q = quotes.loc[leg.symbol] if leg.symbol in quotes.index else None
        bid, ask, mid, last = (
            (_f(q["bid"]), _f(q["ask"]), _f(q["mid"]), _f(q["last"]))
            if q is not None
            else (None,) * 4
        )
        closing = q is not None and q.get("price_basis") == "ultimo_b3"
        price, price_source = _entry_price(leg, bid, ask, last, closing)
        iv = _f(q["iv"]) if q is not None and q.get("iv_status") == "ok" else None
        if leg.sigma is not None:
            sigma, sigma_source = leg.sigma, "informada na perna"
        elif vol_override is not None:
            sigma, sigma_source = vol_override, "volatilidade geral informada"
        elif iv is not None:
            sigma, sigma_source = iv, "IV da série (mid)"
        else:
            sigma, sigma_source = None, "indisponível"
        flags = list(q["quote_flags"]) if q is not None else ["sem cotação no MT5"]
        source = q.get("source", "mt5") if q is not None else None
        if source == "mt5_fora_pregao":
            flags.append("lida fora do pregão")
        captured = q.get("captured_at") if q is not None else None
        expiration = info["expiration_date"]
        legs_out.append(
            {
                "index": i,
                "kind": OPTION_KIND,
                "symbol": leg.symbol,
                "side": leg.side.value,
                "quantity": leg.quantity,
                "option_type": info["option_type"],
                "strike": float(info["strike"]),
                "expiration": expiration.isoformat(),
                "exercise_style": info["exercise_style"],
                "multiplier": float(info.get("contract_size") or 1.0),
                "dte_business_days": business_days_until(calendar, today, expiration),
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "last": last,
                "spread_pct_mid": _f(q["spread_pct_mid"]) if q is not None else None,
                "price_basis": "ultimo_b3" if closing else "book",
                "px_buy": _f(q.get("px_buy")) if q is not None else None,
                "px_sell": _f(q.get("px_sell")) if q is not None else None,
                "px_mid": _f(q.get("px_mid")) if q is not None else None,
                "deals": _f(q["deals"]) if q is not None else None,
                "turnover_brl": _f(q["turnover_brl"]) if q is not None else None,
                "quote_time": q["quote_time"].isoformat()
                if q is not None and pd.notna(q["quote_time"])
                else None,
                "quote_age_seconds": _f(q["quote_age_seconds"]) if q is not None else None,
                "captured_at": pd.Timestamp(captured).isoformat()
                if captured is not None and pd.notna(captured)
                else None,
                "source": source,
                "iv": iv,
                "iv_status": q.get("iv_status") if q is not None else None,
                "sigma_used": sigma,
                "sigma_source": sigma_source,
                "price_used": price,
                "price_source": price_source,
                "price_given": leg.price,
                "flags": flags,
                "ref_note": q.get("ref_note")
                if q is not None and isinstance(q.get("ref_note"), str)
                else None,
            }
        )
        model_legs.append(
            Leg(
                OptionType(info["option_type"]),
                leg.side,
                float(info["strike"]),
                expiration,
                leg.quantity,
                float(info.get("contract_size") or 1.0),
                price,
                leg.symbol,
                info["exercise_style"],
            )
        )
        sigmas.append(sigma)

    missing = [lo["symbol"] for lo in legs_out if lo["price_used"] is None]
    if missing:
        raise SimulationError(
            f"sem preço para {', '.join(missing)}: informe o preço de entrada da perna"
        )
    structure = Structure(
        str(legs[0].info["underlying"] if legs[0].info else legs[0].symbol), tuple(model_legs)
    )
    entry_cash = net_premium(structure)
    sim = simulate(
        structure,
        today,
        calendar,
        rate,
        rate_annual,
        sigmas,
        costs,
        extra_prices=(spot, target_price),
    )
    sim["exit_spread_cost"] = exit_spread_cost(
        [leg.units for leg in structure.legs],
        [lo["bid"] for lo in legs_out],
        [lo["ask"] for lo in legs_out],
    )
    profile = profile_summary(structure, sim, costs)

    # Zerar agora (book atual): vende as compradas no bid, recompra as vendidas no ask (no
    # fechamento da B3, pelo último negócio: colunas px_*; o ativo segue o próprio book).
    def close_value(field: str) -> float | None:
        total = 0.0
        for leg, lo in zip(structure.legs, legs_out, strict=True):
            key = "mid" if field == "mid" else ("sell" if leg.side is Side.LONG else "buy")
            book = {"mid": "mid", "sell": "bid", "buy": "ask"}[key]
            px = lo.get(f"px_{key}", lo[book]) if lo["kind"] == OPTION_KIND else lo[book]
            if px is None:
                return None
            total += leg.side.sign * leg.units * px
        return total

    natural_now, mid_now = close_value("natural"), close_value("mid")

    terms = leg_terms(structure, calendar, today)
    model_ok = model_sigmas_ok(structure, sigmas) and all(
        t > 0
        for leg, t in zip(structure.legs, terms, strict=True)
        if leg.option_type is not OptionType.STOCK
    )
    theo_value = greeks = None
    if model_ok:
        theo_value = float(structure_value(structure, [spot], terms, rate, sigmas)[0])
        greeks = structure_greeks(structure, spot, terms, rate, sigmas)

    # POP: só com um vencimento; σ = média das σ das opções (documentado).
    option_sigmas = [
        s
        for leg, s in zip(structure.legs, sigmas, strict=True)
        if leg.option_type is not OptionType.STOCK
    ]
    pop = None
    pop_reason = None
    pop_method = None
    if len(structure.expirations) > 1:
        pop_reason = "vencimentos diferentes: probabilidade no vencimento não se aplica"
    elif not model_sigmas_ok(structure, sigmas):
        pop_reason = "sem volatilidade em todas as opções"
    else:
        sigma_pop = sum(option_sigmas) / len(option_sigmas)
        dte = business_days_until(calendar, today, first_exp)
        prob = pop_at_expiry(
            structure,
            spot,
            dte / pricing.BUSINESS_DAYS_PER_YEAR,
            rate,
            sigma_pop,
            f"média das volatilidades das opções ({sigma_pop:.1%})",
            costs,
        )
        pop, pop_reason, pop_method = prob.value, prob.reason, prob.method

    # Qualidade das cotações: pernas de momentos diferentes não podem passar por atuais.
    captured = sorted(lo["captured_at"] for lo in legs_out if lo.get("captured_at"))
    if len(captured) > 1:
        span = (pd.Timestamp(captured[-1]) - pd.Timestamp(captured[0])).total_seconds()
        if max_quote_age_seconds is not None and span > max_quote_age_seconds:
            warnings.append(
                f"pernas capturadas em momentos diferentes ({captured[0][11:16]} a "
                f"{captured[-1][11:16]}): o preço natural combina cotações que não coexistiram"
            )
    closing = [lo["symbol"] for lo in legs_out if lo.get("price_basis") == "ultimo_b3"]
    if closing:
        warnings.append(
            f"{', '.join(closing)} pelo fechamento oficial da B3 (último negócio do pregão): "
            "preço indicativo, sem bid/ask; os negócios podem ter sido em horários diferentes"
        )
    bad = [lo["symbol"] for lo in legs_out if lo["flags"]]
    if bad:
        warnings.append(f"cotação com problema em {', '.join(bad)}: preços podem não ser reais")
    given = [lo["symbol"] for lo in legs_out if lo["price_given"] is not None]
    if given:
        warnings.append(
            f"preço informado manualmente em {', '.join(given)} (não é cotação do mercado)"
        )
    if len(structure.expirations) > 1:
        warnings.append(
            "vencimentos diferentes (calendário/diagonal): o perfil no 1º vencimento depende do "
            "modelo para as pernas posteriores"
        )
    alerts = _early_exercise(structure, legs_out, spot, early_exercise)

    units = [leg.units for leg in structure.legs]
    same_units = len(set(units)) == 1
    margin = margin_estimate(structure)
    return {
        "underlying": structure.underlying,
        "kind_label": describe_simulation(structure),
        "spot": spot,
        "stock": stock,
        "target_price": target_price,
        "legs": legs_out,
        "entry_cash_total": entry_cash,
        "entry_flow": "credito" if entry_cash > 0 else "debito" if entry_cash < 0 else "zero",
        "entry_net_per_unit": abs(entry_cash) / units[0] if same_units else None,
        "costs_brl": costs,
        "close_natural_now": natural_now,
        "close_mid_now": mid_now,
        "pnl_close_natural_now": natural_now + entry_cash - costs
        if natural_now is not None
        else None,
        "pnl_close_mid_now": mid_now + entry_cash - costs if mid_now is not None else None,
        "theoretical_value_now": theo_value,
        "pnl_theoretical_now": theo_value + entry_cash - costs if theo_value is not None else None,
        "greeks": greeks,
        "pop": pop,
        "pop_method": pop_method,
        "pop_unavailable_reason": pop_reason,
        **profile,
        # JSON não tem infinito (vira null): sinaliza explicitamente o risco/lucro ilimitado.
        "max_profit_unbounded": profile["max_profit"] == math.inf,
        "max_loss_unbounded": profile["max_loss"] == math.inf,
        "margin": margin,
        "first_expiration": first_exp.isoformat(),
        "dte_business_days": business_days_until(calendar, today, first_exp),
        "simulation": sim,
        "warnings": warnings,
        "alerts": alerts,
    }
