"""Alvo por ANDAMENTO EM PONTOS, com ordem de eventos -- e features dos tijolos
anteriores.

O criterio antigo ("o extremo contrario nao e violado em 4 tijolos") e fraco:
ele nao exige que o preco ande. Um sinal que fica parado 4 tijolos conta como
acerto. Aqui o alvo e explicito:

    a partir do fechamento do tijolo de reversao, o preco alcanca +G pontos
    a favor ANTES de violar a ancora (a abertura do tijolo, a 50 pts), dentro
    de H tijolos.

Ordem de eventos: dentro de um mesmo tijolo o Renko nao diz o que veio primeiro,
entao a simulacao assume SEMPRE o pior caso -- se o tijolo violou a ancora, e
stop, mesmo que o fechamento ja estivesse no alvo. Numero conservador.

Todas as features aqui sao GEOMETRICAS (so OHLC) de proposito: assim elas podem
ser calculadas identicamente no Renko sintetico de passeio aleatorio, que vira a
hipotese nula. Um padrao de tijolos anteriores so vale se aparecer na base real
e NAO aparecer no sintetico.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

B = 50.0


# ----------------------------------------------------------------------
# simulacao do trade
# ----------------------------------------------------------------------
def simular(o, h, l, c, dirn, nivel, alvo_pts, H):
    """Para cada barra: alcanca +alvo_pts antes de violar 'nivel', em H tijolos?

    Devolve (res, pts, tijolos_ate) com res: +1 alvo, -1 stop, 0 estourou o prazo.
    """
    n = len(c)
    res = np.zeros(n, np.int8)
    pts = np.full(n, np.nan)
    ate = np.full(n, np.nan)
    for i in range(n - H):
        d = dirn[i]
        nv = nivel[i]
        risco = abs(c[i] - nv)
        ganho = 0.0
        r, t = 0, H
        for k in range(i + 1, i + H + 1):
            # pior caso primeiro: a ancora foi violada neste tijolo?
            if (d < 0 and h[k] > nv) or (d > 0 and l[k] < nv):
                r, t = -1, k - i
                ganho = -risco
                break
            ganho = (c[i] - c[k]) if d < 0 else (c[k] - c[i])
            if ganho >= alvo_pts:
                r, t = 1, k - i
                ganho = alvo_pts
                break
        res[i] = r
        pts[i] = ganho
        ate[i] = t
    res[n - H:] = 0
    pts[n - H:] = np.nan
    return res, pts, ate


# ----------------------------------------------------------------------
# features geometricas dos tijolos ANTERIORES (valem no real e no sintetico)
# ----------------------------------------------------------------------
def geo_previos(d: pd.DataFrame) -> pd.DataFrame:
    """So usa o,h,l,c,dir. Nada de fluxo: precisa rodar igual no sintetico."""
    d = d.copy()
    o, h, l, c = (d[k].to_numpy(float) for k in "ohlc")
    dirn = d["dir"].to_numpy(int)
    n = len(d)
    eps = 1e-9

    # pavio contrario de cada tijolo (relativo ao proprio sentido)
    pav = np.where(dirn < 0, h - c, c - l)
    d["pav"] = pav
    for k in (1, 2, 3):
        d[f"pav{k}"] = pd.Series(pav).shift(k)

    # sequencia e perna quebrada
    seq = np.ones(n, np.int32)
    for i in range(1, n):
        if dirn[i] == dirn[i - 1]:
            seq[i] = seq[i - 1] + 1
    d["seq"] = seq
    d["virou"] = np.r_[0, (dirn[1:] != dirn[:-1]).astype(int)]
    perna = pd.Series(seq).shift(1).fillna(0).to_numpy(int)
    d["perna"] = perna

    # deslocamento e limpeza da perna quebrada
    pontos = np.full(n, np.nan)
    limpeza = np.full(n, np.nan)
    for i in range(n):
        k = perna[i]
        if k <= 0 or i - k < 0:
            continue
        pontos[i] = abs(c[i - 1] - o[i - k])
        limpeza[i] = pav[i - k:i].mean()
    d["perna_pts"] = pontos
    d["perna_pav"] = limpeza            # pavio medio da perna: baixo = tendencia limpa

    # eficiencia e amplitude recentes
    s_c = pd.Series(c)
    for m in (10, 20, 50):
        d[f"amp{m}"] = (pd.Series(h).rolling(m).max() - pd.Series(l).rolling(m).min())
        d[f"net{m}"] = (s_c - s_c.shift(m)).abs()
        d[f"efic{m}"] = d[f"net{m}"] / (d[f"amp{m}"] + eps)
        d[f"viradas{m}"] = pd.Series(d["virou"]).rolling(m).sum()

    # onde a reversao esta acontecendo em relacao ao extremo recente
    for m in (20, 50):
        topo = pd.Series(h).shift(1).rolling(m).max()
        fundo = pd.Series(l).shift(1).rolling(m).min()
        # distancia do extremo do tijolo ao extremo recente, em tijolos.
        # ~0 = a reversao esta bem no topo/fundo (repique no nivel);
        # >0 = esta acontecendo longe do extremo (no meio do range)
        dist = np.where(dirn < 0, (topo - h) / B, (l - fundo) / B)
        d[f"dext{m}"] = dist
        # posicao no range, SEMPRE relativa ao sentido do sinal: 1 = o sinal
        # esta na ponta favoravel (vende no topo / compra no fundo), 0 = na
        # ponta errada. Sem isso o teste confunde padrao com deriva do periodo.
        bruta = (c - fundo) / (topo - fundo + eps)
        d[f"pos{m}"] = np.where(dirn < 0, bruta, 1.0 - bruta)

    # excesso: o quanto o tijolo furou o extremo recente antes de virar
    topo20 = pd.Series(h).shift(1).rolling(20).max()
    fundo20 = pd.Series(l).shift(1).rolling(20).min()
    d["furo"] = np.where(dirn < 0, (h - topo20) / B, (fundo20 - l) / B)
    return d


def preparar_geo(d: pd.DataFrame, alvo_pts=100.0, H=8, ancora="abertura") -> pd.DataFrame:
    d = geo_previos(d).reset_index(drop=True)
    o, h, l, c = (d[k].to_numpy(float) for k in "ohlc")
    dirn = d["dir"].to_numpy(int)
    if ancora == "abertura":
        nivel = o.copy()
    else:
        nivel = np.where(dirn < 0, h, l)
    res, pts, ate = simular(o, h, l, c, dirn, nivel, alvo_pts, H)
    d["res"] = res
    d["pts"] = pts
    d["ate"] = ate
    d["alvo"] = (res == 1).astype(float)
    d["risco"] = np.abs(c - nivel)
    d.loc[d.index[-H:], ["alvo", "pts"]] = np.nan
    return d


if __name__ == "__main__":
    pd.set_option("display.width", 240)
    from dados import carregar

    real = carregar()
    real = real[(real.c - real.o).abs() == B].reset_index(drop=True)
    sint = pd.read_pickle("sintetico.pkl").reset_index(drop=True)
    sint["dir"] = sint["dir"].astype(int)

    print("Taxa de acerto do alvo (chegar a +G antes de perder a abertura),")
    print("so tijolos de REVERSAO, real x passeio aleatorio.\n")
    linhas = []
    for G in (50, 100, 150, 200):
        for H in (4, 8, 12):
            rr = preparar_geo(real, G, H)
            ss = preparar_geo(sint, G, H)
            rr = rr[(rr.virou == 1) & rr.alvo.notna()]
            ss = ss[(ss.virou == 1) & ss.alvo.notna()]
            linhas.append(dict(
                G=G, H=H, R=G / B,
                n_real=len(rr), p_real=rr.alvo.mean(), pts_real=rr.pts.mean(),
                p_acaso=ss.alvo.mean(), pts_acaso=ss.pts.mean(),
                lift=rr.alvo.mean() - ss.alvo.mean()))
    t = pd.DataFrame(linhas)
    print(t.round(4).to_string(index=False))
    print("\nR = alvo/risco. p = P(alvo antes do stop). lift = real - acaso.")
