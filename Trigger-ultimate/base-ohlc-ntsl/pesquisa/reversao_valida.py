"""Validacao da unica regra que sobreviveu: reversao + agressao a favor.

Achado bruto: nas reversoes, a_favor = dir*imb > 0.15 rende ~6-9 pts/sinal em
treino E teste, e continua positivo depois de descartar caminhos com tijolo
fantasma. Antes de acreditar, quatro controles:

  1  POR LADO. O indice caiu 3.825 pts nos 35 pregoes. Numa reversao de baixa,
     a_favor>0 e agressao vendedora -- pode ser so a deriva. Se o efeito existe
     so no lado vendido, e deriva, nao regra.
  2  DERIVA NEUTRALIZADA. O efeito medido como excesso sobre a media do proprio
     lado no mesmo periodo.
  3  PERMUTACAO. Embaralha a_favor DENTRO de cada pregao (preserva a deriva, o
     numero de sinais e a estrutura do dia) e ve onde cai o valor observado.
  4  WALK-FORWARD por blocos de pregao: o efeito aparece em quantas dobras?
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from reversao_regra import montar, rev, boot_dia

LIMIAR = 0.15


def excesso(x: pd.DataFrame, col_pnl: str, limiar=LIMIAR) -> float:
    """pnl da regra - pnl de todas as reversoes, dentro do mesmo lado e periodo."""
    tot = 0.0
    peso = 0
    for _, g in x.groupby("lado"):
        m = g.a_favor > limiar
        if m.sum() < 20:
            continue
        tot += (g[m][col_pnl].mean() - g[col_pnl].mean()) * m.sum()
        peso += m.sum()
    return tot / peso if peso else np.nan


def permutar(x: pd.DataFrame, col_pnl: str, n=3000, limiar=LIMIAR, seed=0):
    """Embaralha a_favor dentro do pregao; preserva deriva e composicao do dia."""
    rng = np.random.default_rng(seed)
    obs = excesso(x, col_pnl, limiar)
    nulo = np.empty(n)
    grupos = [g.copy() for _, g in x.groupby(["dia", "lado"])]
    for i in range(n):
        for g in grupos:
            g["a_favor"] = rng.permutation(g["a_favor"].to_numpy())
        nulo[i] = excesso(pd.concat(grupos), col_pnl, limiar)
    p = (nulo >= obs).mean()
    return obs, nulo, p


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    d = montar()
    r = rev(d)
    r["lado"] = r["dir"]

    print("=" * 84)
    print("CONTROLE 1 -- por lado (a deriva mora aqui)")
    print("=" * 84)
    dias = np.sort(r.dia.unique())
    corte = dias[int(len(dias) * 0.6)]
    for col_pnl, col_ok, tag in (("pnl", "ok", "stop no pavio"),
                                 ("pnl_ab", "ok_ab", "stop na abertura")):
        print(f"\n--- {tag} ---")
        linhas = []
        for lado, nome in ((-1, "BAIXA (vende)"), (1, "ALTA (compra)")):
            s = r[r.lado == lado]
            for rot, m in (("todas", np.ones(len(s), bool)),
                           (f"a_favor>{LIMIAR}", (s.a_favor > LIMIAR).to_numpy())):
                a = s[m]
                lo, hi = boot_dia(a, col_pnl)
                lim = a[a.fant_caminho == 0]
                linhas.append(dict(lado=nome, regra=rot, n=len(a),
                                   ok=a[col_ok].mean(), pnl=a[col_pnl].mean(),
                                   ic_lo=lo, ic_hi=hi, pnl_limpo=lim[col_pnl].mean(),
                                   pnl_tr=a[a.dia < corte][col_pnl].mean(),
                                   pnl_te=a[a.dia >= corte][col_pnl].mean()))
        print(pd.DataFrame(linhas).set_index(["lado", "regra"]).round(3).to_string())

    print("\n" + "=" * 84)
    print("CONTROLE 2+3 -- excesso sobre o proprio lado, contra permutacao intra-pregao")
    print("=" * 84)
    for col_pnl, tag in (("pnl", "stop no pavio"), ("pnl_ab", "stop na abertura")):
        for base, rot in ((r, "todos os sinais"), (r[r.fant_caminho == 0], "so caminho limpo")):
            obs, nulo, p = permutar(base, col_pnl, n=1500)
            z = (obs - nulo.mean()) / nulo.std()
            print(f"  {tag:<18} {rot:<18} excesso = {obs:+6.2f} pts   "
                  f"nulo {nulo.mean():+.2f}+-{nulo.std():.2f}   z = {z:+5.2f}   p = {p:.4f}")

    print("\n" + "=" * 84)
    print("CONTROLE 4 -- walk-forward por blocos de pregao")
    print("=" * 84)
    blocos = np.array_split(dias, 5)
    for col_pnl, tag in (("pnl", "stop no pavio"), ("pnl_ab", "stop na abertura")):
        print(f"\n--- {tag} ---")
        linhas = []
        for k, b in enumerate(blocos, 1):
            s = r[r.dia.isin(b)]
            m = s.a_favor > LIMIAR
            lim = s[(m) & (s.fant_caminho == 0)]
            linhas.append(dict(dobra=k, pregoes=len(b), n=int(m.sum()),
                               pnl_regra=s[m][col_pnl].mean(),
                               pnl_todas=s[col_pnl].mean(),
                               excesso=excesso(s, col_pnl),
                               pnl_limpo=lim[col_pnl].mean()))
        t = pd.DataFrame(linhas).set_index("dobra")
        print(t.round(3).to_string())
        print(f"  dobras com excesso > 0: {(t.excesso > 0).sum()}/5   "
              f"com pnl_limpo > 0: {(t.pnl_limpo > 0).sum()}/5")

    print("\n" + "=" * 84)
    print("CONTROLE 5 -- sensibilidade ao limiar (efeito suave ou cliff?)")
    print("=" * 84)
    linhas = []
    for th in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35):
        m = r.a_favor > th
        if m.sum() < 100:
            continue
        lim = r[m & (r.fant_caminho == 0)]
        linhas.append(dict(limiar=th, n=int(m.sum()), n_dia=m.sum() / r.dia.nunique(),
                           ok=r[m].ok.mean(), pnl=r[m].pnl.mean(),
                           pnl_limpo=lim.pnl.mean(), exc=excesso(r, "pnl", th),
                           ok_ab=r[m].ok_ab.mean(), pnl_ab=r[m].pnl_ab.mean(),
                           pnl_ab_limpo=lim.pnl_ab.mean()))
    print(pd.DataFrame(linhas).set_index("limiar").round(3).to_string())
