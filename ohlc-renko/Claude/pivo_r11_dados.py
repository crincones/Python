#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Series base do R11 e utilitarios de janela, compartilhados pelos passos 9 e 10.

Regra dura: toda estatistica movel para em j-1. Nenhuma feature olha para
frente -- com Direita = 0 a seta sai no fechamento de j e so pode usar j, j-1,
j-2, ...
"""
import numpy as np
import pandas as pd
import pivo_r11_core as C

PER = 50
ALVO, STOP = 150.0, 100.0


class Dados:
    def __init__(self, per=PER):
        df = C.carregar()
        n = len(df)
        self.df, self.n, self.per = df, n, per
        self.data = df.dt.dt.date.values
        self.dias = np.sort(pd.unique(self.data))
        self.corte = self.dias[int(len(self.dias) * 0.70)]
        self.dayid = pd.factorize(self.data)[0]

        self.o, self.h = df.o.values, df.h.values
        self.l, self.c = df.l.values, df.c.values
        self.agb = df.agb.values.astype(float)
        self.ags = df.ags.values.astype(float)
        self.qt = df.qt.values.astype(float)
        self.trd = df.trd.values.astype(float)
        self.dur = df.dur_eff.values.astype(float)
        self.dirn, self.is_rev = df.dirn.values, df.is_rev.values
        self.seqb = df.seq_before.values
        self.wick_net, self.trav = df.wick_net.values, df.trav.values
        self.hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values
        self.hora = (df.dt.dt.hour + df.dt.dt.minute / 60.0).values

        self.tot = self.agb + self.ags
        self.imb = np.where(self.tot > 0, (self.agb - self.ags) /
                            np.maximum(self.tot, 1e-9), 0.0)
        self.pcp = np.where(self.tot > 0, self.agb / np.maximum(self.tot, 1e-9), 0.5)
        self.unk = np.where(self.qt > 0, np.clip(self.qt - self.tot, 0, None) /
                            np.maximum(self.qt, 1e-9), 0.0)
        self.sz = np.where(self.trd > 0, self.qt / np.maximum(self.trd, 1e-9), 0.0)
        self.vpm = self.qt / self.dur
        self.tpm = self.trd / self.dur
        self.custo = self.qt / np.maximum(self.trav, 1.0)
        self.cumd = pd.Series(self.agb - self.ags).groupby(self.dayid).cumsum().values
        self.cumq = pd.Series(self.qt).groupby(self.dayid).cumsum().values

        # range do pregao ate a barra
        dhi = np.empty(n); dlo = np.empty(n)
        hi = lo = np.nan
        for k in range(n):
            if k == 0 or self.dayid[k] != self.dayid[k - 1]:
                hi, lo = self.h[k], self.l[k]
            else:
                hi, lo = max(hi, self.h[k]), min(lo, self.l[k])
            dhi[k], dlo[k] = hi, lo
        self.dhi, self.dlo = dhi, dlo
        self.faixa = np.maximum(dhi - dlo, C.BODY)
        self.meio = (dhi + dlo) / 2.0

        # profundidade continua do extremo, com teto
        prof_lo = np.zeros(n, int); prof_hi = np.zeros(n, int)
        for j in range(n):
            k = 1
            while k <= 40 and j - k >= 0 and self.l[j] <= self.l[j - k]:
                k += 1
            prof_lo[j] = k - 1
            k = 1
            while k <= 40 and j - k >= 0 and self.h[j] >= self.h[j - k]:
                k += 1
            prof_hi[j] = k - 1
        self.prof_lo, self.prof_hi = prof_lo, prof_hi

        # inicio da perna corrente: ultimo indice em que a direcao mudou
        ini = np.zeros(n, int)
        p = 0
        for k in range(1, n):
            if self.dirn[k] != self.dirn[k - 1]:
                p = k
            ini[k] = p
        self.ini_perna = ini

    # -- utilitarios ------------------------------------------------------- #
    def zs(self, x, per=None):
        per = per or self.per
        s = pd.Series(x)
        m = s.rolling(per).mean().shift(1).values
        q = s.pow(2).rolling(per).mean().shift(1).values
        d = np.sqrt(np.maximum(q - m * m, 0.0))
        return np.where(d > 1e-12, (x - m) / np.maximum(d, 1e-12), 0.0)

    def lag(self, x, k):
        if k == 0:
            return np.asarray(x, float).copy()
        out = np.full(self.n, np.nan)
        out[k:] = np.asarray(x, float)[:-k]
        return out

    def soma(self, x, k0, k1):
        """soma de x nas barras j-k0 .. j-k1 (inclusive, k0 <= k1)."""
        acc = np.zeros(self.n)
        for k in range(k0, k1 + 1):
            acc += np.nan_to_num(self.lag(x, k))
        return acc

    def candidatos(self, esq):
        n, l, h = self.n, self.l, self.h
        pb = np.ones(n, bool); pa = np.ones(n, bool)
        for k in range(1, esq + 1):
            pb &= np.r_[np.zeros(k, bool), l[k:] <= l[:-k]]
            pa &= np.r_[np.zeros(k, bool), h[k:] >= h[:-k]]
        val = np.arange(n) >= self.per + esq + 5
        return pb & val, pa & val


def nz(a, b):
    """razao limitada em (-1,1), monotona em log(a/b). NTSL faz so aritmetica."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    s = a + b
    return np.where(np.abs(s) > 1e-12, (a - b) / np.where(np.abs(s) > 1e-12, s, 1.0), 0.0)


def populacao(D, esq, alvo=ALVO, stop=STOP):
    """candidatos dos dois lados, ordenados no tempo, com rotulo."""
    pb, pa = D.candidatos(esq)
    yB, nBr, yA, nAr = C.resultados(D.df, alvo, stop)
    jb = np.where(pb & ~np.isnan(yB))[0]
    ja = np.where(pa & ~np.isnan(yA))[0]
    J = np.r_[jb, ja]
    L = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    Y = np.r_[yB[jb], yA[ja]]
    NB = np.r_[nBr[jb], nAr[ja]]
    s = np.argsort(J, kind="stable")
    return J[s], L[s], Y[s], NB[s]
