#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 3: isolar o que carrega o sinal, montar a regra e testar robustez.

Suspeita a checar: cAbs>0 e cPav alto podem nao medir absorcao nem rejeicao,
e sim apenas o TIPO do brick do pivo (reversao x continuacao) -- que no Renko
determina pavio e posicao do fechamento por construcao.
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

h, l, c, o = df.h.values, df.l.values, df.c.values, df.o.values
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

P = dict(C.PADRAO, Esquerda=3, Direita=1, TolerPivoFrac=0.0)
K = C.componentes(df, b, P)
dB, dA = C.divergencia(df, b, K, P)
d = P["Direita"]
jB = np.where(K["pb"])[0]; jB = jB[jB + d < n]
jA = np.where(K["pa"])[0]; jA = jA[jA + d < n]
lado = np.r_[np.ones(len(jB), int), -np.ones(len(jA), int)]
j = np.r_[jB, jA]
srt = np.argsort(j, kind="stable")
lado, j = lado[srt], j[srt]
i = j + d
y = np.where(lado == 1, yB[i], yA[i])
dia = data[i]
val = ~np.isnan(y)

pos_op = lado * (c[j] - meio[j]) / faixa[j]
tipo_ok = (dirn[j] == lado)              # brick do pivo ja aponta para o trade
rev_ok = tipo_ok & (is_rev[j] == 1)      # ... e e o brick de reversao
cDiv = np.where(lado == 1, dB[j], dA[j])
cAbs = np.where(lado == 1, K["cAbsB"][j], K["cAbsA"][j])
cPav = np.where(lado == 1, K["cPavB"][j], K["cPavA"][j])
cClx = K["cClx"][j]
cCmp = K["cCmp"][j]
cFlip = np.where(lado == 1, K["cFlipB"][j], K["cFlipA"][j])
deltaN = b["deltaN"]
fluxo = lado * deltaN[j]                 # agressao a favor do trade, no pivo
fluxo_conf = lado * deltaN[i]            # agressao na barra de confirmacao


def avalia(nome, sel, mostrar=True):
    m = sel & val
    yt = y[m & (dia < corte)]
    yv = y[m & (dia >= corte)]
    ya = y[m]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(yt); nv, pv = f(yv); na, pa = f(ya)
    e = pa * ALVO - (1 - pa) * STOP
    if mostrar:
        print("  %-46s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
              % (nome, nt, pt, nv, pv, na, pa, e))
    return na, pa, pt, pv


todos = np.ones(n if False else len(j), bool)
print("=" * 118)
print("1. E ABSORCAO/REJEICAO OU E SO O TIPO DO BRICK?  (Esq=3 Dir=1 Toler=0)")
print("=" * 118)
avalia("todo pivo", todos)
avalia("cAbs > 0", cAbs > 0)
avalia("cPav > 0.90", cPav > 0.90)
print()
avalia("brick do pivo ja aponta para o trade", tipo_ok)
avalia("... e e brick de REVERSAO", rev_ok)
avalia("brick do pivo aponta CONTRA o trade", ~tipo_ok)
print()
avalia("cAbs>0 DENTRO de tipo_ok", tipo_ok & (cAbs > 0))
avalia("cAbs=0 DENTRO de tipo_ok", tipo_ok & (cAbs <= 0))
avalia("cPav>0.90 DENTRO de tipo_ok", tipo_ok & (cPav > 0.90))
print("\n  -> se as duas linhas 'DENTRO de tipo_ok' empatam, cAbs/cPav nao")
print("     acrescentam nada: eram apenas o tipo do brick disfarcado.")

print("\n" + "=" * 118)
print("2. EMPILHAMENTO A PARTIR DE tipo_ok")
print("=" * 118)
m = todos.copy();          avalia("todo pivo", m)
m = m & tipo_ok;           avalia("+ brick aponta para o trade", m)
for t in [0.0, 0.10, 0.20, 0.25, 0.30, 0.35]:
    avalia("  + pos_op >= %.2f" % t, m & (pos_op >= t))
print()
mm = m & (pos_op >= 0.20)
avalia("BASE: tipo_ok + pos_op>=0.20", mm)
for nome, extra in [("+ cDiv > 0", cDiv > 0),
                    ("+ cDiv >= 0.6", cDiv >= 0.6),
                    ("+ cClx > 0.30", cClx > 0.30),
                    ("+ cCmp > 0", cCmp > 0),
                    ("+ fluxo no pivo >= 0", fluxo >= 0),
                    ("+ fluxo na confirmacao >= 0", fluxo_conf >= 0),
                    ("+ fluxo na confirmacao >= 0.10", fluxo_conf >= 0.10),
                    ("+ seq_before >= 3", seqb[j] >= 3),
                    ("+ seq_before >= 4", seqb[j] >= 4),
                    ("+ Time >= 1000", hhmm[i] >= 1000),
                    ("+ Time <= 1600", hhmm[i] <= 1600)]:
    avalia(nome, mm & extra)

print("\n" + "=" * 118)
print("3. SENSIBILIDADE DE Esquerda E pos_op  (plateau ou pico?)")
print("=" * 118)
print("  %-8s" % "Esq", end="")
for t in [0.10, 0.15, 0.20, 0.25, 0.30]:
    print(" %14s" % ("pos>=%.2f" % t), end="")
print()
for esq in [2, 3, 4, 5]:
    Pe = dict(C.PADRAO, Esquerda=esq, Direita=1, TolerPivoFrac=0.0)
    Ke = C.componentes(df, b, Pe)
    jb = np.where(Ke["pb"])[0]; jb = jb[jb + 1 < n]
    ja = np.where(Ke["pa"])[0]; ja = ja[ja + 1 < n]
    la = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    jj = np.r_[jb, ja]
    s = np.argsort(jj, kind="stable"); la, jj = la[s], jj[s]
    ii = jj + 1
    yy = np.where(la == 1, yB[ii], yA[ii])
    po = la * (c[jj] - meio[jj]) / faixa[jj]
    tk = dirn[jj] == la
    vv = ~np.isnan(yy)
    print("  %-8d" % esq, end="")
    for t in [0.10, 0.15, 0.20, 0.25, 0.30]:
        mk = vv & tk & (po >= t)
        print(" %6.4f/%5d" % (yy[mk].mean(), mk.sum()), end="")
    print()

print("\n" + "=" * 118)
print("4. REGRA FINAL -- detalhamento")
print("=" * 118)
fin = todos & tipo_ok & (pos_op >= 0.20)
na, pa, pt, pv = avalia("REGRA", fin)
mf = fin & val
print("\n  %d sinais em %d pregoes = %.2f/pregao | pregoes sem sinal: %d"
      % (mf.sum(), len(dias), mf.sum() / len(dias),
         len(dias) - len(np.unique(dia[mf]))))
print("  duracao mediana ate resolver: %.0f bricks" % np.nanmedian(
    np.where(lado[mf] == 1, nBr[i[mf]], nAr[i[mf]])))
print("  compras: %.4f (n=%d) | vendas: %.4f (n=%d)"
      % (y[mf & (lado == 1)].mean(), (mf & (lado == 1)).sum(),
         y[mf & (lado == -1)].mean(), (mf & (lado == -1)).sum()))
print("  brick de reversao: %.4f (n=%d) | continuacao: %.4f (n=%d)"
      % (y[mf & rev_ok].mean(), (mf & rev_ok).sum(),
         y[mf & ~rev_ok].mean(), (mf & ~rev_ok).sum()))

pnl = np.where(y[mf] > 0, ALVO, -STOP)
ordem = np.argsort(i[mf])
pnl = pnl[ordem]
print("\n  custo   total      pts/trade   maxDD     PF")
for cu in [0, 2, 5, 10, 15, 20]:
    eq = np.cumsum(pnl - cu)
    dd = eq - np.maximum.accumulate(eq)
    pos, neg = (pnl - cu)[pnl - cu > 0], (pnl - cu)[pnl - cu < 0]
    print("  %2d pts  %+7.0f    %+7.1f    %6.0f   %.2f"
          % (cu, eq[-1], eq[-1] / len(pnl), dd.min(),
             pos.sum() / abs(neg.sum()) if len(neg) else np.inf))

print("\n" + "=" * 118)
print("5. ROBUSTEZ")
print("=" * 118)
rng = np.random.default_rng(11)
ds = np.unique(dia[mf])
por_dia = {k: y[mf][dia[mf] == k] for k in ds}
boot = []
for _ in range(4000):
    pick = rng.choice(ds, len(ds), replace=True)
    v = np.concatenate([por_dia[k] for k in pick])
    boot.append(v.mean())
boot = np.array(boot)
print("  bootstrap POR PREGAO (%d pregoes): media %.4f  IC95%% [%.4f ; %.4f]"
      % (len(ds), boot.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5)))
print("  P(acerto <= breakeven %.3f) = %.4f" % (BE, (boot <= BE).mean()))

# aleatorizacao do rotulo DENTRO do pregao
obs = y[mf].mean()
cnt = 0
for _ in range(4000):
    sim = []
    for k in ds:
        pool = y[val & (dia == k)]
        nsel = (mf & (dia == k)).sum()
        if len(pool) and nsel:
            sim.append(rng.choice(pool, nsel, replace=False) if nsel <= len(pool)
                       else rng.choice(pool, nsel, replace=True))
    if len(np.concatenate(sim)) and np.concatenate(sim).mean() >= obs:
        cnt += 1
print("  aleatorizacao dentro do pregao: p = %.4f" % (cnt / 4000))

blocos = np.array_split(ds, 5)
print("  walk-forward por blocos de pregoes:")
for bi, bl in enumerate(blocos):
    mb = mf & np.isin(dia, bl)
    print("    bloco %d (%s a %s): n=%3d acerto %.4f  %+6.1f pts/trade"
          % (bi + 1, bl[0], bl[-1], mb.sum(), y[mb].mean(),
             y[mb].mean() * ALVO - (1 - y[mb].mean()) * STOP))
