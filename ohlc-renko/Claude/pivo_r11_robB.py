#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robustez completa da regra do arquivo B (com janela de pregao)."""
import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
import pivo_r11_core as C

ALVO, STOP = 150.0, 100.0
BE = STOP/(ALVO+STOP)
df = C.carregar(); b = C.base(df,1); n = len(df)
dias = np.sort(df.dt.dt.date.unique()); corte = dias[int(len(dias)*0.70)]
data = df.dt.dt.date.values
h,l,c = df.h.values, df.l.values, df.c.values
dirn = df.dirn.values
hhmm = (df.dt.dt.hour*100 + df.dt.dt.minute).values
yB,nB,yA,nA = C.resultados(df, ALVO, STOP)
dayid = pd.factorize(data)[0]
dhi=np.empty(n); dlo=np.empty(n); hi=lo=np.nan
for k in range(n):
    if k==0 or dayid[k]!=dayid[k-1]: hi,lo = h[k],l[k]
    else: hi,lo = max(hi,h[k]), min(lo,l[k])
    dhi[k],dlo[k]=hi,lo
fx = np.maximum(dhi-dlo, C.BODY); mi = (dhi+dlo)/2.0

P = dict(C.PADRAO, Esquerda=6, Direita=1, TolerPivoFrac=0.0)
K = C.componentes(df,b,P)
jb = np.where(K["pb"])[0]; jb=jb[jb+1<n]; ja = np.where(K["pa"])[0]; ja=ja[ja+1<n]
la = np.r_[np.ones(len(jb),int), -np.ones(len(ja),int)]; jj = np.r_[jb,ja]
s = np.argsort(jj,kind="stable"); la,jj = la[s],jj[s]; ii = jj+1
y = np.where(la==1, yB[ii], yA[ii]); bars = np.where(la==1, nB[ii], nA[ii])
po = la*(c[jj]-mi[jj])/fx[jj]; tk = dirn[jj]==la
hh = hhmm[ii]

cand = tk & (((la==1)&(po>=0.25))|((la==-1)&(po>=0.35))) & ~((hh>=1000)&(hh<1200))
sel = np.zeros(len(jj),bool); uC=uV=-10**9
for k in np.where(cand)[0]:
    if la[k]==1:
        if ii[k]-uC>=5: sel[k]=True; uC=ii[k]
    else:
        if ii[k]-uV>=5: sel[k]=True; uV=ii[k]
sel &= ~np.isnan(y)
dia = data[ii]
print("REGRA B: Esq=6 Dir=1 | tipo_ok | compra>=0.25 venda>=0.35 | fora 10h-12h | MinBarras=5")
print("  tr n=%d %.4f | te n=%d %.4f | tudo n=%d %.4f  %+.1f pts"
      %((sel&(dia<corte)).sum(), y[sel&(dia<corte)].mean(),
        (sel&(dia>=corte)).sum(), y[sel&(dia>=corte)].mean(),
        sel.sum(), y[sel].mean(), y[sel].mean()*ALVO-(1-y[sel].mean())*STOP))
print("  compra %.4f (n=%d) | venda %.4f (n=%d) | %.2f/pregao | mediana %.0f bricks | pregoes sem sinal %d"
      %(y[sel&(la==1)].mean(),(sel&(la==1)).sum(),y[sel&(la==-1)].mean(),(sel&(la==-1)).sum(),
        sel.sum()/len(dias), np.nanmedian(bars[sel]), len(dias)-len(np.unique(dia[sel]))))
rng = np.random.default_rng(7); ds = np.unique(dia[sel])
pd_={k_:y[sel][dia[sel]==k_] for k_ in ds}
boot=np.array([np.concatenate([pd_[k_] for k_ in rng.choice(ds,len(ds),True)]).mean() for _ in range(4000)])
print("  bootstrap por pregao: %.4f IC95%% [%.4f ; %.4f]  P(<=BE)=%.4f"
      %(boot.mean(),np.percentile(boot,2.5),np.percentile(boot,97.5),(boot<=BE).mean()))
val=~np.isnan(y); obs=y[sel].mean(); cnt=0
for _ in range(4000):
    sim=[]
    for k_ in ds:
        pool=y[val&(dia==k_)]; ns=(sel&(dia==k_)).sum()
        if len(pool) and ns: sim.append(rng.choice(pool,ns,replace=ns>len(pool)))
    if np.concatenate(sim).mean()>=obs: cnt+=1
print("  aleatorizacao dentro do pregao: p=%.4f"%(cnt/4000))
print("  walk-forward:")
for bi,bl in enumerate(np.array_split(ds,5)):
    m=sel&np.isin(dia,bl); p=y[m].mean()
    print("    bloco %d (%s a %s) n=%3d %.4f %+6.1f"%(bi+1,bl[0],bl[-1],m.sum(),p,p*ALVO-(1-p)*STOP))
pnl=np.where(y[sel][np.argsort(ii[sel])]>0,ALVO,-STOP)
print("  custo  total   pts/trade  maxDD   PF")
for cu in [0,5,10,15,20,25]:
    eq=np.cumsum(pnl-cu); dd=(eq-np.maximum.accumulate(eq)).min()
    po_,ne=(pnl-cu)[pnl-cu>0],(pnl-cu)[pnl-cu<0]
    print("  %2d pts %+7.0f  %+7.1f  %6.0f  %.2f"%(cu,eq[-1],eq[-1]/len(pnl),dd,po_.sum()/abs(ne.sum())))
print("\n  sensibilidade da janela evitada (plateau ou pico?):")
for a,z in [(930,1130),(1000,1130),(1000,1200),(1000,1230),(1030,1200),(930,1200)]:
    cd = tk & (((la==1)&(po>=0.25))|((la==-1)&(po>=0.35))) & ~((hh>=a)&(hh<z))
    s2=np.zeros(len(jj),bool); uC=uV=-10**9
    for k in np.where(cd)[0]:
        if la[k]==1:
            if ii[k]-uC>=5: s2[k]=True; uC=ii[k]
        else:
            if ii[k]-uV>=5: s2[k]=True; uV=ii[k]
    s2&=~np.isnan(y)
    print("    evitar %d-%d: n=%3d tr %.4f te %.4f tudo %.4f"
          %(a,z,s2.sum(),y[s2&(dia<corte)].mean(),y[s2&(dia>=corte)].mean(),y[s2].mean()))
