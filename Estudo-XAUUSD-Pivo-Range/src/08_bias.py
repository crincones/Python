import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import roc_auc_score
from catboost import CatBoostClassifier
from scipy import stats
from lib import load,label_paths
np.random.seed(7)
df=load(); n=len(df); TR,VA=int(n*.50),int(n*.70)
X=pd.read_parquet("out/features.parquet")
ev=pd.read_parquet("out/events_raw.parquet")
FE=[c for c in X.columns if c!="idx"]; BE=1.3/4.3; expR=lambda p:p*3-(1-p)*1.3

print("="*88); print("A) TRADES QUE ATRAVESSAM GAP TEMPORAL (>6h)"); print("="*88)
gap=(df.DT.diff().dt.total_seconds()>6*3600).to_numpy()
e=ev[ev.success>=0].copy()
cross=np.array([gap[i+1:i+1+int(b)].any() for i,b in zip(e.idx,e.bars_to_exit.fillna(0))])
e["cross"]=cross
print(f"eventos atravessando gap: {cross.sum()} ({cross.mean():.2%})")
print(e.groupby(["pattern","cross"]).success.agg(["count","mean"]).round(4).to_string())
cl=e[~e.cross]
print("\nsem trades sobre gap:")
print(cl.groupby("pattern").success.agg(["count","mean"]).assign(exp_R=lambda d:d["mean"].apply(expR)).round(4).to_string())

print("\n"+"="*88); print("B) CONTROLE ALEATORIO PAREADO (mesma qtde, direcao aleatoria)"); print("="*88)
res=[]
for s in range(20):
    rng=np.random.default_rng(s)
    ii=np.sort(rng.choice(np.arange(2,n-1),7000,replace=False))
    dd=rng.choice([-1,1],len(ii))
    L=label_paths(df,ii,dd,df.RANGE.to_numpy()[ii])
    r=pd.DataFrame(L); r=r[r.success>=0]; res.append(r.success.mean())
res=np.array(res)
print(f"controle aleatorio (n=7000 x 20 seeds): media={res.mean():.4f} sd={res.std():.4f} "
      f"IC95=[{np.percentile(res,2.5):.4f},{np.percentile(res,97.5):.4f}]")
for p,g in e.groupby("pattern"):
    z=(g.success.mean()-res.mean())/res.std()
    print(f"  {p}: p={g.success.mean():.4f}  z vs controle = {z:+.2f}")

print("\n"+"="*88); print("C) CONTROLE DE VAZAMENTO / SANIDADE DO PIPELINE"); print("="*88)
def wf_auc(d,feats,shuffle=False,nfolds=5):
    d=d.sort_values("idx").reset_index(drop=True); N=len(d)
    bounds=[int(N*(0.4+0.6*i/nfolds)) for i in range(nfolds+1)]; oof=np.full(N,np.nan)
    for k in range(nfolds):
        a,b=bounds[k],bounds[k+1]; tr=d[d.idx<=d.idx.iloc[a-1]-100]; te=d.iloc[a:b]
        if len(tr)<500: continue
        y=tr.success.astype(int).values
        if shuffle: y=np.random.default_rng(k).permutation(y)
        m=CatBoostClassifier(iterations=400,depth=4,learning_rate=.03,l2_leaf_reg=10,
            random_seed=7,verbose=0,allow_writing_files=False)
        m.fit(tr[feats].replace([np.inf,-np.inf],np.nan),y)
        oof[a:b]=m.predict_proba(te[feats].replace([np.inf,-np.inf],np.nan))[:,1]
    ok=~np.isnan(oof); return roc_auc_score(d.success.astype(int)[ok],oof[ok])

E=ev[ev.success>=0].drop(columns=[c for c in ev.columns if c in X.columns and c!="idx"]).merge(X,on="idx")
print(f"C1 real            (P1+P2): AUC={wf_auc(E,FE):.4f}")
print(f"C2 labels embaralhados     : AUC={wf_auc(E,FE,shuffle=True):.4f}   (esperado ~0.50)")
Ep=E.copy(); Ep["FUTURO"]=Ep.mfe.values     # controle positivo: feature com lookahead
print(f"C3 controle POSITIVO (+MFE): AUC={wf_auc(Ep,FE+['FUTURO']):.4f}   (deve ser >>0.5 => pipeline detecta sinal)")

print("\n"+"="*88); print("D) IMPORTANCIA DE FEATURES — estabilidade entre periodos"); print("="*88)
imps={}
for lbl,a,b in [("1o terco",0,int(len(E)/3)),("2o terco",int(len(E)/3),int(2*len(E)/3)),("3o terco",int(2*len(E)/3),len(E))]:
    s=E.sort_values("idx").iloc[a:b]
    m=CatBoostClassifier(iterations=400,depth=4,learning_rate=.03,l2_leaf_reg=10,random_seed=7,verbose=0,allow_writing_files=False)
    m.fit(s[FE].replace([np.inf,-np.inf],np.nan),s.success.astype(int))
    imps[lbl]=pd.Series(m.get_feature_importance(),index=FE)
I=pd.DataFrame(imps)
I["rank1"]=I["1o terco"].rank(ascending=False); I["rank3"]=I["3o terco"].rank(ascending=False)
print(I.sort_values("1o terco",ascending=False).head(12).round(2).to_string())
print(f"\ncorrelacao de Spearman entre rankings de importancia 1o vs 3o terco: "
      f"{stats.spearmanr(I['1o terco'],I['3o terco']).statistic:.3f}  (1.0 = estavel, ~0 = ruido)")

print("\n"+"="*88); print("E) EXPECTATIVA POR THRESHOLD DE PROBABILIDADE (OOF walk-forward)"); print("="*88)
o=pd.read_parquet("out/oof_P1_P2.parquet"); o=o[o.oof.notna()]
for q in [0,.5,.7,.8,.9,.95]:
    thr=o.oof.quantile(q); s=o[o.oof>=thr]
    k,N=int(s.success.sum()),len(s)
    print(f"  q>={q:.2f} (p>={thr:.4f}): n={N:5d} sucesso={k/N:.4f} exp={expR(k/N):+.4f} "
          f"binom_p(>BE)={stats.binomtest(k,N,BE,alternative='greater').pvalue:.4f}")
