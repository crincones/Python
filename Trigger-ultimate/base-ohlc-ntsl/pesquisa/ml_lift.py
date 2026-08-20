"""Teste de lift: o fluxo (agressao, tempo, volume, negocios) acrescenta algo
alem da geometria do proprio tijolo (tamanho do pavio contrario)?

Compara, fora da amostra e em ordem cronologica:
    geo    -> so o pavio contrario (risco)
    fluxo  -> so agressao/tempo/volume/negocios
    tudo   -> geo + fluxo + contexto
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score

from universo import universo

GEO = ["risco", "seq", "pos20", "pos50", "net5", "net10", "net20", "viradas5", "viradas20"]
FLUXO = ["imb", "part", "tam", "vel", "fluxo", "intens", "dur_s", "qtd", "trades",
         "r_qtd", "r_trades", "r_dur_s", "r_tam", "r_fluxo", "z_qtd", "z_trades",
         "z_dur_s", "z_agr", "imb3", "imb5", "imb_l1", "imb_l2", "cimb5", "cimb10",
         "cimb20", "cdelta5", "cdelta10", "div", "div3", "div5", "absorc",
         "esf5", "esf10", "esf20", "cdelta_dia", "hora", "nbar_dia"]


def limpar(x: pd.DataFrame) -> pd.DataFrame:
    """Universo executavel: fora tijolo fantasma (gap: varios fecham no mesmo tick)."""
    return x[(x.fantasma == 0) & (x.agr > 0)].copy()


def split(x: pd.DataFrame, frac=0.6):
    dias = np.sort(x.dia.unique())
    corte = dias[int(len(dias) * frac)]
    return x[x.dia < corte], x[x.dia >= corte], corte


def avaliar(x, cols, alvo="ok", seed=0):
    tr, te, corte = split(x)
    Xtr, Xte = tr[cols].to_numpy(np.float64), te[cols].to_numpy(np.float64)
    m = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05,
                                       min_samples_leaf=80, l2_regularization=1.0,
                                       random_state=seed)
    m.fit(Xtr, tr[alvo])
    p = m.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(te[alvo], p)
    # decis da previsao no teste
    q = pd.qcut(p, 5, labels=False, duplicates="drop")
    tab = te.assign(q=q).groupby("q").agg(n=("ok", "size"), ok=("ok", "mean"),
                                          R=("R", "mean"), risco=("risco", "mean"))
    return auc, tab, corte, m, te, p


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    dn, up = universo()
    for nome, x in (("BAIXA (seta acima)", dn), ("ALTA (seta abaixo)", up)):
        x = limpar(x)
        print(f"\n############ {nome}  n={len(x)} base_ok={x.ok.mean():.3f} base_R={x.R.mean():+.3f}")
        for cj, cols in (("geo", GEO), ("fluxo", FLUXO), ("tudo", GEO + FLUXO)):
            auc, tab, corte, *_ = avaliar(x, cols)
            print(f"\n  [{cj}] AUC(ok) fora da amostra = {auc:.4f}   (corte {pd.Timestamp(corte).date()})")
            print(tab.round(3).to_string())
