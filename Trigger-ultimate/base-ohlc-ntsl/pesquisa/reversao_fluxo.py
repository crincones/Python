"""O teste que o corte de reversao viabiliza: agressao/tempo/volume DENTRO das
reversoes.

Por que aqui e diferente. Na base inteira o pavio contrario varia de 50 a 150 e
domina tudo -- tijolo lento e pesado TEM pavio grande, entao qualquer feature de
fluxo so reconstruia o pavio. Nas reversoes o pavio ja nasce entre 95 e 150
(99,98% dos casos): o confundidor esta quase congelado. Se agressao valer alguma
coisa, e aqui que aparece.

Features especificas de reversao (nao existiam no estudo anterior):
    perna      tijolos da tendencia que acabou de ser quebrada
    imb_perna  agressao acumulada durante essa perna
    a_favor    agressao do tijolo de reversao a favor da reversao
    contraste  a_favor - agressao media da perna quebrada
    exaust     volume da perna / deslocamento da perna (esforco crescente)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from dados import carregar
from features import preparar
from universo import universo
from ml_lift import limpar, split

BRICK = 50.0


def extras(d: pd.DataFrame) -> pd.DataFrame:
    """Features que so fazem sentido num tijolo de reversao."""
    d = d.copy()
    eps = 1e-9
    # a perna quebrada: o 'seq' do tijolo anterior
    d["perna"] = d["seq"].shift(1)

    # agressao acumulada da perna quebrada (soma dos 'perna' tijolos anteriores)
    delta = d["delta"].to_numpy(float)
    agr = d["agr"].to_numpy(float)
    qtd = d["qtd"].to_numpy(float)
    dur = d["dur_s"].to_numpy(float)
    perna = d["perna"].fillna(0).to_numpy(int)
    n = len(d)
    ip = np.full(n, np.nan)
    vq = np.full(n, np.nan)
    vd = np.full(n, np.nan)
    for i in range(n):
        k = perna[i]
        if k <= 0 or i - k < 0:
            continue
        sl = slice(i - k, i)
        ip[i] = delta[sl].sum() / (agr[sl].sum() + eps)
        vq[i] = qtd[sl].sum()
        vd[i] = dur[sl].sum()
    d["imb_perna"] = ip
    d["qtd_perna"] = vq
    d["dur_perna"] = vd
    # esforco da perna: volume gasto por tijolo deslocado
    d["exaust"] = d["qtd_perna"] / (d["perna"].abs() + 1.0)
    # a agressao do tijolo de reversao, a favor da reversao
    d["a_favor"] = d["dir"] * d["imb"]
    # contraste: o fluxo virou junto com o preco?
    d["contraste"] = d["a_favor"] - (-d["dir"] * d["imb_perna"])
    # o tijolo de reversao foi mais rapido/pesado que a media da perna?
    d["vel_rel"] = (d["dur_perna"] / (d["perna"] + eps)) / (d["dur_s"] + 1.0)
    d["qtd_rel"] = d["qtd"] / (d["qtd_perna"] / (d["perna"] + eps) + eps)
    return d


def universo_rev(h: int = 4):
    d = extras(preparar(carregar()))
    d = d[(d.c - d.o).abs() == BRICK].copy()
    dn = d[(d.dir == -1) & (d.virou == 1)].dropna(subset=["ok_baixa"]).copy()
    up = d[(d.dir == 1) & (d.virou == 1)].dropna(subset=["ok_alta"]).copy()
    dn["lado"], up["lado"] = -1, 1
    dn["ok"], up["ok"] = dn["ok_baixa"], up["ok_alta"]
    dn["risco"], up["risco"] = dn["h"] - dn["c"], up["c"] - up["l"]
    dn["mfe"], up["mfe"] = dn["mfe_baixa"], up["mfe_alta"]
    dn["net"], up["net"] = dn["net_baixa"], up["net_alta"]
    for x in (dn, up):
        x["pnl"] = np.where(x["ok"] == 1, x["net"], -x["risco"])
        x["R"] = x["pnl"] / x["risco"]
        x["mfeR"] = x["mfe"] / x["risco"]
    return limpar(dn), limpar(up)


GEO = ["risco", "perna", "pos20", "pos50", "net5", "net10", "net20",
       "viradas5", "viradas20"]
FLUXO = ["imb", "a_favor", "imb_perna", "contraste", "part", "tam", "vel",
         "fluxo", "intens", "dur_s", "qtd", "trades", "r_qtd", "r_trades",
         "r_dur_s", "r_fluxo", "z_qtd", "z_trades", "z_dur_s", "z_agr",
         "imb3", "imb5", "imb_l1", "imb_l2", "cimb5", "cimb10", "cimb20",
         "div", "div3", "div5", "absorc", "esf5", "esf10", "esf20",
         "exaust", "vel_rel", "qtd_rel", "qtd_perna", "dur_perna",
         "cdelta_dia", "hora", "nbar_dia"]


def ic95(x):
    x = np.asarray(x, float)
    return 1.96 * np.nanstd(x, ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


def decis_ctrl(x: pd.DataFrame, col: str, q: int = 5) -> pd.DataFrame:
    """Decis da feature DENTRO de cada faixa de pavio, depois agregados.

    Assim o efeito nao pode vir do pavio: cada bucket tem a mesma mistura.
    """
    x = x.dropna(subset=[col]).copy()
    if len(x) < 200:
        return pd.DataFrame()
    fx = pd.cut(x.risco, [94, 115, 135, 151])
    partes = []
    for _, g in x.groupby(fx, observed=True):
        if len(g) < 100:
            continue
        try:
            g = g.assign(qq=pd.qcut(g[col], q, labels=False, duplicates="drop"))
        except ValueError:
            continue
        partes.append(g)
    if not partes:
        return pd.DataFrame()
    z = pd.concat(partes)
    return z.groupby("qq").agg(n=("ok", "size"), ok=("ok", "mean"),
                               R=("R", "mean"), pnl=("pnl", "mean"),
                               risco=("risco", "mean"), v=(col, "mean"))


def avaliar(x, cols, alvo="ok", seed=0):
    tr, te, corte = split(x)
    m = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05,
                                       min_samples_leaf=60, l2_regularization=1.0,
                                       random_state=seed)
    m.fit(tr[cols].to_numpy(np.float64), tr[alvo])
    p = m.predict_proba(te[cols].to_numpy(np.float64))[:, 1]
    return roc_auc_score(te[alvo], p), corte, te, p


if __name__ == "__main__":
    pd.set_option("display.width", 240)
    dn, up = universo_rev()
    tudo = pd.concat([dn, up])
    print(f"universo de reversoes executaveis: {len(tudo)}  "
          f"(baixa {len(dn)}, alta {len(up)})   ok base = {tudo.ok.mean():.4f}")

    print("\n" + "=" * 78)
    print("PAINEL D1 -- fluxo, decis DENTRO da faixa de pavio")
    print("=" * 78)
    for col in ["a_favor", "imb", "contraste", "imb_perna", "div", "absorc",
                "vel_rel", "qtd_rel", "exaust", "z_qtd", "z_dur_s", "r_fluxo",
                "perna", "viradas20", "pos50", "tam"]:
        t = decis_ctrl(tudo, col)
        if t.empty:
            continue
        amp = t.ok.max() - t.ok.min()
        print(f"\n--- {col}   (amplitude ok = {amp:.3f})")
        print(t.round(3).to_string())

    print("\n" + "=" * 78)
    print("PAINEL D2 -- ML fora da amostra, dentro das reversoes")
    print("=" * 78)
    rng = np.random.default_rng(0)
    for nome, cols in (("geo (pavio+contexto)", GEO), ("fluxo", FLUXO),
                       ("geo+fluxo", GEO + FLUXO)):
        auc, corte, te, p = avaliar(tudo, cols)
        print(f"  {nome:<22} AUC = {auc:.4f}   (n_teste={len(te)}, corte {pd.Timestamp(corte).date()})")
    emb = tudo.copy()
    emb["ok"] = rng.permutation(emb["ok"].to_numpy())
    auc, *_ = avaliar(emb, GEO + FLUXO)
    print(f"  {'alvo embaralhado':<22} AUC = {auc:.4f}")
