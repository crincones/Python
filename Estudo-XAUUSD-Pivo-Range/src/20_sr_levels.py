"""Niveis S/R CAUSAIS usando o motor do SR-metatrader5.

O Renko e uma construcao incremental: o tijolo i so depende de barras <= pos[i].
Entao construimos o Renko UMA vez sobre todo o historico e, a cada ancora de
recalculo, fatiamos os tijolos ate aquele instante e rodamos eventos ->
clustering -> score somente sobre o passado. Um sinal na barra t so enxerga o
conjunto de niveis da ancora imediatamente anterior a t.
"""
import sys, os, pickle, time
import numpy as np, pandas as pd
SR = r"C:\Users\Carlos\Documents\GitHub\Python\SR-metatrader5"
sys.path.insert(0, SR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load

from config import Config
from data.renko import build_renko
from detection.renko_events import build_renko_events
from detection.events import event_weights
from clustering import cluster_events
from scoring.score import build_levels, select_levels

TICK = 0.01
cfg = Config(
    mode="renko", symbol="XAUUSD", tick_size=TICK,
    renko_box_ticks=1640,                 # 16.40 USD (~5 range bars)
    cluster_method="dbscan", min_events=2,
    level_separation=400 * TICK,          # 4.00
    window_points=80000 * TICK,           # +-800
    max_gap=1500 * TICK,                  # 15.00
    top_n=50,
)
import sys as _s
VARIANT = _s.argv[1] if len(_s.argv) > 1 else "renko"
cfg.renko_price_method = VARIANT
BOX = cfg.renko_box_ticks * TICK
BAND = cfg.cluster_box_factor * BOX
SEP = cfg.level_separation

df = load()
src = pd.DataFrame({
    "open": df.OPEN.to_numpy(), "high": df.HIGH.to_numpy(),
    "low": df.LOW.to_numpy(), "close": df.CLOSE.to_numpy(),
    "volume": df.AGGT.to_numpy(),         # agressao total = compra + venda
}, index=pd.DatetimeIndex(df.DT, name="timestamp"))
n = len(src)
print(f"VARIANTE={VARIANT}")
print(f"barras={n}  box={BOX}  band={BAND}  sep={SEP}")

t0 = time.time()
bricks = build_renko(src, BOX, cfg.renko_anchor)
print(f"renko: {len(bricks)} tijolos em {time.time()-t0:.1f}s")

rel_vol = (src.volume / src.volume.rolling(cfg.vol_norm_window,
           min_periods=max(50, cfg.vol_norm_window // 20)).mean().bfill()).to_numpy()

# ancoras de recalculo: a cada virada de dia de pregao, apos aquecimento
day = pd.Series(df.DT.dt.normalize().to_numpy())
anchors = np.flatnonzero(day.ne(day.shift()).to_numpy())
WARMUP = 15000
anchors = anchors[anchors >= WARMUP]
print(f"ancoras de recalculo: {len(anchors)} (1a na barra {anchors[0]})")

bpos = bricks["pos"].to_numpy()
snapshots = []          # (bar_idx_valido_a_partir_de, DataFrame de niveis)
t0 = time.time()
for k, a in enumerate(anchors):
    nb = np.searchsorted(bpos, a)         # tijolos fechados estritamente antes de a
    if nb < 40:
        continue
    bs = bricks.iloc[:nb]
    sub = src.iloc[:a]
    ev = build_renko_events(bs, sub, cfg, rel_vol[:a], BOX)
    if len(ev) < 10:
        continue
    ref_time = sub.index[-1]
    ref_price = float(sub.close.iloc[-1])
    w = event_weights(ev, cfg, ref_time)
    labels, info = cluster_events(ev["price"].to_numpy(), w, cfg, BAND,
                                  cfg.peak_distance_ratio * SEP, space="linear",
                                  grid_step=BOX)
    levels = build_levels(ev, w, labels, cfg, TICK, ref_time, peaks=info.get("peaks"))
    sel = select_levels(levels, cfg, SEP, ref_price=ref_price)
    if not sel:
        continue
    snapshots.append((int(a), pd.DataFrame([{
        "price": lv.price, "score": lv.score, "n_events": lv.n_events,
        "unique_days": lv.unique_days, "span_days": lv.span_days,
        "mean_strength": lv.mean_strength,
        "age_days": (ref_time - lv.last_event).total_seconds() / 86400.0,
    } for lv in sel])))
    if k % 40 == 0:
        print(f"  ancora {k}/{len(anchors)} barra={a} eventos={len(ev)} "
              f"niveis={len(sel)} maior_cluster={info['maior_cluster']:.2f} "
              f"({time.time()-t0:.0f}s)")

print(f"snapshots={len(snapshots)} em {time.time()-t0:.1f}s")
with open(f"out/sr_snapshots_{VARIANT}.pkl", "wb") as fh:
    pickle.dump({"snapshots": snapshots, "box": BOX, "sep": SEP}, fh)

nl = [len(s[1]) for s in snapshots]
print(f"niveis por snapshot: mediana={np.median(nl):.0f} min={min(nl)} max={max(nl)}")
print("\nexemplo (ultimo snapshot, 10 niveis mais proximos do preco):")
a, L = snapshots[-1]
p = float(src.close.iloc[a - 1])
print(f"preco de referencia={p:.2f}")
print(L.assign(dist=(L.price - p).round(2)).reindex(
    (L.price - p).abs().sort_values().index).head(10).to_string(index=False))
