#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analise condicional: em vez de um modelo global, existe algum RECORTE em que a
taxa base se desloca de forma estavel entre treino e teste?
Tambem testa: stop mais largo, o lado contrario do trade, e o teto do GBM.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings("ignore")

import r11_virada as V

BODY = V.BODY_PTS

df = V.carregar(V.CSV_DEFAULT)
df = V.geometria(df)
df["elig"] = ((df.is_rev == 1) & (df.seq_before >= 3) & (df.ok == 1)).astype(int)
df = V.construir_features(df)

print("=" * 78)
print("A) ROTULO x LARGURA DO STOP  (K = perna alvo, S = stop em corpos)")
print("=" * 78)
print("%3s %4s %8s %8s %10s %12s" % ("K", "S", "alvo", "stop", "breakeven", "taxa base"))
best = {}
for K in [2, 3, 4, 5, 6, 8]:
    for S in [1.0, 2.0, 3.0, 4.0]:
        lab, bars = V.rotular(df, K, stop_bodies=S)
        v = lab[~np.isnan(lab)]
        alvo, stop = (K - 1) * BODY, S * BODY
        be = stop / (alvo + stop)
        exp = v.mean() * alvo - (1 - v.mean()) * stop
        print("%3d %4.0f %8.0f %8.0f %10.3f %12.4f   exp=%+7.1f pts  n=%d  bars_med=%.0f"
              % (K, S, alvo, stop, be, v.mean(), exp, len(v),
                 np.nanmedian(bars)))
        best[(K, S)] = (lab, exp, v.mean())
    print()

# rotulo principal
K, S = 4, 2.0
df["y"], df["bars"] = V.rotular(df, K, S)
alvo, stop = (K - 1) * BODY, S * BODY

d = df[(df.elig == 1) & (df.ref_ok == 1) & df.y.notna()].dropna(subset=V.FEATS).copy()
dias = np.sort(d.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
d["split"] = np.where(d.dt.dt.date < corte, "treino", "teste")
print("amostra %d | treino %d | teste %d | taxa base %.4f"
      % (len(d), (d.split == "treino").sum(), (d.split == "teste").sum(), d.y.mean()))


def recorte(nome, cond_series, bins):
    """taxa base por faixa, com treino e teste lado a lado."""
    print("\n" + "=" * 78)
    print("B) RECORTE POR %s" % nome)
    print("=" * 78)
    d["_b"] = pd.cut(cond_series, bins) if not isinstance(bins, int) else \
        pd.qcut(cond_series, bins, duplicates="drop")
    print("%-26s %6s %8s %6s %8s %9s" % ("faixa", "n_tr", "p_tr", "n_te", "p_te", "exp_te"))
    for b, g in d.groupby("_b", observed=True):
        gt, gv = g[g.split == "treino"], g[g.split == "teste"]
        if len(gt) < 30 or len(gv) < 20:
            continue
        e = gv.y.mean() * alvo - (1 - gv.y.mean()) * stop
        print("%-26s %6d %8.3f %6d %8.3f %+9.1f"
              % (str(b), len(gt), gt.y.mean(), len(gv), gv.y.mean(), e))


recorte("HORA", d.hora_dec, [9, 9.5, 10, 11, 12, 14, 16, 19])
recorte("SEQ_LEN contrariada", d.seq_len, [2.5, 3.5, 4.5, 5.5, 7.5, 40])
recorte("DAY_POS (pos no dia, + = a favor)", d.day_pos, 5)
recorte("REV_DENS (fracao de reversoes em 40)", d.rev_dens, 5)
recorte("DELTA_CL (agressao a favor)", d.delta_cl, 5)
recorte("WICK_NET (sondagem alem da seq)", d.wick_net_n, [-1, 0.001, 0.2, 0.5, 1.0, 3])
recorte("COST_NZ (custo vs reversoes ant.)", d.cost_nz, 5)
recorte("EFF_RATIO (tendencia do regime)", d.eff_ratio, 5)
recorte("PACE_NZ (velocidade)", d.pace_nz, 5)

print("\n" + "=" * 78)
print("C) 2D: HORA x DAY_POS (taxa base; treino / teste)")
print("=" * 78)
d["hb"] = pd.cut(d.hora_dec, [9, 10, 12, 19], labels=["9-10h", "10-12h", "12-19h"])
d["dp"] = pd.qcut(d.day_pos, 3, labels=["baixo", "medio", "alto"])
for hb, g in d.groupby("hb", observed=True):
    row = []
    for dp, gg in g.groupby("dp", observed=True):
        gt, gv = gg[gg.split == "treino"], gg[gg.split == "teste"]
        row.append("%s: %.3f(%d)/%.3f(%d)" % (dp, gt.y.mean(), len(gt),
                                              gv.y.mean() if len(gv) else np.nan, len(gv)))
    print("%-8s %s" % (hb, "  |  ".join(row)))

print("\n" + "=" * 78)
print("D) TETO NAO-LINEAR: GBM com CV temporal")
print("=" * 78)
X = d[V.FEATS].values
y = d.y.values
tss = TimeSeriesSplit(n_splits=6)
au = []
for itr, iva in tss.split(X):
    m = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.04,
                                       min_samples_leaf=50, l2_regularization=2.0,
                                       random_state=11).fit(X[itr], y[itr])
    au.append(roc_auc_score(y[iva], m.predict_proba(X[iva])[:, 1]))
print("GBM AUC por dobra:", np.round(au, 4), " media %.4f +/- %.4f" % (np.mean(au), np.std(au)))

print("\n" + "=" * 78)
print("E) O LADO CONTRARIO: apostar na CONTINUACAO da sequencia original")
print("=" * 78)
print("Entrada contra o brick elegivel (a favor da seq original), no fechamento dele.")
for Kc in [2, 3, 4]:
    for Sc in [1.0, 2.0, 3.0]:
        # espelha: alvo = Kc corpos na direcao da seq original, stop = Sc corpos
        c, h, l, dirn = df.c.values, df.h.values, df.l.values, df.dirn.values
        n = len(df)
        lab = np.full(n, np.nan)
        for i in np.where(df.elig.values.astype(bool))[0]:
            dd = -dirn[i]
            tgt = c[i] + dd * Kc * BODY
            stp = c[i] - dd * Sc * BODY
            for j in range(i + 1, n):
                if dd > 0:
                    if l[j] <= stp: lab[i] = 0.0; break
                    if h[j] >= tgt: lab[i] = 1.0; break
                else:
                    if h[j] >= stp: lab[i] = 0.0; break
                    if l[j] <= tgt: lab[i] = 1.0; break
        v = lab[~np.isnan(lab)]
        a, s = Kc * BODY, Sc * BODY
        print("alvo %3.0f stop %3.0f | breakeven %.3f | acerto %.4f | exp %+6.1f pts | n=%d"
              % (a, s, s / (a + s), v.mean(), v.mean() * a - (1 - v.mean()) * s, len(v)))

print("\n" + "=" * 78)
print("F) ESTABILIDADE DIA A DIA da taxa base (K=4, S=2)")
print("=" * 78)
g = d.groupby(d.dt.dt.date).y.agg(["size", "mean"])
g = g[g["size"] >= 20]
print(g.describe().to_string())
print("pregoes com taxa acima do breakeven 0.400: %d de %d"
      % ((g["mean"] > 0.4).sum(), len(g)))
