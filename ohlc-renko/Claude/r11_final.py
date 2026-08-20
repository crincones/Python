#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirmacao final: a regra operavel, sua estabilidade e sua curva de capital.

Leitura de day_pos = dir * (close - meio_do_range_do_dia) / range_do_dia:
  o brick elegivel e um brick CONTRARIO a uma sequencia. day_pos ALTO significa
  que, apesar da sequencia contrariada, o preco esta no lado do range do dia para
  onde ESTE brick aponta -- ou seja, a sequencia contrariada era um PULLBACK e o
  brick elegivel RETOMA a direcao dominante do pregao.
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
df = V.carregar(V.CSV_DEFAULT)
df = V.geometria(df)
df["elig"] = ((df.is_rev == 1) & (df.seq_before >= 3) & (df.ok == 1)).astype(int)
df = V.construir_features(df)

n = len(df)
c, h, l, o, dirn = df.c.values, df.h.values, df.l.values, df.o.values, df.dirn.values
dayid = pd.factorize(df.dt.dt.date)[0]

dhi = np.empty(n); dlo = np.empty(n); dop = np.empty(n)
hi = lo = op = np.nan
for i in range(n):
    if i == 0 or dayid[i] != dayid[i - 1]:
        hi, lo, op = h[i], l[i], o[i]
    else:
        hi, lo = max(hi, h[i]), min(lo, l[i])
    dhi[i], dlo[i], dop[i] = hi, lo, op
rng = np.maximum(dhi - dlo, BODY)
df["dpos_mid"] = dirn * (c - (dhi + dlo) / 2.0) / rng     # o que o estudo usou
df["dpos_open"] = dirn * (c - dop) / rng                  # alternativa mais simples
df["dpos_ext"] = dirn * (c - np.where(dirn > 0, dlo, dhi)) / rng - 0.5

dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
ix = df.index
h10 = pd.Series((df.hora_dec >= 10).values, index=ix)
CACHE = {}


def avaliar(mask, K, S, nome, quiet=False):
    if (K, S) not in CACHE:
        CACHE[(K, S)] = V.rotular(df, K, S)
    lab, bars = CACHE[(K, S)]
    dd = df.assign(y=lab, bars=bars)
    dd = dd[(dd.elig == 1) & (dd.ref_ok == 1) & dd.y.notna()].dropna(subset=V.FEATS)
    dd = dd[mask.reindex(dd.index).fillna(False).values]
    a, s = (K - 1) * BODY, S * BODY
    out = []
    for sp, g in [("treino", dd[dd.dt.dt.date < corte]), ("teste", dd[dd.dt.dt.date >= corte]),
                  ("TUDO", dd)]:
        if len(g) < 10:
            out.append("%s n=%d" % (sp, len(g)))
            continue
        p = g.y.mean()
        out.append("%s n=%4d p=%.4f exp=%+6.1f" % (sp, len(g), p, p * a - (1 - p) * s))
    if not quiet:
        print("%-46s %s" % (nome, " | ".join(out)))
    return dd, a, s


print("=" * 122)
print("A) A POSICAO NO PREGAO -- as tres formulacoes, sempre com hora >= 10")
print("=" * 122)
for K, S in [(3, 2.0), (4, 2.0)]:
    print("-- K=%d S=%.0f (alvo %d / stop %d, breakeven %.3f)"
          % (K, S, (K - 1) * BODY, S * BODY, S / (K - 1 + S)))
    avaliar(h10, K, S, "   hora>=10 (sem filtro de posicao)")
    for col, rot in [("dpos_mid", "meio do range"), ("dpos_open", "abertura do dia")]:
        for th in [0.0, 0.10, 0.25]:
            avaliar(h10 & pd.Series((df[col] >= th).values, index=ix), K, S,
                    "   + %s >= %+.2f (ref: %s)" % (col, th, rot))
    avaliar(h10 & pd.Series((df.dpos_mid < 0.25).values, index=ix), K, S,
            "   + dpos_mid <  +0.25  (o que sai)")
    print()

print("=" * 122)
print("B) A REGRA FINAL -- hora >= 10  &  dpos_mid >= 0.25")
print("=" * 122)
base = h10 & pd.Series((df.dpos_mid >= 0.25).values, index=ix)
print("%-46s %s" % ("grade K x S sob a regra final:", ""))
for K in [2, 3, 4, 5]:
    for S in [1.0, 2.0, 3.0]:
        avaliar(base, K, S, "   K=%d S=%.0f (alvo %3d / stop %3d, be %.3f)"
                % (K, S, (K - 1) * BODY, S * BODY, S / (K - 1 + S)))
    print()

print("=" * 122)
print("C) INTERACAO COM seq_len sob a regra final (K=3, S=2)")
print("=" * 122)
for lo_, hi_ in [(3, 3), (4, 5), (6, 40)]:
    avaliar(base & pd.Series(((df.seq_before >= lo_) & (df.seq_before <= hi_)).values, index=ix),
            3, 2.0, "   seq_len em [%d,%d]" % (lo_, hi_))

print("\n" + "=" * 122)
print("D) CURVA DE CAPITAL -- regra final, K=3, alvo 100 / stop 100")
print("=" * 122)
dd, a, s = avaliar(base, 3, 2.0, "   REGRA FINAL")
dd = dd.sort_values("dt")
pnl = np.where(dd.y.values > 0, a, -s)
print()
for custo in [0, 2, 5, 8, 10, 15]:
    eq = np.cumsum(pnl - custo)
    ddn = eq - np.maximum.accumulate(eq)
    pos, neg = (pnl - custo)[pnl - custo > 0], (pnl - custo)[pnl - custo < 0]
    print("   custo %2d pts -> total %+7.0f pts | %+5.1f pts/trade | maxDD %6.0f | PF %.2f"
          % (custo, eq[-1], eq[-1] / len(dd), ddn.min(),
             pos.sum() / abs(neg.sum()) if len(neg) else np.inf))
print("\n   sinais: %d em %d pregoes = %.2f/pregao | duracao mediana %.0f bricks | p90 %.0f"
      % (len(dd), df.dt.dt.date.nunique(), len(dd) / df.dt.dt.date.nunique(),
         dd.bars.median(), dd.bars.quantile(.9)))
gm = dd.groupby(dd.dt.dt.to_period("M")).y.agg(["size", "mean"])
print("\n   por mes:")
print(gm.to_string())

print("\n" + "=" * 122)
print("E) PLACEBO -- a mesma regra aplicada onde ela nao deveria funcionar")
print("=" * 122)


def placebo(sel, nome, K=3, S=2.0):
    lab, _ = V.rotular(df.assign(elig=sel), K, S)
    g = df.assign(y=lab)
    g = g[(sel == 1) & g.y.notna() & (g.hora_dec >= 10) & (g.dpos_mid >= 0.25)]
    a_, s_ = (K - 1) * BODY, S * BODY
    if len(g) < 10:
        print("   %-46s n=%d" % (nome, len(g))); return
    p = g.y.mean()
    print("   %-46s n=%4d p=%.4f exp=%+6.1f" % (nome, len(g), p, p * a_ - (1 - p) * s_))


placebo(((df.is_rev == 1) & (df.seq_before < 3) & (df.ok == 1)).astype(int),
        "contrario a seq < 3 (pre-condicao relaxada)")
placebo(((df.is_rev == 0) & (df.ok == 1)).astype(int),
        "brick de CONTINUACAO (nao e ponto de virada)")
rng_ = np.random.default_rng(7)
sel = np.zeros(n, dtype=int)
cand = np.where((df.ok == 1).values)[0]
sel[rng_.choice(cand, size=int(df.elig.sum()), replace=False)] = 1
placebo(pd.Series(sel, index=ix), "brick sorteado ao acaso")

fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
for custo, cor in [(0, "tab:blue"), (5, "tab:orange"), (10, "tab:red")]:
    ax[0].plot(np.cumsum(pnl - custo), label="custo %d pts/trade" % custo, color=cor)
ax[0].axvline((dd.dt.dt.date < corte).sum(), color="k", ls="--", lw=1, label="inicio do teste")
ax[0].axhline(0, color="k", lw=.8)
ax[0].set_title("Regra final -- curva de capital (alvo 100 / stop 100)")
ax[0].set_xlabel("trade"); ax[0].set_ylabel("pontos"); ax[0].legend(); ax[0].grid(alpha=.3)
gd = dd.groupby(dd.dt.dt.date).y.agg(["size", "mean"])
gd = gd[gd["size"] >= 3]
ax[1].bar(range(len(gd)), gd["mean"], color=np.where(gd["mean"] > .5, "tab:green", "tab:red"))
ax[1].axhline(.5, color="k", ls="--", label="breakeven")
ax[1].axhline(dd.y.mean(), color="tab:blue", ls=":", label="media %.3f" % dd.y.mean())
ax[1].set_title("Acerto por pregao (pregoes com >= 3 sinais)")
ax[1].set_xlabel("pregao"); ax[1].legend()
plt.tight_layout()
plt.savefig("saida_r11/03_regra_final.png", dpi=110)
plt.close()
dd.to_csv("saida_r11/regra_final.csv", sep=";", decimal=",", index=False)
print("\nok")
