"""Renko 11R sintetico a partir de passeio aleatorio puro (sem deriva).

Serve de REGUA. Como a serie real se mostrou um martingale (P(cont)=0.6855 no
papel, mas -1.14 pts/tijolo depois de corrigir o preenchimento dos tijolos
fantasma), a pergunta certa deixa de ser "esse numero e alto?" e passa a ser
"esse numero e diferente do que o puro acaso produziria com esta geometria?".

Usa exatamente as regras deduzidas em renko11r.py:
  dir=+1 -> sobe se preco >  base+B   ; inverte se preco <  base-2B
  dir=-1 -> cai   se preco <  base-B  ; inverte se preco >  base+2B
  o tick que dispara pertence a barra seguinte
  alta:  h=c, l=min(minima real, o)   |   baixa: l=c, h=max(maxima real, o)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

B = 50.0
TICK = 5.0


def caminho(n_ticks: int, seed: int = 0, deriva: float = 0.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    passos = rng.choice([-TICK, TICK], size=n_ticks) + deriva
    return 100000.0 + np.cumsum(passos)


def renko(preco: np.ndarray, brick: float = B) -> pd.DataFrame:
    base = np.floor(preco[0] / brick) * brick
    dirn = 1
    o = h = l = None
    barras = []
    hi = lo = preco[0]
    aberto = False
    for px in preco:
        if not aberto:
            hi = lo = px
            aberto = True
        else:
            if px > hi:
                hi = px
            if px < lo:
                lo = px
        while True:
            teto = base + brick if dirn > 0 else base + 2 * brick
            piso = base - 2 * brick if dirn > 0 else base - brick
            if px > teto:
                ab, fe = teto - brick, teto
                base, dirn = teto, 1
                barras.append((ab, fe, fe, min(lo, ab), 1))
            elif px < piso:
                ab, fe = piso + brick, piso
                base, dirn = piso, -1
                barras.append((ab, fe, max(hi, ab), fe, -1))
            else:
                break
            hi = lo = px
    return pd.DataFrame(barras, columns=["o", "c", "h", "l", "dir"])


def metricas(d: pd.DataFrame, h: int = 4) -> pd.DataFrame:
    d = d.copy()
    d["risco"] = np.where(d.dir < 0, d.h - d.c, d.c - d.l)
    d["cont"] = (d.dir.shift(-1) == d.dir).astype(float)
    fmaxh = d.h.shift(-1).rolling(h, min_periods=h).max().shift(-(h - 1))
    fminl = d.l.shift(-1).rolling(h, min_periods=h).min().shift(-(h - 1))
    d["ok"] = np.where(d.dir < 0, (fmaxh <= d.h).astype(float), (fminl >= d.l).astype(float))
    d.loc[fmaxh.isna(), "ok"] = np.nan
    d["net_fav"] = d.dir * (d.c.shift(-h) - d.c) / B
    d["mfe"] = np.where(d.dir < 0, d.c - fminl, fmaxh - d.c)
    d["pnl"] = np.where(d.ok == 1, d.net_fav * B, -d.risco)
    d["R"] = d.pnl / d.risco
    return d.dropna(subset=["ok"])


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    d = metricas(renko(caminho(40_000_000, seed=7)))
    print(f"tijolos sinteticos: {len(d)}")
    print(f"P(continuacao) = {d.cont.mean():.4f}   (teorico 2/3 = {2/3:.4f})")
    print(f"P(ok 4 tijolos) = {d.ok.mean():.4f}")
    print(f"R medio = {d.R.mean():+.4f}   pnl medio = {d.pnl.mean():+.3f} pts")
    faixa = pd.cut(d.risco, [49, 55, 70, 95, 125, 151])
    print("\npor pavio contrario:")
    print(d.groupby(faixa, observed=True).agg(n=("ok", "size"), P_cont=("cont", "mean"),
                                              ok=("ok", "mean"), R=("R", "mean")).round(4).to_string())
    print("\ndistribuicao do pavio contrario (%):")
    print((d.groupby(faixa, observed=True).size() / len(d) * 100).round(2).to_string())
    d.to_pickle("sintetico.pkl")
