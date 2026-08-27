"""VWAP (volume = agressao de compra + venda) e features de contexto S/R.

Tudo causal: VWAP acumula dentro da sessao ate a barra t inclusive; os niveis
vem do snapshot cuja ancora e <= t (calculado so com barras < ancora).
"""
import pickle
import numpy as np, pandas as pd
from lib import load

df = load(); n = len(df)
H, L, C = df.HIGH.to_numpy(), df.LOW.to_numpy(), df.CLOSE.to_numpy()
R, D = df.RANGE.to_numpy(), df.DIR.to_numpy()
V = df.AGGT.to_numpy()                      # volume = TICKVOL + VOL

# ---------------------------------------------------------------- sessoes
gap = np.zeros(n, bool)
gap[1:] = df.DT.diff().dt.total_seconds().to_numpy()[1:] > 3600
sess = np.cumsum(gap)
print(f"sessoes detectadas (gap > 1h): {sess.max()+1}")
bars_sess = pd.Series(np.ones(n)).groupby(sess).cumsum().to_numpy()
print(f"barras por sessao: mediana={np.median(np.bincount(sess)):.0f}")

# ---------------------------------------------------------------- VWAP
TP = (H + L + C) / 3.0
g = pd.DataFrame({"s": sess, "pv": TP * V, "v": V, "pv2": TP * TP * V})
cum = g.groupby("s").cumsum()
cv = cum.v.to_numpy(); cv = np.where(cv > 0, cv, np.nan)
VWAP = cum.pv.to_numpy() / cv
var = cum.pv2.to_numpy() / cv - VWAP ** 2
SIG = np.sqrt(np.maximum(var, 0.0))
VWAP = pd.Series(VWAP).ffill().to_numpy()
SIG = pd.Series(SIG).ffill().fillna(0.0).to_numpy()
print(f"VWAP: sigma mediano={np.nanmedian(SIG):.2f} USD ({np.nanmedian(SIG)/3.27:.2f} R)")

sess_hi = pd.Series(H).groupby(sess).cummax().to_numpy()
sess_lo = pd.Series(L).groupby(sess).cummin().to_numpy()

# VWAP defasado 20 barras dentro da sessao, para a inclinacao
vw_lag = pd.Series(VWAP).shift(20).to_numpy()
same_sess = pd.Series(sess).shift(20).to_numpy() == sess

# ---------------------------------------------------------------- eventos
ev = pd.read_parquet("out/events_raw.parquet")
ev = ev[ev.success >= 0].copy().sort_values("idx").reset_index(drop=True)
i = ev.idx.to_numpy(); s = ev.side.to_numpy(); r = ev.R.to_numpy()
ext = np.where(s > 0, L[i], H[i])           # ponto onde o mercado virou

F = {}
F["sess_bars"] = bars_sess[i]
F["vwap_dist_R"] = (C[i] - VWAP[i]) / r
F["vwap_gap_R"] = np.abs(C[i] - VWAP[i]) / r
F["vwap_z"] = np.where(SIG[i] > 1e-9, (C[i] - VWAP[i]) / np.maximum(SIG[i], 1e-9), 0.0)
F["vwap_z_aligned"] = F["vwap_z"] * s
F["vwap_toward"] = (s * (VWAP[i] - C[i]) > 0).astype(float)
sl = np.where(same_sess[i], (VWAP[i] - vw_lag[i]) / r, 0.0)
F["vwap_slope_R"] = sl
F["vwap_slope_aligned"] = sl * s
F["sess_hi_dist_R"] = (sess_hi[i] - C[i]) / r
F["sess_lo_dist_R"] = (C[i] - sess_lo[i]) / r
F["sess_pos"] = np.where(sess_hi[i] > sess_lo[i],
                         (C[i] - sess_lo[i]) / np.maximum(sess_hi[i] - sess_lo[i], 1e-9), .5)
F["sess_pos_aligned"] = np.where(s > 0, F["sess_pos"], 1 - F["sess_pos"])
F["round10_R"] = np.abs(ext - np.round(ext / 10) * 10) / r
F["round50_R"] = np.abs(ext - np.round(ext / 50) * 50) / r

# ---------------------------------------------------------------- niveis S/R
for variant in ("renko", "extreme"):
    snap = pickle.load(open(f"out/sr_snapshots_{variant}.pkl", "rb"))["snapshots"]
    anchors = np.array([a for a, _ in snap])
    tabs = [t for _, t in snap]
    m = len(i)
    dist = np.full(m, np.nan); score = np.full(m, np.nan); ndays = np.full(m, np.nan)
    age = np.full(m, np.nan); room = np.full(m, np.nan); behind = np.full(m, np.nan)
    pierce = np.zeros(m); nlev = np.full(m, np.nan)
    k = np.searchsorted(anchors, i, side="right") - 1
    for j in range(m):
        if k[j] < 0:
            continue
        T = tabs[k[j]]
        p = T.price.to_numpy(); sc = T.score.to_numpy()
        ud = T.unique_days.to_numpy(); ag = T.age_days.to_numpy()
        nlev[j] = len(p)
        d = np.abs(p - ext[j]); q = d.argmin()
        dist[j] = d[q] / r[j]; score[j] = sc[q]; ndays[j] = ud[q]; age[j] = ag[q]
        if s[j] > 0:
            ahead = p[p > C[j]]; back = p[p < C[j]]
            room[j] = (ahead.min() - C[j]) / r[j] if ahead.size else 99.0
            behind[j] = (C[j] - back.max()) / r[j] if back.size else 99.0
            pierce[j] = float(((p > L[i[j]]) & (p < C[j])).any())
        else:
            ahead = p[p < C[j]]; back = p[p > C[j]]
            room[j] = (C[j] - ahead.max()) / r[j] if ahead.size else 99.0
            behind[j] = (back.min() - C[j]) / r[j] if back.size else 99.0
            pierce[j] = float(((p < H[i[j]]) & (p > C[j])).any())
    v = variant[:3]
    F[f"{v}_dist_R"] = dist
    F[f"{v}_touch"] = (dist <= 0.5).astype(float)
    F[f"{v}_pierce"] = pierce
    F[f"{v}_score"] = score
    F[f"{v}_ndays"] = ndays
    F[f"{v}_age"] = age
    F[f"{v}_room_R"] = room
    F[f"{v}_behind_R"] = behind
    F[f"{v}_room_ok"] = (room >= 3.0).astype(float)
    F[f"{v}_nlev"] = nlev
    print(f"[{variant}] dist ao nivel mais proximo (R): mediana={np.nanmedian(dist):.2f} "
          f"p10={np.nanpercentile(dist,10):.2f} | room mediana={np.nanmedian(room):.2f} R "
          f"| touch={np.nanmean(F[f'{v}_touch']):.1%} | pierce={np.nanmean(pierce):.1%}")

X = pd.DataFrame(F); X["idx"] = i
X.to_parquet("out/context.parquet")
print(f"\ncontexto: {X.shape[1]-1} features x {len(X)} eventos -> out/context.parquet")
