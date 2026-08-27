import pandas as pd, numpy as np
from lib import load
df=load(); n=len(df)
C=df.CLOSE.to_numpy(); D=df.DIR.to_numpy(); R=df.RANGE.to_numpy()

# runlength de barras consecutivas na mesma direcao ANTES da barra t (i.e. terminando em t-1)
run=np.zeros(n,int); run[0]=1
for i in range(1,n): run[i]=run[i-1]+1 if D[i]==D[i-1] else 1
df["RUN_PREV"]=pd.Series(run).shift(1).fillna(1)   # comprimento da sequencia que termina em t-1

# rollings causais (incluem barra t)
for w in (10,20,50):
    df[f"DUR_MED{w}"]=df.DUR.rolling(w,min_periods=w//2).median()
    df[f"AGGT_MED{w}"]=df.AGGT.rolling(w,min_periods=w//2).median()
df["AGGDN_SUM3"]=df.AGGDN.rolling(3).sum()
df["AGGDN_SUM5"]=df.AGGDN.rolling(5).sum()
df["AGGDN_SUM10"]=df.AGGDN.rolling(10).sum()
df["INTENS"]=df.AGGT/df.DUR.clip(lower=0.5)          # agressao por segundo
df["INTENS_MED20"]=df.INTENS.rolling(20,min_periods=10).median()

FEATS={}
def F(name,arr): FEATS[name]=np.asarray(arr,float)

t=np.arange(2,n)
s=D[t]                                   # lado da reversao (+1 long)
g=lambda col: df[col].to_numpy()

# ---------- estrutura / preco ----------
F("br0",g("BODYRATIO")[t]);  F("br1",g("BODYRATIO")[t-1]); F("br2",g("BODYRATIO")[t-2])
F("wick0",g("WICKR")[t]);    F("wick1",g("WICKR")[t-1]);   F("wick2",g("WICKR")[t-2])
F("openpos0",g("OPENPOS")[t])
F("rng_ratio01",R[t]/R[t-1]); F("rng_ratio12",R[t-1]/R[t-2])
F("run_prev",g("RUN_PREV")[t])
F("dclose01",(C[t]-C[t-1])/R[t]*s); F("dclose12",(C[t-1]-C[t-2])/R[t]*s)
for k in (3,5,10,20):
    idx=np.maximum(t-k,0)
    F(f"disp{k}",(C[t]-C[idx])/R[t]*s)   # deslocamento liquido, sinal alinhado ao trade
# posicao no canal recente
for k in (20,50):
    hh=df.HIGH.rolling(k,min_periods=k//2).max().to_numpy()[t]
    ll=df.LOW.rolling(k,min_periods=k//2).min().to_numpy()[t]
    pos=(C[t]-ll)/np.maximum(hh-ll,1e-9)
    F(f"chanpos{k}", np.where(s>0,pos,1-pos))        # 0 = extremo a favor do trade

# ---------- agressao ----------
F("aggdn0",g("AGGDN")[t]*s); F("aggdn1",g("AGGDN")[t-1]*s); F("aggdn2",g("AGGDN")[t-2]*s)
F("aggratio0",g("AGGRATIO")[t]*s); F("aggratio1",g("AGGRATIO")[t-1]*s)
F("aggdn_sum3",g("AGGDN_SUM3")[t]*s); F("aggdn_sum5",g("AGGDN_SUM5")[t]*s); F("aggdn_sum10",g("AGGDN_SUM10")[t]*s)
F("daggdn",(g("AGGDN")[t]-g("AGGDN")[t-1])*s)
F("diverg0",g("AGGDN")[t]*D[t])          # >0 agressao concorda com a barra t
F("diverg1",g("AGGDN")[t-1]*D[t-1])
F("aggt0",np.log1p(g("AGGT")[t])); F("aggt1",np.log1p(g("AGGT")[t-1]))
F("aggt_rel0",g("AGGT")[t]/np.maximum(g("AGGT_MED20")[t],1)); F("aggt_rel1",g("AGGT")[t-1]/np.maximum(g("AGGT_MED20")[t-1],1))
F("aggt_rel50",g("AGGT")[t]/np.maximum(g("AGGT_MED50")[t],1))
F("aggt_ratio01",g("AGGT")[t]/np.maximum(g("AGGT")[t-1],1))
F("buy_rel",df.BUY.to_numpy()[t]/np.maximum(g("AGGT_MED20")[t]/2,1))
F("sell_rel",df.SELL.to_numpy()[t]/np.maximum(g("AGGT_MED20")[t]/2,1))
F("agg_per_R",g("AGGT")[t]/R[t])

# ---------- tempo ----------
F("dur0",np.log1p(g("DUR")[t])); F("dur1",np.log1p(g("DUR")[t-1])); F("dur2",np.log1p(g("DUR")[t-2]))
F("dur_rel0",g("DUR")[t]/np.maximum(g("DUR_MED20")[t],.5))
F("dur_rel1",g("DUR")[t-1]/np.maximum(g("DUR_MED20")[t-1],.5))
F("dur_rel50",g("DUR")[t]/np.maximum(g("DUR_MED50")[t],.5))
F("dur_ratio01",g("DUR")[t]/np.maximum(g("DUR")[t-1],.5))
F("dur_ratio12",g("DUR")[t-1]/np.maximum(g("DUR")[t-2],.5))
F("dur_accel",np.log1p(g("DUR")[t])-2*np.log1p(g("DUR")[t-1])+np.log1p(g("DUR")[t-2]))
F("intens0",np.log1p(g("INTENS")[t]))
F("intens_rel",g("INTENS")[t]/np.maximum(g("INTENS_MED20")[t],1e-6))
F("dur_per_R",g("DUR")[t]/R[t])

# ---------- regime / contexto ----------
F("regime_dur",np.log1p(g("DUR_MED20")[t]))       # inverso da volatilidade (s por 3.27 usd)
F("regime_aggt",np.log1p(np.maximum(g("AGGT_MED20")[t],1)))
hh=df.DT.dt.hour.to_numpy()[t]; dw=df.DT.dt.dayofweek.to_numpy()[t]
F("hour",hh); F("dow",dw)
F("hour_sin",np.sin(2*np.pi*hh/24)); F("hour_cos",np.cos(2*np.pi*hh/24))
F("side",s)

X=pd.DataFrame(FEATS); X["idx"]=t
X.to_parquet("out/features.parquet")
print("features:",X.shape[1]-1,"linhas:",len(X))
print(list(FEATS.keys()))
