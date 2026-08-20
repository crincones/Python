"""Score continuo 0-100 para a reversao, no molde do PivoReversao_Claude.

Motivo: os filtros booleanos (pavio<=110 E extremo<=0.5) cortam de 162,8 para
7,7 sinais/pregao sem meio-termo. Um score com rampas deixa a frequencia ser
regulada continuamente por MinScore.

Cada componente vira uma rampa 0..1 e entra com um peso. Os pesos NAO sao
chutados: cada componente e medido isolado antes (painel A), e o peso segue a
amplitude que ele mostra. Componentes que nao movem nada ficam com peso 0 --
e isso e a maioria, coerente com o resto da pesquisa.

Alvo: +100 pts antes de perder a abertura do tijolo, em ate 8 tijolos, pior caso
na ordem de eventos. Numero de referencia: o mesmo score no Renko sintetico.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from alvo import preparar_geo, B
from dados import carregar

G, H = 100.0, 8


def rampa(x, ini, fim):
    """0 abaixo de ini, 1 acima de fim, linear no meio. Aceita fim < ini."""
    r = (np.asarray(x, float) - ini) / (fim - ini)
    return np.clip(r, 0.0, 1.0)


def componentes(d: pd.DataFrame, com_fluxo=True) -> pd.DataFrame:
    d = d.copy()
    # --- geometricos (existem tambem no sintetico) ---------------------
    # pavio curto: a reversao mais apertada. 150 -> 0 ; 95 -> 1
    d["cPav"] = rampa(d.pav, 150.0, 95.0)
    # no extremo recente: dext 3 tijolos -> 0 ; 0 -> 1
    d["cExt"] = rampa(d.dext50, 3.0, 0.0)
    # furou o extremo de 20 e voltou (falso rompimento): -1 -> 0 ; +0.5 -> 1
    d["cFuro"] = rampa(d.furo, -1.0, 0.5)
    # perna quebrada longa: 1 -> 0 ; 5 -> 1
    d["cPerna"] = rampa(d.perna, 1.0, 5.0)
    # perna limpa (pouco repique antes de quebrar): 110 -> 0 ; 60 -> 1
    d["cLimpa"] = rampa(d.perna_pav, 110.0, 60.0)
    # tendencia eficiente sendo quebrada: efic20 0.2 -> 0 ; 0.6 -> 1
    d["cEfic"] = rampa(d.efic20, 0.2, 0.6)
    # LONGE do extremo -- o inverso de cExt. Medido no painel A: no conjunto
    # limpo a reversao no topo/fundo e PIOR (P 0.297 contra 0.326). O filtro
    # DistExtremo da versao anterior estava, portanto, invertido.
    d["cLonge"] = rampa(d.dext50, 0.0, 3.0)
    # --- fluxo (so na base real) ---------------------------------------
    if com_fluxo:
        agr = d.buy + d.sell
        imb = np.where(agr > 0, (d.buy - d.sell) / np.maximum(agr, 1e-9), 0.0)
        d["aFavor"] = d.dir * imb
        d["cAgr"] = rampa(d.aFavor, 0.0, 0.30)
    else:
        d["cAgr"] = 0.0
    return d


COMPS = ["cPav", "cExt", "cFuro", "cPerna", "cLimpa", "cEfic", "cAgr", "cLonge"]

# Pesos vindos do painel A, medidos no conjunto LIMPO (sem tijolo fantasma no
# caminho), que e o unico executavel. So entram componentes com gradiente
# monotonico nos 4 quartis:
#     cPav   P 0.309 -> 0.330   pts -3.64 -> -0.51   (e o acaso fica plano)
#     cAgr   P 0.294 -> 0.340   pts -5.90 -> +1.04
#     cLonge P 0.297 -> 0.326   pts -5.49 -> -1.11   (2 niveis so)
# Ficaram de fora: cFuro e cExt (andam ao contrario), cPerna e cLimpa (o
# quartil do meio e o melhor -- ruido), cEfic (amplitude 0.016).
PESOS = dict(cPav=40, cAgr=40, cLonge=20,
             cExt=0, cFuro=0, cPerna=0, cLimpa=0, cEfic=0)

# variantes comparadas no painel B
JOGOS = {
    "so geometria (cPav+cLonge)": dict(cPav=65, cLonge=35),
    "geometria + agressao": PESOS,
    "so pavio": dict(cPav=100),
    "so agressao": dict(cAgr=100),
    "os pesos supostos (errados)": dict(cPav=35, cExt=35, cFuro=10, cPerna=5,
                                        cLimpa=5, cAgr=10),
}


def pontuar(d: pd.DataFrame, pesos=PESOS) -> pd.Series:
    tot = sum(pesos.values())
    if tot <= 0:
        tot = 1
    s = sum(w * d[c] for c, w in pesos.items() if w)
    return 100.0 * s / tot


def carregar_real():
    real = carregar()
    real = real[(real.c - real.o).abs() == B].reset_index(drop=True)
    d = preparar_geo(real, G, H)
    dur = d["dur"].to_numpy(float)
    qtd = d["qtd"].to_numpy(float)
    ate = d["ate"].to_numpy(float)
    n = len(d)
    fant = np.zeros(n)
    for i in range(n - H):
        k = int(ate[i]) if not np.isnan(ate[i]) else H
        f = slice(i + 1, i + k + 1)
        fant[i] = float(((dur[f] == 0) | (qtd[f] == 0)).any())
    d["fant_caminho"] = fant
    d["ibar"] = np.arange(len(d))          # posicao do tijolo na serie original
    d = d[(d.virou == 1) & d.alvo.notna() & (d.dur > 0) & (d.qtd > 0)].copy()
    return componentes(d).reset_index(drop=True)


def carregar_sint():
    s = pd.read_pickle("sintetico.pkl").reset_index(drop=True)
    s["dir"] = s["dir"].astype(int)
    s = preparar_geo(s, G, H)
    s = s[(s.virou == 1) & s.alvo.notna()].copy()
    s = componentes(s, com_fluxo=False)
    s["fant_caminho"] = 0.0
    return s.reset_index(drop=True)


def espacar(d: pd.DataFrame, minbarras: int) -> np.ndarray:
    """Cooldown por lado, em TIJOLOS -- a mesma conta do .ntsl.

    Usa `ibar`, o indice do tijolo na serie original. Usar o indice do
    DataFrame filtrado contaria SINAIS em vez de tijolos, que e coisa bem
    diferente: entre dois sinais consecutivos podem passar varios tijolos.
    """
    if minbarras <= 0:
        return np.ones(len(d), bool)
    if "ibar" not in d.columns:
        raise KeyError("falta a coluna ibar (indice do tijolo na serie original)")
    idx = d["ibar"].to_numpy()
    lado = d.dir.to_numpy()
    ok = np.zeros(len(d), bool)
    ult = {-1: -10**9, 1: -10**9}
    for i in range(len(d)):
        s = lado[i]
        if idx[i] - ult[s] >= minbarras:
            ok[i] = True
            ult[s] = idx[i]
    return ok


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    r = carregar_real()
    s = carregar_sint()
    nd = r.dia.nunique()
    lim = r[r.fant_caminho == 0]
    print(f"reversoes: real {len(r)} ({len(r)/nd:.1f}/pregao) | acaso {len(s)}")
    print(f"base: P={r.alvo.mean():.4f} (acaso {s.alvo.mean():.4f}, breakeven "
          f"{B/(G+B):.4f})  pts={r.pts.mean():+.2f}  limpo={lim.pts.mean():+.2f}")

    print("\n" + "=" * 92)
    print("PAINEL A -- cada componente isolado (so caminho limpo, que e o executavel)")
    print("=" * 92)
    for c in COMPS:
        x = lim.dropna(subset=[c])
        if x[c].nunique() < 4:
            continue
        q = pd.qcut(x[c], 4, labels=False, duplicates="drop")
        t = x.assign(q=q).groupby("q").agg(n=("alvo", "size"), P=("alvo", "mean"),
                                           pts=("pts", "mean"), v=(c, "mean"))
        # o mesmo componente no acaso, para saber quanto e geometria
        if c != "cAgr":
            qs = pd.qcut(s[c], 4, labels=False, duplicates="drop")
            ta = s.assign(q=qs).groupby("q").agg(P_ac=("alvo", "mean"))
            t = t.join(ta)
        print(f"\n--- {c}  (amplitude P = {t.P.max()-t.P.min():.3f})")
        print(t.round(4).to_string())

    print("\n" + "=" * 92)
    print("PAINEL B -- curva de frequencia por jogo de pesos (so caminho limpo)")
    print("=" * 92)
    dias = np.sort(r.dia.unique())
    corte = dias[int(len(dias) * 0.6)]
    for nome, pesos in JOGOS.items():
        r["score"] = pontuar(r, pesos)
        usa_fluxo = pesos.get("cAgr", 0) > 0
        if not usa_fluxo:
            s["score"] = pontuar(s, pesos)
        linhas = []
        for ms in (0, 30, 40, 50, 60, 70, 80):
            a = r[r.score >= ms]
            if len(a) < 40:
                continue
            al = a[a.fant_caminho == 0]
            tr_ = al[al.dia < corte]
            te_ = al[al.dia >= corte]
            lin = dict(MinScore=ms, por_dia=len(a) / nd, P=a.alvo.mean(),
                       n_limpo=len(al), P_limpo=al.alvo.mean(),
                       pts_limpo=al.pts.mean(),
                       pts_tr=tr_.pts.mean() if len(tr_) > 30 else np.nan,
                       pts_te=te_.pts.mean() if len(te_) > 30 else np.nan)
            if not usa_fluxo:
                b = s[s.score >= ms]
                lin["P_acaso"] = b.alvo.mean() if len(b) > 100 else np.nan
            linhas.append(lin)
        print(f"\n--- {nome}")
        print(pd.DataFrame(linhas).set_index("MinScore").round(4).to_string())

    print("\n" + "=" * 92)
    print("PAINEL C -- espacamento MinBarras (pesos medidos, MinScore=50)")
    print("=" * 92)
    r["score"] = pontuar(r, PESOS)
    base = r[r.score >= 50]
    linhas = []
    for mb in (0, 2, 4, 6, 10, 15):
        a = base[espacar(base, mb)]
        al = a[a.fant_caminho == 0]
        linhas.append(dict(MinBarras=mb, n=len(a), por_dia=len(a) / nd,
                           P=a.alvo.mean(), n_limpo=len(al),
                           P_limpo=al.alvo.mean(), pts_limpo=al.pts.mean()))
    print(pd.DataFrame(linhas).set_index("MinBarras").round(4).to_string())
    print(f"\nbreakeven do alvo {G:.0f}/{B:.0f} = {B/(G+B):.4f}   "
          f"acaso da base = {s.alvo.mean():.4f}")
