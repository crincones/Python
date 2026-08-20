#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostico: quais componentes do PivoReversao_Claude sobrevivem ao Renko R11.

O indicador foi escrito para barra de TICKS, onde High/Low/Close sao livres.
No Renko R11 a barra e construida: corpo fixo de 10 ticks, abertura amarrada
ao brick anterior, fechamento no gatilho. Varias metricas do score viram
constantes ou viram apenas um proxy do TIPO do brick (continuacao x reversao).
Este script mede isso antes de qualquer otimizacao.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import r11_virada as V

TICK = V.TICK
df = V.geometria(V.carregar(V.CSV_DEFAULT))
n = len(df)
o, h, l, c = df.o.values, df.h.values, df.l.values, df.c.values
dirn, is_rev = df.dirn.values, df.is_rev.values

print("=" * 100)
print("BASE: %d bricks | %s a %s | %d pregoes"
      % (n, df.dt.min().date(), df.dt.max().date(), df.dt.dt.date.nunique()))
print("=" * 100)

rng = h - l
print("\n1. RANGE (High-Low) -- entra em zRng, mRng, tol, e no denominador de tudo")
print("   continuacao: mediana %5.1f pts  p10 %5.1f  p90 %5.1f  (n=%d)"
      % (np.median(rng[is_rev == 0]), np.percentile(rng[is_rev == 0], 10),
         np.percentile(rng[is_rev == 0], 90), (is_rev == 0).sum()))
print("   reversao   : mediana %5.1f pts  p10 %5.1f  p90 %5.1f  (n=%d)"
      % (np.median(rng[is_rev == 1]), np.percentile(rng[is_rev == 1], 10),
         np.percentile(rng[is_rev == 1], 90), (is_rev == 1).sum()))
sep = (rng[is_rev == 1].mean() - rng[is_rev == 0].mean()) / rng.std()
print("   -> separacao entre os dois tipos: %.2f desvios. zRng mede TIPO DE BRICK." % sep)

# posFech / posTopo
pf = np.where(rng > 0, (c - l) / np.maximum(rng, 1e-9), 0.5)
print("\n2. posFech = (Close-Low)/range -- entra em cAbs e no cFlip de Direita=0")
for nome, m in [("brick de ALTA", dirn > 0), ("brick de BAIXA", dirn < 0)]:
    x = pf[m]
    print("   %-15s mediana %.3f | fracao exatamente 0 ou 1: %.1f%%"
          % (nome, np.median(x), 100 * np.mean((x < 1e-9) | (x > 1 - 1e-9))))
print("   -> no Renko o brick FECHA no gatilho: Close==High na alta, Close==Low na baixa.")

# pavios
cmin = np.minimum(o, c)
cmax = np.maximum(o, c)
pinf = (cmin - l) / np.maximum(rng, 1e-9)
psup = (h - cmax) / np.maximum(rng, 1e-9)
print("\n3. PAVIOS -- entram em cPav")
print("   %-32s %8s %8s %8s %8s" % ("", "pavInf", "pavSup", "medInf", "medSup"))
for nome, m in [("alta continuacao", (dirn > 0) & (is_rev == 0)),
                ("alta reversao   ", (dirn > 0) & (is_rev == 1)),
                ("baixa continuacao", (dirn < 0) & (is_rev == 0)),
                ("baixa reversao  ", (dirn < 0) & (is_rev == 1))]:
    print("   %-32s %8.3f %8.3f %8.3f %8.3f"
          % (nome, pinf[m].mean(), psup[m].mean(), np.median(pinf[m]), np.median(psup[m])))
print("   -> o pavio do lado da origem e ESTRUTURAL: a reversao precisa andar")
print("      20 ticks contra 10 da continuacao, entao nasce com 10 ticks de pavio.")
print("      cPav num pivo de baixa (compra) mede 'este brick e reversao', nao rejeicao.")

# quanto do pavio e excedente real
wn = df.wick_net.values
print("\n   pavio liquido (acima do piso estrutural), em ticks:")
for nome, m in [("continuacao", is_rev == 0), ("reversao", is_rev == 1)]:
    print("     %-12s mediana %4.1f  p75 %4.1f  p90 %4.1f  fracao zero %.1f%%"
          % (nome, np.median(wn[m]), np.percentile(wn[m], 75),
             np.percentile(wn[m], 90), 100 * np.mean(wn[m] <= 0)))

# agressao
agtot = df.agtot.values
qt = df.qt.values
print("\n4. AGRESSAO -- entra em zAgrC, zAgrV, deseq, cumd, deltaN")
print("   volume SEM agressor identificado: %.1f%% do total"
      % (100 * (qt - agtot).clip(0).sum() / qt.sum()))
cor = np.corrcoef(df.unk_share.values, np.log(np.maximum(qt, 1)))[0, 1]
print("   corr(fracao sem agressor, log Quantity) = %+.3f" % cor)
print("   -> normalizar por Quantity dilui o delta nos bricks grandes.")
print("      pC=agrC/(agrC+agrV) (NormalizarAgressao=1) e a forma correta aqui.")

pC = np.where(agtot > 0, df.agb.values / np.maximum(agtot, 1), 0.5)
print("   pC por tipo de brick: alta %.3f | baixa %.3f  (dif %.3f)"
      % (pC[dirn > 0].mean(), pC[dirn < 0].mean(), pC[dirn > 0].mean() - pC[dirn < 0].mean()))

# duracao
dur = df.dur.values
print("\n5. BarDurationF -- entra em zVel (climax)")
print("   mediana %.2f min | p90 %.2f | p99 %.2f | max %.1f"
      % (np.median(dur), np.percentile(dur, 90), np.percentile(dur, 99), dur.max()))
print("   continuacao %.2f x reversao %.2f (mediana)"
      % (np.median(dur[is_rev == 0]), np.median(dur[is_rev == 1])))
print("   -> valido: o brick R11 tem tamanho fixo, entao a duracao mede velocidade pura.")

# frequencia de pivos com Direita=0
print("\n6. TESTE DE PIVO COM Direita=0 (default do arquivo original)")
for esq in [2, 3, 4]:
    pb = np.ones(n, bool)
    pa = np.ones(n, bool)
    for k in range(1, esq + 1):
        pb[esq:] &= l[esq:] <= l[esq - k:n - k]
        pa[esq:] &= h[esq:] >= h[esq - k:n - k]
    pb[:esq] = False
    pa[:esq] = False
    print("   Esquerda=%d -> pivo de baixa em %.1f%% dos bricks | pivo de alta em %.1f%%"
          % (esq, 100 * pb.mean(), 100 * pa.mean()))
print("   -> numa sequencia Renko TODO brick faz nova extrema no sentido da perna.")
print("      Sem barra de confirmacao o 'pivo' dispara o tempo todo dentro da")
print("      tendencia. Direita >= 1 nao e opcional no Renko, e obrigatorio.")

# com Direita=1
print("\n   com Direita=1 e TolerPivoFrac=0.30:")
mr = pd.Series(rng).rolling(50).mean().values
for esq in [1, 2, 3]:
    pb = np.zeros(n, bool)
    pa = np.zeros(n, bool)
    for j in range(esq, n - 1):
        if np.isnan(mr[j]):
            continue
        tol = 0.30 * mr[j]
        ok = all(l[j] <= l[j - k] for k in range(1, esq + 1)) and (l[j] <= l[j + 1] + tol)
        if ok:
            pb[j] = True
        ok = all(h[j] >= h[j - k] for k in range(1, esq + 1)) and (h[j] >= h[j + 1] - tol)
        if ok:
            pa[j] = True
    print("     Esquerda=%d -> baixa %.1f%% | alta %.1f%%" % (esq, 100 * pb.mean(), 100 * pa.mean()))
