#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 10: segunda rodada de features, guiada pelo achado da primeira.

Rodada 1 mostrou:
  - imb (agressao alinhada ao lado da operacao) NA barra do pivo nao informa
    nada (AUC 0.4997); em n-1 informa INVERTIDO (0.4780) e o efeito decai
    monotonamente ate n-3. Equivalente positivo: zctr_1 0.5147, zctr_2 0.5155.
    Leitura: quem empurra o extremo com agressao pesada A FAVOR do movimento
    NAS BARRAS ANTERIORES esta se exaurindo -- entrar contra funciona.
  - Quantity e Trades isolados valem pouco; a soma de 3 barras vale mais.
  - GBM decora (treino 0.78 / teste 0.53). Logistica regularizada da 0.539.

Aqui: lag ate 8, esforco/resultado (volume contra dividido pela distancia
percorrida), agregados por PERNA em vez de lag fixo, interacoes com contexto,
e a conversao de AUC em taxa de acerto por decil.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import pivo_r11_dados as DD
import pivo_r11_core as C

ESQ = 2
D = DD.Dados()
J, L, Y, NB = DD.populacao(D, ESQ)
n = D.n
TR = D.data[J] < D.corte
TE = ~TR
nz = DD.nz

print("=" * 118)
print("POPULACAO  Direita=0, Esquerda=%d, alvo %d / stop %d" % (ESQ, DD.ALVO, DD.STOP))
print("  n=%d  treino=%d  teste=%d   base tudo %.4f | treino %.4f | teste %.4f"
      % (len(J), TR.sum(), TE.sum(), Y.mean(), Y[TR].mean(), Y[TE].mean()))
print("=" * 118)

F = {}


def put(nome, v_barra, alinhar=False):
    v = np.asarray(v_barra, float)[J]
    if alinhar:
        v = v * L
    F[nome] = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)


# --------------------------------------------------------------------------- #
# A. o eixo que funcionou: agressao defasada, alinhada, ate lag 8
# --------------------------------------------------------------------------- #
zimb = D.zs(D.imb)
for k in range(9):
    put("imb_%d" % k, D.lag(D.imb, k), alinhar=True)
    put("zimb_%d" % k, D.lag(zimb, k), alinhar=True)

# pressao a favor do EXTREMO acumulada em janelas que comecam em n-1
# (o lado que empurrou o preco ate aqui = contrario a operacao)
for k1 in [1, 2, 3, 4, 6, 8]:
    sb = D.soma(D.agb, 1, k1)
    sa = D.soma(D.ags, 1, k1)
    put("push_1a%d" % k1, -(sb - sa) / np.maximum(sb + sa, 1e-9), alinhar=True)
    put("zpush_1a%d" % k1, -D.zs((sb - sa) / np.maximum(sb + sa, 1e-9)), alinhar=True)
# a mesma coisa incluindo a barra do pivo
for k1 in [1, 2, 3, 4, 6]:
    sb = D.soma(D.agb, 0, k1)
    sa = D.soma(D.ags, 0, k1)
    put("push_0a%d" % k1, -(sb - sa) / np.maximum(sb + sa, 1e-9), alinhar=True)

# --------------------------------------------------------------------------- #
# B. esforco x resultado: quanto volume o lado dominante gastou por tick andado
# --------------------------------------------------------------------------- #
for k1 in [2, 3, 4, 6]:
    vol = D.soma(D.qt, 0, k1)
    dist = np.abs(D.c - np.nan_to_num(D.lag(D.c, k1 + 1), nan=np.nan)) / C.BODY
    ef = vol / np.maximum(dist, 0.5)
    put("zesf_%d" % k1, D.zs(ef))
    trab = D.soma(D.trav, 0, k1)
    put("zcusto_%d" % k1, D.zs(vol / np.maximum(trab, 1.0)))
# contra-volume por tick andado: absorcao
for k1 in [2, 3, 4]:
    contra_b = D.soma(D.ags, 0, k1)     # para compra: vendedores gastaram
    contra_a = D.soma(D.agb, 0, k1)
    dist = np.maximum(np.abs(D.c - np.nan_to_num(D.lag(D.c, k1 + 1))) / C.BODY, 0.5)
    vb = D.zs(contra_b / dist)[J]
    va = D.zs(contra_a / dist)[J]
    F["absor_%d" % k1] = np.nan_to_num(np.where(L == 1, vb, va))

# --------------------------------------------------------------------------- #
# C. agregados por PERNA (nao por lag fixo)
# --------------------------------------------------------------------------- #
ini = D.ini_perna
idx = np.arange(n)
cs_b = np.cumsum(D.agb); cs_a = np.cumsum(D.ags)
cs_q = np.cumsum(D.qt); cs_t = np.cumsum(D.trd); cs_d = np.cumsum(D.dur)


def soma_perna(cs, i0, i1):
    return cs[i1] - np.where(i0 > 0, cs[i0 - 1], 0.0)


pb_l = soma_perna(cs_b, ini, idx)
pa_l = soma_perna(cs_a, ini, idx)
pq_l = soma_perna(cs_q, ini, idx)
pt_l = soma_perna(cs_t, ini, idx)
pd_l = soma_perna(cs_d, ini, idx)
nper = (idx - ini + 1).astype(float)
put("perna_imb", (pb_l - pa_l) / np.maximum(pb_l + pa_l, 1e-9), alinhar=True)
put("perna_n", np.minimum(nper, 12))
put("perna_zq", D.zs(pq_l / nper))
put("perna_zsz", D.zs(pq_l / np.maximum(pt_l, 1e-9)))
put("perna_vpm", D.zs(pq_l / np.maximum(pd_l, 1e-6)))
# a perna ANTERIOR (a que terminou em ini-1)
ini_prev = np.where(ini > 0, D.ini_perna[np.maximum(ini - 1, 0)], 0)
fim_prev = np.maximum(ini - 1, 0)
qb = soma_perna(cs_b, ini_prev, fim_prev)
qa = soma_perna(cs_a, ini_prev, fim_prev)
put("perna_ant_imb", (qb - qa) / np.maximum(qb + qa, 1e-9), alinhar=True)
put("perna_razao", nz(pq_l, soma_perna(cs_q, ini_prev, fim_prev)))

# --------------------------------------------------------------------------- #
# D. lote medio, participacao, ritmo -- defasados
# --------------------------------------------------------------------------- #
zsz, zq, zt, zv, zu = (D.zs(D.sz), D.zs(D.qt), D.zs(D.trd),
                       D.zs(D.vpm), D.zs(D.unk))
for k in range(5):
    put("zsz_%d" % k, D.lag(zsz, k))
    put("zqt_%d" % k, D.lag(zq, k))
    put("ztrd_%d" % k, D.lag(zt, k))
    put("zunk_%d" % k, D.lag(zu, k))
put("zqt3", D.zs(D.soma(D.qt, 0, 2) / 3.0))
put("ztrd3", D.zs(D.soma(D.trd, 0, 2) / 3.0))
put("zsz3", D.zs(D.soma(D.qt, 0, 2) / np.maximum(D.soma(D.trd, 0, 2), 1e-9)))
put("zvpm_0", zv)
put("clx_seca", D.lag(zq, 1) - zq)
put("clx_seca2", D.lag(zq, 2) - zq)
put("rsz_01", nz(D.sz, D.lag(D.sz, 1)))
put("rvpm_01", nz(D.vpm, D.lag(D.vpm, 1)))
put("rdur_01", nz(D.dur, D.lag(D.dur, 1)))

# --------------------------------------------------------------------------- #
# E. contexto, geometria, relogio
# --------------------------------------------------------------------------- #
put("pos_op", (D.c - D.meio) / D.faixa, alinhar=True)
F["tipo_ok"] = (D.dirn[J] == L).astype(float)
put("is_rev", D.is_rev.astype(float))
put("seq_b", np.minimum(D.seqb, 8).astype(float))
put("wick_net", D.wick_net)
put("hora", D.hora)
F["prof"] = np.where(L == 1, D.prof_lo[J], D.prof_hi[J]).astype(float)
put("dia_cum", D.cumd / np.maximum(D.cumq, 1e-9), alinhar=True)

# --------------------------------------------------------------------------- #
# F. interacoes com o contexto (o unico eixo que ja sabia funcionar)
# --------------------------------------------------------------------------- #
base_ctx = F["pos_op"]
for k in ["zimb_1", "push_1a2", "push_1a4", "zqt3", "prof"]:
    F["x_%s" % k] = F[k] * base_ctx
F["x_imb1_prof"] = F["zimb_1"] * np.clip(F["prof"] / 8.0, 0, 1)
F["x_imb1_seq"] = F["zimb_1"] * np.clip(F["seq_b"] / 6.0, 0, 1)

for k in list(F):
    F[k] = np.nan_to_num(np.asarray(F[k], float), nan=0.0, posinf=0.0, neginf=0.0)


def auc(v, m):
    if m.sum() < 50:
        return np.nan
    return roc_auc_score(Y[m], v[m])


res = [(k, auc(v, TR), auc(v, TE), auc(v, np.ones(len(J), bool))) for k, v in F.items()]

print("\n" + "=" * 118)
print("A) AGRESSAO ALINHADA POR LAG  (0 = barra do pivo).  <0.5 = INVERTE, e o que se quer")
print("=" * 118)
print("  %-12s %8s %8s %8s      %-12s %8s %8s %8s"
      % ("feature", "treino", "teste", "tudo", "feature", "treino", "teste", "tudo"))
dd = {k: (a, b, c) for k, a, b, c in res}
for k in range(9):
    a = dd["imb_%d" % k]; b = dd["zimb_%d" % k]
    print("  %-12s %8.4f %8.4f %8.4f      %-12s %8.4f %8.4f %8.4f"
          % ("imb_%d" % k, a[0], a[1], a[2], "zimb_%d" % k, b[0], b[1], b[2]))

print("\n" + "=" * 118)
print("B) PRESSAO ACUMULADA QUE CRIOU O EXTREMO  (janela comeca em n-1; >0.5 = ajuda)")
print("=" * 118)
for k in [x for x in F if x.startswith("push_") or x.startswith("zpush_")]:
    a = dd[k]
    print("  %-14s treino %.4f  teste %.4f  tudo %.4f" % (k, a[0], a[1], a[2]))

print("\n" + "=" * 118)
print("C) RANKING GERAL POR |AUC-0.5| NO TESTE  (so as que nao invertem de bloco)")
print("=" * 118)
ok = [(k, a, b, c) for k, a, b, c in res if (a - 0.5) * (b - 0.5) > 0]
ok.sort(key=lambda t: -abs(t[2] - 0.5))
print("  %-16s %8s %8s %8s" % ("feature", "treino", "teste", "tudo"))
for k, a, b, c in ok[:28]:
    print("  %-16s %8.4f %8.4f %8.4f" % (k, a, b, c))

# --------------------------------------------------------------------------- #
# multivariado e decis
# --------------------------------------------------------------------------- #
nomes = [k for k, _, _, _ in res]
X = np.column_stack([F[k] for k in nomes])
mu, sd = X[TR].mean(0), X[TR].std(0) + 1e-9
Xs = (X - mu) / sd

print("\n" + "=" * 118)
print("D) MULTIVARIADO  (ajuste so no treino)")
print("=" * 118)
best = None
for Cr in [0.001, 0.003, 0.01, 0.03, 0.1]:
    lr = LogisticRegression(C=Cr, max_iter=5000)
    lr.fit(Xs[TR], Y[TR])
    atr = roc_auc_score(Y[TR], lr.predict_proba(Xs[TR])[:, 1])
    ate = roc_auc_score(Y[TE], lr.predict_proba(Xs[TE])[:, 1])
    print("  logistica todas as %d features, C=%-6.3f  treino %.4f  teste %.4f"
          % (len(nomes), Cr, atr, ate))
    if best is None or ate > best[0]:
        best = (ate, Cr)

print("\n  --- selecao gulosa, criterio = AUC de TREINO ---")
esc, rest, prev = [], list(nomes), 0.5
for _ in range(10):
    mel = None
    for k in rest:
        cols = [nomes.index(x) for x in esc + [k]]
        lr = LogisticRegression(C=0.03, max_iter=3000)
        lr.fit(Xs[TR][:, cols], Y[TR])
        a = roc_auc_score(Y[TR], lr.predict_proba(Xs[TR][:, cols])[:, 1])
        if mel is None or a > mel[0]:
            mel = (a, k)
    if mel[0] - prev < 0.0012:
        break
    prev = mel[0]
    esc.append(mel[1]); rest.remove(mel[1])
    cols = [nomes.index(x) for x in esc]
    lr = LogisticRegression(C=0.03, max_iter=3000)
    lr.fit(Xs[TR][:, cols], Y[TR])
    print("    +%-16s treino %.4f  teste %.4f"
          % (mel[1], mel[0], roc_auc_score(Y[TE], lr.predict_proba(Xs[TE][:, cols])[:, 1])))
print("    conjunto:", ", ".join(esc))

cols = [nomes.index(x) for x in esc]
lr = LogisticRegression(C=0.03, max_iter=3000).fit(Xs[TR][:, cols], Y[TR])
p = lr.predict_proba(Xs[:, cols])[:, 1]
print("\n  coeficientes (features padronizadas no treino):")
for k, w in sorted(zip(esc, lr.coef_[0]), key=lambda t: -abs(t[1])):
    print("    %-16s %+7.3f" % (k, w))

print("\n" + "=" * 118)
print("E) O QUE ESSA AUC VALE: taxa de acerto por decil do modelo, NO TESTE")
print("=" * 118)
qs = np.quantile(p[TR], np.linspace(0, 1, 11))
qs[0], qs[-1] = -np.inf, np.inf
print("  %-8s %8s %8s %8s %8s %10s" % ("decil", "n tr", "acerto tr", "n te", "acerto te", "pts/trade te"))
for k in range(10):
    mtr = TR & (p >= qs[k]) & (p < qs[k + 1])
    mte = TE & (p >= qs[k]) & (p < qs[k + 1])
    ate_ = Y[mte].mean() if mte.sum() else np.nan
    print("  %-8d %8d %9.4f %8d %9.4f %+10.1f"
          % (k + 1, mtr.sum(), Y[mtr].mean(), mte.sum(), ate_,
             ate_ * DD.ALVO - (1 - ate_) * DD.STOP))

print("\n  acumulado a partir do topo (corte = quantil do TREINO):")
print("  %-10s %8s %10s %8s %10s %11s" % ("corte", "n tr", "acerto tr", "n te", "acerto te", "pts/trade te"))
for q in [0.50, 0.70, 0.80, 0.90, 0.95]:
    t = np.quantile(p[TR], q)
    mtr = TR & (p >= t); mte = TE & (p >= t)
    a_ = Y[mte].mean()
    print("  q%-9.2f %8d %10.4f %8d %10.4f %+11.1f"
          % (q, mtr.sum(), Y[mtr].mean(), mte.sum(), a_, a_ * DD.ALVO - (1 - a_) * DD.STOP))
