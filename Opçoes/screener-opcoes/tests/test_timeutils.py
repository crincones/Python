from __future__ import annotations

import pandas as pd

from screener.timeutils import server_epoch_to_local


def test_server_epoch_is_wall_clock_in_server_timezone() -> None:
    # Tick real da XP: epoch 1789641291 exibido como 10:34:51 no horário de Brasília.
    result = server_epoch_to_local(pd.Series([1789641291]), "America/Sao_Paulo")
    assert result.iloc[0] == pd.Timestamp("2026-09-17 10:34:51", tz="America/Sao_Paulo")


def test_zero_epoch_is_missing() -> None:
    result = server_epoch_to_local(pd.Series([0, 1789641291]), "America/Sao_Paulo")
    assert pd.isna(result.iloc[0])
    assert str(result.dt.tz) == "America/Sao_Paulo"
