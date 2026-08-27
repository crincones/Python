import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from catboost import CatBoostClassifier
from scipy import stats
from lib import load
np.random.seed(7)
df=load(); n=len(df); TR,VA=int(n*.50),int(n*.70)
X=pd.read_parquet("out/features.parquet")
ev=pd.read_parquet("out/events_raw.parquet"); ev=ev[ev.success>=0]
FE=[c for c in X.columns if c!="idx"]
E=ev.drop(columns=[c for c in ev.columns if c in X.columns and c!="idx"]).merge(X,on="idx").sort_values("idx").reset_index(drop=True)
E["split"]=np.where(E.idx<TR,"TRAIN",np.where(E.idx<VA,"VAL","TEST"))
BE=1.3/4.3
def expR(p,c=0.0): return p*(3-c)-(1-p)*(1.3+c)
def be(c): return (1.3+c)/4.3

print("="*88);print("CUSTO DE TRANSACAO — quanto edge sobra");print("="*88)
print(f"{'custo':>12} {'custo(USD)':>11} {'p breakeven':>12}   P1(0.3132)   P2(0.3110)   TODAS(0.3082)")
for c in [0.0,0.02,0.05,0.10,0.15]:
    b=be(c)
    print(f"{c:>10.2f}R {c*3.27:>10.2f} {b:>12.4f}   {expR(.3132,c):+.4f}      {expR(.3110,c):+.4f}      {expR(.3082,c):+.4f}")
print("\n=> spread real tipico XAUUSD ~0.15-0.35 USD = 0.05-0.11 R")

print("\n"+"="*88);print("TESTE FINAL OUT-OF-SAMPLE (modelo treinado ate 70% das barras)");print("="*88)
tr=E[E.idx<=E.loc[E.split=='VAL','idx'].max()-0]  # TRAIN+VAL
tr=E[E.split.isin(["TRAIN","VAL"])]; te=E[E.split=="TEST"]
tr_fit=tr[tr.idx<=te.idx.min()-100]
m=CatBoostClassifier(iterations=400,depth=4,learning_rate=.03,l2_leaf_reg=10,random_seed=7,verbose=0,allow_writing_files=False)
m.fit(tr_fit[FE].replace([np.inf,-np.inf],np.nan),tr_fit.success.astype(int))
pv=m.predict_proba(E.loc[E.split=="VAL",FE].replace([np.inf,-np.inf],np.nan))[:,1]
pt=m.predict_proba(te[FE].replace([np.inf,-np.inf],np.nan))[:,1]
yt=te.success.astype(int).values
print(f"TEST: n={len(te)} base={yt.mean():.4f} AUC={roc_auc_score(yt,pt):.4f} "
      f"PR-AUC={average_precision_score(yt,pt):.4f} Brier={brier_score_loss(yt,pt):.4f} (const={np.mean((yt-yt.mean())**2):.4f})")
thr=np.quantile(pv,0.80)   # threshold escolhido SO na VAL
sel=pt>=thr
k,N=int(yt[sel].sum()),int(sel.sum())
print(f"threshold (p80 da VAL)={thr:.4f} -> TEST selecionados n={N} sucesso={k/N:.4f} "
      f"(nao-selecionados {yt[~sel].mean():.4f})")
print(f"   binom_p(>breakeven s/ custo)={stats.binomtest(k,N,BE,alternative='greater').pvalue:.4f}")
print(f"   binom_p(>breakeven c/ 0.05R)={stats.binomtest(k,N,be(.05),alternative='greater').pvalue:.4f}")

print("\n--- bootstrap em blocos (respeita dependencia entre eventos vizinhos) ---")
def bboot(y,B=4000,bs=50):
    N=len(y); nb=int(np.ceil(N/bs)); rng=np.random.default_rng(1); out=[]
    for _ in range(B):
        st=rng.integers(0,max(N-bs,1),nb)
        s=np.concatenate([y[i:i+bs] for i in st])[:N]; out.append(s.mean())
    return np.array(out)
for nm,y in [("TEST todos",yt),("TEST selecionados",yt[sel])]:
    b=bboot(y); print(f"  {nm:20s} p={y.mean():.4f} IC95_bloco=[{np.percentile(b,2.5):.4f},{np.percentile(b,97.5):.4f}] "
                      f"P(p>BE)={np.mean(b>BE):.3f}  P(p>BE+0.05R)={np.mean(b>be(.05)):.3f}")

print("\n"+"="*88);print("REGRAS SIMPLES (Opcao A) — melhor combinacao encontrada no TRAIN, testada OOS");print("="*88)
cands={
 "P2 & saldo agressao a favor (aggdn0>0)": lambda d:(d.pattern=="P2")&(d.aggdn0>0),
 "P2 & barra rapida (dur_rel0<1)":        lambda d:(d.pattern=="P2")&(d.dur_rel0<1),
 "P2 & agressao baixa (aggt_rel0<0.8)":   lambda d:(d.pattern=="P2")&(d.aggt_rel0<0.8),
 "P1 & regime volatil (dur_rel50<1)":     lambda d:(d.pattern=="P1")&(d.dur_rel50<1),
 "P1|P2 & run_prev==4":                   lambda d:(d.run_prev==4),
 "P2 & aggdn0>0 & dur_rel0<1":            lambda d:(d.pattern=="P2")&(d.aggdn0>0)&(d.dur_rel0<1),
}
rows=[]
for nm,f in cands.items():
    r={"regra":nm}
    for sp in ["TRAIN","VAL","TEST"]:
        s=E[(E.split==sp)&f(E)]
        r[f"{sp}_n"]=len(s); r[f"{sp}_p"]=round(s.success.mean(),4) if len(s) else np.nan
    rows.append(r)
R=pd.DataFrame(rows); print(R.to_string(index=False))
print(f"\nreferencia: breakeven s/custo={BE:.4f}  c/ 0.05R={be(.05):.4f}")
