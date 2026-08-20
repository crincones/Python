"""Varredura de padroes dos tijolos ANTERIORES a reversao.

Todas as condicoes sao geometricas e sao aplicadas IDENTICAMENTE na base real e
no Renko sintetico de passeio aleatorio (181.822 tijolos). Assim cada regra tem
sua propria hipotese nula, com n grande:

    lift = P(alvo | condicao)_real  -  P(alvo | condicao)_acaso

Uma regra so interessa se (a) o lift for positivo e (b) sobreviver na metade
final dos pregoes, que nao foi usada para escolher nada.

Alvo: +G pontos antes de perder a abertura do tijolo de reversao (50 pts),
em ate H tijolos, com a ordem de eventos no pior caso (ver alvo.py).
"""

from __future__ import annotations

import itertools
import numpy as np
import pandas as pd

from alvo import preparar_geo, B
from dados import carregar

G, H = 100.0, 8


def bases(g=G, h=H):
    real = carregar()
    real = real[(real.c - real.o).abs() == B].reset_index(drop=True)
    r = preparar_geo(real, g, h)
    r = r[(r.virou == 1) & r.alvo.notna() & (r.dur > 0) & (r.qtd > 0)].copy()

    s = pd.read_pickle("sintetico.pkl").reset_index(drop=True)
    s["dir"] = s["dir"].astype(int)
    s = preparar_geo(s, g, h)
    s = s[(s.virou == 1) & s.alvo.notna()].copy()
    return r, s


def condicoes(x: pd.DataFrame) -> dict:
    """Condicoes elementares, todas replicaveis em NTSL com OHLC puro."""
    c = {}
    # --- a perna que foi quebrada
    c["perna>=3"] = x.perna >= 3
    c["perna>=4"] = x.perna >= 4
    c["perna>=5"] = x.perna >= 5
    c["perna<=2"] = x.perna <= 2
    c["pernapts>=200"] = x.perna_pts >= 200
    c["pernapts>=300"] = x.perna_pts >= 300
    # perna limpa = tendencia sem repique antes de quebrar
    c["pernapav<=70"] = x.perna_pav <= 70
    c["pernapav<=60"] = x.perna_pav <= 60
    c["pernapav>=90"] = x.perna_pav >= 90
    # --- o proprio tijolo de reversao
    c["pav<=110"] = x.pav <= 110
    c["pav>=130"] = x.pav >= 130
    c["pav=150"] = x.pav >= 150
    # --- os tijolos imediatamente anteriores
    c["pav1<=70"] = x.pav1 <= 70
    c["pav1>=110"] = x.pav1 >= 110
    c["pav2<=70"] = x.pav2 <= 70
    c["pav2>=110"] = x.pav2 >= 110
    # --- estrutura recente
    c["efic20>=0.5"] = x.efic20 >= 0.5
    c["efic20<=0.25"] = x.efic20 <= 0.25
    c["efic50>=0.5"] = x.efic50 >= 0.5
    c["efic50<=0.25"] = x.efic50 <= 0.25
    c["vira20<=5"] = x.viradas20 <= 5
    c["vira20>=9"] = x.viradas20 >= 9
    c["vira50<=14"] = x.viradas50 <= 14
    c["vira50>=22"] = x.viradas50 >= 22
    c["amp20>=500"] = x.amp20 >= 500
    c["amp20<=300"] = x.amp20 <= 300
    # --- onde a reversao acontece
    c["dext20<=0.5"] = x.dext20 <= 0.5      # bem no topo/fundo de 20
    c["dext20>=2"] = x.dext20 >= 2          # no meio do range
    c["dext50<=0.5"] = x.dext50 <= 0.5
    c["dext50>=3"] = x.dext50 >= 3
    c["furo>=0"] = x.furo >= 0              # furou o extremo de 20 e voltou
    c["furo<=-1"] = x.furo <= -1
    c["pos20<=0.2"] = x.pos20 <= 0.2
    c["pos20>=0.8"] = x.pos20 >= 0.8
    c["pos50<=0.2"] = x.pos50 <= 0.2
    c["pos50>=0.8"] = x.pos50 >= 0.8
    return c


def split(x, frac=0.6):
    dias = np.sort(x.dia.unique())
    corte = dias[int(len(dias) * frac)]
    return x[x.dia < corte], x[x.dia >= corte], corte


def varrer(r, s, kmax=2, min_te=80, min_ac=300):
    Cr, Cs = condicoes(r), condicoes(s)
    tr, te, corte = split(r)
    Ctr, Cte = condicoes(tr), condicoes(te)
    linhas = []
    nomes = list(Cr)
    for k in range(1, kmax + 1):
        for combo in itertools.combinations(nomes, k):
            mr = np.logical_and.reduce([Cr[n].to_numpy() for n in combo])
            ms = np.logical_and.reduce([Cs[n].to_numpy() for n in combo])
            mt = np.logical_and.reduce([Ctr[n].to_numpy() for n in combo])
            mv = np.logical_and.reduce([Cte[n].to_numpy() for n in combo])
            if mv.sum() < min_te or ms.sum() < min_ac or mt.sum() < 100:
                continue
            a, b = r[mr], s[ms]
            linhas.append(dict(
                regra=" & ".join(combo), n=len(a), por_dia=len(a) / r.dia.nunique(),
                p=a.alvo.mean(), p_acaso=b.alvo.mean(),
                lift=a.alvo.mean() - b.alvo.mean(),
                pts=a.pts.mean(), pts_acaso=b.pts.mean(),
                n_tr=int(mt.sum()), p_tr=tr[mt].alvo.mean(),
                n_te=int(mv.sum()), p_te=te[mv].alvo.mean(),
                pts_te=te[mv].pts.mean()))
    return pd.DataFrame(linhas), corte


if __name__ == "__main__":
    pd.set_option("display.width", 260)
    r, s = bases()
    nd = r.dia.nunique()
    print(f"reversoes executaveis: real {len(r)} ({len(r)/nd:.1f}/pregao) | "
          f"acaso {len(s)}")
    print(f"base: P(alvo) real {r.alvo.mean():.4f}  acaso {s.alvo.mean():.4f}  "
          f"breakeven {B/(G+B):.4f}   pts/sinal real {r.pts.mean():+.2f}")

    t, corte = varrer(r, s)
    print(f"\n{len(t)} regras varridas | corte treino/teste {pd.Timestamp(corte).date()}")

    cols = ["regra", "n", "por_dia", "p", "p_acaso", "lift", "pts", "n_te", "p_te", "pts_te"]
    print("\n=== top 15 por LIFT sobre o acaso (amostra inteira) ===")
    print(t.nlargest(15, "lift")[cols].round(4).to_string(index=False))

    print("\n=== top 15 por pts/sinal no TESTE (metade final, nao usada) ===")
    print(t.nlargest(15, "pts_te")[cols].round(4).to_string(index=False))

    print("\n=== controle por lado: a regra tem que valer nas duas pontas ===")
    top = t.nlargest(10, "lift").regra.tolist()
    Cr = condicoes(r)
    linhas = []
    for regra in top:
        m = np.logical_and.reduce([Cr[n].to_numpy() for n in regra.split(" & ")])
        a = r[m]
        dn_, up_ = a[a.dir < 0], a[a.dir > 0]
        linhas.append(dict(regra=regra, n_baixa=len(dn_), p_baixa=dn_.alvo.mean(),
                           pts_baixa=dn_.pts.mean(), n_alta=len(up_),
                           p_alta=up_.alvo.mean(), pts_alta=up_.pts.mean()))
    print(pd.DataFrame(linhas).round(4).to_string(index=False))

    print("\n>>> o lift do treino sobrevive no teste?")
    t["lift_tr"] = t.p_tr - t.p_acaso
    t["lift_te"] = t.p_te - t.p_acaso
    print("   correlacao lift_tr x lift_te :", round(np.corrcoef(t.lift_tr, t.lift_te)[0, 1], 4))
    print("   mesmo sinal                  :", round((np.sign(t.lift_tr) == np.sign(t.lift_te)).mean(), 4))
    print("   regras com lift > 0 na amostra inteira:", int((t.lift > 0).sum()), "de", len(t))
    t.to_csv("padroes.csv", index=False)
