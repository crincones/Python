"""Calibracao do modo REVERSAO, para ir embutida no .ntsl.

Duas ancoras de stop, medidas na base real e no passeio aleatorio:
    pavio     -- o extremo contrario do tijolo (o criterio original). Nas
                 reversoes fica a ~125 pts: caro.
    abertura  -- a abertura do tijolo de reversao, sempre a 50 pts do
                 fechamento. E o nivel que, perdido, desfaz a reversao.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from reversao_regra import montar, rev
from ml_lift import limpar

FAIXAS = [(95, 110), (115, 130), (135, 145), (150, 150)]
NOMES = ["95-110", "115-130", "135-145", "150"]
B = 50.0
H = 4


def sint():
    """Renko sintetico com as duas ancoras de stop."""
    s = pd.read_pickle("sintetico.pkl").reset_index(drop=True)
    h, l, c, o, dirn = (s[k].to_numpy(float) for k in ("h", "l", "c", "o", "dir"))
    n = len(s)
    okab = np.full(n, np.nan)
    for i in range(n - H):
        f = slice(i + 1, i + H + 1)
        okab[i] = float(h[f].max() <= o[i]) if dirn[i] < 0 else float(l[f].min() >= o[i])
    s["ok_ab"] = okab
    s["net"] = s.net_fav * B
    s["pnl_ab"] = np.where(s.ok_ab == 1, s.net, -B)
    s["R_ab"] = s.pnl_ab / B
    s["rev"] = (s.dir != s.dir.shift(1)).astype(int)
    return s.dropna(subset=["ok_ab"]).iloc[1:]


def tab(x, cols) -> pd.DataFrame:
    linhas = []
    for (lo, hi), nome in zip(FAIXAS, NOMES):
        g = x[(x.risco >= lo) & (x.risco <= hi)]
        if len(g) < 50:
            continue
        linhas.append(dict(faixa=nome, n=len(g), **{k: g[k].mean() for k in cols}))
    return pd.DataFrame(linhas).set_index("faixa")


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    d = montar()
    r = rev(d)
    nd = r.dia.nunique()
    s = sint()
    sr = s[s.rev == 1]

    print("=" * 92)
    print("CALIBRACAO -- so reversoes, base real")
    print("=" * 92)
    t = tab(r, ["ok", "ok_ab", "risco", "mfe", "pnl", "pnl_ab", "R", "R_ab"])
    t["sinais_dia"] = [len(r[(r.risco >= lo) & (r.risco <= hi)]) / nd
                       for (lo, hi), nm in zip(FAIXAS, NOMES) if nm in t.index]
    print(t.round(4).to_string())

    print("\n=== a mesma coisa no passeio aleatorio (a regua) ===")
    ts = tab(sr, ["ok", "ok_ab", "risco", "mfe", "R", "R_ab"])
    print(ts.round(4).to_string())
    print("\n=== lift real - acaso ===")
    print(pd.DataFrame({"d_ok": t.ok - ts.ok, "d_ok_ab": t.ok_ab - ts.ok_ab,
                        "d_R": t.R - ts.R, "d_R_ab": t.R_ab - ts.R_ab}).round(4).to_string())

    print("\n" + "=" * 92)
    print("AJUSTE para o .ntsl (u = pavio/tijolo)")
    print("=" * 92)
    u = (r.risco / B).to_numpy(float)
    for alvo, nome in ((r.ok.to_numpy(float), "ok  (stop no pavio)"),
                       (r.ok_ab.to_numpy(float), "ok_ab (stop na abertura)")):
        a, b = np.polyfit(u, alvo, 1)
        print(f"  {nome:<26} P = {b:.4f} + {a:.4f}*u     media = {alvo.mean():.4f}")
    print(f"  MFE medio nas reversoes    = {r.mfe.mean():.1f} pts "
          f"({r.mfe.mean()/B:.2f} tijolos)   |  no acaso = {sr.mfe.mean():.1f} pts")
    print(f"  sinais de reversao por pregao = {len(r)/nd:.1f}  (em {nd} pregoes)")

    print("\n=== fantasma no caminho ===")
    for nome, x in (("reversoes", r), ("continuacoes", limpar(d[d.virou == 0]))):
        f = x.fant_caminho.mean()
        print(f"  {nome:<14} {f:.3%} dos sinais   "
              f"pnl {x.pnl.mean():+6.2f} -> limpo {x[x.fant_caminho==0].pnl.mean():+6.2f}   |  "
              f"pnl_ab {x.pnl_ab.mean():+6.2f} -> limpo {x[x.fant_caminho==0].pnl_ab.mean():+6.2f}")
