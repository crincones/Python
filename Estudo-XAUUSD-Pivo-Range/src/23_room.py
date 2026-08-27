import numpy as np, pandas as pd, pickle, warnings
warnings.filterwarnings("ignore")
from scipy import stats
from lib import load
df = load(); n = len(df); TR, VA = int(n*.50), int(n*.70)
BE = 1.3/4.3; BEC = (1.3+.05)/4.3; expR = lambda p: p*3-(1-p)*1.3
E = pd.read_parquet("out/events_ctx.parquet")
C = df.CLOSE.to_numpy(); R = df.RANGE.to_numpy()

print(f"breakeven={BE:.4f}   com custo 0,05R={BEC:.4f}\n")
print("="*100); print("1) room_R EM DECIS — TRAIN (exploracao)"); print("="*100)
d = E[E.split=="TRAIN"].copy()
d["b"] = pd.cut(d.ext_room_R, [0,1,1.5,2,2.5,3,3.5,4,99])
g = d.groupby("b", observed=True).success.agg(["count","mean"])
g["exp_R"] = g["mean"].apply(expR); g["vs_BEc"] = (g["mean"]-BEC).round(4)
print(g.round(4).to_string())
x = d.ext_room_R.replace([np.inf,-np.inf],np.nan); ok = x.notna()
print(f"\nSpearman={stats.spearmanr(x[ok],d.success[ok]).statistic:.4f} "
      f"p={stats.spearmanr(x[ok],d.success[ok]).pvalue:.4f}")

print("\n"+"="*100)
print("2) CONTROLE DECISIVO — niveis FALSOS com o mesmo espacamento")
print("="*100)
print("Se 'room' medisse so a posicao dentro de uma grade arbitraria, uma grade")
print("aleatoria com o mesmo passo produziria o mesmo efeito.\n")
snap = pickle.load(open("out/sr_snapshots_extreme.pkl","rb"))["snapshots"]
anchors = np.array([a for a,_ in snap]); tabs = [t for _,t in snap]
i = E.idx.to_numpy(); s = E.side.to_numpy(); r = E.R.to_numpy()
k = np.searchsorted(anchors, i, side="right") - 1
rows=[]
for seed in range(12):
    rng = np.random.default_rng(seed)
    room = np.full(len(i), np.nan)
    off = {}
    for j in range(len(i)):
        if k[j] < 0: continue
        if k[j] not in off:
            p = tabs[k[j]].price.to_numpy()
            step = np.median(np.diff(np.sort(p)))
            off[k[j]] = (np.sort(p).min() + rng.uniform(0,step), step, len(p))
        base, step, m = off[k[j]]
        grid = base + step*np.arange(-m-5, m+5)
        if s[j] > 0:
            a = grid[grid > C[i[j]]]; room[j] = (a.min()-C[i[j]])/r[j] if a.size else 99
        else:
            a = grid[grid < C[i[j]]]; room[j] = (C[i[j]]-a.max())/r[j] if a.size else 99
    t = E.assign(fake=room); t = t[(t.split=="TRAIN") & t.fake.notna()]
    lo = t[t.fake<2].success.mean(); hi = t[t.fake>=3].success.mean()
    rows.append(hi-lo)
fake = np.array(rows)
tt = E[(E.split=="TRAIN") & E.ext_room_R.notna()]
real = tt[tt.ext_room_R>=3].success.mean() - tt[tt.ext_room_R<2].success.mean()
print(f"grade FALSA  (12 seeds): diferenca [room>=3R] - [room<2R] = {fake.mean():+.4f} +- {fake.std():.4f}")
print(f"niveis REAIS            : diferenca                        = {real:+.4f}")
print(f"z do efeito real contra a grade falsa = {(real-fake.mean())/fake.std():+.2f}")

print("\n"+"="*100)
print("3) VALIDACAO FORA DA AMOSTRA — regra room>=3R")
print("="*100)
for lbl, sub in [("P1+P2", E), ("P1", E[E.pattern=="P1"]), ("P2", E[E.pattern=="P2"])]:
    print(f"\n[{lbl}]")
    for sp in ("TRAIN","VAL","TEST"):
        t = sub[(sub.split==sp) & sub.ext_room_R.notna()]
        a = t[t.ext_room_R>=3]; b = t[t.ext_room_R<3]
        if len(a) < 40: print(f"  {sp:5s} amostra insuficiente"); continue
        pv = stats.fisher_exact([[int(a.success.sum()),len(a)-int(a.success.sum())],
                                 [int(b.success.sum()),len(b)-int(b.success.sum())]])[1]
        print(f"  {sp:5s} room>=3R n={len(a):5d} p={a.success.mean():.4f} exp={expR(a.success.mean()):+.4f}"
              f" | room<3R n={len(b):5d} p={b.success.mean():.4f} | fisher_p={pv:.4f}")

print("\n"+"="*100)
print("4) COMBINACOES — testadas nos tres periodos")
print("="*100)
rules = {
 "room>=3R":                        lambda t: t.ext_room_R>=3,
 "room>=3R & nivel tocado":         lambda t: (t.ext_room_R>=3)&(t.ext_touch==1),
 "room>=3R & perfurou nivel":       lambda t: (t.ext_room_R>=3)&(t.ext_pierce==1),
 "room>=3R & extremo de sessao":    lambda t: (t.ext_room_R>=3)&(t.sess_pos_aligned<=0.25),
 "room>=3R & P2":                   lambda t: (t.ext_room_R>=3)&(t.pattern=="P2"),
 "room>=3R & aponta p/ VWAP":       lambda t: (t.ext_room_R>=3)&(t.vwap_toward==1),
 "nivel tocado":                    lambda t: t.ext_touch==1,
 "extremo de sessao a favor":       lambda t: t.sess_pos_aligned<=0.25,
}
out=[]
for nm,f in rules.items():
    row={"regra":nm}
    for sp in ("TRAIN","VAL","TEST"):
        t = E[(E.split==sp) & E.ext_room_R.notna()]; a = t[f(t)]
        row[f"{sp[:2]}_n"]=len(a); row[f"{sp[:2]}_p"]=round(a.success.mean(),4) if len(a)>=40 else np.nan
    out.append(row)
print(pd.DataFrame(out).to_string(index=False))
print(f"\nbreakeven={BE:.4f}  com custo 0,05R={BEC:.4f}")
