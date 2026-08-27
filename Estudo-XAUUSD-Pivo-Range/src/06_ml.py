import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from catboost import CatBoostClassifier
import lightgbm as lgb
from lib import load
np.random.seed(7)
df=load(); n=len(df)
X=pd.read_parquet("out/features.parquet")
ev=pd.read_parquet("out/events_raw.parquet"); ev=ev[ev.success>=0]
base=pd.read_parquet("out/baseline_all.parquet"); base=base[base.success>=0]
FE=[c for c in X.columns if c!="idx"]
BE=1.3/4.3
EMBARGO=100   # barras: trade mediano=6, p90=17, max=70 -> 100 e conservador

def prep(e,tag):
    e=e.drop(columns=[c for c in e.columns if c in X.columns and c!="idx"])
    m=e.merge(X,on="idx",how="left").sort_values("idx").reset_index(drop=True)
    m["tag"]=tag; return m

def walkforward(d,label,nfolds=5,model="cat"):
    """Folds expansivos com embargo. Treina no passado, testa no futuro."""
    d=d.sort_values("idx").reset_index(drop=True)
    N=len(d); bounds=[int(N*(0.4+0.6*i/nfolds)) for i in range(nfolds+1)]
    oof=np.full(N,np.nan); rows=[]
    for k in range(nfolds):
        a,b=bounds[k],bounds[k+1]
        tr_end_idx=d.idx.iloc[a-1]-EMBARGO
        tr=d[d.idx<=tr_end_idx]
        te=d.iloc[a:b]
        if len(tr)<500 or len(te)<100: continue
        Xtr,ytr=tr[FE].replace([np.inf,-np.inf],np.nan),tr.success.astype(int)
        Xte,yte=te[FE].replace([np.inf,-np.inf],np.nan),te.success.astype(int)
        if model=="cat":
            m=CatBoostClassifier(iterations=400,depth=4,learning_rate=0.03,l2_leaf_reg=10,
                random_seed=7,verbose=0,allow_writing_files=False)
            m.fit(Xtr,ytr)
        else:
            m=lgb.LGBMClassifier(n_estimators=400,num_leaves=15,learning_rate=0.03,
                min_child_samples=60,subsample=.8,colsample_bytree=.7,reg_lambda=10,
                random_state=7,verbose=-1)
            m.fit(Xtr,ytr)
        p=m.predict_proba(Xte)[:,1]; oof[a:b]=p
        rows.append(dict(fold=k,n_tr=len(tr),n_te=len(te),base=yte.mean(),
            auc=roc_auc_score(yte,p) if yte.nunique()>1 else np.nan,
            pr=average_precision_score(yte,p) if yte.nunique()>1 else np.nan,
            brier=brier_score_loss(yte,p)))
    r=pd.DataFrame(rows)
    ok=~np.isnan(oof); y=d.success.values[ok].astype(int); p=oof[ok]
    print(f"\n--- {label} [{model}] n={N} ---")
    print(r.round(4).to_string(index=False))
    print(f"OOF agregado: n={ok.sum()} base={y.mean():.4f} AUC={roc_auc_score(y,p):.4f} "
          f"PR-AUC={average_precision_score(y,p):.4f} Brier={brier_score_loss(y,p):.4f} "
          f"(Brier const={np.mean((y-y.mean())**2):.4f})")
    d=d.copy(); d["oof"]=oof
    return d,r

E=prep(ev,"ev"); B=prep(base.assign(pattern="ALL"),"all")
P1=E[E.pattern=="P1"]; P2=E[E.pattern=="P2"]; POOL=E
out={}
for nm,d in [("P1",P1),("P2",P2),("P1+P2",POOL),("TODAS AS BARRAS",B)]:
    for mdl in ("cat","lgb"):
        dd,r=walkforward(d,nm,model=mdl)
        out[(nm,mdl)]=dd
        if mdl=="cat": dd.to_parquet(f"out/oof_{nm.replace('+','_').replace(' ','_')}.parquet")
