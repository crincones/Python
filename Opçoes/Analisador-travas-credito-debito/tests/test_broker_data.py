"""Diferenças entre corretoras no MT5: ativo-objeto (basis) e volume/negócios das opções."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.normalize import (
    apply_reference,
    normalize_chain,
    option_catalog,
    resolve_underlying,
)
from travas.settings import load_settings

TZ = "America/Sao_Paulo"
EXP = int(pd.Timestamp("2026-11-19 23:59:59").tz_localize("UTC").timestamp())


def symbols(rows):
    cols = [
        "name",
        "basis",
        "path",
        "option_strike",
        "option_right",
        "option_mode",
        "expiration_time",
        "trade_contract_size",
    ]
    return pd.DataFrame(rows, columns=cols)


def ref(rows):
    """Referência B3: (symbol, underlying, strike, vencimento, estilo)."""
    cols = ["symbol", "underlying", "strike", "expiration_date", "exercise_style"]
    return pd.DataFrame(rows, columns=cols).set_index("symbol")


def test_resolve_underlying_prefers_b3_map_and_validates_basis():
    names = pd.Series(["PETRK1", "YDUQK886", "PETRA239", "XYZW1"])
    basis = pd.Series(["PETR4", "YDUQK886", "PETR4", ""])
    # B3: PETRA239 é opção de PETR3 (mesma raiz "PETR" da PETR4)
    b3 = ref([("YDUQK886", "YDUQ3", 8.86, None, None), ("PETRA239", "PETR3", 23.9, None, None)])
    out = resolve_underlying(names, basis, b3)
    assert out.tolist()[:3] == ["PETR4", "YDUQ3", "PETR3"]
    assert pd.isna(out.iloc[3])  # sem mapa e basis vazio: não inventa
    no_map = resolve_underlying(names, basis, None)
    assert pd.isna(no_map.iloc[1])  # "YDUQK886" não tem formato de ativo


def test_catalog_drops_bmf_and_unresolved():
    rows = [
        ("PETRK1", "PETR4", "BOVESPA\OPCOES\PETRK1", 30.0, 0, 1, EXP, 1.0),
        ("YDUQK886", "YDUQK886", "BOVESPA\YDUQK886", 8.86, 0, 0, EXP, 1.0),
        ("DOLF29C005500E", "DOLF29C005500E", "BMF\DOLF29C005500E", 5500.0, 0, 0, EXP, 1.0),
    ]
    cat = option_catalog(symbols(rows), TZ, ref([("YDUQK886", "YDUQ3", 8.86, None, None)]))
    assert cat["symbol"].tolist() == ["PETRK1", "YDUQK886"]
    assert cat["underlying"].tolist() == ["PETR4", "YDUQ3"]
    assert option_catalog(symbols(rows), TZ)["symbol"].tolist() == ["PETRK1"]


def test_volume_falls_back_to_d1_bar_when_session_fields_are_empty():
    calendar = B3Calendar.from_csv(load_settings().paths.holidays_file)
    rows = [
        ("PETRK1", "PETR4", "BOVESPA\OPCOES\PETRK1", 30.0, 0, 1, EXP, 1.0),
        ("PETRK2", "PETR4", "BOVESPA\OPCOES\PETRK2", 31.0, 0, 1, EXP, 1.0),
        ("PETRK3", "PETR4", "BOVESPA\OPCOES\PETRK3", 32.0, 0, 1, EXP, 1.0),
    ]
    raw = symbols(rows).assign(
        bid=[1.0, 0.8, 0.5],
        ask=[1.1, 0.9, 0.6],
        last=[1.05, 0.85, 0.55],
        time=[100, 100, 100],
        session_deals=[40, 0, 0],
        session_volume=[5000.0, 0.0, 0.0],
        session_aw=[1.02, 0.0, 0.0],
        session_close=[1.0, 0.8, 0.5],
        session_interest=[0, 0, 0],
        trade_tick_size=[0.01] * 3,
        underlying_bid=[57.0] * 3,
        underlying_ask=[57.1] * 3,
        underlying_last=[57.05] * 3,
        underlying_time=[100] * 3,
        read_time=[pd.Timestamp("2026-10-15 11:00", tz=TZ)] * 3,
        d1_tick_volume=[np.nan, 6.0, np.nan],
        d1_real_volume=[np.nan, 10400.0, np.nan],
        d1_close=[np.nan, 0.86, np.nan],
    )
    chain = normalize_chain(raw, dt.date(2026, 10, 15), TZ, calendar).set_index("symbol")
    assert chain.loc["PETRK1", "volume_source"] == "sessão" and chain.loc["PETRK1", "deals"] == 40
    assert chain.loc["PETRK2", "volume_source"] == "barra D1"
    assert chain.loc["PETRK2", "deals"] == 6 and chain.loc["PETRK2", "volume_qty"] == 10400
    assert chain.loc["PETRK2", "turnover_brl"] == 10400 * 0.86
    assert chain.loc["PETRK3", "volume_source"] == "sem negócios hoje"
    assert chain.loc["PETRK3", "turnover_brl"] == 0


def test_reference_fixes_stale_strike_and_holiday_expiration():
    # Valores reais da Genial em 15/10/2026: strike sem ajuste de provento (58,05 x 56,86 na B3)
    # e vencimento de novembro em 20/11 (feriado; a B3 vence em 19/11).
    catalog = pd.DataFrame(
        {
            "symbol": ["PETRJ580", "PETRK576", "PETRK999"],
            "underlying": ["PETR4"] * 3,
            "option_type": ["call"] * 3,
            "exercise_style": ["american", "american", "american"],
            "strike": [58.05, 56.41, 60.0],
            "expiration_date": [
                dt.date(2026, 10, 16),
                dt.date(2026, 11, 20),
                dt.date(2026, 11, 20),
            ],
            "contract_size": [1.0] * 3,
        }
    )
    b3 = ref(
        [
            ("PETRJ580", "PETR4", 56.86, dt.date(2026, 10, 16), "american"),
            ("PETRK576", "PETR4", 56.41, dt.date(2026, 11, 19), "european"),
        ]
    )
    out = apply_reference(catalog, b3).set_index("symbol")
    assert out.loc["PETRJ580", "strike"] == 56.86
    assert "strike corrigido pela B3 (MT5 informava 58,05)" in out.loc["PETRJ580", "ref_note"]
    assert out.loc["PETRK576", "expiration_date"] == dt.date(2026, 11, 19)
    assert "vencimento corrigido" in out.loc["PETRK576", "ref_note"]
    assert out.loc["PETRK576", "exercise_style"] == "european"
    # Série fora da referência: mantém o MT5, sem nota.
    assert out.loc["PETRK999", "strike"] == 60.0 and out.loc["PETRK999", "ref_note"] is None
