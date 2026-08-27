import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from scipy import stats
from lib import load
E = pd.read_parquet("out/events_ctx.parquet")
BE = 1.3/4.3; BEC = (1.3+.05)/4.3; expR = lambda p: p*3-(1-p)*1.3
print(f"breakeven={BE:.4f}   com custo 0,05R={BEC:.4f}")

print("\n"+"="*100)
print("1) PROXIMIDADE DO NIVEL — varredura de limiar nos tres periodos")
print("="*100)
rows=[]
for thr in [0.25,0.5,0.75,1.0,1.5,2.0]:
    row={"dist<=": thr}
    for sp in ("TRAIN","VAL","TEST"):
        t = E[(E.split==sp) & E.ext_dist_R.notna()]
        a = t[t.ext_dist_R<=thr]
        row[f"{sp[:2]}_n"]=len(a)
        row[f"{sp[:2]}_p"]=round(a.success.mean(),4) if len(a)>=60 else np.nan
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))

print("\n"+"="*100)
print("2) QUAL PADRAO TEM MAIS SUCESSO — resposta final, por periodo")
print("="*100)
g = E.groupby(["pattern","split"]).success.agg(["count","mean"]).unstack(1)
print(g.round(4).to_string())
print("\ncom o contexto mais favoravel (nivel tocado, dist<=0,5R):")
t = E[E.ext_dist_R<=0.5]
print(t.groupby(["pattern","split"]).success.agg(["count","mean"]).unstack(1).round(4).to_string())
print("\nteste P1 vs P2 na amostra completa:")
a = E[E.pattern=="P1"]; b = E[E.pattern=="P2"]
odds, pv = stats.fisher_exact([[int(a.success.sum()), len(a)-int(a.success.sum())],
                               [int(b.success.sum()), len(b)-int(b.success.sum())]])
print(f"  P1={a.success.mean():.4f} (n={len(a)})  P2={b.success.mean():.4f} (n={len(b)})"
      f"  OR={odds:.3f}  fisher_p={pv:.4f}")

print("\n"+"="*100)
print("3) TESTE DE TIRO UNICO — melhor regra escolhida em TRAIN+VAL, avaliada uma vez no TEST")
print("="*100)
dev = E[E.split.isin(["TRAIN","VAL"])]; te = E[E.split=="TEST"]
cands = {
 "nivel tocado (<=0,5R)":            lambda t: t.ext_dist_R<=0.5,
 "nivel tocado & extremo de sessao": lambda t: (t.ext_dist_R<=0.5)&(t.sess_pos_aligned<=0.25),
 "nivel tocado & P1":                lambda t: (t.ext_dist_R<=0.5)&(t.pattern=="P1"),
 "nivel tocado & room>=3R":          lambda t: (t.ext_dist_R<=0.5)&(t.ext_room_R>=3),
 "extremo de sessao a favor":        lambda t: t.sess_pos_aligned<=0.25,
 "perfurou nivel & extremo sessao":  lambda t: (t.ext_pierce==1)&(t.sess_pos_aligned<=0.25),
}
best, bestp = None, -1
for nm,f in cands.items():
    a = dev[f(dev)]
    if len(a) < 200: continue
    print(f"  {nm:36s} DEV n={len(a):5d} p={a.success.mean():.4f}")
    if a.success.mean() > bestp: best, bestp = nm, a.success.mean()
print(f"\n  regra escolhida em DEV: '{best}' (p={bestp:.4f})")
a = te[cands[best](te)]
k, N = int(a.success.sum()), len(a)
print(f"  >>> TESTE: n={N} acerto={k/N:.4f} exp={expR(k/N):+.4f}")
print(f"      binom p(>breakeven)={stats.binomtest(k,N,BE,alternative='greater').pvalue:.4f}")
print(f"      binom p(>breakeven c/ custo)={stats.binomtest(k,N,BEC,alternative='greater').pvalue:.4f}")
def bboot(y,B=4000,bs=40):
    N=len(y); nb=int(np.ceil(N/bs)); rng=np.random.default_rng(1); o=[]
    for _ in range(B):
        st=rng.integers(0,max(N-bs,1),nb)
        o.append(np.concatenate([y[i:i+bs] for i in st])[:N].mean())
    return np.array(o)
b = bboot(a.success.values)
print(f"      IC95 em blocos=[{np.percentile(b,2.5):.4f},{np.percentile(b,97.5):.4f}] "
      f"P(>BE)={np.mean(b>BE):.3f}  P(>BE c/custo)={np.mean(b>BEC):.3f}")

print("\n"+"="*100)
print("4) CONTROLE DE MULTIPLOS TESTES")
print("="*100)
print("Hipoteses avaliadas nesta rodada de contexto:")
print("  27 features de contexto x 3 grupos (univariada)      = 81")
print("  12 cortes de contexto x 2 direcoes                   = 24")
print("   6 limiares de proximidade x 3 periodos              = 18")
print("   8 regras combinadas x 3 periodos                    = 24")
print("   3 conjuntos de features x 3 grupos (ML walk-forward)=  9")
print("  ------------------------------------------------------------")
print("  total ~156 hipoteses. Ao nivel de 5%, ~8 falsos positivos sao esperados por acaso.")
print("  Nenhuma feature de contexto sobreviveu a correcao BH em nenhum grupo (0 de 27 x 3).")
