#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 8: uma abordagem alternativa merece arquivo proprio?

Duas mudancas estruturais candidatas:
  A) PROFUNDIDADE CONTINUA no lugar de Esquerda fixo. Esquerda=6 e um corte
     duro: 5 barras nao vale, 6 vale. Medir quantas barras a extrema domina
     (ate um teto) e combinar com o contexto num limiar unico deixa um pivo
     raso passar quando o contexto e otimo, e exige pivo fundo quando nao e.
  B) RANGE MOVEL no lugar do range do pregao. O sinal se concentra na
     primeira hora, quando o range do dia ainda e pequeno e o denominador de
     pos_op e instavel. Um range de N bricks nao depende do relogio nem do
     acumulador de sessao -- e mais simples no NTSL, inclusive.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_core as C

df = C.carregar()
b = C.base(df, normalizar=1)
n = len(df)
dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
data = df.dt.dt.date.values
h, l, c = df.h.values, df.l.values, df.c.values
dirn = df.dirn.values
hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values
yB, nBr, yA, nAr = C.resultados(df, 150.0, 100.0)

dayid = pd.factorize(data)[0]
dhi = np.empty(n); dlo = np.empty(n)
hi = lo = np.nan
for k in range(n):
    if k == 0 or dayid[k] != dayid[k - 1]:
        hi, lo = h[k], l[k]
    else:
        hi, lo = max(hi, h[k]), min(lo, l[k])
    dhi[k], dlo[k] = hi, lo
faixa_dia = np.maximum(dhi - dlo, C.BODY)
meio_dia = (dhi + dlo) / 2.0

# ---- profundidade continua: quantas barras a extrema domina ---------------
CAP = 40
prof_lo = np.zeros(n, int)
prof_hi = np.zeros(n, int)
for j in range(n):
    k = 1
    while k <= CAP and j - k >= 0 and l[j] <= l[j - k]:
        k += 1
    prof_lo[j] = k - 1
    k = 1
    while k <= CAP and j - k >= 0 and h[j] >= h[j - k]:
        k += 1
    prof_hi[j] = k - 1


def monta(prof_min, usar_movel, janela, tc, tv, minb=5, conf=1):
    """devolve mascara de sinais + arrays paralelos."""
    pbm = prof_lo >= prof_min
    pam = prof_hi >= prof_min
    # confirmacao: a barra seguinte nao viola a extrema
    pbm[:n - conf] &= l[:n - conf] <= l[conf:]
    pam[:n - conf] &= h[:n - conf] >= h[conf:]
    pbm[n - conf:] = False
    pam[n - conf:] = False
    jb = np.where(pbm)[0]; ja = np.where(pam)[0]
    la = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    jj = np.r_[jb, ja]
    s = np.argsort(jj, kind="stable"); la, jj = la[s], jj[s]
    ii = jj + conf
    if usar_movel:
        hi_m = pd.Series(h).rolling(janela).max().values
        lo_m = pd.Series(l).rolling(janela).min().values
        fx = np.maximum(hi_m - lo_m, C.BODY)
        mi = (hi_m + lo_m) / 2.0
    else:
        fx, mi = faixa_dia, meio_dia
    po = la * (c[jj] - mi[jj]) / fx[jj]
    tk = dirn[jj] == la
    cand = tk & ~np.isnan(po) & (((la == 1) & (po >= tc)) | ((la == -1) & (po >= tv)))
    sel = np.zeros(len(jj), bool)
    uC = uV = -10 ** 9
    for k in np.where(cand)[0]:
        if la[k] == 1:
            if ii[k] - uC >= minb:
                sel[k] = True; uC = ii[k]
        else:
            if ii[k] - uV >= minb:
                sel[k] = True; uV = ii[k]
    y = np.where(la == 1, yB[ii], yA[ii])
    sel &= ~np.isnan(y)
    return sel, la, jj, ii, y, po, prof_lo[jj] * (la == 1) + prof_hi[jj] * (la == -1)


def rel(nome, sel, ii, y):
    dd = data[ii][sel]
    yy = y[sel]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(yy[dd < corte]); nv, pv = f(yy[dd >= corte]); na, pa = f(yy)
    print("  %-40s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f  (%4.1f/preg)"
          % (nome, nt, pt, nv, pv, na, pa, pa * 150 - (1 - pa) * 100, na / len(dias)))
    return pa, pt, pv, na


print("=" * 122)
print("REFERENCIA: a regra do arquivo A (Esquerda=6 fixo, range do pregao)")
print("=" * 122)
sel, la, jj, ii, y, po, pf = monta(6, False, 0, 0.25, 0.35)
rel("Esq=6 | pregao | 0.25 / 0.35", sel, ii, y)

print("\n" + "=" * 122)
print("A) PROFUNDIDADE MINIMA x LIMIAR DE CONTEXTO  (range do pregao)")
print("=" * 122)
for pm in [3, 4, 6, 8, 10]:
    for tc, tv in [(0.20, 0.30), (0.25, 0.35), (0.30, 0.40)]:
        s2, _, _, i2, y2, _, _ = monta(pm, False, 0, tc, tv)
        rel("prof>=%-2d  %.2f / %.2f" % (pm, tc, tv), s2, i2, y2)

print("\n" + "=" * 122)
print("B) RANGE MOVEL no lugar do range do pregao  (prof>=6)")
print("=" * 122)
for jan in [40, 60, 100, 150, 250]:
    for tc, tv in [(0.20, 0.30), (0.25, 0.35), (0.30, 0.40)]:
        s2, _, _, i2, y2, _, _ = monta(6, True, jan, tc, tv)
        rel("movel %-4d  %.2f / %.2f" % (jan, tc, tv), s2, i2, y2)

print("\n" + "=" * 122)
print("C) LIMIAR UNICO SOBRE profundidade + contexto  (troca dois cortes por um)")
print("=" * 122)
sel0, la0, jj0, ii0, y0, po0, pf0 = monta(3, False, 0, -9, -9, minb=0)
qual = np.clip(pf0 / 12.0, 0, 1) * 0.5 + np.clip((po0 + 0.2) / 0.7, 0, 1) * 0.5
val0 = ~np.isnan(y0) & (dirn[jj0] == la0)
for q in [0.45, 0.55, 0.60, 0.65, 0.70, 0.75]:
    cand = val0 & (qual >= q)
    s2 = np.zeros(len(jj0), bool)
    uC = uV = -10 ** 9
    for k in np.where(cand)[0]:
        if la0[k] == 1:
            if ii0[k] - uC >= 5:
                s2[k] = True; uC = ii0[k]
        else:
            if ii0[k] - uV >= 5:
                s2[k] = True; uV = ii0[k]
    rel("qualidade >= %.2f" % q, s2, ii0, y0)

print("\n" + "=" * 122)
print("D) JANELA DE PREGAO  (o vazio das 10h-12h se confirma nos dois blocos?)")
print("=" * 122)
sel, la, jj, ii, y, po, pf = monta(6, False, 0, 0.25, 0.35)
hh = hhmm[ii]
for nome, m in [("tudo", np.ones(len(jj), bool)),
                ("fora de 10h-12h", ~((hh >= 1000) & (hh < 1200))),
                ("fora de 10h-1230", ~((hh >= 1000) & (hh < 1230))),
                ("so antes das 10h", hh < 1000)]:
    rel(nome, sel & m, ii, y)
