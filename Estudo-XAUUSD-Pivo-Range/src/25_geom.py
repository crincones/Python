"""O nivel S/R serve como STOP melhor que uma distancia fixa?

Ideia: numa reversao de alta sobre um suporte, o stop natural fica logo abaixo
do nivel -- normalmente mais perto que 1,3R. Se o nivel protege de verdade, a
taxa de acerto nao cai proporcionalmente e a expectativa melhora.

Controle decisivo: permutar as distancias de stop entre os eventos. Mantem a
MESMA distribuicao de distancias, destrui o vinculo com o nivel.
"""
import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from lib import load
np.random.seed(7)
df = load(); n = len(df)
H, L, C = df.HIGH.to_numpy(), df.LOW.to_numpy(), df.CLOSE.to_numpy()
E = pd.read_parquet("out/events_ctx.parquet").sort_values("idx").reset_index(drop=True)

def paths(idx, side, R, tgt_R, stp_R, W=1500):
    """tgt_R / stp_R: arrays com a distancia em multiplos de R, por evento."""
    m = len(idx); succ = np.full(m, -1, np.int8)
    for k in range(m):
        t, d, r, c = idx[k], side[k], R[k], C[idx[k]]
        tg, sp = c + d*tgt_R[k]*r, c - d*stp_R[k]*r
        a, b = t+1, min(n, t+1+W)
        if a >= b: continue
        hi, lo = H[a:b], L[a:b]
        ht = (hi >= tg) if d > 0 else (lo <= tg)
        hs = (lo <= sp) if d > 0 else (hi >= sp)
        it = ht.argmax() if ht.any() else -1
        isx = hs.argmax() if hs.any() else -1
        if it < 0 and isx < 0: continue
        if isx < 0: succ[k] = 1
        elif it < 0: succ[k] = 0
        else: succ[k] = 1 if it < isx else 0     # empate -> stop (conservador)
    return succ

# stop derivado do nivel: logo alem do extremo do candle OU do nivel, o que for mais longe
i = E.idx.to_numpy(); s = E.side.to_numpy(); R = E.R.to_numpy()
lvl = np.where(s > 0, C[i] - E.ext_dist_R.to_numpy()*R, C[i] + E.ext_dist_R.to_numpy()*R)
ext = np.where(s > 0, L[i], H[i])
lvl = np.where(s > 0, np.minimum(lvl, ext), np.maximum(lvl, ext))   # stop nunca dentro do candle
BUF = 0.15
sd_lvl = np.abs(C[i] - lvl)/R + BUF
E["sd_lvl"] = sd_lvl

usable = E.ext_dist_R.notna() & (sd_lvl >= 0.6) & (sd_lvl <= 1.6)
print(f"eventos com stop de nivel utilizavel (0,6R a 1,6R): {usable.sum()} de {len(E)} ({usable.mean():.1%})")
print(f"distancia do stop: mediana={np.median(sd_lvl[usable]):.2f}R  "
      f"p10={np.percentile(sd_lvl[usable],10):.2f}R  p90={np.percentile(sd_lvl[usable],90):.2f}R\n")

U = E[usable].reset_index(drop=True)
iu, su, Ru = U.idx.to_numpy(), U.side.to_numpy(), U.R.to_numpy()
sdu = U.sd_lvl.to_numpy()
one = np.ones(len(U))

def rep(nm, succ, stp):
    ok = succ >= 0; p = succ[ok].mean(); sd = stp[ok].mean()
    e = p*3 - (1-p)*sd
    be = sd/(3+sd)
    return dict(cenario=nm, n=int(ok.sum()), acerto=round(p,4), stop_med=round(sd,3),
                breakeven=round(be,4), exp_R=round(e,4), margem=round(p-be,4))

rows = [
  rep("A) 3R / 1,3R fixo  (referencia)", paths(iu,su,Ru,3*one,1.3*one), 1.3*one),
  rep("B) 3R / 1,1R fixo",               paths(iu,su,Ru,3*one,1.1*one), 1.1*one),
  rep("C) 3R / stop no NIVEL",           paths(iu,su,Ru,3*one,sdu),      sdu),
]
# controle: mesma distribuicao de distancias, vinculo com o nivel destruido
ctrl = []
for seed in range(15):
    perm = np.random.default_rng(seed).permutation(sdu)
    r = rep("ctrl", paths(iu,su,Ru,3*one,perm), perm)
    ctrl.append((r["acerto"], r["exp_R"], r["margem"]))
ctrl = np.array(ctrl)
print(pd.DataFrame(rows).to_string(index=False))
print(f"\nD) CONTROLE — distancias PERMUTADAS entre eventos (15 seeds):")
print(f"   acerto  = {ctrl[:,0].mean():.4f} +- {ctrl[:,0].std():.4f}")
print(f"   exp_R   = {ctrl[:,1].mean():+.4f} +- {ctrl[:,1].std():.4f}")
print(f"   margem  = {ctrl[:,2].mean():+.4f} +- {ctrl[:,2].std():.4f}")
zc = (rows[2]["exp_R"] - ctrl[:,1].mean())/ctrl[:,1].std()
print(f"\n   >>> z do stop-no-nivel contra o controle permutado: {zc:+.2f}")

print("\n" + "="*96)
print("O stop no nivel testado nos TRES periodos")
print("="*96)
U = U.assign(succ_lvl=paths(iu,su,Ru,3*one,sdu), sd=sdu)
for sp in ("TRAIN","VAL","TEST"):
    t = U[(U.split==sp) & (U.succ_lvl>=0)]
    if len(t) < 60: continue
    p = t.succ_lvl.mean(); sd = t.sd.mean(); be = sd/(3+sd)
    tA = U[(U.split==sp)]
    print(f"  {sp:5s} n={len(t):5d} acerto={p:.4f} stop_med={sd:.2f}R "
          f"breakeven={be:.4f} exp={p*3-(1-p)*sd:+.4f} margem={p-be:+.4f}")
print("\n(margem = acerto - breakeven; positiva e necessaria, nao suficiente: falta o custo)")
