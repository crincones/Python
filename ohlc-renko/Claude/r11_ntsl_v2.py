#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mede o custo de simplificar o indicador:
  - filtro de sessao pelo RELOGIO (Time >= 1000) no lugar de BarDurationF acumulado
  - max/min do dia por acumulador persistente (identico, mas sem varredura)
  - higiene reduzida: so Quantity > 0 e nao-primeiro-brick-do-dia
    (sai o filtro de quebra de encadeamento e o de duracao patologica)
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import r11_virada as V

BODY = V.BODY_PTS
K, S = 4, 2.0
A, ST = (K - 1) * BODY, S * BODY
BE = ST / (A + ST)

df = V.carregar(V.CSV_DEFAULT)
df = V.geometria(df)
n = len(df)
c, h, l, dirn = df.c.values, df.h.values, df.l.values, df.dirn.values
dayid = pd.factorize(df.dt.dt.date)[0]

dhi = np.empty(n); dlo = np.empty(n)
hi = lo = np.nan
for i in range(n):
    if i == 0 or dayid[i] != dayid[i - 1]:
        hi, lo = h[i], l[i]
    else:
        hi, lo = max(hi, h[i]), min(lo, l[i])
    dhi[i], dlo[i] = hi, lo
df["dpos"] = dirn * (c - (dhi + dlo) / 2.0) / np.maximum(dhi - dlo, BODY)
df["hhmm"] = df.dt.dt.hour * 100 + df.dt.dt.minute

dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]

hig_cheia = (df.qt > 0) & (df.newday == 0) & (df.brk == 0) & (df.dur <= 60)
hig_magra = (df.qt > 0) & (df.newday == 0)

CACHE = {}


def med(nome, sel):
    key = tuple(np.where(sel)[0][:5]) + (int(sel.sum()),)
    if key not in CACHE:
        CACHE[key] = V.rotular(df.assign(elig=sel.astype(int)), K, S)
    lab, bars = CACHE[key]
    x = df.assign(y=lab, bars=bars)
    x = x[sel.values & ~np.isnan(lab)]
    xt, xv = x[x.dt.dt.date < corte], x[x.dt.dt.date >= corte]
    f = lambda g: (len(g), g.y.mean(), g.y.mean() * A - (1 - g.y.mean()) * ST)
    nt, pt, et = f(xt); nv, pv, ev = f(xv); na, pa, ea = f(x)
    print("%-46s tr n=%4d %.4f %+6.1f | te n=%4d %.4f %+6.1f | tudo n=%4d %.4f %+6.1f"
          % (nome, nt, pt, et, nv, pv, ev, na, pa, ea, ))
    return x


base = (df.is_rev == 1) & (df.seq_before >= 3)
print("K=%d S=%.0f | alvo %d stop %d | breakeven %.3f\n" % (K, S, A, ST, BE))
print("=" * 122)
print("EFEITO DE CADA SIMPLIFICACAO (todas com dpos >= 0.25)")
print("=" * 122)
med("higiene cheia + BarDurationF acum >= 60 min", base & hig_cheia &
    (df.groupby(dayid).dur.cumsum().shift(1).fillna(0) >= 60) & (df.dpos >= 0.25))
med("higiene cheia + relogio Time >= 1000", base & hig_cheia & (df.hhmm >= 1000) & (df.dpos >= 0.25))
med("higiene MAGRA + relogio Time >= 1000", base & hig_magra & (df.hhmm >= 1000) & (df.dpos >= 0.25))
print()
print("=" * 122)
print("SENSIBILIDADE DO HORARIO NA VERSAO MAGRA (dpos >= 0.25)")
print("=" * 122)
for hm in [900, 930, 1000, 1030, 1100]:
    med("Time >= %d" % hm, base & hig_magra & (df.hhmm >= hm) & (df.dpos >= 0.25))
print()
print("=" * 122)
print("SENSIBILIDADE DO DPOS NA VERSAO MAGRA (Time >= 1000)")
print("=" * 122)
for dp in [0.15, 0.20, 0.25, 0.30, 0.35]:
    med("dpos >= %.2f" % dp, base & hig_magra & (df.hhmm >= 1000) & (df.dpos >= dp))
print()
print("=" * 122)
print("QUANTOS SINAIS A VERSAO MAGRA PRODUZ")
print("=" * 122)
sel = base & hig_magra & (df.hhmm >= 1000) & (df.dpos >= 0.25)
g = df[sel]
print("  %d sinais em %d pregoes = %.2f/pregao | pregoes sem sinal: %d"
      % (len(g), len(dias), len(g) / len(dias), len(dias) - g.dt.dt.date.nunique()))
print("  por hora:")
print(g.groupby(g.dt.dt.hour).size().to_string())
