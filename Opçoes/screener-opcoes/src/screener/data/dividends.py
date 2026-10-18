"""Datas ex de proventos informadas manualmente em config/proventos.csv (o MT5 não fornece)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DIVIDEND_COLUMNS = ["underlying", "ex_date", "description"]


def load_dividends(path: Path) -> pd.DataFrame:
    """Colunas: underlying (str), ex_date (datetime64 sem timezone), description (str).

    Arquivo inexistente é erro: o alerta de exercício antecipado é obrigatório e um CSV ausente
    não pode ser confundido com "nenhum provento".
    """
    frame = pd.read_csv(path, dtype={"underlying": "string", "description": "string"})
    missing = set(DIVIDEND_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name}: colunas ausentes {sorted(missing)}")
    frame["ex_date"] = pd.to_datetime(frame["ex_date"], format="%Y-%m-%d")
    frame["underlying"] = frame["underlying"].str.strip().str.upper()
    return frame[DIVIDEND_COLUMNS]
