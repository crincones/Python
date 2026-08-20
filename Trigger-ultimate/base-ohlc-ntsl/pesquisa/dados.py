"""Carga e preparacao da base 11R (Renko 50 pts) exportada do ProfitChart.

A base vem em ordem cronologica INVERSA e com o rotulo do Plot2 trocado
("Export_OHLC" e, na verdade, AgressionVolSell -- ver Export_OHLC.ntsl).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "profitpro-ohlc-11R.csv"
BRICK = 50.0


def carregar(caminho=None) -> pd.DataFrame:
    df = pd.read_csv(caminho or CSV, sep=";", encoding="utf-8-sig", decimal=",")
    df.columns = ["data", "o", "h", "l", "c", "buy", "sell", "dur", "qtd", "trades"]
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y %H:%M:%S.%f")
    df = df.iloc[::-1].reset_index(drop=True)          # cronologico
    for col in ("o", "h", "l", "c"):
        df[col] = df[col].astype(float)
    df["dir"] = np.where(df["c"] > df["o"], 1, -1)
    df["dia"] = df["data"].dt.normalize()
    df["hora"] = df["data"].dt.hour + df["data"].dt.minute / 60.0
    return df


def checar(df: pd.DataFrame) -> None:
    """Sanidade: grade, tamanho do tijolo, extremos travados."""
    corpo = (df["c"] - df["o"]).abs().value_counts()
    print("corpo dos tijolos:", dict(corpo))
    grade = ((df["o"] % BRICK == 0) & (df["c"] % BRICK == 0)).mean()
    print(f"na grade de 50: {grade:.4%}")
    alta = df["dir"] == 1
    print("alta  com h==c:", (df.loc[alta, "h"] == df.loc[alta, "c"]).mean())
    print("baixa com l==c:", (df.loc[~alta, "l"] == df.loc[~alta, "c"]).mean())
    print("periodo:", df["data"].iloc[0], "->", df["data"].iloc[-1])
    print("pregoes:", df["dia"].nunique(), " barras:", len(df))
    print("dur==0:", (df["dur"] == 0).mean(), " qtd==0:", (df["qtd"] == 0).mean())
    agr = df["buy"] + df["sell"]
    print("agressao total / quantity:", (agr.sum() / df["qtd"].sum()))
    print("barras com agressao 0:", (agr == 0).mean())


if __name__ == "__main__":
    d = carregar()
    checar(d)
    print(d.head())
