"""Universo de sinais + metricas de avaliacao.

Um sinal so faz sentido no tijolo do PROPRIO vies (ver README): a maxima de um
tijolo de alta e sempre violada pelo tijolo seguinte, entao "seta acima" so pode
nascer em tijolo de baixa, e "seta abaixo" so em tijolo de alta.

Trade implicito para medir valor:
    seta acima  -> vende no fechamento do tijolo, stop na maxima do tijolo,
                   sai no fechamento do 4o tijolo seguinte.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dados import carregar
from features import preparar

BRICK = 50.0


def universo(h: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = preparar(carregar())
    d = d[(d.c - d.o).abs() == BRICK].copy()

    dn = d[d.dir == -1].dropna(subset=["ok_baixa"]).copy()
    up = d[d.dir == 1].dropna(subset=["ok_alta"]).copy()

    dn["lado"] = -1
    up["lado"] = 1
    dn["ok"] = dn["ok_baixa"]
    up["ok"] = up["ok_alta"]
    dn["risco"] = dn["h"] - dn["c"]
    up["risco"] = up["c"] - up["l"]
    dn["mfe"] = dn["mfe_baixa"]
    up["mfe"] = up["mfe_alta"]
    dn["net"] = dn["net_baixa"]
    up["net"] = up["net_alta"]

    for x in (dn, up):
        # resultado do trade: stop batido = -risco; senao, deslocamento liquido
        x["pnl"] = np.where(x["ok"] == 1, x["net"], -x["risco"])
        x["R"] = x["pnl"] / x["risco"]
        x["mfeR"] = x["mfe"] / x["risco"]
    return dn, up


def resumo(x: pd.DataFrame, nome: str = "") -> dict:
    return {
        "nome": nome,
        "n": len(x),
        "ok": x["ok"].mean() if len(x) else np.nan,
        "pnl": x["pnl"].mean() if len(x) else np.nan,
        "R": x["R"].mean() if len(x) else np.nan,
        "net": x["net"].mean() if len(x) else np.nan,
        "mfe": x["mfe"].mean() if len(x) else np.nan,
        "risco": x["risco"].mean() if len(x) else np.nan,
    }


def decis(x: pd.DataFrame, col: str, q: int = 10) -> pd.DataFrame:
    try:
        b = pd.qcut(x[col], q, duplicates="drop")
    except ValueError:
        return pd.DataFrame()
    g = x.groupby(b, observed=True)
    out = g.agg(n=("ok", "size"), ok=("ok", "mean"), pnl=("pnl", "mean"),
                R=("R", "mean"), net=("net", "mean"), risco=("risco", "mean"))
    return out


def tabela(dn, up, cols, q=6):
    for col in cols:
        for nome, x in (("BAIXA(seta acima)", dn), ("ALTA(seta abaixo)", up)):
            t = decis(x, col, q)
            if t.empty:
                continue
            print(f"\n--- {col} | {nome} | base ok={x.ok.mean():.3f} R={x.R.mean():+.3f}")
            print(t.round(3).to_string())


if __name__ == "__main__":
    dn, up = universo()
    print(pd.DataFrame([resumo(dn, "baixa"), resumo(up, "alta")]).round(4).to_string(index=False))
    tabela(dn, up, ["imb", "z_dur_s", "z_qtd", "vel", "part", "risco", "seq", "intens"])
