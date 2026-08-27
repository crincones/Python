"""Gera a referencia de paridade Python <-> MQL5.

Reproduz, em Python, EXATAMENTE as formulas de MQL5/Indicators/RangeReversalScanner.mq5
(inclusive as janelas moveis estritas: mediana so e calculada quando ha janela completa).
Rodando o indicador sobre a mesma base no MetaTrader e comparando os dois CSVs,
verifica-se a fidelidade da implementacao antes de qualquer uso.
"""
import numpy as np, pandas as pd
from lib import load

WIN20, WIN50 = 20, 50
MIN_BARS = WIN50 + 5

df = load()
n = len(df)
O, H, L, C = (df[c].to_numpy() for c in ("OPEN", "HIGH", "LOW", "CLOSE"))
D, R, BR = df.DIR.to_numpy(), df.RANGE.to_numpy(), df.BODYRATIO.to_numpy()
BUY, SELL = df.BUY.to_numpy(), df.SELL.to_numpy()

sDur = df.DUR.to_numpy()
sAggT = BUY + SELL
sIntens = sAggT / np.maximum(sDur, 0.5)


def rollmed(src, win):
    """Mediana causal de janela estrita; 0.0 onde a janela nao esta completa
    (identico ao RollMedian do MQL5)."""
    s = pd.Series(src).rolling(win, min_periods=win).median()
    return s.fillna(0.0).to_numpy()


aggtMed20, aggtMed50 = rollmed(sAggT, WIN20), rollmed(sAggT, WIN50)
durMed20, durMed50 = rollmed(sDur, WIN20), rollmed(sDur, WIN50)
intensMed20 = rollmed(sIntens, WIN20)

# runlength terminando em t-1 (identico ao laco do indicador)
run = np.ones(n, int)
for i in range(1, n):
    run[i] = run[i - 1] + 1 if D[i] == D[i - 1] else 1

t = np.arange(MIN_BARS, n - 1)          # ultima barra fica de fora (em formacao)
same = D[t - 2] == D[t - 1]
opp = D[t] == -D[t - 1]
isP1 = same & opp & (BR[t] <= 0.50)
isP2 = same & opp & (BR[t - 1] >= 0.70) & (BR[t] >= 0.70)
sel = isP1 | isP2
i = t[sel]
pat = np.where(isP2[sel], "P2", "P1")   # P2 tem precedencia, como no MQL5
side = D[i]

aggt0, aggt1 = sAggT[i], sAggT[i - 1]
aggdn0_raw = np.divide(BUY[i] - SELL[i], aggt0, out=np.zeros(len(i)), where=aggt0 > 0)
aggdn1_raw = np.divide(BUY[i - 1] - SELL[i - 1], aggt1, out=np.zeros(len(i)), where=aggt1 > 0)
wick = np.where(side > 0, O[i] - L[i], H[i] - O[i])

out = pd.DataFrame({
    "close_time": df.DT.to_numpy()[i],
    "pattern": pat,
    "side": side,
    "close": C[i].round(2),
    "R": R[i].round(2),
    "br0": BR[i], "br1": BR[i - 1], "br2": BR[i - 2],
    "wick0": wick / R[i],
    "openpos0": (O[i] - L[i]) / R[i],
    "run_prev": run[i - 1],
    "aggdn0": aggdn0_raw * side,
    "aggdn1": aggdn1_raw * side,
    "daggdn": (aggdn0_raw - aggdn1_raw) * side,
    "diverg0": aggdn0_raw * side,
    "aggt0": np.log1p(aggt0),
    "aggt_rel0": aggt0 / np.maximum(aggtMed20[i], 1.0),
    "aggt_ratio01": aggt0 / np.maximum(aggt1, 1.0),
    "agg_per_R": aggt0 / R[i],
    "dur0": np.log1p(sDur[i]),
    "dur_rel0": sDur[i] / np.maximum(durMed20[i], 0.5),
    "dur_rel50": sDur[i] / np.maximum(durMed50[i], 0.5),
    "dur_ratio01": sDur[i] / np.maximum(sDur[i - 1], 0.5),
    "intens0": np.log1p(sIntens[i]),
    "intens_rel": sIntens[i] / np.maximum(intensMed20[i], 1e-6),
    "regime_dur": np.log1p(durMed20[i]),
    "regime_aggt": np.log1p(aggtMed20[i]),
    "hour": pd.to_datetime(df.DT.to_numpy()[i]).hour,
    "dow": (pd.to_datetime(df.DT.to_numpy()[i]).dayofweek + 1) % 7,  # MQL5: 0=domingo
})
for c in out.columns:
    if out[c].dtype.kind == "f" and c not in ("close", "R"):
        out[c] = out[c].round(6)

out.to_csv("out/parity_reference.csv", index=False)
print(f"out/parity_reference.csv  ->  {len(out)} sinais  (P1={(pat=='P1').sum()}, P2={(pat=='P2').sum()})")
print("\nultimas 5 linhas:")
print(out.tail(5).to_string(index=False))
print("\nComo validar:")
print("  1. anexe o indicador ao grafico Range 3.27 do XAUUSD com InpLogToCSV=true")
print("  2. compare MQL5/Files/range_reversal_log.csv com out/parity_reference.csv")
print("     (junte por close_time; toda feature deve bater ate 1e-6)")
