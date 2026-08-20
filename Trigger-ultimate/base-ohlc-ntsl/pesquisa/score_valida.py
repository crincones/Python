"""Validacao do score de agressao com o alvo em pontos.

A curva "so agressao" e a unica monotonica e com treino E teste positivos.
Mas e o MESMO efeito que ja falhou em p=0.10 na secao 6 -- reencontra-lo com
outro alvo nao e evidencia nova, e a mesma amostra. Aqui ele leva os testes
que decidem:

  1  bootstrap de PREGAO sobre pts/sinal (sinais do mesmo dia andam juntos)
  2  permutacao de aFavor DENTRO do pregao (preserva deriva e composicao)
  3  walk-forward em 5 blocos
  4  por lado, para separar padrao de deriva
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from score import carregar_real, pontuar, espacar, G, B

LIMIARES = (50, 60, 70, 80)
PESOS_AGR = dict(cAgr=100)


def boot_dia(x, col, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    g = [v[col].to_numpy(float) for _, v in x.groupby("dia")]
    if len(g) < 5:
        return np.nan, np.nan
    m = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(g), len(g))
        m[i] = np.concatenate([g[j] for j in pick]).mean()
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def permutar(x, ms, n=2000, seed=0):
    """Embaralha aFavor dentro de (pregao, lado) e refaz o corte do score."""
    rng = np.random.default_rng(seed)
    from score import rampa
    obs = x[pontuar(x, PESOS_AGR) >= ms].pts.mean()
    grupos = [g.copy() for _, g in x.groupby(["dia", "dir"])]
    nulo = np.empty(n)
    for i in range(n):
        for g in grupos:
            g["aFavor"] = rng.permutation(g["aFavor"].to_numpy())
        z = pd.concat(grupos)
        z["cAgr"] = rampa(z.aFavor, 0.0, 0.30)
        sel = z[pontuar(z, PESOS_AGR) >= ms]
        nulo[i] = sel.pts.mean() if len(sel) > 30 else np.nan
    nulo = nulo[~np.isnan(nulo)]
    return obs, nulo, (nulo >= obs).mean()


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    r = carregar_real()
    lim = r[r.fant_caminho == 0].copy()
    nd = r.dia.nunique()
    lim["score"] = pontuar(lim, PESOS_AGR)
    dias = np.sort(lim.dia.unique())
    blocos = np.array_split(dias, 5)

    print(f"universo limpo: {len(lim)} sinais ({len(lim)/nd:.1f}/pregao)  "
          f"pts base {lim.pts.mean():+.2f}  breakeven P={B/(G+B):.4f}")

    print("\n" + "=" * 88)
    print("1+3+4 -- bootstrap de pregao, walk-forward e lados")
    print("=" * 88)
    linhas = []
    for ms in LIMIARES:
        a = lim[lim.score >= ms]
        lo, hi = boot_dia(a, "pts")
        dn_, up_ = a[a.dir < 0], a[a.dir > 0]
        wf = [a[a.dia.isin(b)].pts.mean() for b in blocos]
        linhas.append(dict(MinScore=ms, n=len(a), por_dia=len(a) / nd,
                           P=a.alvo.mean(), pts=a.pts.mean(),
                           ic_lo=lo, ic_hi=hi,
                           pts_baixa=dn_.pts.mean(), pts_alta=up_.pts.mean(),
                           dobras_pos=int(np.sum(np.array(wf) > 0)),
                           pior_dobra=np.nanmin(wf)))
    print(pd.DataFrame(linhas).set_index("MinScore").round(3).to_string())

    print("\n" + "=" * 88)
    print("2 -- permutacao de aFavor dentro do pregao")
    print("=" * 88)
    for ms in LIMIARES:
        obs, nulo, p = permutar(lim, ms, n=1200)
        z = (obs - nulo.mean()) / nulo.std()
        print(f"  MinScore={ms:<3} pts obs {obs:+6.2f}   nulo {nulo.mean():+.2f} "
              f"+- {nulo.std():.2f}   z = {z:+5.2f}   p = {p:.4f}")

    print("\n" + "=" * 88)
    print("SUGESTAO DE OPERACAO (score de agressao + espacamento)")
    print("=" * 88)
    linhas = []
    for ms in (50, 60, 70):
        for mb in (0, 4):
            a = lim[lim.score >= ms]
            a = a[espacar(a, mb)]
            lo, hi = boot_dia(a, "pts")
            linhas.append(dict(MinScore=ms, MinBarras=mb, n=len(a),
                               por_dia=len(a) / nd, P=a.alvo.mean(),
                               pts=a.pts.mean(), ic_lo=lo, ic_hi=hi))
    print(pd.DataFrame(linhas).set_index(["MinScore", "MinBarras"]).round(3).to_string())
