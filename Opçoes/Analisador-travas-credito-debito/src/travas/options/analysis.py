"""Gera, avalia e ranqueia travas verticais a partir de uma cadeia de opções normalizada.

Funções puras (sem MT5): recebem a cadeia (`travas.data.normalize.CHAIN_COLUMNS`), o spot e os
parâmetros do usuário; devolvem dicionários prontos para a API. Toda trava é montada pelas pernas e
validada por `validate_vertical` — o rótulo pedido não basta.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.options import pricing
from travas.options.implied_vol import IVStatus, atm_implied_vol, options_implied_vol
from travas.options.limit_price import suggest_limit
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.options.models import (
    Direction,
    Flow,
    Leg,
    OptionType,
    Side,
    Structure,
    VerticalKind,
    vertical_kind,
)
from travas.options.payoff import expiry_profile, pnl_at_expiry
from travas.options.probability import pop_at_expiry, prob_finish_beyond, prob_touch
from travas.options.simulation import simulate
from travas.options.validation import validate_vertical
from travas.options.valuation import (
    structure_greeks,
    structure_value,
    theoretical_pnl,
    valid_sigmas,
)
from travas.settings import EarlyExerciseSettings, PricingSettings

RANKING_COMPONENTS: dict[str, tuple[str, bool, str]] = {
    # nome → (métrica, maior é melhor, descrição)
    "scenario": ("scenario_return_on_risk", True, "resultado no cenário-alvo ÷ perda máxima"),
    "reward_risk": ("reward_risk", True, "lucro máximo ÷ perda máxima"),
    "pop": ("pop", True, "probabilidade de lucro no vencimento"),
    "liquidity": ("liquidity_score", True, "liquidez da pior perna"),
    "execution_cost": ("execution_cost_pct_width", False, "(natural − mid) ÷ largura"),
}

# Filtro Rafael Nobre (travas de débito):
# 1) com alvo conhecido, a perna mais afastada (a vendida) deve ficar ANTES do alvo — de
#    preferência; o usuário escolhe se é exigência ou só prioridade no ranking;
# 2) o custo (débito natural) não deve passar de 1/4 da distância entre os strikes (lucro
#    máximo ≥ 3 × perda máxima); o usuário pode afrouxar para 1/3 (lucro ≥ 2 × perda);
# 3) entre as que passam, priorizar strikes mais próximos (menor largura primeiro).
NOBRE_COST_FRACTIONS = {0.25: "1/4", 1 / 3: "1/3"}
NOBRE_MAX_COST_FRACTION = 0.25  # padrão
NOBRE_COST_REASON = "Rafael Nobre: custo acima do teto da distância entre strikes"
NOBRE_TARGET_REASON = "Rafael Nobre: perna vendida além do alvo"


def nobre_min_reward_risk(fraction: float) -> float:
    """Custo ≤ f × largura ⇔ lucro máx./perda máx. ≥ (1 − f)/f (1/4 → 3; 1/3 → 2)."""
    return (1 - fraction) / fraction


def nobre_fraction_label(fraction: float) -> str:
    return next(
        (v for k, v in NOBRE_COST_FRACTIONS.items() if abs(k - fraction) < 1e-9), f"{fraction:.0%}"
    )


def nobre_check(
    kind: VerticalKind,
    short_strike: float,
    width: float,
    entry: float,
    target: float | None,
    max_cost_fraction: float = NOBRE_MAX_COST_FRACTION,
) -> dict | None:
    """Critérios do filtro Rafael Nobre para uma trava de débito (None nas de crédito)."""
    if kind.flow is not Flow.DEBIT:
        return None
    if target is None:
        target_ok = None
    elif kind.direction is Direction.BULL:
        target_ok = short_strike <= target + 1e-9
    else:
        target_ok = short_strike >= target - 1e-9
    max_cost = width * max_cost_fraction
    return {
        "max_cost_fraction": max_cost_fraction,
        "cost_ratio": entry / width,
        "max_cost": max_cost,
        "cost_ok": entry <= max_cost + 1e-9,
        "target_ok": target_ok,
        "ok": entry <= max_cost + 1e-9 and target_ok is not False,
    }


SETTLEMENT_NOTE = (
    "Opções de ações na B3 têm liquidação física: exercício/atribuição gera compra ou venda do "
    "ativo. Verifique as regras de exercício automático e o calendário da B3."
)


@dataclass(frozen=True)
class AnalysisParams:
    direction: Direction
    flow: Flow
    quantity: int
    rate_annual: float
    liquidity: LiquidityRules
    weights: dict[str, float]
    pricing: PricingSettings
    early_exercise: EarlyExerciseSettings
    dte_min: int = 3
    dte_max: int = 60
    expirations: tuple[dt.date, ...] | None = None
    strike_min: float | None = None
    strike_max: float | None = None
    max_width: float | None = None
    max_loss_total: float | None = None
    target_price: float | None = None
    horizon_date: dt.date | None = None
    scenarios: tuple[tuple[str, float], ...] = ()
    vol_override: float | None = None
    include_illiquid: bool = False
    illiquid_score_cap: float = 40.0
    limit_aggressiveness: float = 0.25
    min_reward_risk: float | None = None
    nobre_filter: bool = False  # filtro Rafael Nobre (só travas de débito)
    nobre_target_required: bool = False  # True = exige perna vendida antes do alvo
    nobre_max_cost_fraction: float = NOBRE_MAX_COST_FRACTION  # 1/4 (padrão) ou 1/3
    nobre_prefer_close: bool = True  # strikes mais próximos primeiro no ranking
    # Exige perna VENDIDA europeia: o risco de exercício antecipado (atribuição) é da vendida
    # americana; a comprada só é exercida se o titular (o usuário) quiser.
    european_short: bool = False
    costs_brl: float = 0.0
    max_results: int = 300

    @property
    def kind(self) -> VerticalKind:
        return vertical_kind(self.direction, self.flow)


@dataclass
class PreparedChain:
    """Cadeia com IV, liquidez e σ por série, e IV ATM por vencimento."""

    chain: pd.DataFrame
    atm: pd.DataFrame
    spot: float
    today: dt.date
    rate: float  # contínua
    params: AnalysisParams
    calendar: B3Calendar
    horizon_business_days: int | None
    discarded: dict[str, int] = field(default_factory=dict)

    def atm_iv(self, expiration: dt.date) -> float | None:
        row = self.atm[self.atm["expiration_date"] == expiration]
        return float(row["atm_iv"].iloc[0]) if len(row) else None

    def vol_source(self, expiration: dt.date) -> tuple[float | None, str]:
        if self.params.vol_override is not None:
            v = self.params.vol_override
            return v, f"volatilidade informada pelo usuário ({v:.1%})"
        atm = self.atm_iv(expiration)
        if atm is None:
            return None, "sem IV ATM confiável no vencimento"
        return atm, f"IV ATM do vencimento ({atm:.1%}), calculada sobre o mid"


def prepare_chain(
    chain: pd.DataFrame,
    spot: float,
    today: dt.date,
    calendar: B3Calendar,
    params: AnalysisParams,
) -> PreparedChain:
    frame = chain.copy()
    frame = frame.join(evaluate_liquidity(frame, params.liquidity))
    iv = options_implied_vol(frame, params.rate_annual, params.pricing)
    frame = frame.join(iv)
    atm = atm_implied_vol(frame, params.pricing)
    atm_by_exp = dict(zip(atm["expiration_date"], atm["atm_iv"], strict=True))
    if params.vol_override is not None:
        frame["sigma"] = params.vol_override
        frame["sigma_source"] = "usuário"
    else:
        own = frame["iv"].where(frame["iv_status"] == IVStatus.OK.value)
        fallback = frame["expiration_date"].map(atm_by_exp)
        frame["sigma"] = own.fillna(fallback)
        frame["sigma_source"] = np.where(
            own.notna(), "IV da série", np.where(fallback.notna(), "IV ATM", "indisponível")
        )
    horizon = None
    if params.horizon_date is not None:
        horizon = int(calendar.sessions_until(today, pd.Series([params.horizon_date])).iloc[0])
    return PreparedChain(
        chain=frame,
        atm=atm,
        spot=spot,
        today=today,
        rate=float(pricing.continuous_rate(params.rate_annual)),
        params=params,
        calendar=calendar,
        horizon_business_days=horizon,
    )


def _f(value: object) -> float | None:
    if value is None:
        return None
    try:
        x = float(value)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None
    return x if math.isfinite(x) else None


def _leg(row: pd.Series, side: Side, price: float | None, quantity: int) -> Leg:
    return Leg(
        option_type=OptionType(row["option_type"]),
        side=side,
        strike=float(row["strike"]),
        expiration=row["expiration_date"],
        quantity=quantity,
        multiplier=float(row["contract_size"]),
        price=price,
        symbol=str(row["symbol"]),
        exercise_style=str(row["exercise_style"]),
    )


def _leg_info(row: pd.Series, side: Side) -> dict:
    return {
        "symbol": row["symbol"],
        "side": side.value,
        "option_type": row["option_type"],
        "strike": _f(row["strike"]),
        "exercise_style": row["exercise_style"],
        "bid": _f(row["bid"]),
        "ask": _f(row["ask"]),
        "last": _f(row["last"]),
        "mid": _f(row["mid"]),
        "spread_pct_mid": _f(row["spread_pct_mid"]),
        "quote_time": row["quote_time"].isoformat() if pd.notna(row["quote_time"]) else None,
        "quote_age_seconds": _f(row["quote_age_seconds"]),
        "deals": int(row["deals"]) if pd.notna(row["deals"]) else None,
        "volume_qty": _f(row["volume_qty"]),
        "turnover_brl": _f(row["turnover_brl"]),
        "volume_source": row.get("volume_source"),
        "ref_note": row.get("ref_note") if isinstance(row.get("ref_note"), str) else None,
        "contract_size": _f(row["contract_size"]),
        "iv": _f(row["iv"]),
        "iv_status": row["iv_status"],
        "sigma": _f(row["sigma"]),
        "sigma_source": row["sigma_source"],
        "liquidity_ok": bool(row["liquidity_ok"]),
        "liquidity_score": _f(row["liquidity_score"]),
        "flags": list(row["quote_flags"]),
    }


def candidate_pairs(prep: PreparedChain) -> list[tuple[pd.Series, pd.Series]]:
    """Pares (comprada, vendida) com a geometria da trava pedida, dentro dos filtros."""
    p = prep.params
    kind = p.kind
    frame = prep.chain[prep.chain["option_type"] == kind.option_type.value]
    frame = frame[frame["dte_business_days"].between(max(p.dte_min, 1), p.dte_max)]
    if p.expirations:
        frame = frame[frame["expiration_date"].isin(p.expirations)]
    if p.strike_min is not None:
        frame = frame[frame["strike"] >= p.strike_min]
    if p.strike_max is not None:
        frame = frame[frame["strike"] <= p.strike_max]
    long_lower = kind.direction is Direction.BULL
    pairs: list[tuple[pd.Series, pd.Series]] = []
    for _, group in frame.groupby("expiration_date", sort=True):
        rows = [r for _, r in group.sort_values("strike").iterrows()]
        for i, low in enumerate(rows):
            for high in rows[i + 1 :]:
                width = float(high["strike"] - low["strike"])
                if width <= 0 or (p.max_width is not None and width > p.max_width + 1e-9):
                    continue
                pairs.append((low, high) if long_lower else (high, low))
    return pairs


def evaluate_pair(prep: PreparedChain, long_row: pd.Series, short_row: pd.Series) -> dict:
    """Todas as métricas de uma trava. `invalid` lista motivos que impedem o uso no ranking."""
    p = prep.params
    expiration = long_row["expiration_date"]
    dte = int(long_row["dte_business_days"])
    t_now = dte / pricing.BUSINESS_DAYS_PER_YEAR
    width = abs(float(long_row["strike"]) - float(short_row["strike"]))
    long_ask, short_bid = _f(long_row["ask"]), _f(short_row["bid"])
    long_mid, short_mid = _f(long_row["mid"]), _f(short_row["mid"])
    sign = 1 if p.flow is Flow.DEBIT else -1  # entrada positiva no sentido da estrutura

    # Arredonda a 1e-6 para eliminar ruído de ponto flutuante (preços têm tick de R$ 0,01).
    natural = (
        None if long_ask is None or short_bid is None else round(sign * (long_ask - short_bid), 6)
    )
    mid = None if long_mid is None or short_mid is None else round(sign * (long_mid - short_mid), 6)

    result: dict = {
        "id": f"{long_row['symbol']}|{short_row['symbol']}",
        "kind": p.kind.value,
        "kind_label": p.kind.label,
        "expiration": expiration.isoformat(),
        "dte_business_days": dte,
        "dte_calendar_days": int(long_row["dte_calendar_days"]),
        "width": width,
        "quantity": p.quantity,
        "legs": [_leg_info(long_row, Side.LONG), _leg_info(short_row, Side.SHORT)],
        "entry_natural": natural,
        "entry_mid": mid,
        "invalid": [],
        "warnings": [],
    }
    style_errors = exercise_style_errors(p, short_row)
    if style_errors:
        result["invalid"].extend(style_errors)
        return result
    if natural is None:
        result["invalid"].append("sem bid/ask para o preço natural (não estimável)")
        return result

    structure = Structure(
        str(long_row["underlying"]),
        (
            _leg(long_row, Side.LONG, long_ask, p.quantity),
            _leg(short_row, Side.SHORT, short_bid, p.quantity),
        ),
    )
    validation = validate_vertical(structure, p.direction, p.flow)
    result["invalid"].extend(validation.errors)
    result["warnings"].extend(validation.warnings)
    if not validation.ok:
        return result

    units = structure.legs[0].units
    profile = expiry_profile(structure, p.costs_brl)
    result.update(
        {
            "units": units,
            "entry_per_unit": natural,
            "entry_total": natural * units,
            "net_premium_total": profile.net_premium,
            "costs_brl": p.costs_brl,
            "max_profit": profile.max_profit,
            "max_loss": profile.max_loss,
            "max_profit_per_unit": profile.max_profit / units,
            "max_loss_per_unit": profile.max_loss / units,
            "breakevens": [round(x, 6) for x in profile.breakevens],
            "reward_risk": profile.reward_risk,
            "risk_reward": profile.risk_reward,
            "execution_cost_pct_width": (natural - mid) / width if mid is not None else None,
        }
    )
    if p.max_loss_total is not None and profile.max_loss > p.max_loss_total + 1e-9:
        result["invalid"].append("perda máxima acima do orçamento")

    # Volatilidade, POP e probabilidades do alvo.
    sigma_pop, vol_source = prep.vol_source(expiration)
    pop = pop_at_expiry(structure, prep.spot, t_now, prep.rate, sigma_pop, vol_source, p.costs_brl)
    result["pop"] = pop.value
    result["pop_method"] = pop.method
    result["pop_unavailable_reason"] = pop.reason
    result["vol_source"] = vol_source
    result["sigma_pop"] = sigma_pop

    sigmas = [_f(long_row["sigma"]), _f(short_row["sigma"])]
    sigmas_ok = valid_sigmas(sigmas)
    result["model_available"] = sigmas_ok
    if sigmas_ok:
        theo_total = float(structure_value(structure, [prep.spot], t_now, prep.rate, sigmas)[0])
        result["entry_theoretical"] = sign * theo_total / units
        result["greeks"] = structure_greeks(structure, prep.spot, t_now, prep.rate, sigmas)
    else:
        result["entry_theoretical"] = None
        result["greeks"] = None

    # Cenários: alvo e cenários extras, na data do horizonte (ou no vencimento).
    horizon = prep.horizon_business_days
    at_expiry = horizon is None or horizon >= dte
    t_left = 0.0 if at_expiry else (dte - horizon) / pricing.BUSINESS_DAYS_PER_YEAR
    result["scenario_at_expiry"] = at_expiry
    scenarios = []
    named = ([("alvo", p.target_price)] if p.target_price else []) + list(p.scenarios)
    for name, price in named:
        if at_expiry:
            pnl = float(pnl_at_expiry(structure, [price], p.costs_brl)[0])
            basis = "payoff no vencimento"
        elif sigmas_ok:
            pnl = float(
                theoretical_pnl(structure, [price], t_left, prep.rate, sigmas, p.costs_brl)[0]
            )
            basis = f"valor teórico com {dte - horizon} du restantes"
        else:
            pnl, basis = None, "sem volatilidade para avaliar antes do vencimento"
        scenarios.append({"name": name, "price": price, "pnl": pnl, "basis": basis})
    result["scenarios"] = scenarios
    target = next((s for s in scenarios if s["name"] == "alvo"), None)
    result["scenario_pnl"] = target["pnl"] if target else None
    result["scenario_return_on_risk"] = (
        target["pnl"] / profile.max_loss
        if target and target["pnl"] is not None and profile.max_loss > 0
        else None
    )
    if p.target_price:
        above = p.direction is Direction.BULL
        result["prob_target_at_expiry"] = prob_finish_beyond(
            prep.spot, p.target_price, above, t_now, prep.rate, sigma_pop
        ).value
        t_touch = t_now if at_expiry else horizon / pricing.BUSINESS_DAYS_PER_YEAR
        result["prob_touch_target"] = prob_touch(
            prep.spot, p.target_price, t_touch, prep.rate, sigma_pop
        ).value
    else:
        result["prob_target_at_expiry"] = result["prob_touch_target"] = None

    # Liquidez e qualidade de dados: a trava herda a pior perna.
    legs_ok = bool(long_row["liquidity_ok"]) and bool(short_row["liquidity_ok"])
    result["liquidity_ok"] = legs_ok
    result["liquidity_score"] = float(
        min(long_row["liquidity_score"], short_row["liquidity_score"])
    )
    result["data_flags"] = sorted(set(long_row["quote_flags"]) | set(short_row["quote_flags"]))

    nobre = nobre_check(
        p.kind,
        float(short_row["strike"]),
        width,
        natural,
        p.target_price,
        p.nobre_max_cost_fraction,
    )
    result["nobre"] = nobre
    nobre_active = p.nobre_filter and nobre is not None
    min_rr = p.min_reward_risk
    if nobre_active:  # preço-limite também respeita o teto de custo do filtro
        min_rr = max(min_rr or 0.0, nobre_min_reward_risk(p.nobre_max_cost_fraction))
    limit = suggest_limit(
        structure,
        p.flow,
        width,
        natural,
        mid,
        result["entry_theoretical"],
        p.limit_aggressiveness,
        min_rr,
        p.max_loss_total,
        p.costs_brl,
    )
    result["limit"] = _limit_dict(limit)
    result["early_exercise"] = early_exercise_alert(prep, short_row)
    for row_, side in ((long_row, "comprada"), (short_row, "vendida")):
        note = row_.get("ref_note")
        if isinstance(note, str) and note:
            result["warnings"].append(f"{row_['symbol']} ({side}): {note}")
    if nobre_active:
        if not nobre["cost_ok"]:
            result["invalid"].append(NOBRE_COST_REASON)
        if p.nobre_target_required and nobre["target_ok"] is False:
            result["invalid"].append(NOBRE_TARGET_REASON)
    return result


EUROPEAN_SHORT_REASON = "filtro de estilo: perna vendida americana (pode ser exercida antes)"


def exercise_style_errors(p: AnalysisParams, short_row: pd.Series) -> list[str]:
    if p.european_short and short_row["exercise_style"] != "european":
        return [EUROPEAN_SHORT_REASON]
    return []


def early_exercise_alert(prep: PreparedChain, short_row: pd.Series) -> str | None:
    """Alerta quando a perna vendida é americana, está ITM e tem pouco valor extrínseco."""
    if short_row["exercise_style"] != "american":
        return None
    strike = float(short_row["strike"])
    is_call = short_row["option_type"] == "call"
    intrinsic = max(prep.spot - strike, 0.0) if is_call else max(strike - prep.spot, 0.0)
    if intrinsic <= 0:
        return "vendida americana (OTM agora): risco de exercício antecipado baixo, mas existe"
    premium = _f(short_row["bid"]) or _f(short_row["mid"]) or _f(short_row["last"])
    if premium is None:
        return "vendida americana ITM sem preço para medir o valor extrínseco"
    extrinsic = premium - intrinsic
    s = prep.params.early_exercise
    if extrinsic < max(s.min_extrinsic_brl, s.min_extrinsic_pct_premium * premium):
        return (
            f"RISCO de exercício antecipado: vendida americana ITM com extrínseco "
            f"R$ {extrinsic:.2f}"
        )
    return "vendida americana ITM: acompanhar valor extrínseco e datas de proventos"


def _limit_dict(limit) -> dict:
    return {
        "flow": limit.flow.value,
        "natural": limit.natural,
        "mid": limit.mid,
        "theoretical": limit.theoretical,
        "suggested": limit.suggested,
        "range_low": limit.range_low,
        "range_high": limit.range_high,
        "notes": list(limit.notes),
        "reason_unavailable": limit.reason_unavailable,
        "impacts": {
            name: {
                "price": i.price,
                "max_profit": i.max_profit,
                "max_loss": i.max_loss,
                "breakevens": list(i.breakevens),
                "reward_risk": i.reward_risk,
            }
            for name, i in limit.impacts.items()
        },
    }


def score_candidates(rows: list[dict], weights: dict[str, float], cap: float) -> None:
    """Score 0–100 = Σ peso × percentil (entre as travas desta análise), com pesos
    redistribuídos quando um componente não está disponível para a trava. Trava com perna
    reprovada em liquidez/cotação fica limitada a `cap`."""
    if not rows:
        return
    frame = pd.DataFrame(
        {
            name: [r.get(metric) for r in rows]
            for name, (metric, _, _) in RANKING_COMPONENTS.items()
        },
        dtype="float64",
    )
    pct = pd.DataFrame(index=frame.index)
    for name, (_, higher, _) in RANKING_COMPONENTS.items():
        pct[name] = frame[name].rank(pct=True, ascending=higher, method="average")
    for i, row in enumerate(rows):
        available = {n: w for n, w in weights.items() if w > 0 and pd.notna(pct.at[i, n])}
        total_w = sum(available.values())
        components = {}
        for name, (_, higher, description) in RANKING_COMPONENTS.items():
            value = pct.at[i, name]
            components[name] = {
                "percentile": None if pd.isna(value) else float(value),
                "weight": weights.get(name, 0.0),
                "effective_weight": available.get(name, 0.0) / total_w if total_w else 0.0,
                "description": description,
                "higher_is_better": higher,
            }
        score = (
            100 * sum(w * float(pct.at[i, n]) for n, w in available.items()) / total_w
            if total_w
            else None
        )
        capped = score is not None and not row["liquidity_ok"] and score > cap
        row["score"] = min(score, cap) if capped else score
        row["score_capped"] = capped
        row["score_components"] = components


def analyze(
    chain: pd.DataFrame,
    spot: float,
    today: dt.date,
    calendar: B3Calendar,
    params: AnalysisParams,
) -> dict:
    return analyze_prepared(prepare_chain(chain, spot, today, calendar, params))


def analyze_prepared(prep: PreparedChain) -> dict:
    params = prep.params
    spot = prep.spot
    discarded: dict[str, int] = {}
    ranked: list[dict] = []
    for long_row, short_row in candidate_pairs(prep):
        row = evaluate_pair(prep, long_row, short_row)
        if row["invalid"]:
            for reason in row["invalid"]:
                discarded[reason] = discarded.get(reason, 0) + 1
            continue
        if not row["liquidity_ok"] and not params.include_illiquid:
            discarded["perna com liquidez/cotação reprovada"] = (
                discarded.get("perna com liquidez/cotação reprovada", 0) + 1
            )
            continue
        ranked.append(row)
    score_candidates(ranked, params.weights, params.illiquid_score_cap)
    nobre_active = params.nobre_filter and params.flow is Flow.DEBIT
    ranked.sort(
        key=lambda r: (
            # Filtro Nobre "preferencial": travas com a vendida antes do alvo vêm primeiro.
            nobre_active and (r.get("nobre") or {}).get("target_ok") is False,
            # …e, entre elas, strikes mais próximos (menor largura) primeiro; empate → score.
            round(r["width"], 4) if nobre_active and params.nobre_prefer_close else 0,
            r["score"] is None,
            -(r["score"] or 0),
        )
    )
    for position, row in enumerate(ranked, start=1):
        row["rank"] = position
    return {
        "kind": params.kind.value,
        "kind_label": params.kind.label,
        "spot": spot,
        "candidates_evaluated": len(ranked) + sum(discarded.values()),
        "discarded": discarded,
        "results": ranked[: params.max_results],
        "total_ranked": len(ranked),
        "atm_iv": [
            {"expiration": r.expiration_date.isoformat(), "atm_iv": float(r.atm_iv)}
            for r in prep.atm.itertuples()
        ],
        "expirations": sorted({d.isoformat() for d in prep.chain["expiration_date"].unique()}),
        "assumptions": assumptions(prep),
        "nobre": nobre_summary(params, ranked),
    }


def nobre_summary(params: AnalysisParams, ranked: list[dict] | None = None) -> dict | None:
    if not params.nobre_filter:
        return None
    if params.flow is not Flow.DEBIT:
        return {"active": False, "note": "filtro Rafael Nobre vale só para travas de débito"}
    f = params.nobre_max_cost_fraction
    notes = [
        f"custo (débito natural) ≤ {nobre_fraction_label(f)} da distância entre strikes "
        f"(lucro máx. ≥ {nobre_min_reward_risk(f):.0f} × perda máx.); o preço-limite sugerido "
        "respeita esse teto"
    ]
    if params.nobre_prefer_close:
        notes.append("ordem: strikes mais próximos primeiro (menor largura), depois o score")
    if params.target_price is None:
        notes.append("sem preço-alvo: o critério da perna antes do alvo não foi aplicado")
    elif params.nobre_target_required:
        notes.append("perna vendida antes do alvo: exigida")
    else:
        notes.append("perna vendida antes do alvo: preferida (aparece primeiro no ranking)")
    both = sum(1 for r in ranked or [] if (r.get("nobre") or {}).get("target_ok") is True)
    warning = None
    if params.target_price is not None and ranked and both == 0:
        warning = (
            "Nenhuma trava cumpre as duas regras ao mesmo tempo: com a perna vendida antes do alvo "
            f"o custo passa de {nobre_fraction_label(f)} da largura. As travas listadas cumprem só "
            "o custo (vendida além do alvo). Considere alvo mais distante ou vencimento mais longo"
            + (" ou o teto de 1/3." if f < 0.3 else ".")
        )
    return {"active": True, "note": "; ".join(notes), "both_rules": both, "warning": warning}


def assumptions(prep: PreparedChain) -> dict:
    p = prep.params
    return {
        "rate_annual": p.rate_annual,
        "rate_continuous": prep.rate,
        "vol_override": p.vol_override,
        "horizon_date": p.horizon_date.isoformat() if p.horizon_date else None,
        "horizon_business_days": prep.horizon_business_days,
        "target_price": p.target_price,
        "costs_brl": p.costs_brl,
        "entry_basis": "preço natural: compra no ask, venda no bid",
        "iv_method": "IV Black-Scholes europeu sobre o mid de cada série (brentq), sem dividendos",
        "ranking_note": (
            "Percentis relativos às travas desta análise; componentes indisponíveis têm o peso "
            "redistribuído. Pernas reprovadas em liquidez limitam o score a "
            f"{p.illiquid_score_cap:.0f}."
        ),
        "weights": p.weights,
        "settlement_note": SETTLEMENT_NOTE,
        "exercise_style_filter": ["perna vendida europeia"] if p.european_short else [],
    }


def find_pair(
    prep: PreparedChain, long_symbol: str, short_symbol: str
) -> tuple[pd.Series, pd.Series]:
    by_symbol = prep.chain.set_index("symbol", drop=False)
    if long_symbol not in by_symbol.index or short_symbol not in by_symbol.index:
        raise KeyError("série não encontrada na cadeia coletada")
    return by_symbol.loc[long_symbol], by_symbol.loc[short_symbol]


def simulation_grid(
    prep: PreparedChain, long_row: pd.Series, short_row: pd.Series, points: int = 161
) -> dict:
    """Curvas de P&L: no vencimento (exato) e valor teórico em cada pregão até o vencimento."""
    p = prep.params
    long_ask, short_bid = _f(long_row["ask"]), _f(short_row["bid"])
    if long_ask is None or short_bid is None:
        return {"available": False, "reason": "sem preço natural"}
    structure = Structure(
        str(long_row["underlying"]),
        (
            _leg(long_row, Side.LONG, long_ask, p.quantity),
            _leg(short_row, Side.SHORT, short_bid, p.quantity),
        ),
    )
    sigmas = [_f(long_row["sigma"]), _f(short_row["sigma"])]
    sim = simulate(
        structure,
        prep.today,
        prep.calendar,
        prep.rate,
        p.rate_annual,
        sigmas,
        p.costs_brl,
        extra_prices=(p.target_price, prep.spot),
        points=points,
    )
    sim["dte_business_days"] = int(long_row["dte_business_days"])
    sim["rate_continuous"] = prep.rate
    return sim
