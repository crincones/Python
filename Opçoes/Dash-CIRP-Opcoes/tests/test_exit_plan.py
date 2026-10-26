from __future__ import annotations

import pytest

from travas.options.exit_plan import ExitLeg, exit_plan
from travas.options.models import Side

# Trava de alta com crédito (puts) aberta: comprada no 19,47, vendida no 20,22; 1.000 unidades.
LONG = ExitLeg("PUT1947", Side.LONG, 1000, bid=0.20, ask=0.22, deals=40)
SHORT = ExitLeg("PUT2022", Side.SHORT, 1000, bid=0.50, ask=0.60, deals=40)


def test_tight_spread_leg_goes_to_market_and_wide_leg_rests_at_mid():
    p = exit_plan([LONG, SHORT])
    assert p["available"]
    assert p["market_leg"] == 0 and p["limit_leg"] == 1
    market, limit = p["legs"]
    assert market["action"] == "vender" and market["market_price"] == pytest.approx(0.20)
    assert limit["action"] == "comprar" and limit["limit_price"] == pytest.approx(0.55)
    # Zerar a trava de crédito custa débito: vende 0,20, recompra 0,55 → −0,35 por unidade.
    assert p["plan_net"] == pytest.approx(-0.35) and p["plan_flow"] == "debito"
    assert p["natural_net"] == pytest.approx(-0.40)
    assert p["mid_net"] == pytest.approx(-0.34)
    assert p["cost_vs_mid_brl"] == pytest.approx(10.0)  # meio spread da perna a mercado
    assert p["saving_vs_natural_brl"] == pytest.approx(50.0)


def test_choice_follows_the_spread_not_the_leg_order_or_side():
    wide_long = ExitLeg("A", Side.LONG, 100, bid=1.00, ask=1.20, deals=5)
    tight_short = ExitLeg("B", Side.SHORT, 100, bid=0.40, ask=0.41, deals=5)
    p = exit_plan([wide_long, tight_short])
    assert p["market_leg"] == 1
    assert p["legs"][0]["limit_price"] == pytest.approx(1.10)
    assert p["plan_net"] == pytest.approx(1.10 - 0.41)  # crédito ao zerar a trava de débito
    assert p["plan_flow"] == "credito"


def test_limit_price_rounds_to_tick_in_favor_of_the_user():
    sell = ExitLeg("A", Side.LONG, 100, bid=1.00, ask=1.11, deals=5)  # mid 1,055 → vende 1,06
    buy = ExitLeg("B", Side.SHORT, 100, bid=0.30, ask=0.31, deals=5)
    assert exit_plan([sell, buy])["legs"][0]["limit_price"] == pytest.approx(1.06)
    sell2 = ExitLeg("A", Side.LONG, 100, bid=0.30, ask=0.31, deals=5)
    buy2 = ExitLeg("B", Side.SHORT, 100, bid=1.00, ask=1.11, deals=5)  # compra 1,05
    assert exit_plan([sell2, buy2])["legs"][1]["limit_price"] == pytest.approx(1.05)


def test_equal_spreads_send_the_more_traded_leg_to_market():
    a = ExitLeg("A", Side.LONG, 100, bid=0.50, ask=0.55, deals=3)
    b = ExitLeg("B", Side.SHORT, 100, bid=0.80, ask=0.85, deals=90)
    p = exit_plan([a, b])
    assert p["market_leg"] == 1 and "spreads iguais" in p["notes"][0]


def test_warns_when_market_leg_is_illiquid():
    illiquid = ExitLeg(
        "A", Side.LONG, 1000, bid=0.20, ask=0.21, deals=0, flags=("poucos negócios",)
    )
    p = exit_plan([illiquid, SHORT])
    assert p["market_leg"] == 0
    assert any("sem negócios" in w for w in p["warnings"])
    assert any("poucos negócios" in w for w in p["warnings"])


@pytest.mark.parametrize(
    "legs, reason",
    [
        ([LONG], "duas pernas"),
        ([LONG, ExitLeg("B", Side.SHORT, 500, 0.5, 0.6)], "quantidades"),
        ([LONG, ExitLeg("B", Side.SHORT, 1000, None, 8.0)], "sem bid/ask"),  # book cruzado
    ],
)
def test_unavailable_without_two_priced_equal_legs(legs, reason):
    p = exit_plan(legs)
    assert not p["available"] and reason in p["reason"]
