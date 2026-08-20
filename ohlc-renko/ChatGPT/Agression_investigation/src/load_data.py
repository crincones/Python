"""
Ingestao do CSV bruto de Renko 11R.

Regras (secao 2 do CLAUDE.md):
  - separador ';'
  - decimal '.'
  - deteccao automatica de encoding (BOM)
  - NAO reordenar cegamente pelo timestamp
  - investigar a ordem real das linhas antes de decidir
"""
from __future__ import annotations

import pandas as pd

from config import CSV_SEP, COLUMN_MAP, DATE_FORMAT, RAW_CSV


def detect_encoding(path) -> str:
    """Deteccao simples e deterministica de encoding via BOM / tentativa."""
    with open(path, "rb") as fh:
        head = fh.read(4)
    if head.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
        return "utf-16"
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as fh:
                for _ in range(200):
                    fh.readline()
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Le o CSV preservando a ordem original das linhas.

    Retorna um DataFrame com colunas renomeadas para ingles e uma coluna
    ``FileOrder`` com o indice original da linha no arquivo.
    """
    enc = detect_encoding(path)
    df = pd.read_csv(
        path,
        sep=CSV_SEP,
        encoding=enc,
        decimal=".",
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]

    missing = [c for c in COLUMN_MAP if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas ausentes no CSV: {missing}. Encontradas: {list(df.columns)}"
        )

    df = df.rename(columns=COLUMN_MAP)
    df["FileOrder"] = range(len(df))

    df["Date"] = pd.to_datetime(df["Date"], format=DATE_FORMAT, errors="coerce")
    for col in ("Open", "High", "Low", "Close", "AggBuy", "AggSell",
                "Duration", "Quantity", "Trades"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.attrs["encoding"] = enc
    df.attrs["source"] = str(path)
    return df


def to_chronological(df: pd.DataFrame) -> pd.DataFrame:
    """Coloca as barras em ordem cronologica ascendente.

    O arquivo exportado pelo ProfitChart vem em ordem DECRESCENTE (barra mais
    recente na primeira linha). Isso e verificado explicitamente aqui em vez
    de assumido: comparamos quantos passos do arquivo sao para frente e
    quantos sao para tras no tempo. So invertemos se o arquivo for
    predominantemente decrescente; nunca aplicamos ``sort_values`` cego,
    porque timestamps repetidos (multiplos bricks fechando no mesmo tick)
    perderiam a ordem correta.
    """
    d = df["Date"]
    fwd = int((d.diff().dt.total_seconds() > 0).sum())
    bwd = int((d.diff().dt.total_seconds() < 0).sum())

    reversed_file = bwd > fwd
    out = df.iloc[::-1].copy() if reversed_file else df.copy()
    out = out.reset_index(drop=True)
    out["BarIndex"] = range(len(out))
    out.attrs.update(df.attrs)
    out.attrs["file_was_reversed"] = reversed_file
    out.attrs["steps_forward_in_file"] = fwd
    out.attrs["steps_backward_in_file"] = bwd
    return out


def load_chronological(path=RAW_CSV) -> pd.DataFrame:
    return to_chronological(load_raw(path))
