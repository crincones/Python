import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from catboost import CatBoostClassifier
from lib import load
np.random.seed(7)
df = load(); n = len(df); TR, VA = int(n*.50), int(n*.70)
E = pd.read_parquet("out/events_ctx.parquet").sort_values("idx").reset_index(drop=True)
FT = pd.read_parquet("out/features.parquet"); CX = pd.read_parquet("out/context.parquet")
BASE = [c for c in FT.columns if c != "idx"]
CTX  = [c for c in CX.columns if c != "idx"]
print(f"features base={len(BASE)}  contexto={len(CTX)}  total={len(BASE)+len(CTX)}")

def wf(d, feats, label, nfolds=5):
    d = d.sort_values("idx").reset_index(drop=True); N = len(d)
    bd = [int(N*(0.4+0.6*i/nfolds)) for i in range(nfolds+1)]
    oof = np.full(N, np.nan)
    for k in range(nfolds):
        a, b = bd[k], bd[k+1]
        tr = d[d.idx <= d.idx.iloc[a-1]-100]; te = d.iloc[a:b]
        if len(tr) < 500: continue
        m = CatBoostClassifier(iterations=400, depth=4, learning_rate=.03, l2_leaf_reg=10,
                               random_seed=7, verbose=0, allow_writing_files=False)
        m.fit(tr[feats].replace([np.inf,-np.inf],np.nan), tr.success.astype(int))
        oof[a:b] = m.predict_proba(te[feats].replace([np.inf,-np.inf],np.nan))[:,1]
    ok = ~np.isnan(oof); y = d.success.astype(int).values[ok]; p = oof[ok]
    print(f"  {label:34s} n={ok.sum():6d} AUC={roc_auc_score(y,p):.4f} "
          f"PR={average_precision_score(y,p):.4f} Brier={brier_score_loss(y,p):.4f} "
          f"(const={np.mean((y-y.mean())**2):.4f})")
    return oof

print("\nWALK-FORWARD com contexto S/R + VWAP")
for lbl, d in [("P1+P2", E), ("P1", E[E.pattern=="P1"]), ("P2", E[E.pattern=="P2"])]:
    print(f"\n[{lbl}]")
    wf(d, BASE, "base (57 features)")
    wf(d, CTX,  "so contexto (S/R + VWAP)")
    wf(d, BASE+CTX, "base + contexto")

print("\n" + "="*92)
print("TESTE FINAL: treino ate 70% das barras, avaliado no periodo reservado")
print("="*92)
tr = E[E.split.isin(["TRAIN","VAL"])]; te = E[E.split=="TEST"]
tr = tr[tr.idx <= te.idx.min()-100]
for nm, feats in [("base", BASE), ("contexto", CTX), ("base+contexto", BASE+CTX)]:
    m = CatBoostClassifier(iterations=400, depth=4, learning_rate=.03, l2_leaf_reg=10,
                           random_seed=7, verbose=0, allow_writing_files=False)
    m.fit(tr[feats].replace([np.inf,-np.inf],np.nan), tr.success.astype(int))
    p = m.predict_proba(te[feats].replace([np.inf,-np.inf],np.nan))[:,1]
    y = te.success.astype(int).values
    print(f"  {nm:16s} AUC={roc_auc_score(y,p):.4f}  PR={average_precision_score(y,p):.4f}  "
          f"Brier={brier_score_loss(y,p):.4f} (const={np.mean((y-y.mean())**2):.4f})")
    if nm == "base+contexto":
        imp = pd.Series(m.get_feature_importance(), index=feats).sort_values(ascending=False)
        print("\n  top 12 features (modelo final):")
        for k, v in imp.head(12).items():
            print(f"    {k:22s} {v:6.2f}  {'[contexto]' if k in CTX else ''}")
