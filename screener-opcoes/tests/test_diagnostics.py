from __future__ import annotations

import pandas as pd

from screener.diagnostics import field_fill_rates


def test_zero_and_empty_count_as_missing() -> None:
    frame = pd.DataFrame({"bid": [0.5, 0.0, 0.4, None], "basis": ["PETR4", "", "VALE3", None]})
    rates = field_fill_rates(frame, ["bid", "basis"]).set_index("field")
    assert rates.loc["bid", "filled"] == 2
    assert rates.loc["basis", "filled"] == 2
    assert rates.loc["bid", "fill_rate"] == 0.5


def test_empty_frame_has_nan_rate() -> None:
    rates = field_fill_rates(pd.DataFrame({"bid": pd.Series([], dtype=float)}), ["bid"])
    assert rates.loc[0, "total"] == 0
    assert pd.isna(rates.loc[0, "fill_rate"])
