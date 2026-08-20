"""Varredura de regras sobre a probabilidade de CONTINUACAO do Renko.

Por que continuacao: no Renko 11R, continuar custa 50 pts e inverter custa 100.
Num passeio aleatorio, P(cont) = 100/150 = 2/3 = 0.6667 -- esse e o ponto de
equilibrio. Ir a favor do tijolo so tem esperanca positiva se P(cont) > 2/3;
ir contra, se P(cont) < 2/3.

    E[pontos] = 50*P - 100*(1-P) = 150*P - 100

Aqui procuramos condicoes, computaveis em NTSL, em que P(cont) se afasta de 2/3
de forma que se sustente FORA DA AMOSTRA (treino nos primeiros 60% dos pregoes,
teste nos 40% finais).
"""

from __future__ import annotations

import itertools
import numpy as np
import pandas as pd

from dados import carregar
from features import preparar

BREAKEVEN = 2.0 / 3.0


def base(h: int = 4) -> pd.DataFrame:
    d = preparar(carregar())
    d = d[(d.c - d.o).abs() == 50].copy()
    d["risco"] = np.where(d.dir < 0, d.h - d.c, d.c - d.l)
    d["prox"] = d["dir"].shift(-1)
    d["cont"] = (d["prox"] == d["dir"]).astype(float)
    # continuacao acumulada: tijolos liquidos a favor nos proximos h
    d["net_fav"] = d["dir"] * (d["c"].shift(-h) - d["c"]) / 50.0
    # esperanca por tijolo se seguir o sentido
    d["pts_fav"] = np.where(d["cont"] == 1, 50.0, -100.0)
    # aceleracao / comparacoes com o tijolo anterior
    d["dur_ant"] = d["dur_s"].shift(1)
    d["acel"] = d["dur_s"] / (d["dur_ant"] + 1.0)
    d["qtd_ant"] = d["qtd"].shift(1)
    d["rel_qtd"] = d["qtd"] / (d["qtd_ant"] + 1.0)
    d["contra"] = -d["dir"] * d["imb"]              # >0 = agressao contra o tijolo
    d["contra3"] = -d["dir"] * d["imb3"]
    d["favor"] = d["dir"] * d["imb"]
    d["pavio_vol"] = d["risco"] / (d["r_qtd"] + 0.01)
    d["ret_dia"] = d["dir"] * d["cdelta_dia"] / (d["qtd"].rolling(50).mean() * 50 + 1)
    d = d[(d.fantasma == 0) & (d.agr > 0)].copy()
    return d.dropna(subset=["cont"])


def split(d, frac=0.6):
    dias = np.sort(d.dia.unique())
    corte = dias[int(len(dias) * frac)]
    return d[d.dia < corte].copy(), d[d.dia >= corte].copy(), pd.Timestamp(corte)


def esperanca(p):
    return 150.0 * p - 100.0


def avalia(mask_tr, tr, mask_te, te, nome, min_n=150):
    ntr, nte = int(mask_tr.sum()), int(mask_te.sum())
    if ntr < min_n or nte < min_n // 2:
        return None
    ptr = tr.loc[mask_tr, "cont"].mean()
    pte = te.loc[mask_te, "cont"].mean()
    return dict(
        regra=nome, n_tr=ntr, P_tr=ptr, E_tr=esperanca(ptr),
        n_te=nte, P_te=pte, E_te=esperanca(pte),
        net_te=te.loc[mask_te, "net_fav"].mean(),
        freq=nte / te.dia.nunique(),
    )


# ---- condicoes elementares, todas replicaveis em NTSL ---------------------
def condicoes(d: pd.DataFrame) -> dict:
    q = lambda c, p: d[c].quantile(p)
    C = {}
    C["contra>0"] = d.contra > 0
    C["contra>.15"] = d.contra > 0.15
    C["contra<-.4"] = d.contra < -0.4
    C["contra<-.6"] = d.contra < -0.6
    C["contra3>0"] = d.contra3 > 0
    C["contra3<-.3"] = d.contra3 < -0.3
    C["pavio=50"] = d.risco <= 50
    C["pavio<=65"] = d.risco <= 65
    C["pavio>=115"] = d.risco >= 115
    C["seq=1"] = d.seq == 1
    C["seq>=3"] = d.seq >= 3
    C["seq>=5"] = d.seq >= 5
    C["rqtd>1.5"] = d.r_qtd > 1.5
    C["rqtd<0.6"] = d.r_qtd < 0.6
    C["rdur>1.5"] = d.r_dur_s > 1.5
    C["rdur<0.6"] = d.r_dur_s < 0.6
    C["rtam>1.3"] = d.r_tam > 1.3
    C["rtam<0.8"] = d.r_tam < 0.8
    C["part>.85"] = d.part > 0.85
    C["part<.70"] = d.part < 0.70
    C["vel_alta"] = d.vel > q("vel", 0.75)
    C["vel_baixa"] = d.vel < q("vel", 0.25)
    C["acel>2"] = d.acel > 2
    C["acel<0.5"] = d.acel < 0.5
    C["relqtd>2"] = d.rel_qtd > 2
    C["relqtd<0.5"] = d.rel_qtd < 0.5
    C["tend5>0"] = d.dir * d.net5 > 0
    C["tend5forte"] = d.dir * d.net5 >= 3
    C["contra_tend5"] = d.dir * d.net5 <= -3
    C["viradas5>=3"] = d.viradas5 >= 3
    C["viradas5<=1"] = d.viradas5 <= 1
    C["manha"] = d.hora < 12
    C["tarde"] = d.hora >= 14
    C["abertura"] = d.nbar_dia < 30
    C["cdelta_fav"] = d.dir * d.cdelta5 > 0
    C["cdelta_ctr"] = d.dir * d.cdelta5 < 0
    C["cimb20_fav"] = d.dir * d.cimb20 > 0.15
    C["cimb20_ctr"] = d.dir * d.cimb20 < -0.15
    return C


def varrer(k=2, min_n=150):
    d = base()
    tr, te, corte = split(d)
    print(f"corte: {corte.date()}   treino n={len(tr)} P={tr.cont.mean():.4f}   "
          f"teste n={len(te)} P={te.cont.mean():.4f}   breakeven={BREAKEVEN:.4f}")
    Ctr, Cte = condicoes(tr), condicoes(te)
    nomes = list(Ctr)
    linhas = []
    for r in range(1, k + 1):
        for combo in itertools.combinations(nomes, r):
            mtr = np.logical_and.reduce([Ctr[c] for c in combo])
            mte = np.logical_and.reduce([Cte[c] for c in combo])
            res = avalia(mtr, tr, mte, te, " & ".join(combo), min_n)
            if res:
                linhas.append(res)
    return pd.DataFrame(linhas), tr, te


if __name__ == "__main__":
    pd.set_option("display.width", 240)
    t, tr, te = varrer(k=2)
    t["desvio_tr"] = t.P_tr - BREAKEVEN
    t["desvio_te"] = t.P_te - BREAKEVEN
    t["consist"] = np.sign(t.desvio_tr) == np.sign(t.desvio_te)
    print(f"\n{len(t)} regras avaliadas")
    print("\n===== TREINO aponta CONTINUACAO (P_tr alto) — top 15 por P_tr =====")
    print(t.nlargest(15, "P_tr")[["regra", "n_tr", "P_tr", "n_te", "P_te", "E_te", "freq", "consist"]].round(4).to_string(index=False))
    print("\n===== TREINO aponta REVERSAO (P_tr baixo) — top 15 =====")
    print(t.nsmallest(15, "P_tr")[["regra", "n_tr", "P_tr", "n_te", "P_te", "E_te", "freq", "consist"]].round(4).to_string(index=False))
    print("\n===== consistencia geral: quanto do desvio do treino sobrevive =====")
    sel = t[t.n_tr >= 300]
    print("correlacao desvio_tr x desvio_te:", round(np.corrcoef(sel.desvio_tr, sel.desvio_te)[0, 1], 4),
          " | mesmo sinal:", round(sel.consist.mean(), 4), f"(n={len(sel)})")
