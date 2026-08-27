import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
from scipy import stats
from lib import load
df=load(); n=len(df); TR,VA=int(n*.50),int(n*.70)
X=pd.read_parquet("out/features.parquet")
ev=pd.read_parquet("out/events_raw.parquet"); ev=ev[ev.success>=0]
base=pd.read_parquet("out/baseline_all.parquet"); base=base[base.success>=0]
BE=1.3/4.3; expR=lambda p:p*3-(1-p)*1.3
def prep(e):
    e=e.drop(columns=[c for c in e.columns if c in X.columns and c!="idx"])
    m=e.merge(X,on="idx",how="left")
    m["split"]=np.where(m.idx<TR,"TRAIN",np.where(m.idx<VA,"VAL","TEST")); return m
E=prep(ev); B=prep(base.assign(pattern="ALL"))
POOL=pd.concat([E,B.assign(pattern="ALL")])

def cut(d,by,label,q=None,minn=150):
    g=d.groupby(by,observed=True).success.agg(["count","mean"])
    g=g[g["count"]>=minn]; g["exp_R"]=g["mean"].apply(expR); g["vs_BE"]=g["mean"]-BE
    print(f"\n{label}"); print(g.round(4).to_string())

print("="*90); print("CORTES ESTATISTICOS (amostra COMPLETA — exploratorio)"); print("="*90)
for p in ["P1","P2"]:
    d=E[E.pattern==p].copy()
    print(f"\n{'#'*30} {p}  (n={len(d)}, base={d.success.mean():.4f}) {'#'*30}")
    cut(d,"side","--- por direcao (1=reversao de alta) ---")
    d["h"]=pd.cut(d.hour,[-1,5,8,11,14,17,20,23],labels=["00-05","06-08","09-11","12-14","15-17","18-20","21-23"])
    cut(d,"h","--- por horario (fechamento da barra, hora do servidor) ---")
    cut(d,"dow","--- por dia da semana (0=seg) ---")
    d["vol"]=pd.qcut(d.regime_dur,4,labels=["Q1 rapido/volatil","Q2","Q3","Q4 lento/calmo"])
    cut(d,"vol","--- por regime de volatilidade (mediana da duracao das 20 barras) ---")
    d["ag"]=pd.qcut(d.aggt_rel0,4,labels=["Q1 agressao baixa","Q2","Q3","Q4 agressao alta"])
    cut(d,"ag","--- por intensidade de agressao (AGGT / mediana20) ---")
    d["bal"]=pd.qcut(d.aggdn0,4,labels=["Q1 contra o trade","Q2","Q3","Q4 a favor do trade"])
    cut(d,"bal","--- por saldo de agressao alinhado ao trade ---")
    d["dr"]=pd.qcut(d.dur_rel0,4,labels=["Q1 barra rapida","Q2","Q3","Q4 barra lenta"])
    cut(d,"dr","--- por tempo de formacao relativo da barra de reversao ---")
    d["rp"]=pd.cut(d.run_prev,[1,2,3,4,100],labels=["2","3","4","5+"])
    cut(d,"rp","--- por n de barras consecutivas antes da reversao ---")

print("\n"+"="*90); print("HIPOTESE SOBREVIVENTE DA UNIVARIADA — validacao OUT-OF-SAMPLE"); print("="*90)
print("Regra descoberta no TRAIN: sucesso maior em regime CALMO (baixa agressao/duracao curta).")
for nm,d in [("P1",E[E.pattern=="P1"]),("P2",E[E.pattern=="P2"]),("P1+P2",E),("TODAS",B)]:
    d=d.copy()
    thr=d.loc[d.split=="TRAIN","regime_aggt"].quantile(.25)
    thr2=d.loc[d.split=="TRAIN","aggt0"].quantile(.25)
    d["rule"]=(d.regime_aggt<=thr)&(d.aggt0<=thr2)
    print(f"\n[{nm}] thr regime_aggt<={thr:.3f} & aggt0<={thr2:.3f}")
    for sp in ["TRAIN","VAL","TEST"]:
        s=d[(d.split==sp)]; a=s[s.rule]; b=s[~s.rule]
        pv=stats.fisher_exact([[int(a.success.sum()),len(a)-int(a.success.sum())],
                               [int(b.success.sum()),len(b)-int(b.success.sum())]])[1] if len(a)>0 else np.nan
        print(f"  {sp:5s} regra n={len(a):5d} p={a.success.mean():.4f} exp={expR(a.success.mean()):+.4f} | "
              f"resto n={len(b):5d} p={b.success.mean():.4f} | fisher_p={pv:.4f}")

print("\n"+"="*90); print("ESTABILIDADE TEMPORAL — taxa de sucesso por mes"); print("="*90)
for nm,d in [("P1",E[E.pattern=="P1"]),("P2",E[E.pattern=="P2"]),("TODAS",B)]:
    d=d.copy(); d["m"]=pd.to_datetime(df.DT.to_numpy()[d.idx]).to_period("M").astype(str)
    g=d.groupby("m").success.agg(["count","mean"]); g["exp_R"]=g["mean"].apply(expR)
    print(f"\n[{nm}]"); print(g.round(4).to_string())
