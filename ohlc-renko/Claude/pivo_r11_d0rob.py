#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 12: robustez da regra com Direita = 0, e escolha da forma de normalizacao
que o NTSL consiga calcular.

A regra candidata (passo 11):
  compra: Low[0] <= Low[1..Esq], brick de alta, pos_op >= 0.35, absorcao alta
  venda : High[0] >= High[1..Esq], brick de baixa, pos_op >= 0.45, absorcao alta

absorcao = volume do lado CONTRARIO nas 3 ultimas barras dividido pela distancia
que o preco de fato percorreu nessas 3 barras (em corpos de brick). Alto = o
lado dominante gastou muito e andou pouco.

Tres formas de normalizar a absorcao, da mais cara a mais barata em NTSL:
  z   : (v - media50) / desvio50          <- precisa de soma dos quadrados
  raz : v / media50                       <- precisa so da soma
  nz  : (v - media50) / (v + media50)     <- limitada em (-1,1), estilo da casa

Se as tres derem a mesma coisa, vai a mais barata e menos fragil.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_dados as DD
import pivo_r11_core as C

D = DD.Dados()
n = D.n
dias, corte = D.dias, D.corte
ALVO, STOP = DD.ALVO, DD.STOP
BODY = C.BODY
yB, nBr, yA, nAr = C.resultados(D.df, ALVO, STOP)

NJAN = 50          # janela da media movel da absorcao
NABS = 3           # barras da soma de absorcao (0,1,2)
PISO = 0.5         # piso da distancia, em corpos


def media_movel(x, per):
    """media de [j-per .. j-1]: mesma coisa que o NTSL faz com soma corrente."""
    return pd.Series(x).rolling(per).mean().shift(1).values


def desvio_movel(x, per):
    s = pd.Series(x)
    m = s.rolling(per).mean().shift(1).values
    q = s.pow(2).rolling(per).mean().shift(1).values
    return np.sqrt(np.maximum(q - m * m, 0.0))


# razao bruta de absorcao, um vetor por lado
dist = np.maximum(np.abs(D.c - np.nan_to_num(D.lag(D.c, NABS))) / BODY, PISO)
rawB = D.soma(D.ags, 0, NABS - 1) / dist     # vendedores gastaram (compra)
rawA = D.soma(D.agb, 0, NABS - 1) / dist     # compradores gastaram (venda)

mB, mA = media_movel(rawB, NJAN), media_movel(rawA, NJAN)
sB_, sA_ = desvio_movel(rawB, NJAN), desvio_movel(rawA, NJAN)

FORMAS = {
    "z":   (np.where(sB_ > 0, (rawB - mB) / np.maximum(sB_, 1e-9), 0.0),
            np.where(sA_ > 0, (rawA - mA) / np.maximum(sA_, 1e-9), 0.0)),
    "raz": (rawB / np.maximum(mB, 1e-9), rawA / np.maximum(mA, 1e-9)),
    "nz":  ((rawB - mB) / np.maximum(rawB + mB, 1e-9),
            (rawA - mA) / np.maximum(rawA + mA, 1e-9)),
}


def monta(esq):
    pb, pa = D.candidatos(esq)
    jb = np.where(pb & ~np.isnan(yB))[0]
    ja = np.where(pa & ~np.isnan(yA))[0]
    J = np.r_[jb, ja]
    L = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    Y = np.r_[yB[jb], yA[ja]]
    s = np.argsort(J, kind="stable")
    return J[s], L[s], Y[s]


def espaca(J, L, cand, minb):
    sel = np.zeros(len(J), bool)
    uC = uV = -10 ** 9
    for k in np.where(cand)[0]:
        if L[k] == 1:
            if J[k] - uC >= minb:
                sel[k] = True; uC = J[k]
        else:
            if J[k] - uV >= minb:
                sel[k] = True; uV = J[k]
    return sel


def regra(esq, tc, tv, forma, lim, minb=5):
    J, L, Y = monta(esq)
    pos = L * (D.c[J] - D.meio[J]) / D.faixa[J]
    tipo = D.dirn[J] == L
    vB, vA = FORMAS[forma]
    ab = np.nan_to_num(np.where(L == 1, vB[J], vA[J]))
    cand = (tipo & (((L == 1) & (pos >= tc)) | ((L == -1) & (pos >= tv)))
            & (ab >= lim))
    sel = espaca(J, L, cand, minb)
    return J[sel], L[sel], Y[sel]


def stat(Jm, Ym, nome="", mostrar=True):
    dd = D.data[Jm]
    tr, te = dd < corte, dd >= corte
    pa_ = Ym.mean() if len(Ym) else np.nan
    e = pa_ * ALVO - (1 - pa_) * STOP
    if mostrar:
        print("  %-34s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f (%4.1f/preg)"
              % (nome, tr.sum(), Ym[tr].mean() if tr.sum() else np.nan,
                 te.sum(), Ym[te].mean() if te.sum() else np.nan,
                 len(Ym), pa_, e, len(Ym) / len(dias)))
    return pa_


print("=" * 118)
print("1) AS TRES NORMALIZACOES DAO A MESMA COISA?   (Esq=4, ctx 0.35/0.45)")
print("=" * 118)
for forma, lims in [("z", [0.0, 0.5, 1.0, 1.5]),
                    ("raz", [1.0, 1.2, 1.4, 1.6]),
                    ("nz", [0.0, 0.10, 0.18, 0.25])]:
    for lim in lims:
        Jm, Lm, Ym = regra(4, 0.35, 0.45, forma, lim)
        stat(Jm, Ym, "%-4s >= %.2f" % (forma, lim))
    print()

print("=" * 118)
print("2) PLATO OU PICO?  (forma nz, varrendo os quatro cortes um de cada vez)")
print("=" * 118)
BASE = dict(esq=4, tc=0.35, tv=0.45, forma="nz", lim=0.18, minb=5)
print("  base:", BASE)
Jb, Lb, Yb = regra(**BASE)
p0 = stat(Jb, Yb, "BASE")
print()
for chave, vals in [("esq", [3, 4, 5, 6]),
                    ("tc", [0.25, 0.30, 0.35, 0.40, 0.45]),
                    ("tv", [0.35, 0.40, 0.45, 0.50, 0.55]),
                    ("lim", [0.00, 0.08, 0.14, 0.18, 0.22, 0.30]),
                    ("minb", [1, 3, 5, 8, 12])]:
    for v in vals:
        P = dict(BASE); P[chave] = v
        Jm, Lm, Ym = regra(**P)
        stat(Jm, Ym, "%s = %s" % (chave, v))
    print()

print("=" * 118)
print("3) ROBUSTEZ DA REGRA BASE")
print("=" * 118)
Jm, Lm, Ym = regra(**BASE)
dd = D.data[Jm]
print("  n=%d  acerto %.4f  breakeven %.4f  %+.1f pts/trade bruto"
      % (len(Ym), Ym.mean(), STOP / (ALVO + STOP), Ym.mean() * ALVO - (1 - Ym.mean()) * STOP))
print("  compra n=%d %.4f | venda n=%d %.4f"
      % ((Lm == 1).sum(), Ym[Lm == 1].mean(), (Lm == -1).sum(), Ym[Lm == -1].mean()))

# bootstrap POR PREGAO
rng = np.random.default_rng(11)
dsig = np.unique(dd)
bs = []
for _ in range(4000):
    esc = rng.choice(dsig, len(dsig), replace=True)
    v = np.concatenate([Ym[dd == x] for x in esc])
    bs.append(v.mean())
bs = np.array(bs)
print("  bootstrap por pregao: IC95 [%.4f, %.4f]   P(<= breakeven) = %.4f"
      % (np.percentile(bs, 2.5), np.percentile(bs, 97.5), (bs <= 0.4).mean()))

# walk-forward em 5 blocos
print("\n  walk-forward em 5 blocos de pregoes:")
blocos = np.array_split(dias, 5)
for k, bl in enumerate(blocos):
    m = np.isin(dd, bl)
    if m.sum():
        print("    bloco %d (%s a %s)  n=%3d  acerto %.4f  %+6.1f pts"
              % (k + 1, bl[0], bl[-1], m.sum(), Ym[m].mean(),
                 Ym[m].mean() * ALVO - (1 - Ym[m].mean()) * STOP))

# randomizacao do rotulo dentro do pregao
pbfull, pafull = D.candidatos(BASE["esq"])
J2, L2, Y2 = monta(BASE["esq"])
d2 = D.data[J2]
idx_sig = np.isin(np.arange(len(J2)), np.searchsorted(J2, Jm))
cnt = 0
for _ in range(2000):
    Ysh = Y2.copy()
    for x in np.unique(d2):
        m = d2 == x
        Ysh[m] = rng.permutation(Ysh[m])
    if Ysh[idx_sig].mean() >= Ym.mean():
        cnt += 1
print("\n  randomizacao do rotulo dentro do pregao: p = %.4f" % (cnt / 2000.0))

# curva de capital e custo
o = np.argsort(Jm)
pnl = np.where(Ym[o] > 0, ALVO, -STOP)
for custo in [0, 5, 10, 15, 25]:
    eq = np.cumsum(pnl - custo)
    dd_ = (eq - np.maximum.accumulate(eq)).min()
    po = (pnl - custo)[pnl - custo > 0]; ne = (pnl - custo)[pnl - custo < 0]
    print("  custo %2d pts:  %+6.1f pts/trade   total %+7.0f   maxDD %6.0f   PF %.2f"
          % (custo, eq[-1] / len(eq), eq[-1], dd_,
             po.sum() / abs(ne.sum()) if len(ne) else np.inf))

print("\n" + "=" * 118)
print("4) CONSTANTES PARA O NTSL")
print("=" * 118)
print("  janela da media movel  NJAN = %d" % NJAN)
print("  barras da absorcao     NABS = %d  (barras 0,1,2)" % NABS)
print("  piso da distancia      PISO = %.2f corpos" % PISO)
print("  Esquerda=%d  Direita=0  MinBarras=%d" % (BASE["esq"], BASE["minb"]))
print("  LimiarCompra=%.2f  LimiarVenda=%.2f  LimiarAbs=%.2f (forma nz)"
      % (BASE["tc"], BASE["tv"], BASE["lim"]))

out = pd.DataFrame({"dt": D.df.dt.values[Jm], "barra": Jm,
                    "lado": np.where(Lm == 1, "compra", "venda"),
                    "close": D.c[Jm], "ok": Ym.astype(int)})
out.to_csv("saida_r11/pivo_d0_sinais.csv", index=False, sep=";", decimal=",")
print("\n  saida_r11/pivo_d0_sinais.csv  (%d sinais)" % len(out))
