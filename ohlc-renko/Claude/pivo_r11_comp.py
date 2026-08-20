#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 1: como o PivoReversao_Claude original se comporta no R11, e quanto cada
um dos seis componentes do score realmente discrimina.

Entrada no fechamento da barra de confirmacao (j + Direita) -- o primeiro
instante em que a seta e acionavel. Alvo 150 pts / stop 100 pts, primeiro
toque, stop testado antes do alvo. Breakeven 40,0%.
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

print("carregando resultados de primeiro toque para todas as barras...")
yB, nBr, yA, nAr = C.resultados(df, ALVO, STOP)


def auc(x, y):
    m = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[m], y[m]
    if len(np.unique(y)) < 2:
        return np.nan
    r = pd.Series(x).rank().values
    n1, n0 = (y == 1).sum(), (y == 0).sum()
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def coleta(P, minscore=None, minbarras=None):
    """Devolve DataFrame de sinais: lado, j, entrada i, score, componentes, y."""
    K = C.componentes(df, b, P)
    dB, dA = C.divergencia(df, b, K, P)
    sB, sA = C.score(K, dB, dA, P)
    ms = P["MinScore"] if minscore is None else minscore
    mb = P["MinBarras"] if minbarras is None else minbarras
    oB, oA = C.aplicar_minbarras(K, sB, sA, ms, mb)
    d = P["Direita"]
    regs = []
    for lado, sel, sc, cdiv, cabs, cflip, cpav in [
            (1, oB, sB, dB, K["cAbsB"], K["cFlipB"], K["cPavB"]),
            (-1, oA, sA, dA, K["cAbsA"], K["cFlipA"], K["cPavA"])]:
        j = np.where(sel)[0]
        j = j[j + d < n]
        i = j + d
        y = yB[i] if lado == 1 else yA[i]
        nb = nBr[i] if lado == 1 else nAr[i]
        regs.append(pd.DataFrame(dict(
            lado=lado, j=j, i=i, dt=df.dt.values[i], dia=data[i],
            score=sc[j], cDiv=cdiv[j], cAbs=cabs[j], cClx=K["cClx"][j],
            cFlip=cflip[j], cCmp=K["cCmp"][j], cPav=cpav[j], y=y, bars=nb)))
    g = pd.concat(regs).sort_values("i").reset_index(drop=True)
    return g[~g.y.isna()]


def linha(nome, g):
    if len(g) == 0:
        print("  %-40s (vazio)" % nome)
        return
    t, v = g[g.dia < corte], g[g.dia >= corte]
    f = lambda x: (len(x), x.y.mean() if len(x) else np.nan)
    nt, pt = f(t); nv, pv = f(v); na, pa = f(g)
    exp = pa * ALVO - (1 - pa) * STOP
    print("  %-40s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f  %+6.1f pts"
          % (nome, nt, pt, nv, pv, na, pa, exp))


print("\n" + "=" * 112)
print("A. O ARQUIVO ORIGINAL, TAL COMO ESTA, NO R11")
print("=" * 112)
P0 = dict(C.PADRAO)
g0 = coleta(P0)
linha("original (Esq2 Dir0 MinScore35)", g0)
print("     %.1f sinais/pregao" % (len(g0) / len(dias)))

print("\n  o Direita=0 e o problema: sem confirmacao, o 'pivo' dispara dentro")
print("  da propria perna Renko. Com confirmacao:")
for d in [1, 2, 3]:
    P = dict(C.PADRAO); P["Direita"] = d
    g = coleta(P)
    linha("Direita=%d" % d, g)
    print("     %.1f sinais/pregao" % (len(g) / len(dias)))

print("\n" + "=" * 112)
print("B. TAXA BASE -- o que da para bater")
print("=" * 112)
todos = np.r_[yB[~np.isnan(yB)], yA[~np.isnan(yA)]]
print("  entrar em qualquer barra, qualquer lado : %.4f  (n=%d)" % (todos.mean(), len(todos)))
print("  breakeven do alvo 150 / stop 100        : %.4f" % BE)
P1 = dict(C.PADRAO); P1["Direita"] = 1
K1 = C.componentes(df, b, P1)
jB = np.where(K1["pb"])[0]; jB = jB[jB + 1 < n]
jA = np.where(K1["pa"])[0]; jA = jA[jA + 1 < n]
elig = np.r_[yB[jB + 1], yA[jA + 1]]
elig = elig[~np.isnan(elig)]
print("  todo pivo (Esq2 Dir1), sem score        : %.4f  (n=%d, %.1f/pregao)"
      % (elig.mean(), len(elig), len(elig) / len(dias)))

print("\n" + "=" * 112)
print("C. PODER DE CADA COMPONENTE, medido SO no conjunto de treino")
print("   (AUC sobre todos os pivos Esq2/Dir1; 0.500 = nao discrimina)")
print("=" * 112)
Pall = dict(C.PADRAO); Pall["Direita"] = 1; Pall["MinScore"] = -1; Pall["MinBarras"] = 0
gall = coleta(Pall)
gt = gall[gall.dia < corte]
gv = gall[gall.dia >= corte]
print("  pivos elegiveis: treino n=%d | teste n=%d" % (len(gt), len(gv)))
print("\n  %-10s %8s %8s %10s %10s %10s" %
      ("comp", "AUC tr", "AUC te", "media", "desvio", "frac>0"))
for cmp_ in ["cDiv", "cAbs", "cClx", "cFlip", "cCmp", "cPav"]:
    at = auc(gt[cmp_].values, gt.y.values)
    av = auc(gv[cmp_].values, gv.y.values)
    print("  %-10s %8.4f %8.4f %10.3f %10.3f %9.1f%%"
          % (cmp_, at, av, gall[cmp_].mean(), gall[cmp_].std(),
             100 * (gall[cmp_] > 0).mean()))
print("  %-10s %8.4f %8.4f" % ("score", auc(gt.score.values, gt.y.values),
                               auc(gv.score.values, gv.y.values)))

print("\n  leitura: componente com desvio ~0 ou frac>0 ~100%% e constante --")
print("  ele so soma um offset no score e nao separa nada.")

print("\n" + "=" * 112)
print("D. AUC DAS VARIAVEIS BRUTAS (antes das rampas), so treino")
print("=" * 112)
Kf = C.componentes(df, b, Pall)
d = 1
lin = []
for nome, arr, sinal in [("zAgrV", Kf["zAgrV"], +1), ("zAgrC", Kf["zAgrC"], +1),
                         ("zRng", Kf["zRng"], +1), ("zVel", Kf["zVel"], +1),
                         ("deseq", Kf["deseq"], +1), ("zConf", Kf["zConf"], +1),
                         ("pavInf", Kf["pavInf"], +1), ("pavSup", Kf["pavSup"], +1),
                         ("posFech", Kf["posFech"], +1)]:
    xs, ys = [], []
    for lado, piv, res in [(1, Kf["pb"], yB), (-1, Kf["pa"], yA)]:
        j = np.where(piv)[0]; j = j[j + d < n]
        keep = data[j + d] < corte
        j = j[keep]
        v = arr[j] * (sinal if lado == 1 else sinal)
        yy = res[j + d]
        m = ~np.isnan(yy)
        xs.append(v[m]); ys.append(yy[m])
    lin.append((nome, auc(np.r_[xs[0], xs[1]], np.r_[ys[0], ys[1]]),
                auc(xs[0], ys[0]), auc(xs[1], ys[1])))
print("  %-10s %10s %10s %10s" % ("variavel", "AUC geral", "AUC compra", "AUC venda"))
for nome, a, ac, av in lin:
    print("  %-10s %10.4f %10.4f %10.4f" % (nome, a, ac, av))

gall.to_csv("saida_r11/pivo_componentes.csv", sep=";", decimal=",", index=False)
print("\nok -> saida_r11/pivo_componentes.csv")
