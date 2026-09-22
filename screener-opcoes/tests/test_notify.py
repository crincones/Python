from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from screener.notify.alerts import select_highlights, send_alerts, spread_caption
from screener.notify.format import brl, num, pct
from screener.notify.payoff_chart import payoff_per_lot, payoff_png
from screener.notify.telegram import NotifyError, read_token
from screener.settings import load_settings

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CAPTION_LIMIT = 1024  # limite da legenda de foto na Bot API
SNAPSHOT_TIME = pd.Timestamp("2026-09-22 13:12", tz="America/Sao_Paulo")


class FakeTelegram:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.photos: list[tuple[bytes, str]] = []

    def send_message(self, text: str) -> None:
        self.messages.append(text)

    def send_photo(self, photo: bytes, caption: str) -> None:
        self.photos.append((photo, caption))


def _spread(**overrides) -> dict:
    row = {
        "underlying": "BOVA11",
        "strategy": "bull_call",
        "direction": "alta",
        "expiration_date": pd.Timestamp("2026-10-16"),
        "dte_business_days": 18,
        "spot": 37.4,
        "long_symbol": "BOVAJ37",
        "short_symbol": "BOVAJ39",
        "long_strike": 37.0,
        "short_strike": 39.0,
        "width": 2.0,
        "debit": 0.73,
        "debit_mid": 0.70,
        "debit_per_lot": 73.0,
        "max_gain_per_lot": 127.0,
        "max_loss_per_lot": 73.0,
        "reward_risk": 1.74,
        "breakeven": 37.73,
        "breakeven_distance_pct": 0.0088,
        "breakeven_distance_sigma": 0.12,
        "pop": 0.404,
        "long_iv": 0.21,
        "short_iv": 0.19,
        "liquidity_score": 0.85,
        "early_exercise_alert": False,
        "early_exercise_reason": None,
        "score": 91.8,
        "rank": 1,
        "ranked": True,
        "bias": "alta",
        "bias_source": "automático",
    }
    row.update(overrides)
    return row


@pytest.fixture
def notify_settings():
    return load_settings().notify.model_copy(update={"min_score": 90})


def test_brazilian_number_format() -> None:
    assert num(1234.5) == "1.234,50"
    assert brl(-12.5) == "−R$ 12,50"
    assert pct(0.4038) == "40,4%"
    assert pct(float("nan")) == "—"


def test_selection_keeps_best_per_group_above_limit(notify_settings) -> None:
    spreads = pd.DataFrame(
        [
            _spread(score=91.8),
            _spread(long_symbol="BOVAJ183", score=91.5, rank=2),
            _spread(long_symbol="BOVAJ36", score=90.0, rank=3),  # não é "superior a 90"
            _spread(underlying="PETR4", score=95.0, ranked=False, rank=pd.NA),  # fora do viés
            _spread(underlying="VALE3", strategy="bear_put", direction="baixa", score=93.0, rank=1),
        ]
    )
    highlights = select_highlights(spreads, notify_settings)
    assert [(h.spread["underlying"], h.variations) for h in highlights] == [
        ("VALE3", 0),
        ("BOVA11", 1),
    ]


def test_no_highlights_sends_only_the_notice(notify_settings) -> None:
    api = FakeTelegram()
    spreads = pd.DataFrame([_spread(score=80.0)])
    assert send_alerts(api, spreads, notify_settings, 100, SNAPSHOT_TIME) == []
    assert len(api.messages) == 1
    assert "Nenhuma trava" in api.messages[0]
    assert api.photos == []


def test_highlights_send_summary_and_charts(notify_settings) -> None:
    api = FakeTelegram()
    spreads = pd.DataFrame([_spread(early_exercise_alert=True, early_exercise_reason="ex <x>")])
    send_alerts(api, spreads, notify_settings, 100, SNAPSHOT_TIME, "http://x/s.html", test=True)
    assert "[TESTE]" in api.messages[0] and "BOVAJ37/BOVAJ39" in api.messages[0]
    (photo, caption), *_ = api.photos
    assert photo.startswith(PNG_SIGNATURE)
    assert "Score 91,8" in caption and "ex &lt;x&gt;" in caption
    assert len(caption) < CAPTION_LIMIT


def test_payoff_matches_definitions() -> None:
    bull = _spread()
    prices = np.array([30.0, 37.73, 45.0])
    np.testing.assert_allclose(payoff_per_lot(bull, prices, 100), [-73.0, 0.0, 127.0], atol=1e-9)
    bear = _spread(strategy="bear_put", long_strike=39.0, short_strike=37.0, breakeven=38.27)
    np.testing.assert_allclose(payoff_per_lot(bear, prices, 100), [127.0, 54.0, -73.0], atol=1e-9)
    assert payoff_png(bear, 100, "teste").startswith(PNG_SIGNATURE)


def test_caption_shows_rank(notify_settings) -> None:
    select = select_highlights(pd.DataFrame([_spread()]), notify_settings)
    assert "#1" in spread_caption(select[0], 100)


def test_token_file_must_exist_and_not_be_empty(tmp_path: Path) -> None:
    with pytest.raises(NotifyError, match="não encontrado"):
        read_token(tmp_path / "ausente")
    empty = tmp_path / "token"
    empty.write_text("  \n", encoding="utf-8")
    with pytest.raises(NotifyError, match="vazio"):
        read_token(empty)
    empty.write_text("123:abc\n", encoding="utf-8")
    assert read_token(empty) == "123:abc"
