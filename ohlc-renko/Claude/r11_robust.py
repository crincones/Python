#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robustez da regra final: sensibilidade dos limiares, bootstrap e walk-forward."""
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

n = len(df)
c, h, l, o, dirn = df.c.values, df.h.values, df.l.values, df.o.values, df.dirn.values
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

K, S = 4, 2.0
ALVO, STOP = (K - 1) * BODY, S * BODY
BE = STOP / (ALVO + STOP)
lab, bars = V.rotular(df, K, S)
d = df.assign(y=lab, bars=bars)
d = d[(d.elig == 1) & (d.ref_ok == 1) & d.y.notna()].dropna(subset=V.FEATS).copy()
dias = np.sort(d.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
d["tr"] = d.dt.dt.date < corte
print("K=%d S=%.0f | alvo %d stop %d | breakeven %.3f | amostra %d"
      % (K, S, ALVO, STOP, BE, len(d)))


def stat(g):
    if len(g) < 10:
        return "n=%d" % len(g)
    p = g.y.mean()
    return "n=%4d p=%.4f exp=%+6.1f" % (len(g), p, p * ALVO - (1 - p) * STOP)


print("\n" + "=" * 108)
print("A) SENSIBILIDADE -- e um plato ou um pico?")
print("=" * 108)
print("%-12s %-26s %-26s %-26s" % ("hora >=", "TREINO", "TESTE", "TUDO"))
for hh in [9.0, 9.5, 10.0, 10.5, 11.0]:
    m = d[d.hora_dec >= hh]
    print("%-12.1f %-26s %-26s %-26s" % (hh, stat(m[m.tr]), stat(m[~m.tr]), stat(m)))

print("\n%-12s %-26s %-26s %-26s" % ("dpos >= (com hora>=10)", "TREINO", "TESTE", "TUDO"))
for th in [-0.10, 0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
    m = d[(d.hora_dec >= 10) & (d.dpos >= th)]
    print("%-12.2f %-26s %-26s %-26s" % (th, stat(m[m.tr]), stat(m[~m.tr]), stat(m)))

print("\n%-12s %-26s %-26s %-26s" % ("dpos >= (SEM filtro hora)", "TREINO", "TESTE", "TUDO"))
for th in [0.0, 0.15, 0.25, 0.35]:
    m = d[d.dpos >= th]
    print("%-12.2f %-26s %-26s %-26s" % (th, stat(m[m.tr]), stat(m[~m.tr]), stat(m)))

REGRA = (d.hora_dec >= 10) & (d.dpos >= 0.25)
g = d[REGRA]
print("\n" + "=" * 108)
print("B) BOOTSTRAP por PREGAO (nao por trade -- trades do mesmo dia sao dependentes)")
print("=" * 108)
rng = np.random.default_rng(42)
dd = list(g.groupby(g.dt.dt.date))
boot = []
for _ in range(5000):
    sel = rng.integers(0, len(dd), len(dd))
    yy = np.concatenate([dd[k][1].y.values for k in sel])
    boot.append(yy.mean())
boot = np.array(boot)
print("acerto observado %.4f | IC95%% por pregao [%.4f, %.4f] | breakeven %.3f"
      % (g.y.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5), BE))
print("P(acerto <= breakeven) no bootstrap: %.4f" % (boot <= BE).mean())
print("expectativa IC95%%: [%+.1f, %+.1f] pts/trade"
      % (np.percentile(boot, 2.5) * ALVO - (1 - np.percentile(boot, 2.5)) * STOP,
         np.percentile(boot, 97.5) * ALVO - (1 - np.percentile(boot, 97.5)) * STOP))

print("\n" + "=" * 108)
print("C) TESTE DE ALEATORIZACAO -- embaralhar o rotulo dentro de cada pregao")
print("=" * 108)
allev = d.copy()
obs = g.y.mean()
cnt = 0
NP = 2000
for _ in range(NP):
    sh = allev.groupby(allev.dt.dt.date, group_keys=False).y.apply(
        lambda s: pd.Series(rng.permutation(s.values), index=s.index))
    if sh[REGRA.values].mean() >= obs:
        cnt += 1
print("p-valor (o filtro seleciona bricks melhores que o acaso do mesmo dia): %.4f"
      % ((cnt + 1) / (NP + 1)))

print("\n" + "=" * 108)
print("D) WALK-FORWARD -- 5 blocos cronologicos, regra FIXA")
print("=" * 108)
blocos = np.array_split(dias, 5)
print("%-26s %-8s %-8s %-9s %-9s" % ("periodo", "n", "acerto", "exp", "pts"))
for b in blocos:
    m = g[(g.dt.dt.date >= b[0]) & (g.dt.dt.date <= b[-1])]
    if len(m) < 5:
        continue
    p = m.y.mean()
    e = p * ALVO - (1 - p) * STOP
    print("%-26s %-8d %-8.4f %+-9.1f %+-9.0f"
          % ("%s a %s" % (b[0].strftime("%d/%m"), b[-1].strftime("%d/%m")),
             len(m), p, e, e * len(m)))

print("\n" + "=" * 108)
print("E) DECOMPOSICAO DO GANHO -- de onde vem cada ponto percentual")
print("=" * 108)
etapas = [
    ("brick qualquer (referencia teorica)", None),
    ("contrario a qualquer sequencia", d.assign(_=1)._ if False else None),
]
lab_all, _ = V.rotular(df.assign(elig=(df.ok == 1).astype(int)), K, S)
a0 = pd.Series(lab_all).dropna()
print("%-52s %-8s %-9s %-9s" % ("etapa", "n", "acerto", "exp"))


def linha(nome, sel):
    v = sel.y.values if hasattr(sel, "y") else sel
    v = v[~np.isnan(v)]
    p = v.mean()
    print("%-52s %-8d %-9.4f %+-9.1f" % (nome, len(v), p, p * ALVO - (1 - p) * STOP))


linha("qualquer brick OK", a0.values)
lab_c, _ = V.rotular(df.assign(elig=((df.is_rev == 1) & (df.ok == 1)).astype(int)), K, S)
linha("contrario a qualquer sequencia", pd.Series(lab_c).dropna().values)
linha("contrario a seq >= 3 (elegivel)", d)
linha("  + hora >= 10", d[d.hora_dec >= 10])
linha("  + dpos >= 0.25  (REGRA FINAL)", g)

print("\n" + "=" * 108)
print("F) O QUE A REGRA CAPTURA -- perfil dos sinais")
print("=" * 108)
print("distribuicao por hora:")
print(g.groupby(pd.cut(g.hora_dec, [10, 11, 12, 14, 16, 19]), observed=True).y.agg(["size", "mean"]).to_string())
print("\ndirecao do sinal: alta %d (p=%.3f) | baixa %d (p=%.3f)"
      % ((g.dirn > 0).sum(), g[g.dirn > 0].y.mean(),
         (g.dirn < 0).sum(), g[g.dirn < 0].y.mean()))
print("sinais por pregao: media %.2f | max %d | pregoes sem sinal %d de %d"
      % (len(g) / len(dias), g.groupby(g.dt.dt.date).size().max(),
         len(dias) - g.dt.dt.date.nunique(), len(dias)))
print("duracao ate resolver: mediana %.0f bricks | p90 %.0f" % (g.bars.median(), g.bars.quantile(.9)))
