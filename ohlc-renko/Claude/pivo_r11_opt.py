#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 2: onde esta o sinal, de fato.

Ordem de investigacao:
  1. geometria do pivo (Esquerda / Direita / TolerPivoFrac) -- sem score
  2. o que se acrescenta por cima: contexto do pregao, relogio, tamanho da
     perna contrariada, e os componentes de fluxo do score original
  3. re-derivacao dos pesos para o R11
  4. escolha de MinScore no treino, com verificacao de plateau
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

# ---- contexto do pregao (o achado do estudo r11) -------------------------
h, l, c = df.h.values, df.l.values, df.c.values
dayid = pd.factorize(data)[0]
dhi = np.empty(n); dlo = np.empty(n)
hi = lo = np.nan
for i in range(n):
    if i == 0 or dayid[i] != dayid[i - 1]:
        hi, lo = h[i], l[i]
    else:
        hi, lo = max(hi, h[i]), min(lo, l[i])
    dhi[i], dlo[i] = hi, lo
faixa = np.maximum(dhi - dlo, C.BODY)
meio = (dhi + dlo) / 2.0
hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values
seqb = df.seq_before.values


def stats(y):
    if len(y) == 0:
        return 0, np.nan, np.nan
    p = y.mean()
    return len(y), p, p * ALVO - (1 - p) * STOP


def avalia(nome, sel, lado_arr, iidx, quiet=False):
    """sel: mascara sobre a lista de sinais. lado_arr/iidx: lado e barra de entrada."""
    y = np.where(lado_arr[sel] == 1, yB[iidx[sel]], yA[iidx[sel]])
    d = data[iidx[sel]]
    m = ~np.isnan(y)
    y, d = y[m], d[m]
    nt, pt, et = stats(y[d < corte])
    nv, pv, ev = stats(y[d >= corte])
    na, pa, ea = stats(y)
    if not quiet:
        print("  %-44s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
              % (nome, nt, pt, nv, pv, na, pa, ea))
    return na, pa, pt, pv


def pivos(P):
    """lista de sinais (lado, j, i) para todo pivo, sem score."""
    K = C.componentes(df, b, P)
    d = P["Direita"]
    jB = np.where(K["pb"])[0]; jB = jB[jB + d < n]
    jA = np.where(K["pa"])[0]; jA = jA[jA + d < n]
    lado = np.r_[np.ones(len(jB), int), -np.ones(len(jA), int)]
    j = np.r_[jB, jA]
    o = np.argsort(j, kind="stable")
    return K, lado[o], j[o], j[o] + d


print("=" * 116)
print("1. GEOMETRIA DO PIVO, SEM SCORE  (alvo %d / stop %d, breakeven %.3f)"
      % (ALVO, STOP, BE))
print("=" * 116)
melhor = None
for esq in [1, 2, 3, 4]:
    for dta in [1, 2, 3]:
        for tolf in [0.0, 0.30, 0.60]:
            P = dict(C.PADRAO, Esquerda=esq, Direita=dta, TolerPivoFrac=tolf)
            K, lado, j, i = pivos(P)
            na, pa, pt, pv = avalia("Esq=%d Dir=%d Toler=%.2f" % (esq, dta, tolf),
                                    np.ones(len(j), bool), lado, i, quiet=True)
            if na >= 400:
                print("  Esq=%d Dir=%d Toler=%.2f  n=%5d (%5.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
                      % (esq, dta, tolf, na, na / len(dias), pt, pv, pa,
                         pa * ALVO - (1 - pa) * STOP))

print("\n" + "=" * 116)
print("2. O QUE ACRESCENTA POR CIMA DO PIVO  (base: Esq=2 Dir=1 Toler=0.30)")
print("=" * 116)
P = dict(C.PADRAO, Esquerda=2, Direita=1, TolerPivoFrac=0.30)
K, lado, j, i = pivos(P)
dB, dA = C.divergencia(df, b, K, P)

# contexto medido NA BARRA DO PIVO j (que ja fechou quando a seta sai)
dpos = lado * (c[j] - meio[j]) / faixa[j]
dposj = np.where(lado == 1, (meio[j] - c[j]) / faixa[j], (c[j] - meio[j]) / faixa[j])
# dpos "de retomada": pivo de baixa -> compra -> so vale se o dia e de alta.
# posicao do fechamento do pivo no range do dia, no sentido da OPERACAO:
pos_op = lado * (c[j] - meio[j]) / faixa[j]
# extremo do dia: pivo de baixa perto da minima do dia = fundo do dia
prox_extremo = np.where(lado == 1, (c[j] - dlo[j]) / faixa[j], (dhi[j] - c[j]) / faixa[j])

comp = dict(cDiv=np.where(lado == 1, dB[j], dA[j]),
            cAbs=np.where(lado == 1, K["cAbsB"][j], K["cAbsA"][j]),
            cClx=K["cClx"][j],
            cFlip=np.where(lado == 1, K["cFlipB"][j], K["cFlipA"][j]),
            cCmp=K["cCmp"][j],
            cPav=np.where(lado == 1, K["cPavB"][j], K["cPavA"][j]))

todos = np.ones(len(j), bool)
avalia("(todo pivo)", todos, lado, i)
print()
print("  -- contexto do pregao --")
for t in [-0.10, 0.0, 0.10, 0.20]:
    avalia("pos_op >= %+.2f (retomada da direcao do dia)" % t, pos_op >= t, lado, i)
print()
for t in [0.10, 0.20, 0.30]:
    avalia("prox_extremo <= %.2f (pivo na extrema do dia)" % t, prox_extremo <= t, lado, i)
print()
print("  -- relogio --")
for t in [930, 1000, 1100, 1200]:
    avalia("Time >= %d" % t, hhmm[i] >= t, lado, i)
print()
print("  -- tamanho da perna contrariada --")
for t in [2, 3, 4, 5]:
    avalia("seq_before >= %d" % t, seqb[j] >= t, lado, i)
print()
print("  -- componentes de fluxo do score original --")
for k, v in comp.items():
    med = np.median(v)
    avalia("%s acima da mediana (%.3f)" % (k, med), v > med, lado, i)

print("\n" + "=" * 116)
print("3. EMPILHAMENTO  (cada linha soma um filtro a anterior)")
print("=" * 116)
m = todos.copy()
avalia("todo pivo", m, lado, i)
m = m & (seqb[j] >= 3)
avalia("+ seq_before >= 3", m, lado, i)
m = m & (hhmm[i] >= 1000)
avalia("+ Time >= 1000", m, lado, i)
m = m & (pos_op >= 0.10)
avalia("+ pos_op >= 0.10", m, lado, i)
for t in [0.15, 0.20, 0.25, 0.30]:
    avalia("   (pos_op >= %.2f no lugar de 0.10)" % t,
           todos & (seqb[j] >= 3) & (hhmm[i] >= 1000) & (pos_op >= t), lado, i)

print("\n" + "=" * 116)
print("4. RE-DERIVACAO DOS PESOS  (correlacao de cada componente com o acerto,")
print("   medida SO no treino, dentro do conjunto ja filtrado)")
print("=" * 116)
mfin = todos & (seqb[j] >= 3) & (hhmm[i] >= 1000)
yy = np.where(lado == 1, yB[i], yA[i])
ok = mfin & ~np.isnan(yy)
tr = ok & (data[i] < corte)
te = ok & (data[i] >= corte)


def auc(x, y):
    r = pd.Series(x).rank().values
    n1, n0 = (y == 1).sum(), (y == 0).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


print("  n treino=%d  teste=%d   acerto treino=%.4f" % (tr.sum(), te.sum(), yy[tr].mean()))
print("\n  %-12s %9s %9s   %s" % ("variavel", "AUC tr", "AUC te", "acerto no quartil alto (tr/te)"))
cands = dict(comp)
cands["pos_op"] = pos_op
cands["prox_extremo"] = -prox_extremo
cands["seq_before"] = seqb[j].astype(float)
for k, v in sorted(cands.items()):
    at, av = auc(v[tr], yy[tr]), auc(v[te], yy[te])
    q = np.quantile(v[tr], 0.75)
    pt = yy[tr & (v > q)].mean() if (tr & (v > q)).sum() > 20 else np.nan
    pv = yy[te & (v > q)].mean() if (te & (v > q)).sum() > 20 else np.nan
    print("  %-12s %9.4f %9.4f   %.4f / %.4f" % (k, at, av, pt, pv))
