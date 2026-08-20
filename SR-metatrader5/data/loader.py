"""Carregamento eficiente de candles de 1 minuto."""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd

OHLC = ["open", "high", "low", "close"]


def _read_metatrader(path: str) -> pd.DataFrame:
    """Export do MetaTrader: <DATE>\\t<TIME>\\t<OPEN>...<TICKVOL>\\t<VOL>\\t<SPREAD>."""
    df = pd.read_csv(
        path,
        sep="\t",
        dtype={"<DATE>": "string", "<TIME>": "string"},
        engine="c",
    )
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    dt = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")

    out = pd.DataFrame({"datetime": dt})
    for c in OHLC:
        out[c] = pd.to_numeric(df[c], errors="coerce")

    # VOL = volume financeiro/contratos; TICKVOL = numero de negocios.
    # Usa VOL quando informado, senao TICKVOL, senao NaN (volume e opcional).
    vol = None
    if "vol" in df.columns:
        vol = pd.to_numeric(df["vol"], errors="coerce")
        if float(np.nansum(vol.to_numpy())) == 0.0:
            vol = None
    if vol is None and "tickvol" in df.columns:
        vol = pd.to_numeric(df["tickvol"], errors="coerce")
    out["volume"] = vol if vol is not None else np.nan
    return out


def _read_generic(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    if "datetime" not in df.columns:
        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = df["date"].astype(str) + " " + df["time"].astype(str)
        else:
            raise ValueError(f"nao encontrei coluna 'datetime' em {path}")
    out = pd.DataFrame({"datetime": pd.to_datetime(df["datetime"])})
    for c in OHLC:
        if c not in df.columns:
            raise ValueError(f"coluna obrigatoria ausente: {c}")
        out[c] = pd.to_numeric(df[c], errors="coerce")
    out["volume"] = pd.to_numeric(df["volume"], errors="coerce") if "volume" in df.columns else np.nan
    return out


def load_candles(
    path: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> pd.DataFrame:
    """Le o historico de 1 minuto e devolve um DataFrame ordenado e sem duplicatas.

    Indice: DatetimeIndex (naive, horario do ativo).
    Colunas: open, high, low, close, volume (volume pode ser todo NaN).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8-sig", errors="ignore") as fh:
        head = fh.readline()

    df = _read_metatrader(path) if head.lstrip().startswith("<DATE>") else _read_generic(path)

    # 1) ordenar  2) remover duplicatas de datetime (mantem a ultima ocorrencia)
    df = df.sort_values("datetime", kind="mergesort")
    df = df.drop_duplicates(subset="datetime", keep="last")
    df = df.set_index("datetime")
    df.index.name = "datetime"

    if date_from is not None:
        df = df.loc[df.index >= pd.Timestamp(date_from)]
    if date_to is not None:
        # limite final inclusivo mesmo quando informado apenas como data
        end = pd.Timestamp(date_to)
        if end.normalize() == end:
            end = end + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)
        df = df.loc[df.index <= end]

    for c in OHLC:
        df[c] = df[c].astype("float64")
    df["volume"] = df["volume"].astype("float64")
    return df[OHLC + ["volume"]]
