import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
from scipy import stats
from lib import load,label_paths
np.random.seed(7)
df=load(); n=len(df); C=df.CLOSE.to_numpy(); D=df.DIR.to_numpy(); R=df.RANGE.to_numpy(); BR=df.BODYRATIO.to_numpy()
t=np.arange(2,n); same=(D[t-2]==D[t-1]); opp=(D[t]==-D[t-1])
p1=same&opp&(BR[t]<=0.50); p2=same&opp&(BR[t-1]>=0.70)&(BR[t]>=0.70)
i1,i2=t[p1],t[p2]

print("="*92);print("1) VIES DIRECIONAL BRUTO — retorno futuro medio (em R), alinhado ao lado da reversao");print("="*92)
print("Se o padrao carrega informacao, o retorno medio deve ser > que o das barras em geral.\n")
rows=[]
for k in [1,2,3,5,10,20,50]:
    j=np.minimum(t+k,n-1); fwd_all=(C[j]-C[t])/R[t]*D[t]
    r={"k_barras":k,"TODAS":round(fwd_all.mean(),4)}
    for nm,ii in [("P1",i1),("P2",i2)]:
        jj=np.minimum(ii+k,n-1); f=(C[jj]-C[ii])/R[ii]*D[ii]
        tt=stats.ttest_ind(f,fwd_all,equal_var=False)
        r[nm]=round(f.mean(),4); r[nm+"_p"]=round(tt.pvalue,3)
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

print("\n"+"="*92);print("2) GRID DE GEOMETRIA alvo/stop — sucesso do padrao MENOS sucesso do baseline (pp)");print("="*92)
allidx=np.arange(2,n-1)
for tgt in [1.0,1.5,2.0,3.0,4.0]:
    line=[]
    for stp in [0.5,0.8,1.0,1.3,2.0]:
        b=pd.DataFrame(label_paths(df,allidx,D[allidx],R[allidx],target_mult=tgt,stop_mult=stp))
        b=b[b.success>=0]; pb=b.success.mean()
        cell=[]
        for nm,ii in [("P1",i1),("P2",i2)]:
            e=pd.DataFrame(label_paths(df,ii,D[ii],R[ii],target_mult=tgt,stop_mult=stp))
            e=e[e.success>=0]; cell.append(f"{(e.success.mean()-pb)*100:+.2f}")
        line.append(f"stop{stp}: base={pb:.3f} P1={cell[0]} P2={cell[1]}")
    print(f"alvo {tgt}R | "+" | ".join(line))
