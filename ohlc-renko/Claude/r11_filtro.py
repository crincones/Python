#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O unico recorte estavel: o filtro de abertura. Isola, testa e mede o custo."""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import r11_virada as V

BODY = V.BODY_PTS
df = V.carregar(V.CSV_DEFAULT)
df = V.geometria(df)
df["elig"] = ((df.is_rev == 1) & (df.seq_before >= 3) & (df.ok == 1)).astype(int)
df = V.construir_features(df)

# ritmo: bricks nos ultimos 15 minutos (alternativa adaptativa ao relogio)
t = df.dt.values.astype("datetime64[s]").astype(np.int64)
cnt15 = np.zeros(len(df))
j = 0
for i in range(len(df)):
    while t[i] - t[j] > 900:
        j += 1
    cnt15[i] = i - j
df["bricks15"] = cnt15

df["y"], df["bars"] = V.rotular(df, 4, 2.0)
d = df[(df.elig == 1) & (df.ref_ok == 1) & df.y.notna()].dropna(subset=V.FEATS).copy()
dias = np.sort(d.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
d["split"] = np.where(d.dt.dt.date < corte, "treino", "teste")


def bloco(nome, mask):
    a, s = 150.0, 100.0
    out = [nome]
    for sp in ["treino", "teste", "TUDO"]:
        g = d[mask] if sp == "TUDO" else d[mask & (d.split == sp)]
        if len(g) < 10:
            out.append("%s: n=%d" % (sp, len(g)))
            continue
        p = g.y.mean()
        out.append("%s n=%4d p=%.4f exp=%+6.1f" % (sp, len(g), p, p * a - (1 - p) * s))
    print(" | ".join(out))


print("=" * 100)
print("A) FILTRO DE HORARIO -- K=4 S=2 (alvo 150 / stop 100, breakeven 0.400)")
print("=" * 100)
bloco("SEM FILTRO              ", np.ones(len(d), bool))
for hh in [9.25, 9.5, 9.75, 10.0, 10.25, 10.5, 11.0]:
    bloco("hora >= %-5.2f          " % hh, (d.hora_dec >= hh).values)
print()
bloco("hora < 10 (o que sai)   ", (d.hora_dec < 10).values)
print()
for hf in [17.0, 17.5, 18.0]:
    bloco("10 <= hora < %-5.1f     " % hf, ((d.hora_dec >= 10) & (d.hora_dec < hf)).values)

print("\n" + "=" * 100)
print("B) FILTRO ADAPTATIVO POR RITMO (bricks nos ultimos 15 min) -- sem relogio")
print("=" * 100)
for b in [20, 30, 40, 50, 60]:
    bloco("bricks15 <= %-3d         " % b, (d.bricks15 <= b).values)
print()
print("correlacao bricks15 x hora: %.3f" % d[["bricks15", "hora_dec"]].corr().iloc[0, 1])
print("bricks15 mediano por faixa de hora:")
print(d.groupby(pd.cut(d.hora_dec, [9, 10, 12, 19]), observed=True).bricks15.median().to_string())

print("\n" + "=" * 100)
print("C) FILTRO DE HORA + DAY_POS")
print("=" * 100)
m10 = (d.hora_dec >= 10).values
bloco("hora>=10                ", m10)
for dp in [-0.2, 0.0, 0.1, 0.25]:
    bloco("hora>=10 & day_pos>=%-5.2f" % dp, m10 & (d.day_pos >= dp).values)

print("\n" + "=" * 100)
print("D) GRADE K x S SOB O FILTRO hora >= 10")
print("=" * 100)
print("%3s %4s %8s %8s %10s   %-28s %-28s" % ("K", "S", "alvo", "stop", "breakeven", "TREINO", "TESTE"))
for K in [2, 3, 4, 5]:
    for S in [1.0, 2.0, 3.0]:
        lab, _ = V.rotular(df, K, S)
        df["_y"] = lab
        dd = df[(df.elig == 1) & (df.ref_ok == 1) & df._y.notna()].dropna(subset=V.FEATS)
        dd = dd[dd.hora_dec >= 10]
        dd = dd.assign(split=np.where(dd.dt.dt.date < corte, "treino", "teste"))
        a, s = (K - 1) * BODY, S * BODY
        cel = []
        for sp in ["treino", "teste"]:
            g = dd[dd.split == sp]
            p = g._y.mean()
            cel.append("n=%4d p=%.4f exp=%+6.1f" % (len(g), p, p * a - (1 - p) * s))
        print("%3d %4.0f %8.0f %8.0f %10.3f   %-28s %-28s" % (K, S, a, s, s / (a + s), cel[0], cel[1]))
    print()

print("=" * 100)
print("E) ESTABILIDADE MENSAL sob hora>=10, K=4 S=2")
print("=" * 100)
g = d[m10].groupby(d[m10].dt.dt.to_period("M")).y.agg(["size", "mean"])
print(g.to_string())
gd = d[m10].groupby(d[m10].dt.dt.date).y.agg(["size", "mean"])
gd = gd[gd["size"] >= 15]
print("\npor pregao (n>=15): media %.4f | desvio observado %.4f | desvio binomial esperado %.4f"
      % (gd["mean"].mean(), gd["mean"].std(),
         np.sqrt(gd["mean"].mean() * (1 - gd["mean"].mean()) / gd["size"].mean())))
print("pregoes acima do breakeven 0.400: %d de %d" % ((gd["mean"] > .4).sum(), len(gd)))

print("\n" + "=" * 100)
print("F) CUSTO: quantos sinais por pregao e quanto tempo cada trade dura")
print("=" * 100)
sub = d[m10]
print("sinais/pregao: %.1f (mediana %.0f)" %
      (len(sub) / d.dt.dt.date.nunique(), sub.groupby(sub.dt.dt.date).size().median()))
print("duracao do trade em bricks: mediana %.0f | p90 %.0f" %
      (sub.bars.median(), sub.bars.quantile(.9)))
mn = sub.dt.diff().dt.total_seconds() / 60
print("\nexpectativa liquida por trade (alvo 150 / stop 100) descontando custo:")
p = sub.y.mean()
for custo in [0, 2, 5, 10, 15]:
    print("  custo %2d pts -> %+6.1f pts/trade  |  %.0f trades no periodo -> %+.0f pts"
          % (custo, p * 150 - (1 - p) * 100 - custo, len(sub),
             (p * 150 - (1 - p) * 100 - custo) * len(sub)))
