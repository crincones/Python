"""Espelho em Python da logica EXATA do TriggerUltimate.ntsl (versao score).

Qualquer mudanca de regra deve ser feita aqui e no .ntsl juntas.

Diferenca conhecida e irrelevante: em alvo.py o componente `furo` usa janela de
20 barras e no .ntsl usa JanelaExtremo (50). PesoFuro e 0 por padrao -- e a
medicao diz que ele aponta para o lado errado de qualquer jeito -- entao nao
afeta nenhum preset.

--- criterio "andamento em pontos" (AlvoPontos > 0) ---
alcancar +G pts antes de violar a ancora, em ate H tijolos, ordem de eventos no
pior caso. Probabilidade de referencia = passeio aleatorio com a mesma
geometria, com j = risco/(G+risco):

    P = j * (1.1894 - 0.187*j)

    G= 50 -> 0.548 previsto / 0.548 sintetico  |  G=100 -> 0.376 / 0.378
    G=150 -> 0.286 / 0.286                     |  G=200 -> 0.230 / 0.230

--- criterio "extremo sobrevive" (AlvoPontos = 0) ---
    Ancora=1: P = 0.3623 constante, R = 2.2
    Ancora=0: P = 0.2422 + 0.1465*u (u<3) | 0.7940 (u=3), R = 2.2/u
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from score import carregar_real, pontuar, espacar, COMPS, G, B

MFE_TIJOLOS = 2.2
P_ABERTURA = 0.3623


def prob_alvo(risco, alvo):
    j = risco / (alvo + risco)
    return j * (1.1894 - 0.187 * j)


def rodar(d: pd.DataFrame, pesos, min_score=60.0, min_barras=0, reversao=1,
          ancora=1, alvo=G, tijolo=B, pavio_maximo=0.0) -> dict:
    """`alvo` so ajusta a probabilidade de referencia; o desfecho vem
    pre-simulado em carregar_real() com G=100. Para outro alvo, regere a base
    com preparar_geo(real, G_novo, H_novo)."""
    x = d.copy()
    x["score"] = pontuar(x, pesos)
    m = x.score >= min_score
    if reversao == 1:
        m &= x.virou == 1
    if reversao == 2:
        m &= x.virou == 0
    if pavio_maximo > 0:
        m &= x.pav <= pavio_maximo
    x = x[m]
    if min_barras > 0:
        x = x[espacar(x, min_barras)]
    if len(x) == 0:
        return dict(n=0)

    risco = np.full(len(x), tijolo) if ancora == 1 else x.pav.to_numpy(float)
    if alvo > 0:
        p = prob_alvo(risco, alvo)
        resp = alvo / risco
    elif ancora == 1:
        p = np.full(len(x), P_ABERTURA)
        resp = np.full(len(x), MFE_TIJOLOS)
    else:
        u = np.clip(risco / tijolo, 1, 3)
        p = np.where(u >= 3, 0.7940, 0.2422 + 0.1465 * u)
        resp = MFE_TIJOLOS / u

    lim = x[x.fant_caminho == 0]
    nd = x.dia.nunique()
    return dict(n=len(x), sinais_dia=len(x) / nd,
                P_ref=p.mean(), R_ref=resp.mean(),
                P=x.alvo.mean(), pts=x.pts.mean(), ate=x.ate.mean(),
                fant=x.fant_caminho.mean(),
                n_limpo=len(lim), P_limpo=lim.alvo.mean(), pts_limpo=lim.pts.mean(),
                pts_baixa=lim[lim.dir < 0].pts.mean(),
                pts_alta=lim[lim.dir > 0].pts.mean())


AGR = dict(cAgr=100)

CD = 4   # cooldown padrao, em tijolos, por lado

PRESETS = [
    ("Sem filtro (MinScore 0)", dict(pesos=AGR, min_score=0, min_barras=CD)),
    ("MinScore 50", dict(pesos=AGR, min_score=50, min_barras=CD)),
    ("MinScore 60  (padrao)", dict(pesos=AGR, min_score=60, min_barras=CD)),
    ("MinScore 70", dict(pesos=AGR, min_score=70, min_barras=CD)),
    ("MinScore 80", dict(pesos=AGR, min_score=80, min_barras=CD)),
    ("MinScore 60, sem cooldown", dict(pesos=AGR, min_score=60, min_barras=0)),
    ("MinScore 60, cooldown 8", dict(pesos=AGR, min_score=60, min_barras=8)),
    # nao ha preset de continuacao: carregar_real() ja entrega so reversoes.
    # Para comparar com continuacao, use padroes_fantasma.py.
    ("So pavio, MinScore 60", dict(pesos=dict(cPav=100), min_score=60,
                                   min_barras=CD)),
    ("Pesos da versao anterior",
     dict(pesos=dict(cPav=35, cExt=35, cFuro=10, cPerna=5, cLimpa=5, cAgr=10),
          min_score=60, min_barras=CD)),
]

if __name__ == "__main__":
    pd.set_option("display.width", 250)
    d = carregar_real()
    print(f"base: {len(d)} reversoes executaveis em {d.dia.nunique()} pregoes "
          f"({len(d)/d.dia.nunique():.1f}/pregao)\n")
    linhas = []
    for nome, kw in PRESETS:
        r = rodar(d, **kw)
        if not r["n"]:
            continue
        linhas.append(dict(preset=nome, por_dia=round(r["sinais_dia"], 1),
                           P_ref=round(r["P_ref"], 3), P=round(r["P"], 3),
                           R=round(r["R_ref"], 2), tij=round(r["ate"], 1),
                           pts=round(r["pts"], 2),
                           n_limpo=r["n_limpo"], P_limpo=round(r["P_limpo"], 3),
                           pts_limpo=round(r["pts_limpo"], 2),
                           baixa=round(r["pts_baixa"], 2),
                           alta=round(r["pts_alta"], 2)))
    print("=== placar dos presets (alvo 100, horizonte 8, ancora na abertura) ===")
    print(pd.DataFrame(linhas).to_string(index=False))
    print("\nP_ref = passeio aleatorio com a mesma geometria | P = realizada")
    print("pts_limpo = pts/sinal descartando caminhos com tijolo fantasma.")
    print("            E O UNICO NUMERO EXECUTAVEL.")
    print("baixa/alta = o mesmo numero por lado. A assimetria e o motivo")
    print("            principal para nao confiar no score de agressao.")
