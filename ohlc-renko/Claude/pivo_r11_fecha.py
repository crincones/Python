#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 6: fechamento.
  a) limiares assimetricos por lado (o vendedor precisa de mais contexto)
  b) sobreposicao REAL com a regra RenkoViradaR11 (tolerando defasagem)
  c) numeros finais da regra que vai para o NTSL + grafico + csv
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pivo_r11_core as C

ALVO, STOP = 150.0, 100.0
BE = STOP / (ALVO + STOP)
ESQ, DIR, MB = 6, 1, 5

df = C.carregar()
b = C.base(df, normalizar=1)
n = len(df)
dias = np.sort(df.dt.dt.date.unique())
corte = dias[int(len(dias) * 0.70)]
data = df.dt.dt.date.values
yB, nBr, yA, nAr = C.resultados(df, ALVO, STOP)

h, l, c = df.h.values, df.l.values, df.c.values
dirn, is_rev, seqb = df.dirn.values, df.is_rev.values, df.seq_before.values
dayid = pd.factorize(data)[0]
dhi = np.empty(n); dlo = np.empty(n)
hi = lo = np.nan
for k in range(n):
    if k == 0 or dayid[k] != dayid[k - 1]:
        hi, lo = h[k], l[k]
    else:
        hi, lo = max(hi, h[k]), min(lo, l[k])
    dhi[k], dlo[k] = hi, lo
faixa = np.maximum(dhi - dlo, C.BODY)
meio = (dhi + dlo) / 2.0
hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values

P = dict(C.PADRAO, Esquerda=ESQ, Direita=DIR, TolerPivoFrac=0.0)
K = C.componentes(df, b, P)
jb = np.where(K["pb"])[0]; jb = jb[jb + DIR < n]
ja = np.where(K["pa"])[0]; ja = ja[ja + DIR < n]
lado = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
j = np.r_[jb, ja]
s = np.argsort(j, kind="stable"); lado, j = lado[s], j[s]
i = j + DIR
y = np.where(lado == 1, yB[i], yA[i])
bars = np.where(lado == 1, nBr[i], nAr[i])
dia = data[i]
val = ~np.isnan(y)
pos = lado * (c[j] - meio[j]) / faixa[j]
tipo = dirn[j] == lado


def av(sel, nome=None):
    m = sel & val
    yy, dd = y[m], dia[m]
    f = lambda x: (len(x), x.mean() if len(x) else np.nan)
    nt, pt = f(yy[dd < corte]); nv, pv = f(yy[dd >= corte]); na, pa = f(yy)
    if nome:
        print("  %-44s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f"
              % (nome, nt, pt, nv, pv, na, pa, pa * ALVO - (1 - pa) * STOP))
    return na, pa, pt, pv


def espaca(sel, minb):
    out = np.zeros(len(sel), bool)
    uC = uV = -10 ** 9
    for k in np.where(sel)[0]:
        if lado[k] == 1:
            if i[k] - uC >= minb:
                out[k] = True; uC = i[k]
        else:
            if i[k] - uV >= minb:
                out[k] = True; uV = i[k]
    return out


print("=" * 116)
print("a) LIMIARES ASSIMETRICOS  (Esq=%d Dir=%d MinBarras=%d)" % (ESQ, DIR, MB))
print("=" * 116)
for tc in [0.20, 0.25, 0.30]:
    for tv in [0.25, 0.30, 0.35, 0.40]:
        sel = espaca(tipo & (((lado == 1) & (pos >= tc)) |
                             ((lado == -1) & (pos >= tv))), MB)
        na, pa, pt, pv = av(sel)
        print("  compra>=%.2f venda>=%.2f  n=%4d (%4.1f/preg) tr %.4f te %.4f tudo %.4f %+6.1f"
              % (tc, tv, na, na / len(dias), pt, pv, pa, pa * ALVO - (1 - pa) * STOP))

TC, TV = 0.25, 0.35
sel = espaca(tipo & (((lado == 1) & (pos >= TC)) |
                     ((lado == -1) & (pos >= TV))), MB) & val
print("\n  ESCOLHIDO: compra >= %.2f | venda >= %.2f" % (TC, TV))
av(sel, "REGRA FINAL")
print("  compra %.4f (n=%d, tr %.4f te %.4f)"
      % (y[sel & (lado == 1)].mean(), (sel & (lado == 1)).sum(),
         y[sel & (lado == 1) & (dia < corte)].mean(),
         y[sel & (lado == 1) & (dia >= corte)].mean()))
print("  venda  %.4f (n=%d, tr %.4f te %.4f)"
      % (y[sel & (lado == -1)].mean(), (sel & (lado == -1)).sum(),
         y[sel & (lado == -1) & (dia < corte)].mean(),
         y[sel & (lado == -1) & (dia >= corte)].mean()))
print("  %.2f sinais/pregao | mediana %.0f bricks | pregoes sem sinal %d de %d"
      % (sel.sum() / len(dias), np.nanmedian(bars[sel]),
         len(dias) - len(np.unique(dia[sel])), len(dias)))

rng = np.random.default_rng(66)
ds = np.unique(dia[sel])
pdic = {k_: y[sel][dia[sel] == k_] for k_ in ds}
boot = np.array([np.concatenate([pdic[k_] for k_ in rng.choice(ds, len(ds), True)]).mean()
                 for _ in range(4000)])
print("\n  bootstrap por pregao: %.4f  IC95%% [%.4f ; %.4f]  P(<=BE)=%.4f"
      % (boot.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5),
         (boot <= BE).mean()))
obs = y[sel].mean(); cnt = 0
for _ in range(4000):
    sim = []
    for k_ in ds:
        pool = y[val & (dia == k_)]
        ns = (sel & (dia == k_)).sum()
        if len(pool) and ns:
            sim.append(rng.choice(pool, ns, replace=ns > len(pool)))
    if np.concatenate(sim).mean() >= obs:
        cnt += 1
print("  aleatorizacao dentro do pregao: p = %.4f" % (cnt / 4000))
print("\n  walk-forward:")
for bi, bl in enumerate(np.array_split(ds, 5)):
    mb_ = sel & np.isin(dia, bl)
    p_ = y[mb_].mean()
    print("    bloco %d (%s a %s) n=%3d  %.4f  %+6.1f pts"
          % (bi + 1, bl[0], bl[-1], mb_.sum(), p_, p_ * ALVO - (1 - p_) * STOP))
pnl = np.where(y[sel][np.argsort(i[sel])] > 0, ALVO, -STOP)
print("\n  custo   total     pts/trade   maxDD     PF")
for cu in [0, 2, 5, 10, 15, 20]:
    eq = np.cumsum(pnl - cu)
    dd = eq - np.maximum.accumulate(eq)
    po, ne = (pnl - cu)[pnl - cu > 0], (pnl - cu)[pnl - cu < 0]
    print("  %2d pts  %+7.0f   %+7.1f    %6.0f   %.2f"
          % (cu, eq[-1], eq[-1] / len(pnl), dd.min(), po.sum() / abs(ne.sum())))

print("\n" + "=" * 116)
print("b) SOBREPOSICAO REAL COM A REGRA RenkoViradaR11")
print("=" * 116)
elig = (is_rev == 1) & (seqb >= 3) & (df.qt.values > 0) & (df.newday.values == 0)
dposR = dirn * (c - meio) / faixa
selR = elig & (hhmm >= 1000) & (dposR >= 0.25)
yR = np.where(dirn == 1, yB, yA)
mR = selR & ~np.isnan(yR)
iR = np.where(mR)[0]
iP = i[sel]
for tol in [0, 1, 2, 3]:
    comum = sum(1 for x in iP if np.any(np.abs(iR - x) <= tol))
    print("  entradas a <= %d brick de distancia: %d de %d sinais do PivoR11 (%.0f%%)"
          % (tol, comum, len(iP), 100 * comum / len(iP)))
print("\n  -> as duas regras olham o MESMO fenomeno com defasagem de um brick:")
print("     o RenkoViradaR11 entra no proprio brick de reversao; o PivoR11")
print("     exige que esse brick seja extrema local de %d barras e entra no" % ESQ)
print("     seguinte. Nao sao independentes -- nao some as duas expectativas.")

por_dia = pd.DataFrame(dict(dia=dia[sel], y=y[sel])).groupby("dia").y.agg(["size", "mean"])
fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
for cu, cor in [(0, "tab:blue"), (5, "tab:orange"), (10, "tab:red")]:
    ax[0].plot(np.cumsum(pnl - cu), color=cor, label="custo %d pts" % cu)
ax[0].axvline((dia[sel] < corte).sum(), color="k", ls="--", lw=1, label="inicio do teste")
ax[0].axhline(0, color="k", lw=.8)
ax[0].set_title("PivoR11 -- capital (alvo %d / stop %d)" % (ALVO, STOP))
ax[0].set_xlabel("trade"); ax[0].set_ylabel("pontos"); ax[0].legend(); ax[0].grid(alpha=.3)
gd = por_dia[por_dia["size"] >= 3]
ax[1].bar(range(len(gd)), gd["mean"], color=np.where(gd["mean"] > BE, "tab:green", "tab:red"))
ax[1].axhline(BE, color="k", ls="--", label="breakeven %.2f" % BE)
ax[1].axhline(y[sel].mean(), color="tab:blue", ls=":", label="media %.3f" % y[sel].mean())
ax[1].set_title("Acerto por pregao"); ax[1].set_xlabel("pregao"); ax[1].legend()
plt.tight_layout()
plt.savefig("saida_r11/04_pivo_r11.png", dpi=110)

pd.DataFrame(dict(dt=df.dt.values[i[sel]], lado=lado[sel], barra_pivo=j[sel],
                  barra_entrada=i[sel], preco=c[i[sel]], pos_op=pos[sel],
                  y=y[sel], bricks=bars[sel])).to_csv(
    "saida_r11/pivo_r11_sinais.csv", sep=";", decimal=",", index=False)
print("\nok -> saida_r11/04_pivo_r11.png | saida_r11/pivo_r11_sinais.csv")
