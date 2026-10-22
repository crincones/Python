"""Snapshots do servidor: gravação, índice, leitura no app e uso com o mercado fechado."""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import pytest
from conftest import SETTINGS, SPOT, TODAY, synthetic_chain

from travas.data import market_data
from travas.data.service import MarketDataService
from travas.data.snapshots import (
    SnapshotSource,
    read_snapshot,
    snapshot_chain,
    write_index,
    write_snapshot,
)
from travas.timeutils import LOCAL_TIMEZONE

CAPTURED = pd.Timestamp("2026-10-14 16:30", tz=LOCAL_TIMEZONE)


def _chain(calendar, shift_days: int = 0) -> pd.DataFrame:
    chain = synthetic_chain(calendar).assign(captured_at=CAPTURED)
    if shift_days:
        chain["expiration_date"] = chain["expiration_date"] + dt.timedelta(days=shift_days)
    chain.loc[0, "ref_note"] = "strike corrigido pela B3"
    return chain


def _write(root, calendar, day=TODAY, slot="1630", status="completo", shift_days=0):
    chain = _chain(calendar, shift_days)
    return write_snapshot(root, day, slot, chain, {"status": status, "series": len(chain)})


def test_roundtrip_keeps_values_and_types(calendar, tmp_path):
    manifest = _write(tmp_path, calendar)
    assert manifest["file"] == "2026-10-14/1630.csv.gz"
    back = read_snapshot(tmp_path / manifest["file"])
    original = _chain(calendar)
    assert len(back) == len(original)
    assert isinstance(back["expiration_date"].iloc[0], dt.date)
    assert str(back["quote_time"].dt.tz) == LOCAL_TIMEZONE
    assert back["captured_at"].iloc[0] == CAPTURED
    pd.testing.assert_series_equal(back["bid"], original["bid"])
    pd.testing.assert_series_equal(back["ask"], original["ask"])
    assert back.loc[0, "ref_note"] == "strike corrigido pela B3"
    assert back.loc[1, "ref_note"] is None  # nulo continua nulo (não vira NaN "verdadeiro")
    assert back["open_interest"].isna().all()


def test_index_lists_snapshots_and_failures(calendar, tmp_path):
    _write(tmp_path, calendar, slot="1100")
    write_snapshot(tmp_path, TODAY, "1630", pd.DataFrame(), {"status": "falhou"})
    index = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    by_slot = {e["slot"]: e for e in index["snapshots"]}
    assert by_slot["1100"]["file"] == "2026-10-14/1100.csv.gz"
    assert by_slot["1630"]["status"] == "falhou" and by_slot["1630"]["file"] is None
    assert write_index(tmp_path)["snapshots"] == index["snapshots"]


def test_snapshot_chain_recomputes_terms_and_spot(calendar, tmp_path):
    frame = read_snapshot(tmp_path / _write(tmp_path, calendar)["file"])
    later = dt.date(2026, 11, 20)  # 1º vencimento (13/11) já passou
    rows, spot = snapshot_chain(frame, "TEST3", later, calendar)
    assert spot == pytest.approx(SPOT)
    assert (rows["expiration_date"] > dt.date(2026, 11, 13)).all()
    expected = calendar.sessions_until(later, pd.Series([dt.date(2026, 12, 18)])).iloc[0]
    assert (rows["dte_business_days"] == expected).all()
    assert snapshot_chain(frame, "OUTRO3", later, calendar)[0].empty


def test_source_picks_latest_usable_and_falls_back_offline(calendar, tmp_path):
    root = tmp_path / "servidor"
    _write(root, calendar, slot="1100")
    _write(root, calendar, slot="1630", status="falhou")  # com arquivo, mas status ruim
    write_snapshot(root, TODAY, "1700", pd.DataFrame(), {"status": "falhou"})
    cache = tmp_path / "cache"
    source = SnapshotSource(root.as_uri(), cache, 5)
    snap = source.latest()
    assert (snap.day, snap.slot, snap.note) == (TODAY, "1100", None)
    assert (cache / "2026-10-14_1100.csv.gz").exists()
    offline = SnapshotSource((tmp_path / "nada").as_uri(), cache, 5)
    snap = offline.latest()
    assert snap.slot == "1100" and "inacessível" in snap.note


def test_monthly_expiration_is_third_friday_or_session_before(calendar):
    assert calendar.monthly_expiration(2026, 10) == dt.date(2026, 10, 16)
    assert calendar.monthly_expiration(2026, 11) == dt.date(2026, 11, 19)  # 20/11 é feriado
    assert calendar.monthly_expiration(2027, 1) == dt.date(2027, 1, 15)
    assert not calendar.is_monthly_expiration(dt.date(2026, 10, 23))  # semanal


def test_select_expirations_keeps_monthlies_and_short_weeklies(calendar):
    # Caso real de PETR4 em 20/10/2026: semanais toda sexta e os mensais de 3ª sexta.
    today = dt.date(2026, 10, 20)
    weeklies = [dt.date(2026, 10, 23), dt.date(2026, 10, 30), dt.date(2026, 11, 6)]
    weeklies += [dt.date(2026, 11, 13), dt.date(2026, 11, 27)]
    monthlies = [dt.date(2026, 11, 19), dt.date(2026, 12, 18), dt.date(2027, 1, 15)]
    later = [dt.date(2027, 2, 19)]
    picked = market_data.select_expirations(weeklies + monthlies + later, today, calendar, 3, 15)
    # Semanais até 15 du: 23/10 (3), 30/10 (8), 06/11 (13); 13/11 (17 du) e 27/11 ficam fora.
    assert picked == set(monthlies) | {
        dt.date(2026, 10, 23),
        dt.date(2026, 10, 30),
        dt.date(2026, 11, 6),
    }
    only_monthly = market_data.select_expirations(weeklies + monthlies, today, calendar, 2, 0)
    assert only_monthly == {dt.date(2026, 11, 19), dt.date(2026, 12, 18)}
    # Padrão desconhecido (nenhum vencimento é mensal): os N mais próximos.
    odd = [dt.date(2026, 12, 2), dt.date(2027, 2, 3)]
    assert market_data.select_expirations(odd, today, calendar, 1, 0) == {dt.date(2026, 12, 2)}


def test_index_options_monthly_is_wednesday_nearest_15th(calendar):
    # Vencimentos reais das opções de IBOV11 (cadastro B3 de 20/10/2026).
    assert calendar.index_monthly_expiration(2026, 11) == dt.date(2026, 11, 18)
    assert calendar.index_monthly_expiration(2026, 12) == dt.date(2026, 12, 16)
    assert calendar.index_monthly_expiration(2027, 1) == dt.date(2027, 1, 13)
    assert calendar.index_monthly_expiration(2027, 2) == dt.date(2027, 2, 17)
    assert calendar.index_monthly_expiration(2027, 4) == dt.date(2027, 4, 14)
    today = dt.date(2026, 10, 20)
    daily = [dt.date(2026, 10, d) for d in (21, 22, 23, 26, 27, 28)] + [dt.date(2026, 11, 13)]
    months = [dt.date(2026, 11, 18), dt.date(2026, 12, 16), dt.date(2027, 1, 13)]
    picked = market_data.select_expirations(daily + months, today, calendar, 3, 5, index=True)
    # Mensais do índice + diários com até 5 du (21/10 a 27/10); 28/10 (6 du) e 13/11 fora.
    assert picked == set(months) | set(daily[:5])


def test_scope_with_monthly_expirations(calendar):
    catalog = synthetic_chain(calendar)  # 13/11 (semanal) e 18/12 (mensal)
    scope = market_data.ChainScope(("call", "put"), 10_000, 0, 1e9, monthly_expirations=1)
    picked = market_data.candidate_symbols(catalog, "TEST3", scope, TODAY, calendar)
    assert set(picked["expiration_date"]) == {dt.date(2026, 12, 18)}


def test_empty_analysis_explains_expirations_outside_term(calendar):
    from conftest import make_params

    from travas.options.analysis import analyze
    from travas.options.models import Direction, Flow

    params = make_params(Direction.BULL, Flow.DEBIT, dte_min=60, dte_max=90)
    result = analyze(synthetic_chain(calendar), SPOT, TODAY, calendar, params)
    assert result["results"] == []
    assert "prazo de 60 a 90 dias úteis" in result["empty_reason"]
    assert "13/11/2026" in result["empty_reason"] and "18/12/2026" in result["empty_reason"]


def test_service_uses_snapshot_when_market_closed(calendar, tmp_path):
    today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
    shift = (today - TODAY).days + 1  # vencimentos sempre no futuro
    root = tmp_path / "servidor"
    _write(root, calendar, shift_days=max(shift, 0))
    settings = SETTINGS.model_copy(
        update={
            "paths": SETTINGS.paths.model_copy(
                update={"quotes_dir": tmp_path / "cotacoes", "snapshots_dir": tmp_path / "cache"}
            ),
            "snapshots": SETTINGS.snapshots.model_copy(update={"server_url": root.as_uri()}),
        }
    )
    service = MarketDataService(settings)
    service.set_off_hours_source("servidor")
    sunday = today + dt.timedelta(days=(6 - today.weekday()) % 7)
    service._clock = lambda: dt.datetime.combine(sunday, dt.time(12)).replace(
        tzinfo=pd.Timestamp.now(tz=LOCAL_TIMEZONE).tzinfo
    )
    chain, meta = service.chain("TEST3")
    assert meta["source"] == "snapshot_servidor"
    assert meta["spot"] == pytest.approx(SPOT)
    assert chain["bid"].notna().all()
    assert "snapshot do servidor de 14/10/2026 16:30" in meta["realtime_warning"]
    legs = service.leg_quotes("TEST3", list(chain["symbol"][:2]))
    assert set(legs["source"]) == {"snapshot_servidor"}
    assert service.status()["snapshot"]["label"] == "14/10/2026 16:30"


def test_options_liquidity_ranks_by_average_turnover(tmp_path):
    from travas.data.snapshots import options_liquidity

    reference = pd.DataFrame(
        {"underlying": ["AAAA3", "BBBB4"]}, index=pd.Index(["AAAAK10", "BBBBW20"], name="symbol")
    )
    days = {
        "2026-10-15": [("AAAAK10", "EQUITY CALL", 100.0, 4), ("BBBBW20", "EQUITY PUT", 900.0, 2)],
        # AAAAJ5 já venceu (fora da referência): vai pela raiz do ticker.
        "2026-10-16": [("AAAAJ5", "EQUITY CALL", 2000.0, 6), ("AAAA3", "CASH", 1e9, 99)],
    }
    for day, rows in days.items():
        (tmp_path / day).mkdir()
        pd.DataFrame(rows, columns=["symbol", "segment", "turnover_brl", "deals"]).to_csv(
            tmp_path / day / "negocios_b3.csv", index=False
        )
    ranking, used = options_liquidity(tmp_path, reference, 5)
    assert used == ["2026-10-15", "2026-10-16"]
    assert list(ranking.index) == ["AAAA3", "BBBB4"]  # ações (CASH) não contam
    assert ranking["AAAA3"] == pytest.approx(1050.0)
    assert ranking["BBBB4"] == pytest.approx(450.0)
    assert options_liquidity(tmp_path, reference, 1)[1] == ["2026-10-16"]
    from travas.data.snapshots import options_liquidity_table

    table = options_liquidity_table(sorted(tmp_path.glob("*/negocios_b3.csv")), reference)
    assert table.loc["AAAA3", "deals"] == pytest.approx(5.0)  # (4 + 6) / 2 pregões
