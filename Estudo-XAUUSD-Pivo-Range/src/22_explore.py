import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from scipy import stats
from lib import load, label_paths
df = load(); n = len(df); TR, VA = int(n*.50), int(n*.70)
BE = 1.3/4.3; expR = lambda p: p*3 - (1-p)*1.3

ev = pd.read_parquet("out/events_raw.parquet"); ev = ev[ev.success >= 0].copy()
ev = ev.sort_values("idx").reset_index(drop=True)
CX = pd.read_parquet("out/context.parquet")
FT = pd.read_parquet("out/features.parquet")
E = ev.merge(CX, on="idx").merge(
        FT.drop(columns=[c for c in FT.columns if c in ev.columns and c != "idx"]), on="idx")
E["split"] = np.where(E.idx < TR, "TRAIN", np.where(E.idx < VA, "VAL", "TEST"))

# rotulos da direcao CONTRARIA (fade), para testar inversao condicional
fl = label_paths(df, E.idx.to_numpy(), -E.side.to_numpy(), E.R.to_numpy())
E["fade"] = fl["success"]
E.to_parquet("out/events_ctx.parquet")

CTX = [c for c in CX.columns if c != "idx"]
TRN = E[E.split == "TRAIN"]
print(f"TRAIN n={len(TRN)}  base={TRN.success.mean():.4f}  fade={TRN[TRN.fade>=0].fade.mean():.4f}")
print(f"breakeven={BE:.4f}  com custo 0.05R={(1.3+.05)/4.3:.4f}\n")

def buckets(d, f, q=4):
    x = d[f].replace([np.inf, -np.inf], np.nan)
    if x.notna().sum() < 400: return None
    try:
        b = pd.qcut(x, q, duplicates="drop")
    except Exception:
        u = x.dropna().unique()
        if len(u) > 6: return None
        b = x
    g = d.groupby(b, observed=True).agg(n=("success","size"), rev=("success","mean"),
                                        fad=("fade", lambda v: v[v>=0].mean()))
    return g[g.n >= 120]

print("="*104)
print("VARREDURA UNIVARIADA NO TRAIN — features de contexto (S/R + VWAP + sessao)")
print("="*104)
rows = []
for lbl, d in [("P1", TRN[TRN.pattern=="P1"]), ("P2", TRN[TRN.pattern=="P2"]), ("P1+P2", TRN)]:
    for f in CTX:
        g = buckets(d, f)
        if g is None or len(g) < 3: continue
        lo, hi = g.rev.iloc[0], g.rev.iloc[-1]
        x = d[f].replace([np.inf,-np.inf], np.nan); ok = x.notna()
        rho, pv = stats.spearmanr(x[ok], d.success[ok])
        rows.append(dict(grupo=lbl, feature=f, n=int(ok.sum()), q_lo=round(lo,4),
                         q_hi=round(hi,4), spread=round(hi-lo,4),
                         best=round(g.rev.max(),4), best_n=int(g.n[g.rev.idxmax()]),
                         rho=round(rho,4), p=pv))
Rr = pd.DataFrame(rows)
for lbl in ("P1","P2","P1+P2"):
    r = Rr[Rr.grupo==lbl].sort_values("p").copy()
    r["rank"] = np.arange(1,len(r)+1); r["bh"] = (r.p*len(r)/r["rank"])[::-1].cummin()[::-1]
    print(f"\n--- {lbl} (n={len(TRN[TRN.pattern==lbl]) if lbl!='P1+P2' else len(TRN)}) — top 10 por p-valor ---")
    print(r.head(10)[["feature","n","q_lo","q_hi","spread","best","best_n","rho","p","bh"]]
          .round(4).to_string(index=False))
    print(f"  features com BH<0.05: {(r.bh<0.05).sum()} / {len(r)}")

print("\n"+"="*104)
print("QUAL PADRAO VENCE EM CADA CONTEXTO? (TRAIN)")
print("="*104)
def cut(d, name, mask):
    a = d[mask]
    if len(a) < 150: return None
    out = {"contexto": name, "n": len(a)}
    for p in ("P1","P2"):
        s = a[a.pattern==p]
        out[f"{p}_n"] = len(s)
        out[f"{p}_rev"] = round(s.success.mean(),4) if len(s) >= 60 else np.nan
    return out
ctxs = [
 ("nivel tocado (extreme, dist<=0.5R)", TRN.ext_touch==1),
 ("nivel NAO tocado",                   TRN.ext_touch==0),
 ("perfurou nivel e voltou",            TRN.ext_pierce==1),
 ("espaco ate 3R livre (room>=3R)",     TRN.ext_room_R>=3),
 ("obstaculo perto (room<2R)",          TRN.ext_room_R<2),
 ("nivel forte (score>=70)",            TRN.ext_score>=70),
 ("trade aponta para o VWAP",           TRN.vwap_toward==1),
 ("trade se afasta do VWAP",            TRN.vwap_toward==0),
 ("|z do VWAP| >= 1",                   TRN.vwap_z.abs()>=1),
 ("extremo da sessao a favor",          TRN.sess_pos_aligned<=0.15),
 ("meio da sessao",                     TRN.sess_pos_aligned.between(.35,.65)),
 ("perto de numero redondo (<0.15R)",   TRN.round10_R<0.15),
]
res = [c for nm,m in ctxs if (c:=cut(TRN,nm,m))]
print(pd.DataFrame(res).to_string(index=False))
print(f"\nreferencia TRAIN: P1={TRN[TRN.pattern=='P1'].success.mean():.4f} "
      f"P2={TRN[TRN.pattern=='P2'].success.mean():.4f}")

print("\n"+"="*104)
print("A DIRECAO SE INVERTE EM ALGUM CONTEXTO? (reversao vs fade, TRAIN)")
print("="*104)
rows=[]
for nm, m in ctxs:
    a = TRN[m]
    if len(a) < 150: continue
    fa = a[a.fade>=0]
    rows.append(dict(contexto=nm, n=len(a), reversao=round(a.success.mean(),4),
                     fade=round(fa.fade.mean(),4),
                     melhor="fade" if fa.fade.mean() > a.success.mean() else "reversao",
                     dif=round(fa.fade.mean()-a.success.mean(),4)))
print(pd.DataFrame(rows).sort_values("dif", ascending=False).to_string(index=False))
