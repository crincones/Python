#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico 2: quebras de encadeamento, dur==0, agressao sem flag."""
import numpy as np
import pandas as pd

PKL = r"C:\Users\Carlos\AppData\Local\Temp\claude\C--Users-Carlos-Documents-GitHub-Python-ohlc-renko-Claude\c80fd796-ad18-45a4-8f91-d44a69f5bfdc\scratchpad\r11.pkl"
TICK = 5.0
df = pd.read_pickle(PKL)
n = len(df)
o, c, h, l = df.o.values, df.c.values, df.h.values, df.l.values

ok_close = np.abs(o[1:] - c[:-1]) < 1e-9
ok_open = np.abs(o[1:] - o[:-1]) < 1e-9
brk = ~(ok_close | ok_open)
idx = np.where(brk)[0] + 1
print("=== QUEBRAS DE ENCADEAMENTO: %d (%.2f%%) ===" % (len(idx), 100 * len(idx) / n))

newday = df.dt.dt.date.values
is_newday = newday[idx] != newday[idx - 1]
print("em virada de pregao:", int(is_newday.sum()))
print("intradia          :", int((~is_newday).sum()))

intr = idx[~is_newday]
gap_ticks = (o[intr] - c[intr - 1]) / TICK
print("\ndeslocamento open[i]-close[i-1] em ticks (intradia):")
print(pd.Series(gap_ticks).describe().to_string())
print("\nvalores mais comuns:")
print(pd.Series(gap_ticks).value_counts().head(10).to_string())

prev_dur = df.dur.values[intr - 1]
print("\ndur do brick ANTERIOR a quebra: mediana=%.3f  frac dur==0: %.3f"
      % (np.median(prev_dur), (prev_dur == 0).mean()))
print("dur do brick da quebra        : mediana=%.3f  frac dur==0: %.3f"
      % (np.median(df.dur.values[intr]), (df.dur.values[intr] == 0).mean()))
print("timestamp igual ao anterior   : %.3f"
      % (df.dt.values[intr] == df.dt.values[intr - 1]).mean())

print("\nexemplo de rajada:")
j = intr[5]
print(df.iloc[j - 3:j + 3][["dt", "o", "h", "l", "c", "dur", "qt", "trd"]].to_string())

# ---- dur == 0 ----
print("\n\n=== dur == 0 (%d bricks) ===" % int((df.dur == 0).sum()))
z = df[df.dur == 0]
print("qt == 0 entre eles: %.3f" % (z.qt == 0).mean())
print("qt mediana entre eles: %.0f  (geral: %.0f)" % (z.qt.median(), df.qt.median()))
print("trd mediana entre eles: %.0f" % z.trd.median())
print("timestamp duplicado do anterior: %.3f"
      % (df.dt.diff().dt.total_seconds() == 0)[df.dur == 0].mean())
print("is_rev entre eles: %.3f (geral %.3f)" % (z.is_rev.mean(), df.is_rev.mean()))
print("\ndistribuicao de dur (min) - quantis:")
print(df.dur.quantile([0, .05, .1, .18, .2, .25, .5, .75, .9, .99, 1]).to_string())

# ---- elegiveis que sao dur==0 / qt==0 ----
elig = (df.is_rev == 1) & (df.seq_before >= 3)
print("\nentre os %d elegiveis: dur==0 %.3f | qt==0 %.3f"
      % (elig.sum(), (df.dur[elig] == 0).mean(), (df.qt[elig] == 0).mean()))

# ---- agressao sem flag ----
print("\n\n=== VOLUME SEM AGRESSOR ===")
d = df.iloc[:-1].copy()
d["unk"] = (d.qt - d.agb - d.ags).clip(lower=0)
d["unk_share"] = np.where(d.qt > 0, d.unk / d.qt, np.nan)
print(d.unk_share.describe().to_string())
print("\npor tipo de brick:")
print(d.groupby("is_rev").unk_share.median().to_string())
print("\ncorrelacao unk_share x log(qt): %.3f"
      % d.loc[d.qt > 0, ["unk_share"]].assign(lq=np.log(d.qt[d.qt > 0])).corr().iloc[0, 1])

# ---- duracao x sessao ----
print("\n\n=== DURACAO PATOLOGICA ===")
print("bricks com dur > 60 min:", int((df.dur > 60).sum()))
print("dur max: %.2f min" % df.dur.max())
first_of_day = df.dt.dt.date != df.dt.dt.date.shift(1)
print("primeiro brick do dia entre os elegiveis:", int((first_of_day & elig).sum()))
print("hora do 1o brick do dia (moda):", df.dt[first_of_day].dt.hour.value_counts().head(3).to_dict())
print("hora do ultimo brick (moda):", df.dt.dt.hour.value_counts().sort_index().to_string())
