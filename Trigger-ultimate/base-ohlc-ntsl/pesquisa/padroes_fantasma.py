"""O ultimo filtro de realidade: o tijolo fantasma no caminho.

Foi o que derrubou o "edge de momentum" na primeira rodada. Aplica aqui aos
candidatos do estudo de padroes: um sinal cujo alvo so foi alcancado porque um
tijolo fechou sem tempo e sem volume nao teve execucao possivel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from padroes import bases, condicoes, G, B
from padroes_valida import CANDIDATOS, boot_dia
from alvo import preparar_geo
from dados import carregar

H = 8


def com_fantasma(g=G, h=H) -> pd.DataFrame:
    real = carregar()
    real = real[(real.c - real.o).abs() == B].reset_index(drop=True)
    d = preparar_geo(real, g, h)
    dur = d["dur"].to_numpy(float)
    qtd = d["qtd"].to_numpy(float)
    n = len(d)
    ate = d["ate"].to_numpy(float)
    fant = np.zeros(n)
    for i in range(n - h):
        k = int(ate[i]) if not np.isnan(ate[i]) else h
        f = slice(i + 1, i + k + 1)
        fant[i] = float(((dur[f] == 0) | (qtd[f] == 0)).any())
    d["fant_caminho"] = fant
    return d[(d.virou == 1) & d.alvo.notna() & (d.dur > 0) & (d.qtd > 0)].copy()


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    r = com_fantasma().reset_index(drop=True)
    _, s = bases()
    nd = r.dia.nunique()
    Cr = condicoes(r)

    print(f"sinais: {len(r)}  |  com fantasma no caminho ate o desfecho: "
          f"{r.fant_caminho.mean():.1%}")

    linhas = []
    for nome, m in ([("TODAS as reversoes", np.ones(len(r), bool))]
                    + [(c, np.logical_and.reduce([Cr[n].to_numpy() for n in c.split(" & ")]))
                       for c in CANDIDATOS]
                    + [("pav<=110", Cr["pav<=110"].to_numpy()),
                       ("dext50<=0.5", Cr["dext50<=0.5"].to_numpy())]):
        a = r[m]
        lim = a[a.fant_caminho == 0]
        lo, hi = boot_dia(lim, "pts") if len(lim) > 100 else (np.nan, np.nan)
        linhas.append(dict(regra=nome, n=len(a), por_dia=len(a) / nd,
                           P=a.alvo.mean(), pts=a.pts.mean(),
                           fant=a.fant_caminho.mean(),
                           n_limpo=len(lim), P_limpo=lim.alvo.mean(),
                           pts_limpo=lim.pts.mean(), ic_lo=lo, ic_hi=hi))
    t = pd.DataFrame(linhas).set_index("regra")
    print("\n=== antes e depois de descartar caminhos com tijolo fantasma ===")
    print(t.round(4).to_string())
    print(f"\nbreakeven do alvo {G:.0f}/{B:.0f} = {B/(G+B):.4f}")
    print("pts_limpo e o unico numero executavel. ic = bootstrap de pregao sobre ele.")
