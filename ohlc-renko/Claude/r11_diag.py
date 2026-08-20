#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico da base R11 antes de modelar. So mede, nao conclui."""
import sys
import numpy as np
import pandas as pd

CSV = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv"
TICK = 5.0

raw = pd.read_csv(CSV, sep=";", decimal=",", encoding="utf-8-sig",
                  engine="python", on_bad_lines="skip")
print("colunas:", list(raw.columns))
print("linhas brutas:", len(raw))

raw = raw.rename(columns={
    "Data": "dt", "Abertura": "o", "Máxima": "h", "Mínima": "l",
    "Fechamento": "c", "AgressionVolBuy": "agb", "AgressionVolSell": "ags",
    "BarDurationF": "dur", "Quantity": "qt", "Trades": "trd"})
raw = raw[["dt", "o", "h", "l", "c", "agb", "ags", "dur", "qt", "trd"]]
raw = raw.dropna(subset=["dt", "o", "c"])
raw["dt"] = pd.to_datetime(raw["dt"], format="%d/%m/%Y %H:%M:%S.%f", errors="coerce")
raw = raw.dropna(subset=["dt"])
for k in ["o", "h", "l", "c", "agb", "ags", "dur", "qt", "trd"]:
    raw[k] = pd.to_numeric(raw[k], errors="coerce")
raw = raw.dropna()

df = raw.sort_values("dt", kind="stable").reset_index(drop=True)
print("linhas validas:", len(df))
print("periodo:", df.dt.iloc[0], "->", df.dt.iloc[-1])
print("pregoes:", df.dt.dt.date.nunique())

# --- corpo do brick ---
body = (df.c - df.o).abs()
print("\n=== CORPO ===")
print(body.value_counts().head(8).to_string())
print("corpo == 50 pts:", (body == 50).mean())

# ultima barra (em formacao?)
print("\nultimas 3 linhas:")
print(df.tail(3).to_string())

# --- Data = abertura ou fechamento? ---
gap = df.dt.diff().shift(-1).dt.total_seconds() / 60.0   # t[i+1]-t[i] em min
ok = gap.notna() & df.dur.notna()
print("\n=== TIMESTAMP ===")
print("corr(t[i+1]-t[i], dur[i]) =", np.corrcoef(gap[ok], df.dur[ok])[0, 1].round(6))
resid = (gap - df.dur)[ok]
print("mediana |t[i+1]-t[i] - dur[i]| =", resid.abs().median().round(6), "min")
print("=> Data e o instante de ABERTURA da barra; BarDurationF em MINUTOS")

# --- agressao vs quantidade ---
print("\n=== AGRESSAO ===")
d = df.iloc[:-1]  # exclui possivel barra em formacao
unk = d.qt - d.agb - d.ags
print("share de volume sem agressor: %.4f" % (unk.clip(lower=0).sum() / d.qt.sum()))
print("bricks com agb+ags > qt:", int((unk < 0).sum()))
print("bricks com agb+ags == qt:", "%.3f" % (unk == 0).mean())

# --- sinteticos ---
print("\n=== SINTETICOS / GAP-FILL ===")
print("dur == 0:", "%.4f" % (d.dur == 0).mean(), int((d.dur == 0).sum()))
print("qt == 0 :", "%.4f" % (d.qt == 0).mean())
print("timestamps duplicados:", int(d.dt.duplicated().sum()))

# --- geometria: encadeamento ---
dirn = np.sign(df.c - df.o).astype(int)
is_rev = np.zeros(len(df), dtype=int)
is_rev[1:] = (dirn.values[1:] != dirn.values[:-1]).astype(int)
opens_prev_close = np.abs(df.o.values[1:] - df.c.values[:-1]) < 1e-9
opens_prev_open = np.abs(df.o.values[1:] - df.o.values[:-1]) < 1e-9
print("\n=== ENCADEAMENTO ===")
print("continuacao abre no close anterior:",
      "%.4f" % opens_prev_close[is_rev[1:] == 0].mean())
print("reversao abre no open anterior:",
      "%.4f" % opens_prev_open[is_rev[1:] == 1].mean())
print("quebras de encadeamento (nem close nem open):",
      int((~(opens_prev_close | opens_prev_open)).sum()))

# --- pavio ---
wick = np.where(dirn > 0, (df.o - df.l) / TICK, (df.h - df.o) / TICK)
df["wick"] = wick
df["is_rev"] = is_rev
df["dirn"] = dirn
print("\n=== PAVIO (ticks) ===")
print(df.groupby("is_rev").wick.describe()[["count", "50%", "max"]].to_string())

# --- populacoes: reversao x continuacao ---
real = df.iloc[:-1]
real = real[real.dur > 0]
print("\n=== POPULACOES (bricks reais, dur>0) ===")
g = real.groupby("is_rev").agg(n=("qt", "size"), dur_med=("dur", "median"),
                               qt_med=("qt", "median"), trd_med=("trd", "median"),
                               wick_med=("wick", "median"))
print(g.to_string())
print("razao rev/cont dur: %.2fx  qt: %.2fx" %
      (g.dur_med.get(1, np.nan) / g.dur_med.get(0, np.nan),
       g.qt_med.get(1, np.nan) / g.qt_med.get(0, np.nan)))

# --- taxa base mecanica ---
print("\n=== TAXA BASE ===")
nxt_same = (dirn.values[1:] == dirn.values[:-1])
print("P(proximo brick mesma direcao) geral: %.4f  n=%d" % (nxt_same.mean(), len(nxt_same)))
seq = np.zeros(len(df), dtype=int)
for i in range(1, len(df)):
    seq[i] = seq[i - 1] + 1 if dirn.values[i] == dirn.values[i - 1] else 1
seq[0] = 1
df["seq_before"] = np.r_[0, seq[:-1]]   # comprimento da seq ANTES deste brick
elig = (df.is_rev == 1) & (df.seq_before >= 3)
print("elegiveis (contrario a seq>=3): %d (%.2f%%)" % (elig.sum(), 100 * elig.mean()))
nxt_dir = np.r_[dirn.values[1:], 0]
df["nxt_same"] = (nxt_dir == dirn.values).astype(int)
print("P(vira em 1 brick | elegivel): %.4f" % df.loc[elig & (df.index < len(df) - 1), "nxt_same"].mean())

# --- pernas em preco ---
print("\n=== PERNA EM PRECO (a partir do close do brick contrario) ===")
cl = df.c.values
dr = dirn.values
n = len(df)
for K in [2, 3, 4, 5, 6]:
    lab = np.full(n, np.nan)
    for i in np.where(elig.values)[0]:
        if i + 1 >= n:
            continue
        target = cl[i] + dr[i] * (K - 1) * 10 * TICK
        stop = cl[i] - dr[i] * 2 * 10 * TICK
        hit = np.nan
        for j in range(i + 1, n):
            if dr[i] > 0:
                if df.h.values[j] >= target:
                    hit = 1.0
                    break
                if df.l.values[j] <= stop:
                    hit = 0.0
                    break
            else:
                if df.l.values[j] <= target:
                    hit = 1.0
                    break
                if df.h.values[j] >= stop:
                    hit = 0.0
                    break
        lab[i] = hit
    v = lab[~np.isnan(lab)]
    print("K=%d  n=%4d  P(alvo antes do stop)=%.4f" % (K, len(v), v.mean()))

df.to_pickle(r"C:\Users\Carlos\AppData\Local\Temp\claude\C--Users-Carlos-Documents-GitHub-Python-ohlc-renko-Claude\c80fd796-ad18-45a4-8f91-d44a69f5bfdc\scratchpad\r11.pkl")
print("\nok")
