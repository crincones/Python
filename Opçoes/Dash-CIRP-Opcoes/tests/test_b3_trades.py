"""Fechamento oficial da B3 como fonte com o mercado fechado (último negócio, sem bid/ask)."""

from __future__ import annotations

import math

import pandas as pd
import pytest
from conftest import SPOT, TODAY, make_params, synthetic_chain

from travas.data.b3_trades import closing_chain, parse_trades
from travas.data.normalize import CHAIN_COLUMNS
from travas.options.analysis import analyze
from travas.options.implied_vol import options_implied_vol
from travas.options.liquidity import (
    FLAG_NO_BOOK,
    FLAG_NO_TICK,
    FLAG_NO_TRADE,
    FLAG_STALE,
    LiquidityRules,
    evaluate_liquidity,
)
from travas.options.models import Direction, Flow

RULES = LiquidityRules(0.20, 0.03, 5000.0, 5, 300.0)

# Trecho real do arquivo de 16/10/2026 (cabeçalho e linhas como a B3 publica).
SAMPLE = (
    "Status do Arquivo: Final\r\n"
    "RptDt;TckrSymb;ISIN;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;OscnPctg;AdjstdQt;"
    "AdjstdQtTax;RefPric;TradQty;FinInstrmQty;NtlFinVol\r\n"
    "2026-10-16;BBAS3;BRBBASACNOR3;CASH;23,29;23,95;23,58;23,63;-0,54;;;;34295;44910900;"
    "1055895199\r\n"
    "2026-10-16;BBASW222;BRBBAS3W1B17;EQUITY PUT;0,9;1,14;1;1,01;16,09;;;0,99;451;2006300;"
    "2026185\r\n"
    "2026-10-16;BBASW222W2;BRBBAS3W1F70;EQUITY PUT;;;;;;;;1,05;;;\r\n"
    "2026-10-16;10BK11;BR10BKCTF006;FORWARD;55,91;56,05;55,98;56,05;0,19;;;;4;48;2687,22\r\n"
).encode("latin-1")


def test_parse_trades_keeps_traded_stocks_and_options():
    table = parse_trades(SAMPLE)
    assert list(table.index) == ["BBAS3", "BBASW222"]  # sem negócio e termo ficam de fora
    put = table.loc["BBASW222"]
    assert put["last"] == pytest.approx(1.01)
    assert put["avg"] == pytest.approx(1.0)
    assert put["deals"] == 451
    assert put["turnover_brl"] == pytest.approx(2_026_185)
    assert table.loc["BBAS3", "turnover_brl"] == pytest.approx(1_055_895_199)


def test_parse_trades_ignores_file_not_final():
    assert parse_trades(SAMPLE.replace(b"Final", b"Parcial")) is None


def _closing(calendar, drop_trade: str | None = None):
    base = synthetic_chain(calendar)
    catalog = base[
        [
            "symbol",
            "underlying",
            "option_type",
            "exercise_style",
            "strike",
            "expiration_date",
            "contract_size",
            "ref_note",
        ]
    ]
    trades = pd.DataFrame(
        {
            "last": [*base["last"], SPOT],
            "avg": [*base["last"], SPOT],
            "deals": [50] * len(base) + [1000],
            "qty": [10_000.0] * len(base) + [1e6],
            "turnover_brl": [*(10_000 * base["last"]), 3e7],
        },
        index=[*base["symbol"], "TEST3"],
    )
    if drop_trade:
        trades = trades.drop(index=drop_trade)
    chain, spot = closing_chain(
        catalog, trades, TODAY, "TEST3", TODAY, calendar, list(CHAIN_COLUMNS)
    )
    return base, chain, spot


def test_closing_chain_has_no_invented_book(calendar):
    base, chain, spot = _closing(calendar)
    assert spot == pytest.approx(SPOT)
    assert len(chain) == len(base)
    assert chain["bid"].isna().all() and chain["ask"].isna().all() and chain["mid"].isna().all()
    assert (chain["price_basis"] == "ultimo_b3").all()
    merged = chain.merge(base[["symbol", "last"]], on="symbol", suffixes=("", "_b"))
    assert (merged["last"] == merged["last_b"]).all()
    assert (chain["underlying_price"] == SPOT).all()


def test_closing_liquidity_uses_last_and_day_volume(calendar):
    sym = "TESTC1131"
    _, chain, _ = _closing(calendar, drop_trade=sym)
    out = chain.join(evaluate_liquidity(chain, RULES))
    traded = out[out["symbol"] != sym]
    # Sem book e sem horário por definição: nada de "sem bid/ask", "sem tick" ou "antiga".
    for flags in traded["quote_flags"]:
        assert not {FLAG_NO_BOOK, FLAG_NO_TICK, FLAG_STALE} & set(flags)
    assert (traded["px_buy"] == traded["last"]).all()
    assert (traded["px_sell"] == traded["last"]).all()
    assert traded.loc[traded["liquidity_ok"], "liquidity_score"].between(0, 1).all()
    missing = out[out["symbol"] == sym].iloc[0]
    assert FLAG_NO_TRADE in missing["quote_flags"] and not missing["liquidity_ok"]
    assert math.isnan(missing["px_mid"])


def test_closing_iv_uses_last_trade(calendar):
    base, chain, _ = _closing(calendar)
    out = chain.join(evaluate_liquidity(chain, RULES))
    iv = options_implied_vol(out, 0.139, make_params(Direction.BULL, Flow.DEBIT).pricing)
    assert (iv["iv_status"] == "ok").mean() > 0.9


@pytest.mark.parametrize("flow", [Flow.DEBIT, Flow.CREDIT])
def test_analysis_on_closing_prices(calendar, flow):
    base, chain, spot = _closing(calendar)
    result = analyze(chain, spot, TODAY, calendar, make_params(Direction.BULL, flow))
    rows = result["results"]
    assert rows
    last = base.set_index("symbol")["last"]
    sign = 1 if flow is Flow.DEBIT else -1
    for row in rows:
        long_leg, short_leg = row["legs"]
        expected = round(sign * (last[long_leg["symbol"]] - last[short_leg["symbol"]]), 6)
        assert row["entry_natural"] == pytest.approx(expected)
        assert row["entry_mid"] == pytest.approx(expected)  # sem spread estimável
        assert long_leg["price_basis"] == "ultimo_b3"
        assert any("fechamento B3" in w for w in row["warnings"])
        assert not row["score_capped"]  # sem book não é motivo para reprovar a perna
    assert "fechamento oficial da B3" in result["assumptions"]["entry_basis"]
