#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replica fiel do PivoReversao_Claude.ntsl em Python, sobre o Renko R11.

Reproduz bar-a-bar: janela estatistica [j-Periodo .. j-1], teste de pivo com
tolerancia, cache dos dois ultimos pivos de cada lado, os seis componentes do
score e a regra de MinScore/MinBarras. Serve de base para medir os componentes
e para otimizar os parametros.

Convencao de indices: o NTSL avalia a barra [p] onde p=Direita, estando na
barra corrente i. Aqui trabalho com j = i - p (a barra do pivo). As barras de
confirmacao sao j+1 .. j+Direita e o sinal so e acionavel no fechamento de
i = j + Direita -- e ali que a entrada e marcada.
"""
import numpy as np
import pandas as pd
import r11_virada as V

BODY = V.BODY_PTS


# --------------------------------------------------------------------------- #
# series base (independentes de parametro)
# --------------------------------------------------------------------------- #
def base(df, normalizar=1):
    b = {}
    agb, ags = df.agb.values.astype(float), df.ags.values.astype(float)
    tot = agb + ags
    delta = agb - ags
    if normalizar:
        pC = np.where(tot > 0, agb / np.maximum(tot, 1e-9), 0.5)
        pV = np.where(tot > 0, ags / np.maximum(tot, 1e-9), 0.5)
        dN = np.where(tot > 0, delta / np.maximum(tot, 1e-9), 0.0)
    else:
        pC, pV, dN = agb, ags, delta
    b["pC"], b["pV"], b["deltaN"] = pC, pV, dN
    b["delta"], b["tot"] = delta, tot
    b["dur"] = df.dur.values.astype(float)
    b["rng"] = df.h.values - df.l.values
    # cumd: delta acumulado do dia, em contratos (reseta na virada de pregao)
    b["cumd"] = pd.Series(delta).groupby(df.dt.dt.date.values).cumsum().values
    return b


def _roll_ms(x, per):
    """media e desvio padrao populacional da janela [j-per .. j-1]."""
    s = pd.Series(x)
    m = s.rolling(per).mean().shift(1).values
    q = s.pow(2).rolling(per).mean().shift(1).values
    v = q - m * m
    return m, np.sqrt(np.maximum(v, 0.0))


def ramp(x, ini, fim):
    if fim == ini:
        return np.where(x >= fim, 1.0, 0.0)
    return np.clip((x - ini) / (fim - ini), 0.0, 1.0)


# --------------------------------------------------------------------------- #
# componentes do score, por barra avaliada j
# --------------------------------------------------------------------------- #
def componentes(df, b, P):
    """P = dict de parametros. Devolve dict de arrays indexados por j."""
    n = len(df)
    h, l, o, c = df.h.values, df.l.values, df.o.values, df.c.values
    per, esq, dta = P["Periodo"], P["Esquerda"], P["Direita"]

    mC, dpC = _roll_ms(b["pC"], per)
    mV, dpV = _roll_ms(b["pV"], per)
    mR, dpR = _roll_ms(b["rng"], per)
    mU, dpU = _roll_ms(b["dur"], per)
    mD, dpD = _roll_ms(b["deltaN"], per)

    tol = P["TolerPivoFrac"] * mR

    # --- teste de pivo ---------------------------------------------------
    pb = np.ones(n, bool)
    pa = np.ones(n, bool)
    idx = np.arange(n)
    for k in range(1, esq + 1):
        pb &= np.r_[np.zeros(k, bool), l[k:] <= l[:-k]]
        pa &= np.r_[np.zeros(k, bool), h[k:] >= h[:-k]]
    for k in range(1, dta + 1):
        pb[:n - k] &= l[:n - k] <= l[k:] + tol[:n - k]
        pa[:n - k] &= h[:n - k] >= h[k:] - tol[:n - k]
        pb[n - k:] = False
        pa[n - k:] = False
    valido = idx >= max(esq, per) + 5
    valido &= ~np.isnan(mR)
    pb &= valido
    pa &= valido

    rng = np.maximum(h - l, 1.0)
    zAgrC = np.where(dpC > 0, (b["pC"] - mC) / np.maximum(dpC, 1e-12), 0.0)
    zAgrV = np.where(dpV > 0, (b["pV"] - mV) / np.maximum(dpV, 1e-12), 0.0)
    zRng = np.where(dpR > 0, (rng - mR) / np.maximum(dpR, 1e-12), 0.0)
    zVel = np.where(dpU > 0, -(b["dur"] - mU) / np.maximum(dpU, 1e-12), 0.0)
    deseq = np.where(b["tot"] > 0, np.abs(b["delta"]) / np.maximum(b["tot"], 1e-9), 0.0)

    posFech = (c - l) / rng
    posTopo = 1.0 - posFech
    cmin, cmax = np.minimum(o, c), np.maximum(o, c)
    pavInf = (cmin - l) / rng
    pavSup = (h - cmax) / rng

    # --- agressao das barras de confirmacao ------------------------------
    if dta > 0:
        acc = np.zeros(n)
        for k in range(1, dta + 1):
            acc[:n - k] += b["deltaN"][k:]
        deltaConf = acc / dta
    else:
        deltaConf = np.zeros(n)
    zConf = np.where(dpD > 0, deltaConf / np.maximum(dpD, 1e-12), 0.0)

    # --- climax e compressao ---------------------------------------------
    cClx = 0.5 * ramp(zVel, P["VelZIni"], P["VelZFim"]) + \
           0.5 * ramp(zRng, P["RngZIni"], P["RngZFim"])
    cCmp = ramp(-zRng, P["RngZIni"], P["RngZFim"]) * \
           ramp(deseq, P["DeseqIni"], P["DeseqFim"])

    # --- absorcao ---------------------------------------------------------
    cAbsB = ramp(zAgrV, P["AbsZIni"], P["AbsZFim"]) * ramp(posFech, P["FechIni"], P["FechFim"])
    cAbsA = ramp(zAgrC, P["AbsZIni"], P["AbsZFim"]) * ramp(posTopo, P["FechIni"], P["FechFim"])

    # --- flip de agressao na confirmacao ---------------------------------
    if dta > 0:
        cFlipB = np.clip(zConf / 1.5, 0, 1)
        cFlipB = np.clip(np.where((b["delta"] < 0) & (deltaConf > 0), cFlipB + 0.3, cFlipB), 0, 1)
        cFlipA = np.clip(-zConf / 1.5, 0, 1)
        cFlipA = np.clip(np.where((b["delta"] > 0) & (deltaConf < 0), cFlipA + 0.3, cFlipA), 0, 1)
    else:
        cFlipB = ramp(posFech, P["FechIni"], P["FechFim"])
        cFlipA = ramp(posTopo, P["FechIni"], P["FechFim"])

    cPavB = ramp(pavInf, P["PavIni"], P["PavFim"])
    cPavA = ramp(pavSup, P["PavIni"], P["PavFim"])

    return dict(pb=pb, pa=pa, mRng=mR, cClx=cClx, cCmp=cCmp,
                cAbsB=cAbsB, cAbsA=cAbsA, cFlipB=cFlipB, cFlipA=cFlipA,
                cPavB=cPavB, cPavA=cPavA,
                zAgrC=zAgrC, zAgrV=zAgrV, zRng=zRng, zVel=zVel, deseq=deseq,
                posFech=posFech, pavInf=pavInf, pavSup=pavSup, zConf=zConf)


def divergencia(df, b, K, P):
    """cDiv dos dois lados, replicando o cache de dois niveis do NTSL."""
    n = len(df)
    l, h = df.l.values, df.h.values
    cumd, dN = b["cumd"], b["deltaN"]
    minDist = P["Esquerda"] + P["Direita"]
    look = P["DivLookback"]
    cDivB = np.zeros(n)
    cDivA = np.zeros(n)

    loB = [-1, -1]; loV = [0.0, 0.0]; loC = [0.0, 0.0]; loD = [0.0, 0.0]
    hiB = [-1, -1]; hiV = [0.0, 0.0]; hiC = [0.0, 0.0]; hiD = [0.0, 0.0]

    for j in range(n):
        if K["pb"][j]:
            achou = False
            for s in (0, 1):
                d = j - loB[s]
                if loB[s] >= 0 and minDist <= d <= look:
                    aV, aC, aD = loV[s], loC[s], loD[s]
                    achou = True
                    break
            if achou:
                if l[j] < aV and cumd[j] > aC:
                    cDivB[j] = 1.0
                elif l[j] < aV and dN[j] > aD:
                    cDivB[j] = 0.6
                elif l[j] >= aV and cumd[j] > aC:
                    cDivB[j] = 0.35
                elif cumd[j] > aC:
                    cDivB[j] = 0.15
            loB[1], loV[1], loC[1], loD[1] = loB[0], loV[0], loC[0], loD[0]
            loB[0], loV[0], loC[0], loD[0] = j, l[j], cumd[j], dN[j]

        if K["pa"][j]:
            achou = False
            for s in (0, 1):
                d = j - hiB[s]
                if hiB[s] >= 0 and minDist <= d <= look:
                    aV, aC, aD = hiV[s], hiC[s], hiD[s]
                    achou = True
                    break
            if achou:
                if h[j] > aV and cumd[j] < aC:
                    cDivA[j] = 1.0
                elif h[j] > aV and dN[j] < aD:
                    cDivA[j] = 0.6
                elif h[j] <= aV and cumd[j] < aC:
                    cDivA[j] = 0.35
                elif cumd[j] < aC:
                    cDivA[j] = 0.15
            hiB[1], hiV[1], hiC[1], hiD[1] = hiB[0], hiV[0], hiC[0], hiD[0]
            hiB[0], hiV[0], hiC[0], hiD[0] = j, h[j], cumd[j], dN[j]

    return cDivB, cDivA


def score(K, cDivB, cDivA, P):
    w = np.array([P["PesoDiv"], P["PesoAbs"], P["PesoClx"],
                  P["PesoFlip"], P["PesoCmp"], P["PesoPav"]], float)
    tw = w.sum()
    if tw <= 0:
        tw = 1.0
    sB = 100 * (w[0] * cDivB + w[1] * K["cAbsB"] + w[2] * K["cClx"] +
                w[3] * K["cFlipB"] + w[4] * K["cCmp"] + w[5] * K["cPavB"]) / tw
    sA = 100 * (w[0] * cDivA + w[1] * K["cAbsA"] + w[2] * K["cClx"] +
                w[3] * K["cFlipA"] + w[4] * K["cCmp"] + w[5] * K["cPavA"]) / tw
    return sB, sA


def aplicar_minbarras(K, sB, sA, minscore, minbarras):
    """Percorre em ordem e devolve os j que viram seta, respeitando MinBarras."""
    n = len(sB)
    outB = np.zeros(n, bool)
    outA = np.zeros(n, bool)
    ultC = -10 ** 9
    ultV = -10 ** 9
    for j in range(n):
        if K["pb"][j] and sB[j] >= minscore and (j - ultC) >= minbarras:
            outB[j] = True
            ultC = j
        if K["pa"][j] and sA[j] >= minscore and (j - ultV) >= minbarras:
            outA[j] = True
            ultV = j
    return outB, outA


# --------------------------------------------------------------------------- #
# rotulagem: primeiro toque, stop testado antes do alvo (pessimista)
# --------------------------------------------------------------------------- #
def resultados(df, alvo_pts, stop_pts, horizonte=3000):
    """Para toda barra i: resultado de entrar no Close[i] comprado e vendido."""
    n = len(df)
    c, h, l = df.c.values, df.h.values, df.l.values
    yB = np.full(n, np.nan); nB = np.full(n, np.nan)
    yA = np.full(n, np.nan); nA = np.full(n, np.nan)
    for i in range(n):
        tg, st = c[i] + alvo_pts, c[i] - stop_pts
        lim = min(n, i + 1 + horizonte)
        for j in range(i + 1, lim):
            if l[j] <= st:
                yB[i], nB[i] = 0.0, j - i; break
            if h[j] >= tg:
                yB[i], nB[i] = 1.0, j - i; break
        tg, st = c[i] - alvo_pts, c[i] + stop_pts
        for j in range(i + 1, lim):
            if h[j] >= st:
                yA[i], nA[i] = 0.0, j - i; break
            if l[j] <= tg:
                yA[i], nA[i] = 1.0, j - i; break
    return yB, nB, yA, nA


PADRAO = dict(Esquerda=2, Direita=0, Periodo=50, DivLookback=60,
              TolerPivoFrac=0.30, MinBarras=3, MinScore=35,
              PesoDiv=25, PesoAbs=25, PesoClx=30, PesoFlip=0,
              PesoCmp=10, PesoPav=10,
              AbsZIni=-0.50, AbsZFim=2.00, FechIni=0.15, FechFim=0.85,
              VelZIni=0.30, VelZFim=2.00, RngZIni=-0.50, RngZFim=1.80,
              PavIni=0.25, PavFim=0.60, DeseqIni=0.05, DeseqFim=0.60)


def carregar():
    return V.geometria(V.carregar(V.CSV_DEFAULT))
