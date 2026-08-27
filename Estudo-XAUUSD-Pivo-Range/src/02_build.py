import pandas as pd, numpy as np
from lib import load, label_paths
df=load(); n=len(df)
D=df.DIR.to_numpy(); BR=df.BODYRATIO.to_numpy()

t=np.arange(2,n)
same=(D[t-2]==D[t-1])&(D[t-1]!=0)
opp=(D[t]==-D[t-1])
p1 = same & opp & (BR[t]<=0.50)
p2 = same & opp & (BR[t-1]>=0.70) & (BR[t]>=0.70)
print("P1:",p1.sum()," P2:",p2.sum()," overlap:",(p1&p2).sum())
print("baseline bars:",n)

# ---- baseline de controle: TODAS as barras ----
allidx=np.arange(n-1)
lab=label_paths(df,allidx,D[allidx],df.RANGE.to_numpy()[allidx])
base=pd.DataFrame(lab); base["idx"]=allidx; base["DIR"]=D[allidx]
res=base[base.success>=0]
print("\n=== BASELINE (toda barra, direcao=da barra, 3R/-1.3R) ===")
print("resolvidos:",len(res),"/",len(base),"  ambiguos:",base.ambiguous.sum())
print("taxa sucesso:",round(res.success.mean(),4))
print("por direcao:\n",res.groupby("DIR").success.agg(["count","mean"]))
base.to_parquet("out/baseline_all.parquet")

# ---- eventos dos padroes ----
def build(mask,name):
    ii=t[mask]
    dd=D[ii]; rr=df.RANGE.to_numpy()[ii]
    L=label_paths(df,ii,dd,rr)
    e=pd.DataFrame(L); e["idx"]=ii; e["pattern"]=name
    e["DT"]=df.DT.to_numpy()[ii]; e["side"]=dd
    e["R"]=rr
    return e
ev=pd.concat([build(p1,"P1"),build(p2,"P2")],ignore_index=True)
ev.to_parquet("out/events_raw.parquet")
print("\n=== EVENTOS ===")
for p,g in ev.groupby("pattern"):
    r=g[g.success>=0]
    print(f"{p}: n={len(g)} resolvidos={len(r)} nao_resolvidos={(g.success<0).sum()} ambiguos={g.ambiguous.sum()}")
    print(f"   sucesso={r.success.mean():.4f}  barras_med={r.bars_to_exit.median():.0f}  MFE_med={r.mfe.median():.2f}R MAE_med={r.mae.median():.2f}R")
    print("   por lado:\n",r.groupby("side").success.agg(["count","mean"]).to_string())
