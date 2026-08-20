#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 5: consolidacao.

  a) MinBarras -- afinar a densidade de setas
  b) um score RE-PESADO para o R11 ainda acrescenta algo sobre o contexto?
  c) o lado vendedor e mais fraco: vale separar limiares?
  d) robustez completa da regra escolhida
  e) comparacao com a regra do estudo RenkoViradaR11 (brick contrario)
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_core as C

ALVO, STOP = 150.0, 100.0
BE = STOP / (ALVO + STOP)
ESQ, DIR = 6, 1

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

P = dict(C.PADRAO, Esquerda=ESQ, Direita=DIR, TolerPivoFrac=0.0)
K = C.componentes(df, b, P)
dB, dA = C.divergencia(df, b, K, P)
jb = np.where(K["pb"])[0]; jb = jb[jb + DIR < n]
ja = np.where(K["pa"])[0]; ja = ja[ja + DIR < n]
lado = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
j = np.r_[jb, ja]
s = np.argsort(j, kind="stable"); lado, j = lado[s], j[s]
i = j + DIR
y = np.where(lado == 1, yB[i], yA[i])
bars = np.where(lado == 1, nBr[i], nAr[i])
dia = data[i]
val = ~np.isnan(y)
pos = lado * (c[j] - meio[j]) / faixa[j]
tipo = dirn[j] == lado
cDiv = np.where(lado == 1, dB[j], dA[j])
cAbs = np.where(lado == 1, K["cAbsB"][j], K["cAbsA"][j])
cClx = K["cClx"][j]
cCmp = K["cCmp"][j]
cPav = np.where(lado == 1, K["cPavB"][j], K["cPavA"][j])
cFlip = np.where(lado == 1, K["cFlipB"][j], K["cFlipA"][j])
fconf = lado * b["deltaN"][i]


def av(sel, nome=None):
    m = sel & val
    yy, dd = y[m], dia[m]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(yy[dd < corte]); nv, pv = f(yy[dd >= corte]); na, pa = f(yy)
    if nome:
        print("  %-46s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
              % (nome, nt, pt, nv, pv, na, pa, pa * ALVO - (1 - pa) * STOP))
    return na, pa, pt, pv


def espaca(sel, minb):
    """aplica MinBarras por lado, em ordem cronologica (igual ao NTSL)."""
    out = np.zeros(len(sel), bool)
    ultC = ultV = -10 ** 9
    for k in np.where(sel)[0]:
        if lado[k] == 1:
            if i[k] - ultC >= minb:
                out[k] = True; ultC = i[k]
        else:
            if i[k] - ultV >= minb:
                out[k] = True; ultV = i[k]
    return out


base_sel = tipo & (pos >= 0.25)
print("=" * 118)
print("a) MinBarras  (Esq=%d Dir=%d Toler=0, tipo_ok + pos>=0.25)" % (ESQ, DIR))
print("=" * 118)
for mb in [0, 3, 5, 8, 12, 20]:
    sel = espaca(base_sel, mb)
    na, pa, pt, pv = av(sel)
    print("  MinBarras=%-3d n=%4d (%5.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
          % (mb, na, na / len(dias), pt, pv, pa, pa * ALVO - (1 - pa) * STOP))

print("\n" + "=" * 118)
print("b) UM SCORE RE-PESADO AINDA ACRESCENTA?  (pesos = lift medido no treino)")
print("=" * 118)
m0 = base_sel & val
tr = m0 & (dia < corte)


def auc(x, yy):
    r = pd.Series(x).rank().values
    n1, n0 = (yy == 1).sum(), (yy == 0).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


comps = dict(cDiv=cDiv, cAbs=cAbs, cClx=cClx, cFlip=cFlip, cCmp=cCmp,
             cPav=cPav, fconf=fconf, seq=seqb[j].astype(float), pos=pos)
print("  dentro do conjunto ja filtrado (n treino=%d):" % tr.sum())
pesos = {}
for k_, v in comps.items():
    a = auc(v[tr], y[tr])
    pesos[k_] = max(0.0, (a - 0.5)) * 200
    print("    %-8s AUC treino %.4f -> peso %5.1f | AUC teste %.4f"
          % (k_, a, pesos[k_], auc(v[m0 & (dia >= corte)], y[m0 & (dia >= corte)])))

sc = np.zeros(len(j))
tw = sum(pesos.values())
for k_, v in comps.items():
    if pesos[k_] > 0:
        r = pd.Series(v).rank(pct=True).values
        sc += pesos[k_] * r
if tw > 0:
    sc = 100 * sc / tw
print("\n  score re-pesado, cortes por quantil do TREINO:")
for q in [0.0, 0.25, 0.50, 0.75]:
    thr = np.quantile(sc[tr], q)
    av(base_sel & (sc >= thr), "  score >= q%.0f do treino (%.1f)" % (q * 100, thr))
print("\n  -> se as linhas nao sobem no teste, nao ha score a construir: o")
print("     contexto de pregao ja esgotou o que essa base tem.")

print("\n" + "=" * 118)
print("c) OS DOIS LADOS SEPARADOS")
print("=" * 118)
for lab, lm in [("compra", lado == 1), ("venda", lado == -1)]:
    print("  --- %s ---" % lab)
    for t in [0.15, 0.20, 0.25, 0.30, 0.35]:
        av(tipo & lm & (pos >= t), "pos >= %.2f" % t)

print("\n" + "=" * 118)
print("d) ROBUSTEZ DA REGRA ESCOLHIDA")
print("=" * 118)
MB = 5
sel = espaca(base_sel, MB) & val
print("  Esq=%d Dir=%d Toler=0 | tipo_ok | pos>=0.25 | MinBarras=%d" % (ESQ, DIR, MB))
na, pa, pt, pv = av(sel, "REGRA")
print("  %.2f sinais/pregao | mediana %.0f bricks ate resolver | pregoes sem sinal %d"
      % (sel.sum() / len(dias), np.nanmedian(bars[sel]),
         len(dias) - len(np.unique(dia[sel]))))
print("  compra %.4f (n=%d) | venda %.4f (n=%d)"
      % (y[sel & (lado == 1)].mean(), (sel & (lado == 1)).sum(),
         y[sel & (lado == -1)].mean(), (sel & (lado == -1)).sum()))

rng = np.random.default_rng(6)
ds = np.unique(dia[sel])
pd_ = {k_: y[sel][dia[sel] == k_] for k_ in ds}
boot = np.array([np.concatenate([pd_[k_] for k_ in rng.choice(ds, len(ds), True)]).mean()
                 for _ in range(4000)])
print("\n  bootstrap por pregao: media %.4f  IC95%% [%.4f ; %.4f]  P(<=BE)=%.4f"
      % (boot.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5),
         (boot <= BE).mean()))

obs = y[sel].mean()
cnt = 0
for _ in range(4000):
    sim = []
    for k_ in ds:
        pool = y[val & (dia == k_)]
        ns = (sel & (dia == k_)).sum()
        if len(pool) and ns:
            sim.append(rng.choice(pool, ns, replace=ns > len(pool)))
    if np.concatenate(sim).mean() >= obs:
        cnt += 1
print("  aleatorizacao do rotulo dentro do pregao: p = %.4f" % (cnt / 4000))

print("\n  walk-forward:")
for bi, bl in enumerate(np.array_split(ds, 5)):
    mb_ = sel & np.isin(dia, bl)
    p_ = y[mb_].mean()
    print("    bloco %d (%s a %s) n=%3d  %.4f  %+6.1f pts"
          % (bi + 1, bl[0], bl[-1], mb_.sum(), p_, p_ * ALVO - (1 - p_) * STOP))

pnl = np.where(y[sel][np.argsort(i[sel])] > 0, ALVO, -STOP)
print("\n  custo   total     pts/trade   maxDD     PF")
for cu in [0, 2, 5, 10, 15, 20]:
    eq = np.cumsum(pnl - cu)
    dd = eq - np.maximum.accumulate(eq)
    po, ne = (pnl - cu)[pnl - cu > 0], (pnl - cu)[pnl - cu < 0]
    print("  %2d pts  %+7.0f   %+7.1f    %6.0f   %.2f"
          % (cu, eq[-1], eq[-1] / len(pnl), dd.min(), po.sum() / abs(ne.sum())))

print("\n" + "=" * 118)
print("e) COMPARACAO COM A REGRA RenkoViradaR11 (brick contrario a seq>=3)")
print("=" * 118)
elig = (is_rev == 1) & (seqb >= 3) & (df.qt.values > 0) & (df.newday.values == 0)
dposR = dirn * (c - meio) / faixa
selR = elig & (hhmm >= 1000) & (dposR >= 0.25)
yR = np.where(dirn == 1, yB, yA)
mR = selR & ~np.isnan(yR)
dR = data[mR]
print("  RenkoViradaR11 : n=%4d (%4.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
      % (mR.sum(), mR.sum() / len(dias), yR[mR & (data < corte)].mean(),
         yR[mR & (data >= corte)].mean(), yR[mR].mean(),
         yR[mR].mean() * ALVO - (1 - yR[mR].mean()) * STOP))
print("  PivoR11 (esta) : n=%4d (%4.1f/preg)  tr %.4f  te %.4f  tudo %.4f %+6.1f"
      % (sel.sum(), sel.sum() / len(dias), pt, pv, pa,
         pa * ALVO - (1 - pa) * STOP))

# sobreposicao
ii_p = set(i[sel].tolist())
ii_r = set(np.where(mR)[0].tolist())
print("  barras de entrada em comum: %d de %d / %d" % (len(ii_p & ii_r), len(ii_p), len(ii_r)))
uni = sorted(ii_p | ii_r)
yu = np.array([yR[x] if x in ii_r else y[i == x][0] for x in uni])
print("  uniao das duas: n=%d  acerto %.4f  %+6.1f pts"
      % (len(yu), yu.mean(), yu.mean() * ALVO - (1 - yu.mean()) * STOP))
