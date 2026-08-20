#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 9: features defasadas, serie por serie, sob Direita = 0.

Restricao nova imposta pelo usuario: a seta tem de sair NO FECHAMENTO da barra
do pivo. Logo Direita = 0 e TODA feature so pode olhar para j, j-1, j-2, ...
Nada de barra de confirmacao. Isso mata deltaConf/cFlip e mata o "teste de pivo
pela direita" -- o candidato passa a ser apenas "nova minima de Esquerda barras".

O que se testa aqui, e que nunca foi testado:
  1. AgressionVolBuy e AgressionVolSell DEFASADAS e SEPARADAS (lags 0..3)
  2. Quantity e Trades defasadas (lags 0..3)
  3. derivadas: aceleracao, razao entre lags, soma movel de 3, inclinacao,
     exaustao (lado contrario secando), climax-e-seca, tamanho medio de lote,
     participacao, ritmo, divergencia local de 3 barras, absorcao
  4. multivariado: logistica e GBM, treino/teste cronologico por pregao

Rotulo: alvo 150 / stop 100, primeiro toque, stop testado antes do alvo.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
import pivo_r11_core as C

ESQ_DESC = 2          # populacao larga para descobrir feature
PER = 50              # janela das estatisticas moveis
ALVO, STOP = 150.0, 100.0

df = C.carregar()
n = len(df)
data = df.dt.dt.date.values
dias = np.sort(pd.unique(data))
corte = dias[int(len(dias) * 0.70)]
dayid = pd.factorize(data)[0]

o, h, l, c = df.o.values, df.h.values, df.l.values, df.c.values
agb, ags = df.agb.values.astype(float), df.ags.values.astype(float)
qt, trd = df.qt.values.astype(float), df.trd.values.astype(float)
dur = df.dur_eff.values.astype(float)
dirn, is_rev, seqb = df.dirn.values, df.is_rev.values, df.seq_before.values
wick_net, trav = df.wick_net.values, df.trav.values
hhmm = (df.dt.dt.hour * 100 + df.dt.dt.minute).values

tot = agb + ags
imb = np.where(tot > 0, (agb - ags) / np.maximum(tot, 1e-9), 0.0)
pcp = np.where(tot > 0, agb / np.maximum(tot, 1e-9), 0.5)
unk = np.where(qt > 0, np.clip(qt - tot, 0, None) / np.maximum(qt, 1e-9), 0.0)
sz = np.where(trd > 0, qt / np.maximum(trd, 1e-9), 0.0)
vpm = qt / dur                       # contratos por minuto
tpm = trd / dur                      # negocios por minuto
custo = qt / np.maximum(trav, 1.0)   # contratos por tick percorrido
cumd = pd.Series(agb - ags).groupby(dayid).cumsum().values
cumq = pd.Series(qt).groupby(dayid).cumsum().values

# range do pregao ate a barra (o contexto que sobreviveu no estudo anterior)
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


def zs(x, per=PER):
    """z-score contra a janela [j-per .. j-1]: zero lookahead."""
    s = pd.Series(x)
    m = s.rolling(per).mean().shift(1).values
    q = s.pow(2).rolling(per).mean().shift(1).values
    d = np.sqrt(np.maximum(q - m * m, 0.0))
    return np.where(d > 1e-12, (x - m) / np.maximum(d, 1e-12), 0.0)


def lag(x, k):
    if k == 0:
        return x.copy()
    out = np.full(n, np.nan)
    out[k:] = x[:-k]
    return out


def nz(a, b):
    """razao limitada em (-1,1), monotona em log(a/b)."""
    s = a + b
    return np.where(np.abs(s) > 1e-12, (a - b) / s, 0.0)


# --------------------------------------------------------------------------- #
# populacao: candidato de compra = nova minima de ESQ barras, e vice-versa
# --------------------------------------------------------------------------- #
def candidatos(esq):
    pb = np.ones(n, bool); pa = np.ones(n, bool)
    for k in range(1, esq + 1):
        pb &= np.r_[np.zeros(k, bool), l[k:] <= l[:-k]]
        pa &= np.r_[np.zeros(k, bool), h[k:] >= h[:-k]]
    val = np.arange(n) >= PER + esq + 5
    return pb & val, pa & val


pb, pa = candidatos(ESQ_DESC)
yB, nB, yA, nA = C.resultados(df, ALVO, STOP)

jb = np.where(pb & ~np.isnan(yB))[0]
ja = np.where(pa & ~np.isnan(yA))[0]
J = np.r_[jb, ja]
L = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]   # lado
Y = np.r_[yB[jb], yA[ja]]
s = np.argsort(J, kind="stable")
J, L, Y = J[s], L[s], Y[s]
TR = data[J] < corte
TE = ~TR

print("=" * 118)
print("POPULACAO DE DESCOBERTA  (Direita=0, Esquerda=%d, alvo %d / stop %d)" % (ESQ_DESC, ALVO, STOP))
print("=" * 118)
print("  candidatos: %d  (compra %d, venda %d)   pregoes: %d   corte treino/teste: %s"
      % (len(J), (L == 1).sum(), (L == -1).sum(), len(dias), corte))
print("  taxa base: tudo %.4f | treino %.4f | teste %.4f   (breakeven %.4f)"
      % (Y.mean(), Y[TR].mean(), Y[TE].mean(), STOP / (ALVO + STOP)))


# --------------------------------------------------------------------------- #
# banco de features, todas alinhadas ao lado da operacao
# --------------------------------------------------------------------------- #
F = {}


def add(nome, serie_por_barra, alinhar=False):
    """serie indexada por barra -> vetor indexado por candidato."""
    v = np.asarray(serie_por_barra, float)[J]
    if alinhar:
        v = v * L
    F[nome] = v


# --- 1. AS SERIES CRUAS, DEFASADAS, UMA A UMA ------------------------------
CRUAS = {"agb": agb, "ags": ags, "qt": qt, "trd": trd, "dur": dur, "sz": sz}
for nome, x in CRUAS.items():
    z = zs(x)
    for k in range(4):
        add("z%s_%d" % (nome, k), lag(z, k))

# --- 2. agressao a favor / contra, defasada --------------------------------
# a favor de uma COMPRA = agb; a favor de uma VENDA = ags. Alinhar troca os dois.
zb, za = zs(agb), zs(ags)
zpc = zs(pcp)
for k in range(4):
    lb, la_ = lag(zb, k)[J], lag(za, k)[J]
    F["zfav_%d" % k] = np.where(L == 1, lb, la_)
    F["zctr_%d" % k] = np.where(L == 1, la_, lb)
    F["imb_%d" % k] = lag(imb, k)[J] * L
    F["zimb_%d" % k] = lag(zs(imb), k)[J] * L

# --- 3. razoes entre lags, por serie (aceleracao / exaustao) ---------------
for nome, x in CRUAS.items():
    for k in range(3):
        F["r%s_%d%d" % (nome, k, k + 1)] = nz(lag(x, k), lag(x, k + 1))[J]
# exaustao do lado contrario: contra[0] menor que contra[1] e contra[2]
rb01, ra01 = nz(agb, lag(agb, 1)), nz(ags, lag(ags, 1))
rb02, ra02 = nz(agb, lag(agb, 2)), nz(ags, lag(ags, 2))
F["exaust1"] = -np.where(L == 1, ra01[J], rb01[J])
F["exaust2"] = -np.where(L == 1, ra02[J], rb02[J])
F["reforco1"] = np.where(L == 1, rb01[J], ra01[J])
F["reforco2"] = np.where(L == 1, rb02[J], ra02[J])

# --- 4. somas moveis de 3 barras e inclinacao ------------------------------
def soma3(x):
    return x + lag(x, 1) + lag(x, 2)


F["imb3"] = (soma3(agb) - soma3(ags))[J] / np.maximum(soma3(tot)[J], 1e-9) * L
F["zimb3"] = zs((soma3(agb) - soma3(ags)) / np.maximum(soma3(tot), 1e-9))[J] * L
F["incl_imb"] = (imb - lag(imb, 3))[J] / 3.0 * L
F["incl_pc"] = (pcp - lag(pcp, 3))[J] / 3.0 * L
F["zqt3"] = zs(soma3(qt) / 3.0)[J]
F["ztrd3"] = zs(soma3(trd) / 3.0)[J]
F["zsz3"] = zs(soma3(qt) / np.maximum(soma3(trd), 1e-9))[J]

# --- 5. persistencia e virada do sinal do delta ----------------------------
sgn = np.sign(imb)
F["persist3"] = ((sgn + lag(sgn, 1) + lag(sgn, 2))[J]) * L
F["flip"] = (((imb * L[0] > 0) & (lag(imb, 1) * L[0] < 0)).astype(float))[J] * 0  # placeholder
imbal = imb[J] * L
imb1 = lag(imb, 1)[J] * L
imb2 = lag(imb, 2)[J] * L
F["flip"] = ((imbal > 0) & (imb1 < 0) & (imb2 < 0)).astype(float)
F["duplo"] = ((imbal > 0) & (imb1 > 0)).astype(float)

# --- 6. climax e seca -------------------------------------------------------
zq = zs(qt)
F["clx_seca"] = lag(zq, 1)[J] - zq[J]
F["clx_seca2"] = lag(zq, 2)[J] - zq[J]
F["zvpm_0"] = zs(vpm)[J]
F["rvpm_01"] = nz(vpm, lag(vpm, 1))[J]
F["ztpm_0"] = zs(tpm)[J]
F["rdur_01"] = nz(dur, lag(dur, 1))[J]
F["zcusto"] = zs(custo)[J]
F["zunk"] = zs(unk)[J]
F["runk_01"] = nz(unk, lag(unk, 1))[J]

# --- 7. divergencia local de 3 barras --------------------------------------
# preco fez extremo de 3 barras contra o lado, mas o fluxo de 3 barras melhorou
mov3 = (c - lag(c, 3))[J] * L / C.BODY
F["div3"] = F["imb3"] - np.clip(mov3 / 3.0, -1, 1)
F["mov3"] = mov3
F["div_cum"] = (cumd[J] / np.maximum(cumq[J], 1e-9)) * L

# --- 8. contexto, geometria e relogio --------------------------------------
F["pos_op"] = ((c - meio) / faixa)[J] * L
F["tipo_ok"] = (dirn[J] == L).astype(float)
F["is_rev"] = is_rev[J].astype(float)
F["seq_b"] = np.minimum(seqb[J], 8).astype(float)
F["wick_net"] = wick_net[J]
F["zdur_rel"] = zs(dur)[J]
F["hora"] = (df.dt.dt.hour + df.dt.dt.minute / 60.0).values[J]
prof_lo = np.zeros(n, int); prof_hi = np.zeros(n, int)
for j in range(n):
    k = 1
    while k <= 40 and j - k >= 0 and l[j] <= l[j - k]:
        k += 1
    prof_lo[j] = k - 1
    k = 1
    while k <= 40 and j - k >= 0 and h[j] >= h[j - k]:
        k += 1
    prof_hi[j] = k - 1
F["prof"] = np.where(L == 1, prof_lo[J], prof_hi[J]).astype(float)

for k in list(F):
    F[k] = np.nan_to_num(np.asarray(F[k], float), nan=0.0, posinf=0.0, neginf=0.0)


# --------------------------------------------------------------------------- #
# AUC individual, treino e teste
# --------------------------------------------------------------------------- #
def auc(v, m):
    if m.sum() < 50 or len(np.unique(Y[m])) < 2:
        return np.nan
    return roc_auc_score(Y[m], v[m])


linhas = []
for k, v in F.items():
    a_tr, a_te, a_all = auc(v, TR), auc(v, TE), auc(v, np.ones(len(J), bool))
    linhas.append((k, a_tr, a_te, a_all, abs(a_all - 0.5)))

print("\n" + "=" * 118)
print("1) LAGS SEPARADOS: AgressionVolBuy, AgressionVolSell, Quantity, Trades")
print("=" * 118)
print("  %-14s %8s %8s %8s     %-14s %8s %8s %8s"
      % ("feature", "treino", "teste", "tudo", "feature", "treino", "teste", "tudo"))
d = {k: (a, b, cc) for k, a, b, cc, _ in linhas}


def par(k1, k2):
    a = d.get(k1, (np.nan,) * 3); b = d.get(k2, (np.nan,) * 3)
    print("  %-14s %8.4f %8.4f %8.4f     %-14s %8.4f %8.4f %8.4f"
          % (k1, a[0], a[1], a[2], k2, b[0], b[1], b[2]))


for k in range(4):
    par("zagb_%d" % k, "zags_%d" % k)
print()
for k in range(4):
    par("zqt_%d" % k, "ztrd_%d" % k)
print()
for k in range(4):
    par("zfav_%d" % k, "zctr_%d" % k)
print()
for k in range(4):
    par("zimb_%d" % k, "imb_%d" % k)

print("\n" + "=" * 118)
print("2) RANKING GERAL POR |AUC - 0.5| (tudo)")
print("=" * 118)
linhas.sort(key=lambda t: -t[4])
print("  %-16s %8s %8s %8s %8s" % ("feature", "treino", "teste", "tudo", "sinal"))
for k, a, b, cc, _ in linhas[:32]:
    print("  %-16s %8.4f %8.4f %8.4f %8s"
          % (k, a, b, cc, "ok" if (a - 0.5) * (b - 0.5) > 0 else "INVERTE"))

print("\n  --- as 10 piores (para conferir que a maioria e ruido) ---")
for k, a, b, cc, _ in linhas[-10:]:
    print("  %-16s %8.4f %8.4f %8.4f" % (k, a, b, cc))


# --------------------------------------------------------------------------- #
# multivariado
# --------------------------------------------------------------------------- #
nomes = [k for k, _, _, _, _ in linhas]
X = np.column_stack([F[k] for k in nomes])
mu, sd = X[TR].mean(0), X[TR].std(0) + 1e-9
Xs = (X - mu) / sd

print("\n" + "=" * 118)
print("3) MULTIVARIADO  (ajuste so no treino, AUC reportada no teste)")
print("=" * 118)

for Cr in [0.003, 0.01, 0.03, 0.1, 1.0]:
    lr = LogisticRegression(C=Cr, max_iter=4000)
    lr.fit(Xs[TR], Y[TR])
    ptr = lr.predict_proba(Xs[TR])[:, 1]
    pte = lr.predict_proba(Xs[TE])[:, 1]
    print("  logistica L2 C=%-6.3f  treino %.4f  teste %.4f"
          % (Cr, roc_auc_score(Y[TR], ptr), roc_auc_score(Y[TE], pte)))

for lf in [15, 31]:
    for it in [80, 200]:
        gb = HistGradientBoostingClassifier(max_leaf_nodes=lf, max_iter=it,
                                            learning_rate=0.05, min_samples_leaf=80,
                                            l2_regularization=1.0, random_state=0)
        gb.fit(X[TR], Y[TR])
        print("  GBM leaves=%-3d iter=%-4d      treino %.4f  teste %.4f"
              % (lf, it, roc_auc_score(Y[TR], gb.predict_proba(X[TR])[:, 1]),
                 roc_auc_score(Y[TE], gb.predict_proba(X[TE])[:, 1])))

# selecao gulosa no treino, validada no teste
print("\n  --- selecao gulosa (criterio = AUC de treino da logistica) ---")
esc = []
rest = list(nomes)
best_prev = 0.5
for passo in range(8):
    melhor = None
    for k in rest:
        cols = [nomes.index(x) for x in esc + [k]]
        lr = LogisticRegression(C=0.03, max_iter=3000)
        lr.fit(Xs[TR][:, cols], Y[TR])
        a = roc_auc_score(Y[TR], lr.predict_proba(Xs[TR][:, cols])[:, 1])
        if melhor is None or a > melhor[0]:
            melhor = (a, k)
    if melhor[0] - best_prev < 0.0015:
        break
    best_prev = melhor[0]
    esc.append(melhor[1]); rest.remove(melhor[1])
    cols = [nomes.index(x) for x in esc]
    lr = LogisticRegression(C=0.03, max_iter=3000)
    lr.fit(Xs[TR][:, cols], Y[TR])
    ate = roc_auc_score(Y[TE], lr.predict_proba(Xs[TE][:, cols])[:, 1])
    print("    +%-16s  treino %.4f   teste %.4f" % (melhor[1], melhor[0], ate))
print("    conjunto final:", ", ".join(esc))

# --------------------------------------------------------------------------- #
# teste de sanidade: embaralhar o rotulo DENTRO do pregao
# --------------------------------------------------------------------------- #
print("\n" + "=" * 118)
print("4) SANIDADE: melhor AUC de teste com rotulo embaralhado dentro do pregao")
print("=" * 118)
rng = np.random.default_rng(7)
top = [k for k, _, _, _, _ in linhas[:5]]
dj = dayid[J]
piores = []
for _ in range(200):
    Ysh = Y.copy()
    for dd in np.unique(dj):
        m = dj == dd
        Ysh[m] = rng.permutation(Ysh[m])
    a = max(abs(roc_auc_score(Ysh[TE], F[k][TE]) - 0.5) for k in top)
    piores.append(a)
piores = np.array(piores)
real = max(abs(d[k][1] - 0.5) for k in top)
print("  |AUC-0.5| real das 5 melhores no teste: %.4f" % real)
print("  embaralhado: media %.4f  p95 %.4f  max %.4f   -> p = %.3f"
      % (piores.mean(), np.percentile(piores, 95), piores.max(),
         (piores >= real).mean()))
