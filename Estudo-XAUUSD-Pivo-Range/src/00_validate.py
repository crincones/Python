import pandas as pd, numpy as np
CSV="OHLC/XAUUSD_327_N_M1_202511041815_202608212148.csv"
df=pd.read_csv(CSV,sep="\t")
df.columns=[c.strip("<>").upper() for c in df.columns]
df["DT"]=pd.to_datetime(df["DATE"]+" "+df["TIME"],format="%Y.%m.%d %H:%M:%S")
df=df.sort_values("DT").reset_index(drop=True)
print("rows",len(df),"period",df.DT.min(),"->",df.DT.max())
print(df.dtypes)
print("\nduplicated DT:",df.DT.duplicated().sum())
print("monotonic:",df.DT.is_monotonic_increasing)

df["RANGE"]=df.HIGH-df.LOW
print("\n--- RANGE distribution ---")
print(df.RANGE.describe(percentiles=[.001,.01,.05,.25,.5,.75,.95,.99,.999]))
r=df.RANGE.round(2)
print("\ntop 10 range values:")
print(r.value_counts().head(10))
mode=r.mode()[0]
print("\nmode range:",mode,"share within +-0.01:",((df.RANGE-mode).abs()<=0.011).mean())
print("share < mode-0.02 (incompletas):",(df.RANGE<mode-0.02).mean())
print("share > mode+0.02 (gaps/extras):",(df.RANGE>mode+0.02).mean())

print("\n--- direcao / fechamento na extremidade ---")
up=df.CLOSE>df.OPEN; dn=df.CLOSE<df.OPEN; dj=df.CLOSE==df.OPEN
print("up",up.sum(),"dn",dn.sum(),"doji",dj.sum())
print("up com CLOSE==HIGH:",(df.loc[up,"CLOSE"]==df.loc[up,"HIGH"]).mean())
print("dn com CLOSE==LOW :",(df.loc[dn,"CLOSE"]==df.loc[dn,"LOW"]).mean())
print("up: wick superior >0:",((df.loc[up,"HIGH"]-df.loc[up,"CLOSE"])>0).mean())
print("dn: wick inferior >0:",((df.loc[dn,"CLOSE"]-df.loc[dn,"LOW"])>0).mean())
print("OPEN==HIGH ou OPEN==LOW share:",((df.OPEN==df.HIGH)|(df.OPEN==df.LOW)).mean())

print("\n--- continuidade OPEN[t] vs CLOSE[t-1] ---")
gap=(df.OPEN-df.CLOSE.shift(1)).abs()
print(gap.describe(percentiles=[.5,.9,.99,.999]))
print("gap==0 share:",(gap==0).mean())

print("\n--- SPREAD (ms) ---")
print(df.SPREAD.describe(percentiles=[.01,.25,.5,.75,.99]))
print("SPREAD<=0:",(df.SPREAD<=0).sum())
print("\n--- TICKVOL / VOL ---")
print(df[["TICKVOL","VOL"]].describe())
print("TICKVOL==0:",(df.TICKVOL==0).sum(),"VOL==0:",(df.VOL==0).sum())
print("corr tickvol/vol:",df.TICKVOL.corr(df.VOL))

print("\n--- gaps temporais (fim de semana etc) ---")
dt=df.DT.diff().dt.total_seconds()
print(dt.describe(percentiles=[.5,.9,.99,.999]))
print("gaps > 1h:",(dt>3600).sum())
print("\n--- SPREAD vs delta tempo real ---")
cmp=pd.DataFrame({"spread_ms":df.SPREAD,"dtsec_next":df.DT.shift(-1)-df.DT})
print((df.SPREAD/1000.0).describe(percentiles=[.5,.9,.99]))
