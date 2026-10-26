"""Plano de saída de uma trava de duas pernas para o robô de estratégia do ProfitChart com
"corrigir encilhamento a mercado": uma perna fica a limite e, quando ela executa, a outra é
enviada a mercado.

- Perna a mercado: a de menor custo para cruzar o book em R$ (unidades × meio spread), porque
  é ela que paga o spread inteiro; empate → a de mais negócios no dia (book mais provável de
  ter profundidade). A outra fica a limite no mid, arredondado ao tick no sentido favorável
  (venda para cima, compra para baixo).
- Preço da trava = valor líquido por unidade com a perna limite no mid e a perna a mercado no
  bid/ask atual. Sinal: > 0 = crédito recebido ao zerar; < 0 = débito pago.
- O MT5 não informa a profundidade do book: a ordem a mercado pode executar pior que o melhor
  bid/ask exibido, e ela só sai depois da perna limite, com o book que houver então.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from travas.options.models import Side

TICK = 0.01


@dataclass(frozen=True, slots=True)
class ExitLeg:
    symbol: str
    side: Side  # lado da posição aberta (comprada → vende para zerar)
    units: float
    bid: float | None
    ask: float | None
    deals: int | None = None
    flags: tuple[str, ...] = ()


def _valid(x: float | None) -> bool:
    return x is not None and math.isfinite(x) and x > 0


def _br(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _round_favorable(price: float, selling: bool) -> float:
    steps = price / TICK
    rounded = math.ceil(steps - 1e-9) if selling else math.floor(steps + 1e-9)
    return round(rounded * TICK, 2)


def exit_plan(legs: list[ExitLeg]) -> dict:
    if len(legs) != 2:
        return {"available": False, "reason": "plano de saída só para travas de duas pernas"}
    if abs(legs[0].units - legs[1].units) > 1e-9:
        return {"available": False, "reason": "pernas com quantidades diferentes"}
    missing = [lg.symbol for lg in legs if not (_valid(lg.bid) and _valid(lg.ask))]
    if missing:
        return {
            "available": False,
            "reason": f"sem bid/ask válido em {', '.join(missing)} (não estimável)",
        }

    units = legs[0].units
    rows = []
    for lg in legs:
        selling = lg.side is Side.LONG
        spread = lg.ask - lg.bid
        mid = (lg.bid + lg.ask) / 2
        rows.append(
            {
                "symbol": lg.symbol,
                "action": "vender" if selling else "comprar",
                "sign": 1 if selling else -1,  # + recebe ao zerar
                "selling": selling,
                "bid": lg.bid,
                "ask": lg.ask,
                "mid": mid,
                "spread": spread,
                "market_price": lg.bid if selling else lg.ask,
                "limit_price": _round_favorable(mid, selling),
                "cross_cost_brl": units * spread / 2,
                "deals": lg.deals,
                "flags": list(lg.flags),
            }
        )
    market_i = min(
        range(2), key=lambda i: (round(rows[i]["cross_cost_brl"], 6), -(rows[i]["deals"] or 0))
    )
    limit_i = 1 - market_i
    market, limit = rows[market_i], rows[limit_i]

    def net(price_m: float, price_l: float) -> float:
        return round(market["sign"] * price_m + limit["sign"] * price_l, 6)

    plan_net = net(market["market_price"], limit["limit_price"])
    natural_net = net(market["market_price"], limit["market_price"])
    mid_net = net(market["mid"], limit["mid"])

    notes = [
        f"{market['symbol']} a mercado: spread {_br(market['spread'])} contra "
        f"{_br(limit['spread'])} de {limit['symbol']}, custo de cruzar "
        f"R$ {_br(market['cross_cost_brl'])} contra R$ {_br(limit['cross_cost_brl'])}"
    ]
    if math.isclose(market["cross_cost_brl"], limit["cross_cost_brl"], abs_tol=1e-6):
        notes[0] = (
            f"spreads iguais ({_br(market['spread'])}): {market['symbol']} a mercado por ter "
            "mais negócios no dia"
        )
    warnings = [
        "o MT5 não mostra a profundidade do book: a ordem a mercado pode sair pior que "
        "o bid/ask exibido, e só é enviada depois que a perna limite executar"
    ]
    if market["flags"]:
        warnings.insert(
            0,
            f"perna a mercado com problema de cotação/liquidez ({', '.join(market['flags'])}): "
            "risco de execução bem pior",
        )
    if not market["deals"]:
        warnings.insert(0, f"{market['symbol']} sem negócios no dia: evite enviá-la a mercado")

    for row in rows:
        row.pop("sign")
        row.pop("selling")
    return {
        "available": True,
        "market_leg": market_i,
        "limit_leg": limit_i,
        "legs": rows,
        "plan_net": plan_net,
        "plan_flow": "credito" if plan_net > 0 else "debito",
        "natural_net": natural_net,
        "mid_net": mid_net,
        "cost_vs_mid_brl": (mid_net - plan_net) * units,
        "saving_vs_natural_brl": (plan_net - natural_net) * units,
        "notes": notes,
        "warnings": warnings,
    }
