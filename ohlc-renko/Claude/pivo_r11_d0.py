#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passo 11: a regra sob Direita = 0, e o fluxo defasado por cima.

Com Direita = 0 a entrada e no fechamento da propria barra do pivo. Perde-se a
barra de confirmacao, mas ganha-se PRECO: numa compra em fundo, esperar uma
barra custa 50 pts (o corpo do brick). Qual dos dois efeitos manda e questao
empirica -- e o que se mede aqui.

Ordem:
  1. grade de geometria com Direita = 0
  2. o filtro de fluxo defasado que a rodada 10 achou, por cima da geometria
  3. robustez completa do vencedor
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import pivo_r11_dados as DD
import pivo_r11_core as C

D = DD.Dados()
n = D.n
nz = DD.nz
dias = D.dias
corte = D.corte
ALVO, STOP = DD.ALVO, DD.STOP
yB, nBr, yA, nAr = C.resultados(D.df, ALVO, STOP)

# ---- series de fluxo usadas como filtro ----------------------------------- #
zimb = D.zs(D.imb)
sb4, sa4 = D.soma(D.agb, 1, 4), D.soma(D.ags, 1, 4)
push4 = -D.zs((sb4 - sa4) / np.maximum(sb4 + sa4, 1e-9))     # >0 = empurrao a favor do extremo
sb2, sa2 = D.soma(D.agb, 1, 2), D.soma(D.ags, 1, 2)
push2 = -D.zs((sb2 - sa2) / np.maximum(sb2 + sa2, 1e-9))
zqt3 = D.zs(D.soma(D.qt, 0, 2) / 3.0)
zvpm = D.zs(D.vpm)
zunk = D.zs(D.unk)
dist2 = np.maximum(np.abs(D.c - np.nan_to_num(D.lag(D.c, 3))) / C.BODY, 0.5)
absor_b = D.zs(D.soma(D.ags, 0, 2) / dist2)
absor_a = D.zs(D.soma(D.agb, 0, 2) / dist2)


def monta(esq, exigir_tipo=True):
    pb, pa = D.candidatos(esq)
    jb = np.where(pb & ~np.isnan(yB))[0]
    ja = np.where(pa & ~np.isnan(yA))[0]
    J = np.r_[jb, ja]
    L = np.r_[np.ones(len(jb), int), -np.ones(len(ja), int)]
    Y = np.r_[yB[jb], yA[ja]]
    s = np.argsort(J, kind="stable")
    J, L, Y = J[s], L[s], Y[s]
    pos = L * (D.c[J] - D.meio[J]) / D.faixa[J]
    tipo = D.dirn[J] == L
    base = tipo if exigir_tipo else np.ones(len(J), bool)
    return J, L, Y, pos, base


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


def rel(nome, J, Y, sel, mostrar=True):
    dd = D.data[J][sel]
    yy = Y[sel]
    if len(yy) < 30:
        return None
    m_tr, m_te = dd < corte, dd >= corte
    pt = yy[m_tr].mean() if m_tr.sum() else np.nan
    pv = yy[m_te].mean() if m_te.sum() else np.nan
    pa_ = yy.mean()
    e = pa_ * ALVO - (1 - pa_) * STOP
    if mostrar:
        print("  %-38s tr n=%4d %.4f | te n=%4d %.4f | tudo n=%4d %.4f %+6.1f (%4.1f/preg)"
              % (nome, m_tr.sum(), pt, m_te.sum(), pv, len(yy), pa_, e, len(yy) / len(dias)))
    return pa_, pt, pv, len(yy)


print("=" * 120)
print("1) GEOMETRIA COM Direita = 0   (entrada no fechamento da propria barra do pivo)")
print("=" * 120)
print("  referencia do arquivo A, com Direita=1: tudo 0.5018, n=568, +25.4 pts\n")
melhor = None
for esq in [2, 3, 4, 6, 8, 10, 12]:
    J, L, Y, pos, base = monta(esq, True)
    for tc, tv in [(0.10, 0.20), (0.20, 0.30), (0.25, 0.35), (0.35, 0.45)]:
        cand = base & (((L == 1) & (pos >= tc)) | ((L == -1) & (pos >= tv)))
        sel = espaca(J, L, cand, 5)
        r = rel("Esq=%-2d tipo_ok  ctx %.2f/%.2f" % (esq, tc, tv), J, Y, sel)
        if r and r[3] >= 200 and (melhor is None or r[0] > melhor[0]):
            melhor = (r[0], esq, tc, tv)
print("\n  melhor da grade: Esq=%d  ctx %.2f/%.2f  ->  %.4f" % (melhor[1], melhor[2], melhor[3], melhor[0]))

print("\n  --- o tipo do brick ainda importa com Direita=0? ---")
for esq in [4, 6, 8]:
    for et in [True, False]:
        J, L, Y, pos, base = monta(esq, et)
        cand = base & (((L == 1) & (pos >= 0.25)) | ((L == -1) & (pos >= 0.35)))
        rel("Esq=%-2d tipo_ok=%-5s ctx 0.25/0.35" % (esq, et), J, Y, espaca(J, L, cand, 5))

# --------------------------------------------------------------------------- #
ESQ, TC, TV = melhor[1], melhor[2], melhor[3]
J, L, Y, pos, base = monta(ESQ, True)
ctx = base & (((L == 1) & (pos >= TC)) | ((L == -1) & (pos >= TV)))

FL = {
    "push4  (empurrao 4 barras a favor do extremo)": push4[J],
    "push2  (empurrao 2 barras)": push2[J],
    "zimb1  (agressao alinhada em n-1; corta ABAIXO)": -zimb[D.lag(np.arange(n), 1).astype(int)[J]] * L,
    "absor2 (contra-volume por brick andado)": np.where(L == 1, absor_b[J], absor_a[J]),
    "zqt3   (volume medio de 3 barras)": zqt3[J],
    "zvpm   (contratos por minuto)": zvpm[J],
    "zunk   (fracao sem agressor)": zunk[J],
}
FL = {k: np.nan_to_num(v) for k, v in FL.items()}

print("\n" + "=" * 120)
print("2) FLUXO DEFASADO POR CIMA DA GEOMETRIA  (base: Esq=%d, tipo_ok, ctx %.2f/%.2f)" % (ESQ, TC, TV))
print("=" * 120)
rel("SEM filtro de fluxo", J, Y, espaca(J, L, ctx, 5))
print()
for nome, v in FL.items():
    for q in [0.30, 0.50]:
        t = np.quantile(v[ctx & (D.data[J] < corte)], q)
        rel("%s >= q%.2f tr (%.2f)" % (nome.split()[0], q, t), J, Y,
            espaca(J, L, ctx & (v >= t), 5))
    print()

print("=" * 120)
print("3) COMBINACOES DE DOIS FILTROS DE FLUXO")
print("=" * 120)
ks = list(FL)
tr_ctx = ctx & (D.data[J] < corte)
res = []
for a in range(len(ks)):
    for b_ in range(a + 1, len(ks)):
        va, vb = FL[ks[a]], FL[ks[b_]]
        for qa in [0.25, 0.40]:
            for qb in [0.25, 0.40]:
                ta = np.quantile(va[tr_ctx], qa); tb = np.quantile(vb[tr_ctx], qb)
                sel = espaca(J, L, ctx & (va >= ta) & (vb >= tb), 5)
                r = rel("", J, Y, sel, mostrar=False)
                if r and r[3] >= 250:
                    res.append((r[2], r[1], r[0], r[3], ks[a], qa, ks[b_], qb))
res.sort(reverse=True)
print("  %-30s %-30s %8s %8s %8s %6s" % ("filtro 1", "filtro 2", "treino", "teste", "tudo", "n"))
for te, tr, tu, nn, k1, q1, k2, q2 in res[:12]:
    print("  %-30s %-30s %8.4f %8.4f %8.4f %6d"
          % ("%s>=q%.2f" % (k1.split()[0], q1), "%s>=q%.2f" % (k2.split()[0], q2), tr, te, tu, nn))
