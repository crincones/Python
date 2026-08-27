import pandas as pd, numpy as np
from scipy import stats
from lib import load
np.random.seed(7)
df=load()
ev=pd.read_parquet("out/events_raw.parquet")
base=pd.read_parquet("out/baseline_all.parquet")
ev=ev[ev.success>=0].copy(); base=base[base.success>=0].copy()
BE=1.3/4.3
print(f"Breakeven teorico (3R vs 1.3R) = {BE:.4f}\n")

def exp_R(p): return p*3.0-(1-p)*1.3
def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); m=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return ((c-m)/d,(c+m)/d)

print("="*78); print("1) OCORRENCIAS, TAXA DE SUCESSO, EXPECTATIVA"); print("="*78)
rows=[]
for name,g in [("BASELINE(todas)",base)]+[(p,x) for p,x in ev.groupby("pattern")]:
    k=int(g.success.sum()); n=len(g); p=k/n; lo,hi=wilson(k,n)
    rows.append(dict(grupo=name,n=n,sucesso=round(p,4),ic95=f"[{lo:.4f},{hi:.4f}]",
                     exp_R=round(exp_R(p),4),vs_BE=round(p-BE,4)))
print(pd.DataFrame(rows).to_string(index=False))

print("\n--- teste vs baseline (todas as barras) ---")
kb,nb=int(base.success.sum()),len(base)
for p,g in ev.groupby("pattern"):
    k,n=int(g.success.sum()),len(g)
    tab=[[k,n-k],[kb-k if False else kb,nb-kb]]
    chi,pv=stats.fisher_exact([[k,n-k],[kb,nb-kb]])[0],stats.fisher_exact([[k,n-k],[kb,nb-kb]])[1]
    # binomial contra taxa base
    pv2=stats.binomtest(k,n,kb/nb,alternative="greater").pvalue
    pv3=stats.binomtest(k,n,BE,alternative="greater").pvalue
    print(f"{p}: n={n} p={k/n:.4f} | vs baseline({kb/nb:.4f}) OR={chi:.3f} fisher_p={pv:.4f} binom_p(greater)={pv2:.4f} | vs breakeven binom_p={pv3:.4f}")

print("\n--- fade: operar na direcao CONTRARIA a reversao ---")
from lib import label_paths
for p,g in ev.groupby("pattern"):
    ii=g.idx.to_numpy(); L=label_paths(df,ii,-g.side.to_numpy(),g.R.to_numpy())
    f=pd.DataFrame(L); f=f[f.success>=0]
    print(f"{p} FADE: n={len(f)} sucesso={f.success.mean():.4f} exp={exp_R(f.success.mean()):.4f}")

print("\n"+"="*78); print("2) DISTRIBUICAO MAE / MFE"); print("="*78)
for p,g in ev.groupby("pattern"):
    print(f"\n[{p}] MFE (R):"); print(g.mfe.describe(percentiles=[.1,.25,.5,.75,.9,.95]).round(3).to_string())
    print(f"[{p}] MAE (R):"); print(g.mae.describe(percentiles=[.1,.25,.5,.75,.9,.95]).round(3).to_string())
    print(f"[{p}] barras ate saida: mediana={g.bars_to_exit.median():.0f} p90={g.bars_to_exit.quantile(.9):.0f} max={g.bars_to_exit.max():.0f}")
    w=g[g.success==1]
    print(f"[{p}] VENCEDORES: barras ate 3R med={w.bars_to_exit.median():.0f} p90={w.bars_to_exit.quantile(.9):.0f} | tempo med={w.secs_to_exit.median()/60:.1f}min p90={w.secs_to_exit.quantile(.9)/60:.1f}min")
    print(f"[{p}] VENCEDORES MAE med={w.mae.median():.2f}R p90={w.mae.quantile(.9):.2f}R")
    l=g[g.success==0]
    print(f"[{p}] PERDEDORES: barras med={l.bars_to_exit.median():.0f} | MFE med={l.mfe.median():.2f}R p90={l.mfe.quantile(.9):.2f}R")

print("\n"+"="*78); print("3) CONTROLE DE DEPENDENCIA / SOBREPOSICAO"); print("="*78)
for p,g in ev.groupby("pattern"):
    g=g.sort_values("idx"); ii=g.idx.to_numpy(); ex=ii+g.bars_to_exit.fillna(1500).to_numpy()
    keep=[]; last=-1
    for i in range(len(ii)):
        if ii[i]>last: keep.append(i); last=ex[i]
    ng=g.iloc[keep]
    print(f"{p}: eventos={len(g)} nao-sobrepostos={len(ng)} ({len(ng)/len(g):.1%}) sucesso_nao_sobreposto={ng.success.mean():.4f} exp={exp_R(ng.success.mean()):.4f}")
    med_gap=np.median(np.diff(ii)); print(f"   gap mediano entre sinais={med_gap:.0f} barras; duracao mediana do trade={g.bars_to_exit.median():.0f} barras -> sobreposicao alta" if med_gap<g.bars_to_exit.median() else "")
