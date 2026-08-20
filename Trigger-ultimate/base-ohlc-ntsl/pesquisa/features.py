"""Features causais (so olham ate o fechamento da barra i) e rotulagem do alvo.

Alvo pedido: depois do sinal, o extremo CONTRARIO ao vies nao pode ser violado
nos 4 tijolos seguintes.

  vies de baixa (seta ACIMA)  -> extremo contrario = maxima da barra do sinal
  vies de alta  (seta ABAIXO) -> extremo contrario = minima da barra do sinal

Score = quanto andou a favor nos 4 tijolos (MFE), em pontos e em tijolos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BRICK = 50.0
H = 4  # horizonte em tijolos


def _roll_max(s: pd.Series, n: int) -> pd.Series:
    """Maximo das n barras SEGUINTES (i+1 .. i+n)."""
    return s.shift(-1).rolling(n, min_periods=n).max().shift(-(n - 1))


def _roll_min(s: pd.Series, n: int) -> pd.Series:
    return s.shift(-1).rolling(n, min_periods=n).min().shift(-(n - 1))


def rotular(df: pd.DataFrame, h: int = H) -> pd.DataFrame:
    d = df.copy()
    fut_max_h = _roll_max(d["h"], h)
    fut_min_l = _roll_min(d["l"], h)
    fut_min_c = _roll_min(d["c"], h)
    fut_max_c = _roll_max(d["c"], h)

    # --- vies de BAIXA: maxima do sinal nao pode ser violada
    d["ok_baixa"] = (fut_max_h <= d["h"]).astype("float")
    d["mfe_baixa"] = d["c"] - fut_min_l            # quanto andou a favor (pts)
    d["mae_baixa"] = fut_max_h - d["c"]            # quanto andou contra (pts)
    d["net_baixa"] = d["c"] - d["c"].shift(-h)     # deslocamento liquido em h tijolos

    # --- vies de ALTA: minima do sinal nao pode ser violada
    d["ok_alta"] = (fut_min_l >= d["l"]).astype("float")
    d["mfe_alta"] = fut_max_h - d["c"]
    d["mae_alta"] = d["c"] - fut_min_l
    d["net_alta"] = d["c"].shift(-h) - d["c"]

    # versoes so com fechamentos (equivalente a "tijolos", ignora pavio)
    d["ok_baixa_c"] = (fut_max_c <= d["c"]).astype("float")
    d["ok_alta_c"] = (fut_min_c >= d["c"]).astype("float")

    for col in ("ok_baixa", "ok_alta", "ok_baixa_c", "ok_alta_c"):
        d.loc[d[col].isna(), col] = np.nan
    return d


def featurizar(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    eps = 1e-9

    agr = d["buy"] + d["sell"]
    d["agr"] = agr
    d["delta"] = d["buy"] - d["sell"]
    d["imb"] = d["delta"] / (agr + eps)                    # -1 .. +1
    d["part"] = agr / (d["qtd"] + eps)                     # fatia agredida do volume
    d["tam"] = d["qtd"] / (d["trades"] + eps)              # tamanho medio do negocio
    d["dur_s"] = d["dur"] * 60.0
    d["vel"] = BRICK / (d["dur_s"] + 1.0)                  # pts por segundo
    d["fluxo"] = d["qtd"] / (d["dur_s"] + 1.0)             # contratos por segundo
    d["intens"] = d["trades"] / (d["dur_s"] + 1.0)         # negocios por segundo

    # tijolo fantasma: fecha sem tempo e/ou sem volume (gap de abertura)
    d["fantasma"] = ((d["dur"] == 0) | (d["qtd"] == 0)).astype(int)

    # --- contexto de sequencia -------------------------------------------
    dirn = d["dir"].to_numpy()
    seq = np.ones(len(d), dtype=int)
    for i in range(1, len(d)):
        if dirn[i] == dirn[i - 1]:
            seq[i] = seq[i - 1] + 1
    d["seq"] = seq                                          # tijolos seguidos no mesmo sentido
    d["virou"] = (d["dir"] != d["dir"].shift(1)).astype(int)

    for n in (5, 10, 20):
        d[f"net{n}"] = (d["c"] - d["c"].shift(n)) / BRICK    # deslocamento liquido em tijolos
        d[f"viradas{n}"] = d["virou"].rolling(n).sum()       # quantas inversoes (choppiness)
        d[f"cdelta{n}"] = d["delta"].rolling(n).sum()
        d[f"cimb{n}"] = d["delta"].rolling(n).sum() / (d["agr"].rolling(n).sum() + eps)
        d[f"cqtd{n}"] = d["qtd"].rolling(n).sum()
        d[f"cdur{n}"] = d["dur_s"].rolling(n).sum()
        # esforco por tijolo liquido: volume gasto para deslocar 1 tijolo
        d[f"esf{n}"] = d[f"cqtd{n}"] / (d[f"net{n}"].abs() + 1.0)

    # --- normalizacao por regime (z-score movel, causal) ------------------
    for col in ("qtd", "trades", "dur_s", "tam", "fluxo", "agr"):
        m = d[col].rolling(100, min_periods=30).mean()
        s = d[col].rolling(100, min_periods=30).std()
        d[f"z_{col}"] = (d[col] - m) / (s + eps)
        d[f"r_{col}"] = d[col] / (m + eps)                   # razao (mais facil no NTSL)

    # --- leituras de fluxo ------------------------------------------------
    # divergencia: tijolo anda para um lado e a agressao aponta para o outro
    d["div"] = -d["dir"] * np.sign(d["imb"]) * d["imb"].abs()   # >0 = agressao contraria ao tijolo
    d["absorc"] = d["div"] * d["r_qtd"]                          # divergencia com volume alto
    for n in (3, 5, 10):
        d[f"div{n}"] = d["div"].rolling(n).mean()

    # delta acumulado no dia (proxy do delta da sessao)
    d["cdelta_dia"] = d.groupby("dia")["delta"].cumsum()
    d["nbar_dia"] = d.groupby("dia").cumcount()

    # esforco relativo do tijolo: volume alto para andar os mesmos 50 pts
    d["custo"] = d["r_qtd"]
    d["custo_lento"] = d["r_qtd"] * d["r_dur_s"]

    # ultimos tijolos (lags) do que interessa
    for lag in (1, 2, 3):
        d[f"imb_l{lag}"] = d["imb"].shift(lag)
        d[f"dir_l{lag}"] = d["dir"].shift(lag)
        d[f"rqtd_l{lag}"] = d["r_qtd"].shift(lag)

    d["imb3"] = d["imb"].rolling(3).mean()
    d["imb5"] = d["imb"].rolling(5).mean()

    # posicao no range recente (0 = fundo, 1 = topo)
    for n in (20, 50):
        hi = d["h"].rolling(n).max()
        lo = d["l"].rolling(n).min()
        d[f"pos{n}"] = (d["c"] - lo) / (hi - lo + eps)
    return d


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    return rotular(featurizar(df))
