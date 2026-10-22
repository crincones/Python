"""Stop 1:1 em travas de crédito (manejo ativo do canal "Credit Spread Investing").

Regra: a trava é encerrada quando o prejuízo atinge o lucro máximo, isto é, quando o custo para
desmontá-la chega a crédito × (1 + m) (m = 1 → stop no dobro do crédito; perda = crédito).

1. Fronteira do stop: para cada pregão até o vencimento, o preço do ativo em que o valor teórico
   de desmontar a trava (Black-Scholes, σ de cada perna) atinge esse custo. No vencimento ela é
   exata: strike vendido ∓ crédito × (1 + m).
2. Monte Carlo do ativo (lognormal, drift = taxa livre de risco, σ do POP), passo diário, com
   correção de ponte browniana entre os pregões (o stop pode ser acionado no meio do dia). Os
   mesmos sorteios valem para todas as travas da análise (números aleatórios comuns: a
   comparação entre elas não depende do acaso).
3. Por caminho: acionou o stop → resultado = −m × crédito − custo de saída (natural − mid da
   trava hoje, como estimativa do spread na saída); não acionou → crédito − valor no vencimento.

Sob a medida neutra ao risco, uma trava precificada exatamente pelo modelo tem resultado
esperado ≈ 0 com ou sem stop: o stop muda a DISTRIBUIÇÃO (perda limitada ao crédito, menos
chance de ganhar), não cria vantagem. O resultado esperado positivo vem do crédito acima do valor
teórico (ex.: IV das opções vendidas acima da IV ATM — o "skew"), e os custos de saída o reduzem.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from travas.options import pricing
from travas.options.models import OptionType, Side, Structure

SEED = 20261019
BISECTION_STEPS = 50
DEFAULT_PATHS = 4000

NOT_APPLICABLE_REASON = (
    "stop 1:1: crédito ≥ metade da largura (perda máxima ≤ crédito; o stop não se aplica)"
)
NO_MODEL_REASON = "stop 1:1: sem volatilidade para estimar a fronteira do stop (não estimável)"
ALREADY_STOPPED_REASON = "stop 1:1: o preço atual do ativo já acionaria o stop"


@functools.lru_cache(maxsize=16)
def _draws(days: int, paths: int, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    """Normais (antitéticas) e uniformes para `paths` caminhos de `days` pregões."""
    rng = np.random.default_rng(seed + days)
    half = rng.standard_normal((paths // 2, days))
    normals = np.vstack([half, -half])
    uniforms = rng.random(normals.shape)
    normals.setflags(write=False)
    uniforms.setflags(write=False)
    return normals, uniforms


def close_cost(
    structure: Structure,
    spot: np.ndarray,
    t_years: np.ndarray,
    rate: float,
    sigmas: Sequence[float],
) -> np.ndarray:
    """Custo teórico por unidade para desmontar a trava (recomprar a vendida, vender a
    comprada), com `spot` e `t_years` em broadcasting. Positivo numa trava de crédito."""
    cost = np.zeros(np.broadcast(spot, t_years).shape)
    for leg, sigma in zip(structure.legs, sigmas, strict=True):
        value = pricing.price(
            spot, leg.strike, t_years, rate, sigma, leg.option_type is OptionType.CALL
        )
        cost = cost - leg.side.sign * value
    return cost


def stop_boundary(
    structure: Structure,
    trigger_cost: float,
    dte: int,
    rate: float,
    sigmas: Sequence[float],
    down: bool,
) -> np.ndarray:
    """Preço do ativo que aciona o stop em cada pregão k = 0…dte (k pregões decorridos).

    `down`: a trava perde com a queda do ativo (put vendida). Pregão em que o custo nunca chega
    ao gatilho (ex.: largura descontada menor que ele) → 0 (queda) ou inf (alta)."""
    taus = (dte - np.arange(dte + 1)) / pricing.BUSINESS_DAYS_PER_YEAR
    return boundary_at(structure, trigger_cost, taus, rate, sigmas, down)


def boundary_at(
    structure: Structure,
    trigger_cost: float,
    taus: np.ndarray,
    rate: float,
    sigmas: Sequence[float],
    down: bool,
) -> np.ndarray:
    """Fronteira do stop para prazos `taus` (anos de dias úteis) até o vencimento."""
    strikes = [leg.strike for leg in structure.legs]
    taus = np.asarray(taus, dtype=np.float64)
    lo = np.full(taus.shape, 1e-6 * min(strikes))
    hi = np.full(taus.shape, 4.0 * max(strikes))
    edge = lo if down else hi  # lado em que o custo é máximo (≈ largura descontada)
    reachable = close_cost(structure, edge, taus, rate, sigmas) >= trigger_cost
    for _ in range(BISECTION_STEPS):
        mid = 0.5 * (lo + hi)
        hit = close_cost(structure, mid, taus, rate, sigmas) >= trigger_cost
        if down:  # custo maior abaixo da fronteira
            lo, hi = np.where(hit, mid, lo), np.where(hit, hi, mid)
        else:
            lo, hi = np.where(hit, lo, mid), np.where(hit, mid, hi)
    boundary = 0.5 * (lo + hi)
    return np.where(reachable, boundary, 0.0 if down else math.inf)


@functools.lru_cache(maxsize=8)
def _paths(
    spot: float, dte: int, rate: float, sigma: float, paths: int
) -> tuple[np.ndarray, np.ndarray]:
    """Log-preços nos fechamentos 1…dte e no fechamento anterior de cada passo (cache: todas
    as travas de um vencimento usam os mesmos caminhos)."""
    normals, _ = _draws(dte, paths)
    dt = 1.0 / pricing.BUSINESS_DAYS_PER_YEAR
    steps = (rate - 0.5 * sigma * sigma) * dt + sigma * math.sqrt(dt) * normals
    log_s = math.log(spot) + np.cumsum(steps, axis=1)
    log_prev = np.hstack([np.full((log_s.shape[0], 1), math.log(spot)), log_s[:, :-1]])
    for a in (log_s, log_prev):
        a.setflags(write=False)
    return log_s, log_prev


@dataclass(frozen=True)
class StopSimulation:
    prob_stop: float
    prob_full_credit: float  # sem stop e vence com a vendida fora do dinheiro
    prob_profit: float  # resultado > 0 com o manejo
    expected_pnl: float  # por unidade, com o manejo
    expected_pnl_no_stop: float  # por unidade, segurando até o vencimento
    median_stop_day: float | None  # pregões até o stop, entre os caminhos que o acionam


def simulate_stop(
    spot: float,
    boundary: np.ndarray,
    down: bool,
    dte: int,
    rate: float,
    sigma: float,
    credit: float,
    stop_loss: float,
    expiry_cost,
    paths: int = DEFAULT_PATHS,
) -> StopSimulation:
    """Monte Carlo do manejo. `stop_loss`: perda por unidade quando o stop é acionado (já com
    o custo de saída). `expiry_cost(S_T)`: custo de desmontar no vencimento (valor intrínseco)."""
    _, uniforms = _draws(dte, paths)
    log_s, log_prev = _paths(spot, dte, rate, sigma, paths)
    dt = 1.0 / pricing.BUSINESS_DAYS_PER_YEAR
    # Fronteira em log; inatingível → ±inf (nenhum caminho a cruza).
    with np.errstate(divide="ignore"):
        lb_end = np.log(np.where(boundary[1:] > 0, boundary[1:], 0.0))
        lb_mid = 0.5 * (lb_end + np.log(np.where(boundary[:-1] > 0, boundary[:-1], 0.0)))
    if down:
        beyond = log_s <= lb_end
        a, c = log_prev - lb_mid, log_s - lb_mid  # > 0: acima da fronteira (lado seguro)
    else:
        beyond = log_s >= lb_end
        a, c = lb_mid - log_prev, lb_mid - log_s
    finite = np.isfinite(lb_mid)
    safe = finite & (a > 0) & (c > 0)
    # Ponte browniana: chance de ter tocado a fronteira entre dois fechamentos.
    with np.errstate(invalid="ignore", over="ignore"):
        cross = np.exp(-2.0 * np.where(safe, a * c, np.inf) / (sigma * sigma * dt))
    hit = beyond | (safe & (uniforms < cross))
    stopped = hit.any(axis=1)
    final_cost = expiry_cost(np.exp(log_s[:, -1]))
    pnl = np.where(stopped, -stop_loss, credit - final_cost)
    no_stop = credit - final_cost
    full = (~stopped) & (final_cost <= 1e-12)
    first = hit.argmax(axis=1) + 1
    return StopSimulation(
        prob_stop=float(stopped.mean()),
        prob_full_credit=float(full.mean()),
        prob_profit=float((pnl > 1e-12).mean()),
        expected_pnl=float(pnl.mean()),
        expected_pnl_no_stop=float(no_stop.mean()),
        median_stop_day=float(np.median(first[stopped])) if stopped.any() else None,
    )


def credit_stop_metrics(
    structure: Structure,
    credit: float,
    mid_credit: float | None,
    width: float,
    dte: int,
    spot: float,
    rate: float,
    leg_sigmas: Sequence[float | None],
    path_sigma: float | None,
    costs_per_unit: float = 0.0,
    loss_multiple: float = 1.0,
    paths: int = DEFAULT_PATHS,
) -> tuple[dict | None, str | None]:
    """Métricas da trava de crédito com o stop. Devolve (métricas, None) ou (None, motivo)."""
    if credit <= 0 or credit * (1 + loss_multiple) >= width - 1e-9:
        return None, NOT_APPLICABLE_REASON
    sigmas = [s for s in leg_sigmas if s is not None and s > 0]
    if len(sigmas) != len(structure.legs) or path_sigma is None or path_sigma <= 0 or dte < 1:
        return None, NO_MODEL_REASON
    short = next(leg for leg in structure.legs if leg.side is Side.SHORT)
    down = short.option_type is OptionType.PUT
    trigger = credit * (1 + loss_multiple)
    boundary = stop_boundary(structure, trigger, dte, rate, sigmas, down)
    finite = boundary[np.isfinite(boundary) & (boundary > 0)]
    if not len(finite):
        return None, NOT_APPLICABLE_REASON
    today = float(boundary[0])
    if (down and spot <= today) or (not down and spot >= today):
        return None, ALREADY_STOPPED_REASON
    # Fronteira mais próxima do spot ao longo da vida da trava (hoje ela pode ser inatingível).
    nearest = float(finite.max() if down else finite.min())
    # Crédito pelo mid ≥ crédito natural; a diferença estima o spread pago também na saída.
    exit_cost = max(0.0, mid_credit - credit) if mid_credit is not None else 0.0
    stop_loss = loss_multiple * credit + exit_cost + costs_per_unit

    def expiry_cost(s_t: np.ndarray) -> np.ndarray:
        return close_cost(structure, s_t, np.zeros_like(s_t), rate, sigmas)

    sim = simulate_stop(
        spot, boundary, down, dte, rate, path_sigma, credit, stop_loss, expiry_cost, paths
    )
    expected = sim.expected_pnl - costs_per_unit
    t = dte / pricing.BUSINESS_DAYS_PER_YEAR
    reachable_today = math.isfinite(today) and today > 0
    return {
        "loss_multiple": loss_multiple,
        "trigger_cost": trigger,
        "stop_loss_per_unit": stop_loss,
        "exit_cost_per_unit": exit_cost,
        "stop_price_today": today if reachable_today else None,
        "stop_price_expiry": float(boundary[-1]),
        "stop_price_nearest": nearest,
        "stop_distance_pct": nearest / spot - 1,
        "stop_distance_sigmas": abs(math.log(nearest / spot)) / (path_sigma * math.sqrt(t)),
        "prob_stop": sim.prob_stop,
        "prob_no_stop": 1 - sim.prob_stop,
        "prob_full_credit": sim.prob_full_credit,
        "prob_profit": sim.prob_profit,
        "expected_pnl_per_unit": expected,
        "expected_pnl_no_stop_per_unit": sim.expected_pnl_no_stop - costs_per_unit,
        "ev_on_risk": expected / stop_loss,
        "credit_on_capital": credit / (width - credit),
        "exit_cost_on_credit": exit_cost / credit,
        "median_stop_day": sim.median_stop_day,
        "paths": paths,
        "path_sigma": path_sigma,
    }, None


STOP_NOT_VERTICAL = "stop 1:1 só para travas verticais (duas opções do mesmo tipo e vencimento)"
STOP_NO_MODEL = "sem volatilidade nas pernas para estimar o preço do stop antes do vencimento"


def _vertical(structure: Structure) -> bool:
    legs = structure.legs
    return (
        len(legs) == 2
        and legs[0].option_type is legs[1].option_type is not OptionType.STOCK
        and legs[0].option_type in (OptionType.CALL, OptionType.PUT)
        and legs[0].side is not legs[1].side
        and legs[0].expiration == legs[1].expiration
        and abs(legs[0].units - legs[1].units) < 1e-9
        and legs[0].strike != legs[1].strike
    )


def stop_levels(
    structure: Structure,
    rate: float,
    sigmas: Sequence[float | None],
    days_left: Sequence[int],
    loss_multiple: float = 1.0,
) -> dict:
    """Preço do ativo em que a trava vertical (crédito ou débito) atinge o stop 1:1 — prejuízo
    = `loss_multiple` × lucro máximo — em cada data com `days_left` pregões até o vencimento.

    Antes do vencimento pelo valor teórico (Black-Scholes, σ de cada perna); no vencimento pelo
    payoff. Sem custos operacionais. Na trava em que a perda máxima já é ≤ o prejuízo do stop
    (débito ≤ metade da largura; crédito ≥ metade), o stop não se aplica."""
    base = {"loss_multiple": loss_multiple, "prices": [None] * len(days_left)}
    if not _vertical(structure):
        return {**base, "available": False, "reason": STOP_NOT_VERTICAL}
    units = structure.legs[0].units
    width = abs(structure.legs[0].strike - structure.legs[1].strike)
    entry = sum(-leg.side.sign * leg.price for leg in structure.legs)  # + crédito, − débito
    max_profit = width + entry if entry < 0 else entry  # débito: largura − débito
    max_loss = width - max_profit
    stop_pnl = -loss_multiple * max_profit
    base |= {
        "flow": "credito" if entry > 0 else "debito",
        "pnl_per_unit": stop_pnl,
        "pnl_total": stop_pnl * units,
        "units": units,
    }
    if max_profit <= 0 or loss_multiple * max_profit >= max_loss - 1e-9:
        reason = (
            "stop 1:1 não se aplica: a perda máxima já é ≤ o lucro máximo"
            if max_profit > 0
            else "stop 1:1 não se aplica: lucro máximo ≤ 0"
        )
        return {**base, "available": False, "reason": reason}
    # Desmontar custa `c` por unidade; P&L = entrada − c; stop quando c ≥ entrada + m × lucro.
    trigger = entry + loss_multiple * max_profit
    probe = np.array([1e-6 * min(structure.strikes), 4.0 * max(structure.strikes)])
    zero = np.zeros(2)
    flat = [1.0, 1.0]  # no vencimento σ não importa
    low_cost, high_cost = close_cost(structure, probe, zero, rate, flat)
    down = bool(low_cost > high_cost)  # perde com a queda do ativo (trava de alta)
    days = np.asarray(days_left, dtype=np.float64)
    ok = all(s is not None and math.isfinite(s) and s > 0 for s in sigmas)
    taus = days / pricing.BUSINESS_DAYS_PER_YEAR
    model = boundary_at(structure, trigger, taus, rate, list(sigmas) if ok else flat, down)
    prices = [
        float(b) if (d == 0 or ok) and math.isfinite(b) and b > 0 else None
        for b, d in zip(model, days, strict=True)
    ]
    return {
        **base,
        "available": True,
        "reason": None if ok else STOP_NO_MODEL,
        "down": down,
        "trigger_cost": trigger,
        "prices": prices,
    }
