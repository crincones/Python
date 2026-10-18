"""Ativo protegido (estruturas do Rafael Nobre): compra do ativo + put de proteção + calls vendidas.

Duas estruturas, mesmo vencimento, descritas por 1 ação (todas as quantidades × `quantity`):

- **Collar**: +1 ativo, +1 put Kp, −1 call Kc (Kp < Kc).
  Valor no vencimento = Kp abaixo de Kp; S entre Kp e Kc; Kc acima de Kc.
- **Collar + borboleta** ("equity butterfly"): +1 ativo, +1 put Kp, −2 calls K1, +1 call K2
  (Kp < K1 < K2). Valor no vencimento = Kp abaixo de Kp; S entre Kp e K1; 2·K1 − S entre K1 e K2;
  2·K1 − K2 acima de K2. Máximo em S = K1.

"Risco zero" (termo do vídeo) = o menor valor da estrutura no vencimento (o **piso**) cobre o custo
de montagem. Vale só no vencimento, com todas as pernas mantidas até lá, sem exercício antecipado
das calls vendidas e com os custos informados. Pela paridade put-call, com preços justos o piso
rende no máximo cerca da taxa livre de risco do período: retorno acima do CDI vem do ganho possível
(região entre os strikes), não do piso.

Funções puras (sem MT5). O perfil é calculado pelas pernas (pontos de quebra + inclinações nas
pontas), não pelo rótulo: estrutura sem piso ou sem teto finito é rejeitada.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.options import pricing
from travas.options.analysis import _f, _leg_info, early_exercise_alert, score_candidates
from travas.options.implied_vol import IVStatus, atm_implied_vol, options_implied_vol
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.options.models import Side
from travas.options.probability import prob_between
from travas.options.simulation import business_days_until
from travas.options.valuation import zero_crossings
from travas.settings import EarlyExerciseSettings, PricingSettings

TOL = 1e-9


class ProtectedKind(StrEnum):
    COLLAR = "collar"
    COLLAR_FLY = "collar_borboleta"

    @property
    def label(self) -> str:
        return KIND_LABELS[self]


KIND_LABELS = {
    ProtectedKind.COLLAR: "Collar (ativo + put − call)",
    ProtectedKind.COLLAR_FLY: "Collar + borboleta (ativo + put − 2 calls + call)",
}

RANKING_COMPONENTS: dict[str, tuple[str, bool, str]] = {
    "floor": ("floor_pct_cdi", True, "retorno mínimo no vencimento (piso) ÷ CDI do período"),
    "unchanged": ("unchanged_pct_cdi", True, "retorno com o ativo parado ÷ CDI do período"),
    "max": ("max_pct_cdi", True, "retorno máximo ÷ CDI do período"),
    "prob_cdi": ("prob_beat_cdi", True, "probabilidade de superar o CDI no vencimento"),
    "liquidity": ("liquidity_score", True, "liquidez da pior perna"),
    "execution_cost": ("execution_cost_pct_profit", False, "(natural − mid) ÷ lucro máximo"),
}

DISMANTLE_NOTE = (
    "Estrutura com várias pernas: desmonte todas as pontas juntas antes do vencimento, quando o "
    "ativo estiver na região desejada, em vez de deixar exercer (exercício gera custos e "
    "liquidação física do ativo)."
)
CALLS_COVER_NOTE = (
    "Uma call vendida é coberta pelas ações; na borboleta, a segunda é coberta pela call "
    "comprada de strike maior. Exercício antecipado de calls americanas vendidas desmonta a "
    "proteção: acompanhe o valor extrínseco e as datas de proventos."
)
DIVIDEND_NOTE = (
    "Proventos do ativo durante a operação ajustam os strikes das opções na B3 e entram como "
    "receita das ações; o cálculo não os inclui (confira o calendário de proventos)."
)


@dataclass(frozen=True, slots=True)
class Piece:
    """Uma posição por ação da estrutura: `kind` = stock | call | put; `qty` com sinal."""

    kind: str
    qty: float
    strike: float | None = None


def collar_pieces(put_k: float, call_k: float) -> tuple[Piece, ...]:
    return (Piece("stock", 1), Piece("put", 1, put_k), Piece("call", -1, call_k))


def collar_fly_pieces(put_k: float, short_k: float, long_k: float) -> tuple[Piece, ...]:
    return (
        Piece("stock", 1),
        Piece("put", 1, put_k),
        Piece("call", -2, short_k),
        Piece("call", 1, long_k),
    )


def value_at_expiry(pieces: Sequence[Piece], spot) -> np.ndarray:
    """Valor da posição (por ação) no vencimento para cada preço do ativo."""
    s = np.asarray(spot, dtype=np.float64)
    value = np.zeros_like(s)
    for p in pieces:
        if p.kind == "stock":
            value = value + p.qty * s
        elif p.kind == "call":
            value = value + p.qty * np.maximum(s - p.strike, 0.0)
        else:
            value = value + p.qty * np.maximum(p.strike - s, 0.0)
    return value


def value_before_expiry(
    pieces: Sequence[Piece], spot, t: float, rate: float, sigmas: Sequence[float | None]
) -> np.ndarray:
    """Valor teórico (Black-Scholes europeu, σ por opção) por ação, com prazo `t` em anos."""
    s = np.asarray(spot, dtype=np.float64)
    value = np.zeros_like(s)
    options = [p for p in pieces if p.kind != "stock"]
    if len(sigmas) != len(options):
        raise ValueError("um σ por opção")
    for p in pieces:
        if p.kind == "stock":
            value = value + p.qty * s
    for p, sigma in zip(options, sigmas, strict=True):
        premium = pricing.price(
            s, p.strike, t, rate, np.nan if sigma is None else sigma, p.kind == "call"
        )
        value = value + p.qty * premium
    return value


@dataclass(frozen=True)
class Profile:
    floor: float  # menor valor no vencimento (por ação)
    cap: float  # maior valor no vencimento
    cap_at: float  # preço do ativo onde o máximo ocorre (o menor deles)
    low_tail: float  # valor com o ativo abaixo de todos os strikes
    high_tail: float  # valor com o ativo acima de todos os strikes


def expiry_profile(pieces: Sequence[Piece]) -> Profile:
    """Piso e teto exatos pelos pontos de quebra. Erro se a estrutura não for limitada."""
    strikes = sorted({p.strike for p in pieces if p.strike is not None})
    if not strikes:
        raise ValueError("estrutura sem opções")
    slope_low = sum(p.qty for p in pieces if p.kind == "stock") - sum(
        p.qty for p in pieces if p.kind == "put"
    )
    slope_high = sum(p.qty for p in pieces if p.kind in ("stock", "call"))
    if abs(slope_low) > TOL:
        raise ValueError("estrutura sem piso: o valor muda com o ativo abaixo do menor strike")
    if abs(slope_high) > TOL:
        raise ValueError("estrutura sem teto finito ou com perda ilimitada na alta")
    xs = np.array(strikes)
    ys = value_at_expiry(pieces, xs)
    i_max = int(np.argmax(ys))
    return Profile(
        floor=float(ys.min()),
        cap=float(ys[i_max]),
        cap_at=float(xs[i_max]),
        low_tail=float(ys[0]),
        high_tail=float(ys[-1]),
    )


def intervals_at_or_above(pieces: Sequence[Piece], level: float) -> list[tuple[float, float]]:
    """Intervalos de preço do ativo (0 a ∞) onde o valor no vencimento ≥ `level` (exato)."""
    strikes = sorted({p.strike for p in pieces if p.strike is not None})
    xs = [0.0, *strikes, strikes[-1] * 2 + 1]  # cauda superior é plana (perfil limitado)
    ys = value_at_expiry(pieces, xs) - level
    out: list[tuple[float, float]] = []
    start = 0.0 if ys[0] >= -TOL else None
    for i in range(len(xs) - 1):
        a, b = ys[i], ys[i + 1]
        if (a >= -TOL) != (b >= -TOL):
            x = xs[i] + (xs[i + 1] - xs[i]) * (-a) / (b - a)
            if start is None:
                start = x
            else:
                out.append((start, x))
                start = None
    if start is not None:
        out.append((start, math.inf))
    return out


def prob_value_at_least(
    pieces: Sequence[Piece], level: float, spot: float, t: float, rate: float, sigma: float
) -> float:
    """P(valor no vencimento ≥ level), lognormal com drift = juros (neutro ao risco)."""
    return sum(
        prob_between(spot, lo, hi, t, rate, sigma)
        for lo, hi in intervals_at_or_above(pieces, level)
    )


def cdi_period(rate_annual: float, business_days: int) -> float:
    """CDI composto no período: (1 + taxa)^(du/252) − 1."""
    return (1 + rate_annual) ** (business_days / pricing.BUSINESS_DAYS_PER_YEAR) - 1


def annualized(ret: float, business_days: int) -> float | None:
    if business_days <= 0 or ret <= -1:
        return None
    return (1 + ret) ** (pricing.BUSINESS_DAYS_PER_YEAR / business_days) - 1


@dataclass(frozen=True)
class StockQuote:
    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    price: float | None
    quote_time: str | None
    source: str


@dataclass(frozen=True)
class ProtectedParams:
    quantity: int  # ações (opções por perna = quantity × proporção ÷ contract_size)
    rate_annual: float
    liquidity: LiquidityRules
    weights: dict[str, float]
    pricing: PricingSettings
    early_exercise: EarlyExerciseSettings
    kinds: tuple[ProtectedKind, ...] = (ProtectedKind.COLLAR, ProtectedKind.COLLAR_FLY)
    dte_min: int = 5
    dte_max: int = 90
    put_min_pct_spot: float = 0.85
    put_max_pct_spot: float = 1.10
    call_max_pct_spot: float = 1.25
    max_wing_pct_spot: float = 0.08
    min_floor_return: float = 0.0  # piso ≥ custo × (1 + isto); 0 = "risco zero"
    costs_brl: float = 0.0  # custos estimados da operação inteira (R$)
    european_short: bool = False
    include_illiquid: bool = False
    illiquid_score_cap: float = 40.0
    limit_aggressiveness: float = 0.25
    max_results: int = 200
    max_candidates: int = 4000  # avaliação completa só das melhores (pelo piso) acima disso


@dataclass
class ProtectedChain:
    chain: pd.DataFrame
    atm: pd.DataFrame
    spot: float
    stock: StockQuote
    stock_entry: float | None  # compra do ativo: ask (ou último preço, sinalizado)
    stock_mid: float | None
    stock_flags: list[str]
    today: dt.date
    rate: float  # contínua
    params: ProtectedParams
    calendar: B3Calendar
    discarded: dict[str, int] = field(default_factory=dict)

    def atm_iv(self, expiration: dt.date) -> float | None:
        row = self.atm[self.atm["expiration_date"] == expiration]
        return float(row["atm_iv"].iloc[0]) if len(row) else None


def stock_prices(stock: StockQuote) -> tuple[float | None, float | None, list[str]]:
    """(entrada, mid, avisos). Compra do ativo no ask; sem book, último preço sinalizado."""
    flags: list[str] = []
    mid = (
        (stock.bid + stock.ask) / 2
        if stock.bid is not None and stock.ask is not None and stock.ask >= stock.bid
        else None
    )
    if stock.ask is not None:
        entry = stock.ask
    else:
        entry = stock.price
        flags.append("ativo sem book: compra calculada pelo último preço (indicativo)")
    if mid is None:
        mid = stock.price
    if stock.source != "mt5":
        flags.append("cotação do ativo fora do pregão (último pregão)")
    return entry, mid, flags


def prepare(
    chain: pd.DataFrame,
    stock: StockQuote,
    spot: float,
    today: dt.date,
    calendar: B3Calendar,
    params: ProtectedParams,
) -> ProtectedChain:
    frame = chain.copy()
    frame = frame.join(evaluate_liquidity(frame, params.liquidity))
    frame = frame.join(options_implied_vol(frame, params.rate_annual, params.pricing))
    atm = atm_implied_vol(frame, params.pricing)
    atm_by_exp = dict(zip(atm["expiration_date"], atm["atm_iv"], strict=True))
    own = frame["iv"].where(frame["iv_status"] == IVStatus.OK.value)
    fallback = frame["expiration_date"].map(atm_by_exp)
    frame["sigma"] = own.fillna(fallback)
    frame["sigma_source"] = np.where(
        own.notna(), "IV da série", np.where(fallback.notna(), "IV ATM", "indisponível")
    )
    entry, mid, flags = stock_prices(stock)
    return ProtectedChain(
        chain=frame,
        atm=atm,
        spot=spot,
        stock=stock,
        stock_entry=entry,
        stock_mid=mid,
        stock_flags=flags,
        today=today,
        rate=float(pricing.continuous_rate(params.rate_annual)),
        params=params,
        calendar=calendar,
    )


def _count(d: dict[str, int], reason: str, n: int = 1) -> None:
    if n:
        d[reason] = d.get(reason, 0) + n


def _usable(frame: pd.DataFrame, price_col: str, prep: ProtectedChain, reason: str) -> pd.DataFrame:
    """Séries com preço para o lado da perna e (salvo pedido) aprovadas em liquidez."""
    ok = frame[price_col].notna()
    _count(prep.discarded, reason, int((~ok).sum()))
    frame = frame[ok]
    if not prep.params.include_illiquid:
        liquid = frame["liquidity_ok"].astype(bool)
        _count(prep.discarded, "série com liquidez/cotação reprovada", int((~liquid).sum()))
        frame = frame[liquid]
    return frame


def candidates(prep: ProtectedChain) -> list[tuple[ProtectedKind, tuple[pd.Series, ...]]]:
    """Combinações (put, calls) por vencimento com piso ≥ custo natural × (1 + piso mínimo).

    Pré-filtro vetorizado; a avaliação completa fica em `evaluate`.
    """
    p = prep.params
    spot = prep.spot
    if prep.stock_entry is None:
        return []
    frame = prep.chain[prep.chain["dte_business_days"].between(max(p.dte_min, 1), p.dte_max)]
    found: list[tuple[float, ProtectedKind, tuple[pd.Series, ...]]] = []
    need = 1 + p.min_floor_return
    for _, group in frame.groupby("expiration_date", sort=True):
        puts = group[
            (group["option_type"] == "put")
            & group["strike"].between(spot * p.put_min_pct_spot, spot * p.put_max_pct_spot)
        ]
        calls = group[
            (group["option_type"] == "call") & (group["strike"] <= spot * p.call_max_pct_spot)
        ]
        puts = _usable(puts, "ask", prep, "put sem oferta de venda (ask)")
        shorts = _usable(calls, "bid", prep, "call sem oferta de compra (bid)")
        if p.european_short:
            eur = shorts["exercise_style"] == "european"
            _count(prep.discarded, "call vendida americana (filtro de estilo)", int((~eur).sum()))
            shorts = shorts[eur]
        longs = _usable(calls, "ask", prep, "call sem oferta de venda (ask)")
        if puts.empty or shorts.empty:
            continue
        pk = puts["strike"].to_numpy()
        pa = puts["ask"].to_numpy()
        sk = shorts["strike"].to_numpy()
        sb = shorts["bid"].to_numpy()
        units = p.quantity
        if ProtectedKind.COLLAR in p.kinds:
            cost = prep.stock_entry + pa[:, None] - sb[None, :]
            floor = np.broadcast_to(pk[:, None], cost.shape)
            ok = (sk[None, :] > pk[:, None]) & (cost > 0)
            ok &= floor * units - p.costs_brl >= cost * units * need - TOL
            for i, j in zip(*np.nonzero(ok), strict=True):
                ratio = (floor[i, j] * units - p.costs_brl) / (cost[i, j] * units)
                found.append((ratio, ProtectedKind.COLLAR, (puts.iloc[i], shorts.iloc[j])))
        if ProtectedKind.COLLAR_FLY in p.kinds and not longs.empty:
            lk = longs["strike"].to_numpy()
            la = longs["ask"].to_numpy()
            max_wing = spot * p.max_wing_pct_spot
            wing_ok = (lk[None, :] > sk[:, None]) & (lk[None, :] - sk[:, None] <= max_wing + TOL)
            for j, m in zip(*np.nonzero(wing_ok), strict=True):
                k1, k2 = sk[j], lk[m]
                cost = prep.stock_entry + pa - 2 * sb[j] + la[m]
                floor = np.minimum(pk, 2 * k1 - k2)
                ok = (pk < k1) & (cost > 0)
                ok &= floor * units - p.costs_brl >= cost * units * need - TOL
                for i in np.nonzero(ok)[0]:
                    ratio = (floor[i] * units - p.costs_brl) / (cost[i] * units)
                    found.append(
                        (
                            ratio,
                            ProtectedKind.COLLAR_FLY,
                            (puts.iloc[i], shorts.iloc[j], longs.iloc[m]),
                        )
                    )
    found.sort(key=lambda x: -x[0])
    if len(found) > p.max_candidates:
        _count(
            prep.discarded,
            "fora das melhores pelo piso (limite de avaliação)",
            len(found) - p.max_candidates,
        )
        found = found[: p.max_candidates]
    return [(kind, rows) for _, kind, rows in found]


def pieces_for(kind: ProtectedKind, rows: Sequence[pd.Series]) -> tuple[Piece, ...]:
    strikes = [float(r["strike"]) for r in rows]
    if kind is ProtectedKind.COLLAR:
        return collar_pieces(*strikes)
    return collar_fly_pieces(*strikes)


def leg_sides(kind: ProtectedKind) -> list[tuple[Side, int]]:
    """(lado, proporção por ação) de cada opção, na ordem das linhas."""
    if kind is ProtectedKind.COLLAR:
        return [(Side.LONG, 1), (Side.SHORT, 1)]
    return [(Side.LONG, 1), (Side.SHORT, 2), (Side.LONG, 1)]


def net_cost(
    kind: ProtectedKind, rows: Sequence[pd.Series], stock_price: float | None, basis: str
) -> float | None:
    """Custo por ação: ativo + Σ (compra +, venda −) × proporção × prêmio.

    `basis` = natural (compra no ask, venda no bid) ou mid.
    """
    if stock_price is None:
        return None
    total = stock_price
    for row, (side, ratio) in zip(rows, leg_sides(kind), strict=True):
        col = "mid" if basis == "mid" else ("ask" if side is Side.LONG else "bid")
        price = _f(row[col])
        if price is None:
            return None
        total += side.sign * ratio * price
    return round(total, 6)


FLOW_TOLERANCE = 0.005  # meio centavo: abaixo disso o pacote de opções sai "a zero"


def _flow(net: float | None) -> str | None:
    if net is None:
        return None
    if net > FLOW_TOLERANCE:
        return "debito"
    if net < -FLOW_TOLERANCE:
        return "credito"
    return "zero"


def options_flow(kind: ProtectedKind, rows: Sequence[pd.Series]) -> dict:
    """Só o pacote de opções (sem o ativo), por ação: + = débito pago, − = crédito recebido.

    A estrutura inteira é sempre débito (compra do ativo); isto mostra se as opções, sozinhas,
    custam (put mais cara que as calls vendidas) ou geram caixa (calls vendidas pagam a put).
    O sentido pelo natural (ask/bid) pode diferir do sentido pelo mid: os dois são devolvidos.
    """
    natural = net_cost(kind, rows, 0.0, "natural")
    mid = net_cost(kind, rows, 0.0, "mid")
    flow_natural, flow_mid = _flow(natural), _flow(mid)
    return {
        "net_natural": natural,
        "net_mid": mid,
        "flow_natural": flow_natural,
        "flow_mid": flow_mid,
        "flow_differs": flow_natural is not None
        and flow_mid is not None
        and flow_natural != flow_mid,
    }


def structure_id(kind: ProtectedKind, rows: Sequence[pd.Series]) -> str:
    return f"{kind.value}:" + "|".join(str(r["symbol"]) for r in rows)


def _returns(value: float, cost: float, units: int, costs: float) -> float:
    return (value * units - costs) / (cost * units) - 1


def evaluate(prep: ProtectedChain, kind: ProtectedKind, rows: Sequence[pd.Series]) -> dict:
    p = prep.params
    units = p.quantity
    first = rows[0]
    expiration = first["expiration_date"]
    dte = int(first["dte_business_days"])
    t = dte / pricing.BUSINESS_DAYS_PER_YEAR
    pieces = pieces_for(kind, rows)
    natural = net_cost(kind, rows, prep.stock_entry, "natural")
    mid = net_cost(kind, rows, prep.stock_mid, "mid")
    result: dict = {
        "id": structure_id(kind, rows),
        "kind": kind.value,
        "kind_label": kind.label,
        "expiration": expiration.isoformat(),
        "dte_business_days": dte,
        "dte_calendar_days": int(first["dte_calendar_days"]),
        "quantity": units,
        "strikes": {
            "put": float(rows[0]["strike"]),
            "short_call": float(rows[1]["strike"]),
            "long_call": float(rows[2]["strike"]) if len(rows) > 2 else None,
        },
        "stock_leg": {
            "symbol": prep.stock.symbol,
            "side": Side.LONG.value,
            "bid": prep.stock.bid,
            "ask": prep.stock.ask,
            "last": prep.stock.last,
            "entry": prep.stock_entry,
            "mid": prep.stock_mid,
            "quote_time": prep.stock.quote_time,
            "source": prep.stock.source,
            "flags": list(prep.stock_flags),
            "shares": units,
        },
        "legs": [
            {
                **_leg_info(row, side),
                "ratio": ratio,
                "contracts": units * ratio / float(row["contract_size"] or 1),
            }
            for row, (side, ratio) in zip(rows, leg_sides(kind), strict=True)
        ],
        "cost_natural": natural,
        "cost_mid": mid,
        "options": options_flow(kind, rows),
        "invalid": [],
        "warnings": [],
    }
    if natural is None or natural <= 0:
        result["invalid"].append("sem preço natural para todas as pernas (não estimável)")
        return result
    try:
        prof = expiry_profile(pieces)
    except ValueError as exc:
        result["invalid"].append(str(exc))
        return result

    cdi = cdi_period(p.rate_annual, dte)
    costs = p.costs_brl
    floor_ret = _returns(prof.floor, natural, units, costs)
    max_ret = _returns(prof.cap, natural, units, costs)
    unchanged_value = float(value_at_expiry(pieces, [prep.spot])[0])
    unchanged_ret = _returns(unchanged_value, natural, units, costs)
    pct = (lambda r: r / cdi) if cdi > 0 else (lambda r: None)
    result.update(
        {
            "cost_total": natural * units + costs,
            "costs_brl": costs,
            "floor_value": prof.floor,
            "cap_value": prof.cap,
            "cap_at": prof.cap_at,
            "low_tail_value": prof.low_tail,
            "high_tail_value": prof.high_tail,
            "floor_return": floor_ret,
            "max_return": max_ret,
            "unchanged_value": unchanged_value,
            "unchanged_return": unchanged_ret,
            "down_return": _returns(prof.low_tail, natural, units, costs),
            "up_return": _returns(prof.high_tail, natural, units, costs),
            "cdi_period": cdi,
            "floor_pct_cdi": pct(floor_ret),
            "max_pct_cdi": pct(max_ret),
            "unchanged_pct_cdi": pct(unchanged_ret),
            "floor_annualized": annualized(floor_ret, dte),
            "max_annualized": annualized(max_ret, dte),
            "min_profit": prof.floor * units - natural * units - costs,
            "max_profit": prof.cap * units - natural * units - costs,
            "risk_zero": prof.floor * units - costs >= natural * units - TOL,
            "execution_cost_pct_profit": (
                (natural - mid) / (prof.cap - natural)
                if mid is not None and prof.cap - natural > TOL
                else None
            ),
            "max_cost_for_floor": (prof.floor * units - costs) / (units * (1 + p.min_floor_return)),
        }
    )
    if not result["risk_zero"]:
        result["invalid"].append("piso abaixo do custo (há risco de perda no vencimento)")
    elif floor_ret < p.min_floor_return - TOL:
        result["invalid"].append("piso abaixo do retorno mínimo pedido")

    sigma = prep.atm_iv(expiration)
    if sigma is not None and t > 0:
        level = (natural * units * (1 + cdi) + costs) / units
        result["prob_beat_cdi"] = prob_value_at_least(pieces, level, prep.spot, t, prep.rate, sigma)
        result["prob_method"] = (
            f"lognormal neutra ao risco (drift = juros {p.rate_annual:.2%} a.a.), σ = IV ATM do "
            f"vencimento ({sigma:.1%}), T = {dte} du/252; probabilidade de o valor da estrutura no "
            "vencimento superar o custo corrigido pelo CDI do período"
        )
        result["prob_unavailable_reason"] = None
    else:
        result["prob_beat_cdi"] = None
        result["prob_method"] = None
        result["prob_unavailable_reason"] = "sem IV ATM confiável no vencimento"
    result["sigma_atm"] = sigma

    legs_ok = all(bool(r["liquidity_ok"]) for r in rows)
    result["liquidity_ok"] = legs_ok
    result["liquidity_score"] = float(min(r["liquidity_score"] for r in rows))
    flags = set().union(*(set(r["quote_flags"]) for r in rows))
    result["data_flags"] = sorted(flags | set(prep.stock_flags))

    short_row = rows[1]
    if p.european_short and short_row["exercise_style"] != "european":
        result["invalid"].append("filtro de estilo: call vendida americana")
    result["early_exercise"] = early_exercise_alert(prep, short_row)
    for row in rows:
        note = row.get("ref_note")
        if isinstance(note, str) and note:
            result["warnings"].append(f"{row['symbol']}: {note}")
    result["limit"] = suggest_limit(prep, natural, mid, prof, units)
    return result


def suggest_limit(
    prep: ProtectedChain, natural: float, mid: float | None, prof: Profile, units: int
) -> dict:
    """Custo líquido por ação sugerido (débito) e impacto nos retornos. Indicativo."""
    p = prep.params
    max_cost = (prof.floor * units - p.costs_brl) / (units * (1 + p.min_floor_return))
    notes = ["compra do ativo e da put/call no ask, venda das calls no bid (natural)"]
    if mid is None:
        suggested = natural
        notes.append("sem mid em alguma perna: sugerido = natural")
    else:
        suggested = mid + p.limit_aggressiveness * (natural - mid)
        notes.append(
            f"sugerido = mid + {p.limit_aggressiveness:.0%} do caminho até o natural; "
            "execução não garantida"
        )
    if suggested > max_cost + TOL:
        suggested = max_cost
        notes.append("limitado ao custo máximo que mantém o piso acima do custo")
    suggested = math.floor(suggested * 100 + 1e-9) / 100  # débito: arredonda a favor (para baixo)

    def impact(price: float | None) -> dict | None:
        if price is None:
            return None
        return {
            "price": price,
            "floor_return": _returns(prof.floor, price, units, p.costs_brl),
            "max_return": _returns(prof.cap, price, units, p.costs_brl),
            "min_profit": (prof.floor - price) * units - p.costs_brl,
            "max_profit": (prof.cap - price) * units - p.costs_brl,
        }

    return {
        "natural": natural,
        "mid": mid,
        "suggested": suggested,
        "max_cost": max_cost,
        "range_low": mid if mid is not None else natural,
        "range_high": natural,
        "notes": notes,
        "impacts": {
            "sugerido": impact(suggested),
            "mid": impact(mid),
            "natural": impact(natural),
            "custo_max": impact(max_cost),
        },
    }


def scan_prepared(prep: ProtectedChain) -> dict:
    p = prep.params
    ranked: list[dict] = []
    for kind, rows in candidates(prep):
        row = evaluate(prep, kind, rows)
        if row["invalid"]:
            for reason in row["invalid"]:
                _count(prep.discarded, reason)
            continue
        ranked.append(row)
    score_candidates(ranked, p.weights, p.illiquid_score_cap, RANKING_COMPONENTS)
    ranked.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    for position, row in enumerate(ranked, start=1):
        row["rank"] = position
    # As melhores no geral + as melhores com call vendida europeia: a interface filtra por estilo
    # sem novo scan e ainda mostra até `max_results` europeias.
    european = [r for r in ranked if is_european_short(r)]
    keep = {r["id"] for r in ranked[: p.max_results]} | {r["id"] for r in european[: p.max_results]}
    return {
        "spot": prep.spot,
        "stock": result_stock(prep),
        "total_ranked": len(ranked),
        "total_european_short": len(european),
        "discarded": dict(prep.discarded),
        "results": [r for r in ranked if r["id"] in keep],
        "max_results": p.max_results,
        "atm_iv": [
            {"expiration": r.expiration_date.isoformat(), "atm_iv": float(r.atm_iv)}
            for r in prep.atm.itertuples()
        ],
        "expirations": sorted({d.isoformat() for d in prep.chain["expiration_date"].unique()}),
        "assumptions": assumptions(prep),
    }


def is_european_short(row: dict) -> bool:
    """Call vendida (2ª perna) europeia: sem risco de exercício antecipado."""
    return row["legs"][1]["exercise_style"] == "european"


def result_stock(prep: ProtectedChain) -> dict:
    s = prep.stock
    return {
        "symbol": s.symbol,
        "bid": s.bid,
        "ask": s.ask,
        "last": s.last,
        "price": s.price,
        "entry": prep.stock_entry,
        "mid": prep.stock_mid,
        "quote_time": s.quote_time,
        "source": s.source,
        "flags": prep.stock_flags,
    }


def assumptions(prep: ProtectedChain) -> dict:
    p = prep.params
    return {
        "rate_annual": p.rate_annual,
        "costs_brl": p.costs_brl,
        "quantity": p.quantity,
        "min_floor_return": p.min_floor_return,
        "entry_basis": "custo natural: ativo e opções compradas no ask, calls vendidas no bid",
        "risk_zero_definition": (
            "piso no vencimento (menor valor da estrutura) ≥ custo de montagem + custos "
            "informados; não considera exercício antecipado, proventos nem custos não informados"
        ),
        "cdi_note": (
            "CDI do período = (1 + taxa)^(du/252) − 1. Pela paridade put-call, com preços justos "
            "o piso rende no máximo cerca do CDI: o ganho acima dele depende do ativo terminar "
            "entre os strikes"
        ),
        "ranking_note": (
            "Percentis relativos às estruturas desta varredura; componentes indisponíveis têm o "
            "peso redistribuído. Pernas reprovadas em liquidez limitam o score a "
            f"{p.illiquid_score_cap:.0f}."
        ),
        "weights": p.weights,
        "components": {k: v[2] for k, v in RANKING_COMPONENTS.items()},
        "notes": [DISMANTLE_NOTE, CALLS_COVER_NOTE, DIVIDEND_NOTE],
        "exercise_style_filter": ["call vendida europeia"] if p.european_short else [],
    }


def find_rows(prep: ProtectedChain, structure: str) -> tuple[ProtectedKind, list[pd.Series]]:
    kind_text, _, symbols = structure.partition(":")
    try:
        kind = ProtectedKind(kind_text)
    except ValueError as exc:
        raise KeyError("estrutura desconhecida") from exc
    by_symbol = prep.chain.set_index("symbol", drop=False)
    names = symbols.split("|")
    expected = 2 if kind is ProtectedKind.COLLAR else 3
    if len(names) != expected or any(n not in by_symbol.index for n in names):
        raise KeyError("série não encontrada na cadeia coletada")
    return kind, [by_symbol.loc[n] for n in names]


def simulation(
    prep: ProtectedChain, kind: ProtectedKind, rows: Sequence[pd.Series], points: int = 161
) -> dict:
    """P&L total no vencimento (exato) e valor teórico em cada pregão até lá."""
    p = prep.params
    units = p.quantity
    natural = net_cost(kind, rows, prep.stock_entry, "natural")
    if natural is None:
        return {"available": False, "reason": "sem preço natural"}
    pieces = pieces_for(kind, rows)
    strikes = [float(r["strike"]) for r in rows]
    lo = min(*strikes, prep.spot) * 0.85
    hi = max(*strikes, prep.spot) * 1.15
    xs = np.linspace(lo, hi, points)
    expiry = (value_at_expiry(pieces, xs) - natural) * units - p.costs_brl
    sigmas = [_f(r["sigma"]) for r in rows]
    sigmas_ok = all(s is not None and s > 0 for s in sigmas)
    expiration = rows[0]["expiration_date"]
    dates = []
    if sigmas_ok:
        for day in prep.calendar.sessions_between(prep.today, expiration):
            left = business_days_until(prep.calendar, day, expiration)
            t = left / pricing.BUSINESS_DAYS_PER_YEAR
            ys = (value_before_expiry(pieces, xs, t, prep.rate, sigmas) - natural) * units
            ys = ys - p.costs_brl
            dates.append(
                {
                    "date": day.isoformat(),
                    "business_days_left": left,
                    "pnl": [round(float(y), 2) for y in ys],
                    "breakevens": zero_crossings(xs, ys),
                }
            )
    vols = ", ".join(f"{s:.1%}" for s in sigmas if s is not None) or "indisponível"
    return {
        "available": True,
        "spots": [round(float(x), 4) for x in xs],
        "expiry_pnl": [round(float(y), 2) for y in expiry],
        "expiry_label": "Payoff no vencimento (exato)",
        "expiry_breakevens": zero_crossings(xs, expiry),
        "dates": dates,
        "model_available": bool(dates),
        "model_reason": None if dates else "sem volatilidade confiável em todas as opções",
        "sigmas": sigmas,
        "assumptions": (
            f"Valor teórico antes do vencimento: ativo a mercado + Black-Scholes europeu por "
            f"opção, σ constante ({vols}), juros {p.rate_annual:.2%} a.a., sem proventos, "
            "T = dias úteis/252. É estimativa para desmontar antes do vencimento (não inclui o "
            "spread de saída); no vencimento o valor é o payoff exato."
        ),
    }
