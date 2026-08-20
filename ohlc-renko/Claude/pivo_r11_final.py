#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 4: fechar os parametros.

Esquerda ainda subia em 5 -- estender. cDiv>=0.6 (divergencia com nova extrema)
foi o unico componente do score original que se manteve no teste. Montar a
regra em torno dele, medir com MinBarras, checar equilibrio entre os lados e
rodar a robustez completa.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_core as C

ALVO, STOP = 150.0, 100.0
BE = STOP / (ALVO + STOP)

df = C.carregar()
b = C.base(df, normalizar=1)
n = len(df)
dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
data = df.dt.dt.date.values
yB, nBr, yA, nAr = C.resultados(df, ALVO, STOP)

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

CACHE = {}


def sinais(esq, look=60, direita=1, toler=0.0):
    key = (esq, look, direita, toler)
    if key in CACHE:
        return CACHE[key]
    P = dict(C.PADRAO, Esquerda=esq, Direita=direita,
             TolerPivoFrac=toler, DivLookback=look)
    K = C.componentes(df, b, P)
    dB, dA = C.divergencia(df, b, K, P)
    jb = np.where(K["pb"])[0]; jb = jb[jb + direita < n]
    ja = np.where(K["pa"])[0]; ja = ja[ja + direita < n]
    la = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    jj = np.r_[jb, ja]
    s = np.argsort(jj, kind="stable")
    la, jj = la[s], jj[s]
    ii = jj + direita
    out = dict(lado=la, j=jj, i=ii,
               y=np.where(la == 1, yB[ii], yA[ii]),
               bars=np.where(la == 1, nBr[ii], nAr[ii]),
               dia=data[ii],
               pos=la * (c[jj] - meio[jj]) / faixa[jj],
               tipo=(dirn[jj] == la),
               cDiv=np.where(la == 1, dB[jj], dA[jj]),
               cClx=K["cClx"][jj],
               seq=seqb[jj], hhmm=hhmm[ii],
               fconf=la * b["deltaN"][ii])
    out["val"] = ~np.isnan(out["y"])
    CACHE[key] = out
    return out


def av(S, sel, nome=None):
    m = sel & S["val"]
    y, dia = S["y"][m], S["dia"][m]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(y[dia < corte]); nv, pv = f(y[dia >= corte]); na, pa = f(y)
    if nome:
        print("  %-46s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
              % (nome, nt, pt, nv, pv, na, pa, pa * ALVO - (1 - pa) * STOP))
    return na, pa, pt, pv


print("=" * 118)
print("1. Esquerda ATE ONDE?  (Dir=1, Toler=0, tipo_ok + pos>=0.25)")
print("=" * 118)
for esq in [3, 4, 5, 6, 8, 10, 12, 15]:
    S = sinais(esq)
    m = S["tipo"] & (S["pos"] >= 0.25)
    na, pa, pt, pv = av(S, m)
    print("  Esq=%-3d n=%5d (%5.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
          % (esq, na, na / len(dias), pt, pv, pa, pa * ALVO - (1 - pa) * STOP))
print("\n  -> Esquerda grande = pivo mais raro e mais 'fundo'. O ganho vem de")
print("     exigir extrema local mais significativa, nao do score.")

print("\n" + "=" * 118)
print("2. DIVERGENCIA (cDiv) EM CADA Esquerda")
print("=" * 118)
for esq in [3, 4, 5, 6, 8]:
    S = sinais(esq)
    for lk in [40, 60, 100]:
        S2 = sinais(esq, look=lk)
        m = S2["tipo"] & (S2["cDiv"] >= 0.6)
        na, pa, pt, pv = av(S2, m)
        if na < 100:
            continue
        print("  Esq=%-3d Lookback=%-4d n=%5d (%5.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
              % (esq, lk, na, na / len(dias), pt, pv, pa,
                 pa * ALVO - (1 - pa) * STOP))

print("\n" + "=" * 118)
print("3. cDiv COMBINADO COM pos_op")
print("=" * 118)
for esq in [4, 5, 6]:
    S = sinais(esq)
    print("  --- Esquerda = %d ---" % esq)
    av(S, S["tipo"] & (S["cDiv"] >= 0.6), "cDiv>=0.6")
    for t in [0.0, 0.10, 0.20, 0.25]:
        av(S, S["tipo"] & (S["cDiv"] >= 0.6) & (S["pos"] >= t),
           "cDiv>=0.6 + pos>=%.2f" % t)
    av(S, S["tipo"] & (S["cDiv"] >= 1.0), "cDiv=1.0 (nova extrema + cumd)")
    av(S, S["tipo"] & (S["cDiv"] >= 1.0) & (S["pos"] >= 0.10),
       "cDiv=1.0 + pos>=0.10")

print("\n" + "=" * 118)
print("4. DUAS ROTAS ALTERNATIVAS -- OU divergencia OU contexto forte")
print("=" * 118)
S = sinais(5)
rotaA = S["tipo"] & (S["cDiv"] >= 0.6)
rotaB = S["tipo"] & (S["pos"] >= 0.25)
av(S, rotaA, "A: divergencia")
av(S, rotaB, "B: contexto de pregao")
av(S, rotaA & rotaB, "A e B")
av(S, rotaA | rotaB, "A ou B")

print("\n" + "=" * 118)
print("5. EQUILIBRIO ENTRE OS LADOS  (o periodo tem vies?)")
print("=" * 118)
tot = df.c.values[-1] - df.c.values[0]
print("  variacao do WIN no periodo: %+.0f pts" % tot)
for nome, m in [("A: divergencia", rotaA), ("B: contexto", rotaB),
                ("A ou B", rotaA | rotaB)]:
    for lab, lm in [("compra", S["lado"] == 1), ("venda", S["lado"] == -1)]:
        na, pa, pt, pv = av(S, m & lm)
        print("  %-18s %-8s n=%4d  tr %.4f  te %.4f  tudo %.4f"
              % (nome, lab, na, pt, pv, pa))
