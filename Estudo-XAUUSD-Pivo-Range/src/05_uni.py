import pandas as pd, numpy as np
from scipy import stats
from lib import load
df=load()
X=pd.read_parquet("out/features.parquet")
ev=pd.read_parquet("out/events_raw.parquet"); ev=ev[ev.success>=0]
base=pd.read_parquet("out/baseline_all.parquet"); base=base[base.success>=0]
n=len(df)
TR,VA=int(n*.50),int(n*.70)
print("SPLIT TEMPORAL")
for nm,a,b in [("TRAIN",0,TR),("VAL",TR,VA),("TEST",VA,n)]:
    print(f" {nm:6s} bars[{a}:{b}] {df.DT[a]} -> {df.DT[b-1]}  ({b-a} barras)")
BE=1.3/4.3
FE=[c for c in X.columns if c!="idx"]

def prep(e):
    e=e.drop(columns=[c for c in e.columns if c in X.columns and c!="idx"])
    m=e.merge(X,on="idx",how="left")
    m["split"]=np.where(m.idx<TR,"TRAIN",np.where(m.idx<VA,"VAL","TEST"))
    return m
E=prep(ev); B=prep(base.assign(pattern="ALL"))

def deciles(d,f,q=5):
    x=d[f].replace([np.inf,-np.inf],np.nan)
    ok=x.notna()
    if ok.sum()<200: return None
    try: b=pd.qcut(x[ok],q,duplicates="drop")
    except Exception: return None
    g=d.loc[ok].groupby(b,observed=True).success.agg(["count","mean"])
    if len(g)<3: return None
    return g

def spread_test(d,f,q=5):
    g=deciles(d,f,q)
    if g is None: return None
    lo,hi=g.iloc[0],g.iloc[-1]
    # fisher entre extremos
    a=int(round(lo["mean"]*lo["count"])); b=int(lo["count"])-a
    c=int(round(hi["mean"]*hi["count"])); e=int(hi["count"])-c
    pv=stats.fisher_exact([[c,e],[a,b]])[1]
    # correlacao ponto-biserial (spearman) em todo o range
    x=d[f].replace([np.inf,-np.inf],np.nan); ok=x.notna()
    rho,pr=stats.spearmanr(x[ok],d.loc[ok,"success"])
    return dict(feature=f,q_lo=lo["mean"],q_hi=hi["mean"],spread=hi["mean"]-lo["mean"],
                fisher_p=pv,spearman=rho,sp_p=pr,n=int(ok.sum()))

for label,D in [("P1",E[(E.pattern=="P1")]),("P2",E[(E.pattern=="P2")]),("TODAS AS BARRAS",B)]:
    d=D[D.split=="TRAIN"]
    res=[r for f in FE if (r:=spread_test(d,f)) is not None]
    r=pd.DataFrame(res).sort_values("sp_p")
    # Benjamini-Hochberg
    r["rank"]=np.arange(1,len(r)+1); r["bh"]=r.sp_p*len(r)/r["rank"]
    r["bh"]=r.bh[::-1].cummin()[::-1]
    print("\n"+"="*100); print(f"UNIVARIADA — {label} (TRAIN, n={len(d)}, taxa base={d.success.mean():.4f})"); print("="*100)
    print(r.head(15)[["feature","n","q_lo","q_hi","spread","spearman","sp_p","bh"]].round(4).to_string(index=False))
    print(f"  features com BH<0.05: {(r.bh<0.05).sum()} / {len(r)}")
