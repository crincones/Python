#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reproduz a regra final usando EXATAMENTE o conjunto de filtros que o NTSL aplica
(sem janela de referencia, sem features de regime). Este e o numero honesto que o
indicador vai entregar. Testa tambem se a agressao acrescenta algo por cima.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import r11_virada as V

BODY = V.BODY_PTS
MINSEQ, MINAPOS, DPOSMIN = 3, 60.0, 0.25
ALVO_C, STOP_C = 3, 2

df = V.carregar(V.CSV_DEFAULT)
df = V.geometria(df)
n = len(df)
c, h, l, o, dirn = df.c.values, df.h.values, df.l.values, df.o.values, df.dirn.values
dur = df.dur.values
dayid = pd.factorize(df.dt.dt.date)[0]

# --- exatamente o que o NTSL faz: varre o dia corrente a cada brick elegivel ---
dhi = np.empty(n); dlo = np.empty(n); minac = np.empty(n)
hi = lo = np.nan; acc = 0.0
for i in range(n):
    if i == 0 or dayid[i] != dayid[i - 1]:
        hi, lo, acc = h[i], l[i], 0.0
    else:
        hi, lo = max(hi, h[i]), min(lo, l[i])
        acc += dur[i - 1]
    dhi[i], dlo[i], minac[i] = hi, lo, acc
rng = np.maximum(dhi - dlo, BODY)
df["dpos"] = dirn * (c - (dhi + dlo) / 2.0) / rng
df["minac"] = minac

# filtros de higiene que o NTSL aplica (identicos a `sujo`, sem nada mais)
sujo_ntsl = ((df.qt <= 0) | (df.brk == 1) | (df.newday == 1) | (df.dur > 60))
df["elig_ntsl"] = ((df.is_rev == 1) & (df.seq_before >= MINSEQ) & (~sujo_ntsl)).astype(int)
df["sinal"] = (df.elig_ntsl & (df.minac >= MINAPOS) & (df.dpos >= DPOSMIN)).astype(int)

lab, bars = V.rotular(df.assign(elig=df.sinal), ALVO_C + 1, float(STOP_C))
df["y"], df["bars"] = lab, bars
g = df[(df.sinal == 1) & df.y.notna()].copy()
A, S = ALVO_C * BODY, STOP_C * BODY
BE = S / (A + S)

dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]


def st(x):
    p = x.y.mean()
    return "n=%4d  acerto=%.4f  exp=%+6.1f pts" % (len(x), p, p * A - (1 - p) * S)


print("=" * 96)
print("REGRA NTSL -- alvo %d pts / stop %d pts / breakeven %.3f" % (A, S, BE))
print("  brick contrario a seq >= %d | >= %.0f min apos a abertura | dpos >= %.2f"
      % (MINSEQ, MINAPOS, DPOSMIN))
print("=" * 96)
print("  treino : " + st(g[g.dt.dt.date < corte]))
print("  teste  : " + st(g[g.dt.dt.date >= corte]))
print("  TUDO   : " + st(g))
print("  sinais/pregao %.2f | duracao mediana %.0f bricks | pregoes sem sinal %d de %d"
      % (len(g) / len(dias), g.bars.median(), len(dias) - g.dt.dt.date.nunique(), len(dias)))

pnl = np.where(g.sort_values("dt").y.values > 0, A, -S)
print("\n  custo   total      pts/trade   maxDD    PF")
for cu in [0, 2, 5, 8, 10, 15]:
    eq = np.cumsum(pnl - cu)
    ddn = eq - np.maximum.accumulate(eq)
    pos, neg = (pnl - cu)[pnl - cu > 0], (pnl - cu)[pnl - cu < 0]
    print("  %2d pts  %+7.0f    %+7.1f    %6.0f   %.2f"
          % (cu, eq[-1], eq[-1] / len(g), ddn.min(), pos.sum() / abs(neg.sum())))

print("\n" + "=" * 96)
print("A AGRESSAO ACRESCENTA ALGO?  (filtros extras por cima da regra)")
print("=" * 96)
g = g.assign(agtot=g.agb + g.ags)
g["delta"] = np.where(g.agtot > 0, g.dirn * (g.agb - g.ags) / g.agtot, 0.0)
g["unk"] = np.where(g.qt > 0, (g.qt - g.agtot).clip(lower=0) / g.qt, 0.0)
g["avgt"] = np.where(g.trd > 0, g.qt / g.trd, 0.0)
g["tr"] = g.dt.dt.date < corte
for nome, m in [("(sem filtro extra)", np.ones(len(g), bool)),
                ("delta a favor >= 0.00", (g.delta >= 0.0).values),
                ("delta a favor >= 0.10", (g.delta >= 0.10).values),
                ("delta a favor >= 0.20", (g.delta >= 0.20).values),
                ("delta a favor <  0.10", (g.delta < 0.10).values),
                ("vol s/ agressor >= 0.25", (g.unk >= 0.25).values),
                ("vol s/ agressor <  0.25", (g.unk < 0.25).values),
                ("lote medio acima da mediana", (g.avgt >= g.avgt.median()).values),
                ("BarDurationF acima da mediana", (g.dur >= g.dur.median()).values),
                ("pavio liquido <= 0.2 corpo", ((g.wick - 10) / 10 <= 0.2).values)]:
    x = g[m]
    if len(x) < 30:
        continue
    print("  %-32s treino %-30s teste %s"
          % (nome, st(x[x.tr]), st(x[~x.tr])))

print("\n" + "=" * 96)
print("SENSIBILIDADE DOS TRES PARAMETROS DA REGRA")
print("=" * 96)
for ms in [3, 4, 5]:
    for ma in [0, 30, 60, 90]:
        for dp in [0.15, 0.25, 0.35]:
            s = ((df.is_rev == 1) & (df.seq_before >= ms) & (~sujo_ntsl) &
                 (df.minac >= ma) & (df.dpos >= dp)).astype(int)
            lb, _ = V.rotular(df.assign(elig=s), ALVO_C + 1, float(STOP_C))
            x = df.assign(y=lb)
            x = x[(s == 1) & x.y.notna()]
            if len(x) < 60:
                continue
            xt, xv = x[x.dt.dt.date < corte], x[x.dt.dt.date >= corte]
            pt, pv, pa = xt.y.mean(), xv.y.mean(), x.y.mean()
            print("  seq>=%d  min>=%2d  dpos>=%.2f | n=%4d | tr %.4f  te %.4f  tudo %.4f  exp %+6.1f"
                  % (ms, ma, dp, len(x), pt, pv, pa, pa * A - (1 - pa) * S))

fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
gg = df[(df.sinal == 1) & df.y.notna()].sort_values("dt")
p2 = np.where(gg.y.values > 0, A, -S)
for cu, cor in [(0, "tab:blue"), (5, "tab:orange"), (10, "tab:red")]:
    ax[0].plot(np.cumsum(p2 - cu), color=cor, label="custo %d pts/trade" % cu)
ax[0].axvline((gg.dt.dt.date < corte).sum(), color="k", ls="--", lw=1, label="inicio do teste")
ax[0].axhline(0, color="k", lw=.8)
ax[0].set_title("Regra NTSL -- capital (alvo %d / stop %d)" % (A, S))
ax[0].set_xlabel("trade"); ax[0].set_ylabel("pontos"); ax[0].legend(); ax[0].grid(alpha=.3)
gd = gg.groupby(gg.dt.dt.date).y.agg(["size", "mean"])
gd = gd[gd["size"] >= 3]
ax[1].bar(range(len(gd)), gd["mean"], color=np.where(gd["mean"] > BE, "tab:green", "tab:red"))
ax[1].axhline(BE, color="k", ls="--", label="breakeven %.2f" % BE)
ax[1].axhline(gg.y.mean(), color="tab:blue", ls=":", label="media %.3f" % gg.y.mean())
ax[1].set_title("Acerto por pregao"); ax[1].set_xlabel("pregao"); ax[1].legend()
plt.tight_layout()
plt.savefig("saida_r11/03_regra_ntsl.png", dpi=110)
gg.to_csv("saida_r11/sinais_ntsl.csv", sep=";", decimal=",", index=False)
print("\nok -> saida_r11/03_regra_ntsl.png")
