import pandas as pd, numpy as np

CSV="OHLC/XAUUSD_327_N_M1_202511041815_202608212148.csv"

def load():
    df=pd.read_csv(CSV,sep="\t")
    df.columns=[c.strip("<>").upper() for c in df.columns]
    df["DT"]=pd.to_datetime(df["DATE"]+" "+df["TIME"],format="%Y.%m.%d %H:%M:%S")
    df=df.sort_values("DT").reset_index(drop=True)
    df["RANGE"]=df.HIGH-df.LOW
    df["DIR"]=np.sign(df.CLOSE-df.OPEN).astype(int)
    df["BODY"]=(df.CLOSE-df.OPEN).abs()
    df["BODYRATIO"]=df.BODY/df.RANGE.replace(0,np.nan)
    # wick oposto ao fechamento
    df["WICK"]=np.where(df.DIR>0, df.OPEN-df.LOW, df.HIGH-df.OPEN)
    df["WICKR"]=df.WICK/df.RANGE.replace(0,np.nan)
    # posicao do OPEN dentro do range
    df["OPENPOS"]=(df.OPEN-df.LOW)/df.RANGE.replace(0,np.nan)
    df["DUR"]=df.SPREAD/1000.0          # segundos
    df["BUY"]=df.TICKVOL.astype(float)
    df["SELL"]=df.VOL.astype(float)
    df["AGGT"]=df.BUY+df.SELL
    df["AGGD"]=df.BUY-df.SELL
    df["AGGDN"]=df.AGGD/df.AGGT.replace(0,np.nan)      # saldo normalizado [-1,1]
    df["AGGRATIO"]=np.log((df.BUY+1)/(df.SELL+1))
    return df

def label_paths(df, idx, direction, R, W=1500, target_mult=3.0, stop_mult=1.3):
    """Simula caminho apos o fechamento da barra idx.
    direction: +1 long (reversao de alta), -1 short.
    Regra conservadora: se alvo e stop cabem na mesma barra -> conta STOP.
    Retorna dict de arrays."""
    H=df.HIGH.to_numpy(); L=df.LOW.to_numpy(); C=df.CLOSE.to_numpy()
    T=df.DT.to_numpy(); DUR=df.DUR.to_numpy()
    n=len(df); m=len(idx)
    succ=np.full(m,-1,np.int8); bars=np.full(m,np.nan); secs=np.full(m,np.nan)
    mfe=np.full(m,np.nan); mae=np.full(m,np.nan); amb=np.zeros(m,bool)
    for k in range(m):
        t=idx[k]; d=direction[k]; r=R[k]; c=C[t]
        tgt=c+d*target_mult*r; stp=c-d*stop_mult*r
        a=t+1; b=min(n,t+1+W)
        if a>=b: continue
        hi=H[a:b]; lo=L[a:b]
        if d>0:
            hit_t=hi>=tgt; hit_s=lo<=stp
            fav=(hi-c)/r; adv=(c-lo)/r
        else:
            hit_t=lo<=tgt; hit_s=hi>=stp
            fav=(c-lo)/r; adv=(hi-c)/r
        it=hit_t.argmax() if hit_t.any() else -1
        isx=hit_s.argmax() if hit_s.any() else -1
        if it<0 and isx<0:
            continue                      # nao resolvido na janela
        if it<0: j=isx; s=0
        elif isx<0: j=it; s=1
        elif isx<it: j=isx; s=0
        elif it<isx: j=it; s=1
        else: j=it; s=0; amb[k]=True       # mesma barra -> conservador
        succ[k]=s; bars[k]=j+1
        secs[k]=DUR[a:a+j+1].sum()
        mfe[k]=fav[:j+1].max(); mae[k]=adv[:j+1].max()
    return dict(success=succ,bars_to_exit=bars,secs_to_exit=secs,mfe=mfe,mae=mae,ambiguous=amb)
