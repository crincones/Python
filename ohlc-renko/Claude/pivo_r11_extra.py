#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 7: dois eixos ainda nao testados.
  a) geometria alvo/stop -- tudo ate aqui foi medido em 150/100
  b) confluencia: o sinal do PivoR11 melhora quando a regra RenkoViradaR11
     tambem dispara na vizinhanca?
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_core as C

ESQ, DIR, MB, TC, TV = 6, 1, 5, 0.25, 0.35

df = C.carregar()
b = C.base(df, normalizar=1)
n = len(df)
dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
data = df.dt.dt.date.values
h, l, c = df.h.values, df.l.values, df.c.values
dirn, is_rev, seqb = df.dirn.values, df.is_rev.values, df.seq_before.values
dayid = pd.factorize(data)[0]
dhi = np.empty(n); dlo = np.empty(n)
hi = lo = np.nan
for k in range(n):
    if k == 0 or dayid[k] != dayid[k - 1]:
        hi, lo = h[k], l[k]
    else:
        hi, lo = max(hi, h[k]), min(lo, l[k])
    dhi[k], dlo[k] = hi, lo
faixa = np.maximum(dhi - dlo, C.BODY)
meio = (dhi + dlo) / 2.0
hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values

P = dict(C.PADRAO, Esquerda=ESQ, Direita=DIR, TolerPivoFrac=0.0)
K = C.componentes(df, b, P)
jb = np.where(K["pb"])[0]; jb = jb[jb + DIR < n]
ja = np.where(K["pa"])[0]; ja = ja[ja + DIR < n]
lado = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
j = np.r_[jb, ja]
s = np.argsort(j, kind="stable"); lado, j = lado[s], j[s]
i = j + DIR
pos = lado * (c[j] - meio[j]) / faixa[j]
tipo = dirn[j] == lado

cand = tipo & (((lado == 1) & (pos >= TC)) | ((lado == -1) & (pos >= TV)))
sel = np.zeros(len(j), bool)
uC = uV = -10 ** 9
for k in np.where(cand)[0]:
    if lado[k] == 1:
        if i[k] - uC >= MB:
            sel[k] = True; uC = i[k]
    else:
        if i[k] - uV >= MB:
            sel[k] = True; uV = i[k]

print("=" * 110)
print("a) GEOMETRIA ALVO / STOP  (regra fixa, n bruto = %d)" % sel.sum())
print("=" * 110)
print("  %-18s %6s %8s %8s %8s %9s %8s" %
      ("alvo/stop (pts)", "BE", "n", "acerto", "tr", "te", "pts/trade"))
melhor = []
for alvo in [50, 100, 150, 200, 250, 300]:
    for stop in [50, 100, 150]:
        yB, nB, yA, nA = C.resultados(df, float(alvo), float(stop))
        y = np.where(lado == 1, yB[i], yA[i])
        m = sel & ~np.isnan(y)
        if m.sum() < 100:
            continue
        pa = y[m].mean()
        pt = y[m & (data[i] < corte)].mean()
        pv = y[m & (data[i] >= corte)].mean()
        be = stop / (alvo + stop)
        e = pa * alvo - (1 - pa) * stop
        melhor.append((e, alvo, stop, pa, pt, pv, m.sum()))
        print("  %-18s %6.3f %8d %8.4f %8.4f %8.4f %+8.1f"
              % ("%d / %d" % (alvo, stop), be, m.sum(), pa, pt, pv, e))
melhor.sort(reverse=True)
print("\n  melhor expectativa bruta: alvo %d / stop %d = %+.1f pts/trade"
      % (melhor[0][1], melhor[0][2], melhor[0][0]))
print("  atencao: expectativa maior com alvo maior vem junto com trade mais")
print("  longo e drawdown maior -- conferir abaixo.")

print("\n  duracao mediana em bricks, por geometria:")
for alvo, stop in [(150, 100), (200, 100), (250, 100), (300, 100), (200, 150)]:
    yB, nB, yA, nA = C.resultados(df, float(alvo), float(stop))
    y = np.where(lado == 1, yB[i], yA[i])
    bb = np.where(lado == 1, nB[i], nA[i])
    m = sel & ~np.isnan(y)
    pnl = np.where(y[m][np.argsort(i[m])] > 0, alvo, -stop)
    eq = np.cumsum(pnl - 10.0)
    dd = (eq - np.maximum.accumulate(eq)).min()
    po, ne = (pnl - 10)[pnl - 10 > 0], (pnl - 10)[pnl - 10 < 0]
    print("    %3d/%3d  mediana %3.0f bricks | com 10 pts de custo: %+6.1f pts/trade  maxDD %6.0f  PF %.2f"
          % (alvo, stop, np.nanmedian(bb[m]), eq[-1] / m.sum(), dd,
             po.sum() / abs(ne.sum())))

print("\n" + "=" * 110)
print("b) CONFLUENCIA COM A REGRA RenkoViradaR11")
print("=" * 110)
yB, nB, yA, nA = C.resultados(df, 150.0, 100.0)
y = np.where(lado == 1, yB[i], yA[i])
val = ~np.isnan(y)
dposR = dirn * (c - meio) / faixa
selR = ((is_rev == 1) & (seqb >= 3) & (df.qt.values > 0) & (df.newday.values == 0) &
        (hhmm >= 1000) & (dposR >= 0.25))
iR = np.where(selR)[0]
conf = np.array([np.any(np.abs(iR - x) <= 1) for x in i])


def av(m, nome):
    m = m & val
    yy, dd = y[m], data[i][m]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(yy[dd < corte]); nv, pv = f(yy[dd >= corte]); na, pa = f(yy)
    print("  %-40s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
          % (nome, nt, pt, nv, pv, na, pa, pa * 150 - (1 - pa) * 100))


av(sel, "PivoR11 (todos)")
av(sel & conf, "  com RenkoViradaR11 na vizinhanca")
av(sel & ~conf, "  SEM RenkoViradaR11 na vizinhanca")
print("\n  -> confluencia so vale se a primeira linha ficar claramente acima da")
print("     terceira NAS DUAS colunas (treino e teste).")

print("\n" + "=" * 110)
print("c) O FILTRO DE RELOGIO AJUDA AQUI?")
print("=" * 110)
for t in [0, 930, 1000, 1100]:
    av(sel & (hhmm[i] >= t), "Time >= %d" % t)
for t in [1700, 1730, 1745]:
    av(sel & (hhmm[i] <= t), "Time <= %d" % t)

print("\n" + "=" * 110)
print("d) DE ONDE VEM A VANTAGEM DE 'SEM RenkoViradaR11 NA VIZINHANCA'?")
print("=" * 110)
av(sel & (hhmm[i] < 1000), "primeira hora (Time < 1000)")
av(sel & (hhmm[i] >= 1000) & (hhmm[i] < 1200), "10h-12h")
av(sel & (hhmm[i] >= 1200) & (hhmm[i] < 1500), "12h-15h")
av(sel & (hhmm[i] >= 1500), "depois das 15h")
print()
for t in [1, 2, 3, 4]:
    av(sel & (seqb[j] < t), "seq_before < %d" % t)
    av(sel & (seqb[j] >= t), "seq_before >= %d" % t)
print()
av(sel & (is_rev[j] == 1), "brick do pivo e REVERSAO")
av(sel & (is_rev[j] == 0), "brick do pivo e CONTINUACAO")
