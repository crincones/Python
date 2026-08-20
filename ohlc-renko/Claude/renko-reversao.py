#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
renko_reversao.py
=================
Estudo de pontos de virada em graficos Renko (ProfitChart / B3).

FORMULACAO B  -- antecipar a virada.
No fechamento do brick i (que ja tem run_len >= MIN_RUN_LEN bricks na mesma
direcao), estimar a probabilidade de que o PROXIMO evento seja uma REVERSAO
(brick contrario) e nao uma continuacao.

Rotulos disponiveis:
  rev_next : o proximo brick e contrario
  rev_conf : o proximo brick e contrario E o seguinte tambem e contrario
             (a virada "anda pelo menos mais 1 candle") -- padrao

Restricao de projeto: todas as features usadas pelo modelo exportado precisam
ser recalculaveis em NTSL em tempo real. Por isso:
  - nada de z-score global do dataset (usa media movel PASSADA de janela fixa)
  - nada de mediana movel (NTSL tem media, mediana e trabalhosa)
  - razoes adimensionais, clipadas, para nao explodir com outliers
  - todo rolling usa .shift(1) -> zero vazamento

Saidas em OUTDIR:
  features.csv          dataset completo com features e rotulos
  relatorio.md          relatorio textual com todas as estatisticas
  modelo_ntsl.txt       constantes + expressao do score prontos para NTSL
  modelo.json           coeficientes, scaler, config
  *.png                 graficos

Uso:
  python renko_reversao.py --csv renko_11R.csv
  python renko_reversao.py --csv renko_11R.csv --label rev_next --min-run 2
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scipy import stats

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.inspection import permutation_importance
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
CFG = {
    "csv_path": "renko_11R.csv",
    "sep": ";",
    "decimal": ",",
    "outdir": "saida_renko",

    "win_ma": 50,          # janela da media movel de normalizacao (bricks)
    "clip_ratio": 5.0,     # teto das razoes (evita outlier dominar o modelo)
    "min_run_len": 3,      # formulacao B: so avalia bricks com run >= isso
    "label": "rev_conf",   # rev_conf | rev_next

    # economia do trade (em BOXES; convertido para pontos com o box detectado)
    "target_boxes": 2.0,   # entrada no fech. do brick i, alvo = fech. do brick de virada
    "stop_boxes": 1.0,     # stop = 1 box (se vier continuacao, o brick fecha 1 box adiante)
    "custo_pontos": 0.0,   # slippage + corretagem por operacao, em pontos

    "test_frac_days": 0.30,  # ultimos 30% dos pregoes = out-of-sample
    "seed": 42,
}

FEATS = [
    # --- o proprio brick ---
    "wick_adv",        # pavio na direcao do movimento / box
    "wick_cnt",        # pavio contrario / box  (rejeicao)
    "rng",             # (max-min) / box        (extensao total)
    "delta_sig",       # (buy-sell)/(buy+sell) assinado na direcao do run
    "vol_rel",         # Quantity / media movel passada
    "trades_rel",      # Trades / media movel passada
    "avgtrade_rel",    # (Quantity/Trades) / media movel passada  -> lote medio
    "dur_rel",         # BarDurationF / media movel passada
    "speed_rel",       # (Quantity/dur) / media movel passada
    "absorcao",        # vol_rel * dur_rel  -> muito volume, muito tempo
    # --- a sequencia (run) ---
    "run_len",
    "run_delta_sum",   # soma dos delta_sig do run ate aqui
    "delta_vs_run",    # delta_sig - media dos anteriores do run  (divergencia)
    "vol_vs_run",
    "dur_vs_run",
    "wick_cnt_run",    # media do pavio contrario no run
    # --- brick anterior ---
    "delta_sig_p1",
    "rng_p1",
    # --- contexto ---
    "extremo_run",     # 0..1 : quanto o run empurrou o preco para o extremo do dia
    "hora_dec",
]


# --------------------------------------------------------------------------- #
# 1. CARGA
# --------------------------------------------------------------------------- #
def carregar(path, sep, decimal):
    df = pd.read_csv(path, sep=sep, decimal=decimal, engine="python")
    df.columns = [c.strip() for c in df.columns]

    ren = {}
    for c in df.columns:
        lc = c.lower()
        if lc.startswith("data"):            ren[c] = "ts"
        elif lc.startswith("abert"):         ren[c] = "open"
        elif lc.startswith(("max", "máx")):  ren[c] = "high"
        elif lc.startswith(("min", "mín")):  ren[c] = "low"
        elif lc.startswith("fech"):          ren[c] = "close"
        elif "buy" in lc:                    ren[c] = "abuy"
        elif "sell" in lc:                   ren[c] = "asell"
        elif "duration" in lc:               ren[c] = "dur"
        elif lc.startswith("quant"):         ren[c] = "qty"
        elif lc.startswith("trade") or lc.startswith("negoc"): ren[c] = "trades"
    df = df.rename(columns=ren)

    faltando = {"ts", "open", "high", "low", "close"} - set(df.columns)
    if faltando:
        sys.exit(f"[ERRO] colunas nao encontradas no CSV: {faltando}")

    df["ts"] = pd.to_datetime(df["ts"], dayfirst=True, format="mixed")
    for c in ["open", "high", "low", "close", "abuy", "asell", "dur", "qty", "trades"]:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                if df[c].dtype == object else df[c],
                errors="coerce")
        else:
            df[c] = np.nan

    # o CSV vem em ordem decrescente -> ordena cronologicamente
    df = df.sort_values("ts").reset_index(drop=True)

    # brick em formacao (ultima linha, duracao zerada) -> fora
    if len(df) and (df["dur"].iloc[-1] == 0 or pd.isna(df["dur"].iloc[-1])):
        df = df.iloc[:-1].reset_index(drop=True)

    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    return df


def detectar_box(df):
    corpo = (df["close"] - df["open"]).abs().round(6)
    corpo = corpo[corpo > 0]
    box = float(corpo.mode().iloc[0])
    frac = float((corpo == box).mean())
    return box, frac


# --------------------------------------------------------------------------- #
# 2. FEATURES  (tudo causal: nenhuma estatistica usa o proprio brick nem o futuro)
# --------------------------------------------------------------------------- #
def razao_movel(s, w, clip):
    """s / media movel dos w valores ANTERIORES. Clipada em [0, clip]."""
    base = s.shift(1).rolling(w, min_periods=max(10, w // 5)).mean()
    r = s / base.replace(0, np.nan)
    return r.clip(0, clip)


def construir_features(df, cfg):
    box = df.attrs["box"]
    w, clip = cfg["win_ma"], cfg["clip_ratio"]

    df["dir"] = np.sign(df["close"] - df["open"]).astype(int)
    df = df[df["dir"] != 0].reset_index(drop=True)

    up = df["dir"] > 0
    # pavio "a favor": alem do fechamento;  "contra": alem da abertura
    df["wick_adv"] = np.where(up, df["high"] - df["close"], df["close"] - df["low"]) / box
    df["wick_cnt"] = np.where(up, df["open"] - df["low"], df["high"] - df["open"]) / box
    df["rng"] = (df["high"] - df["low"]) / box

    tot = (df["abuy"] + df["asell"]).replace(0, np.nan)
    df["delta"] = ((df["abuy"] - df["asell"]) / tot).fillna(0.0)
    df["delta_sig"] = df["delta"] * df["dir"]          # >0 = agressao a favor do brick

    df["avgtrade"] = df["qty"] / df["trades"].replace(0, np.nan)
    df["speed"] = df["qty"] / df["dur"].replace(0, np.nan)

    df["vol_rel"] = razao_movel(df["qty"], w, clip)
    df["trades_rel"] = razao_movel(df["trades"], w, clip)
    df["avgtrade_rel"] = razao_movel(df["avgtrade"], w, clip)
    df["dur_rel"] = razao_movel(df["dur"], w, clip)
    df["speed_rel"] = razao_movel(df["speed"], w, clip)
    df["absorcao"] = (df["vol_rel"] * df["dur_rel"]).clip(0, clip * clip)

    # ---- run (sequencia de mesma cor) ----
    df["run_id"] = (df["dir"] != df["dir"].shift()).cumsum()
    g = df.groupby("run_id")
    df["run_len"] = g.cumcount() + 1
    df["run_delta_sum"] = g["delta_sig"].cumsum()

    def _vs_run(col):
        med = g[col].apply(lambda s: s.shift(1).expanding().mean()).reset_index(level=0, drop=True)
        return (df[col] - med).fillna(0.0)

    df["delta_vs_run"] = _vs_run("delta_sig")
    df["vol_vs_run"] = _vs_run("vol_rel")
    df["dur_vs_run"] = _vs_run("dur_rel")
    df["wick_cnt_run"] = g["wick_cnt"].apply(lambda s: s.expanding().mean()).reset_index(level=0, drop=True)

    # ---- brick anterior, projetado na direcao do run atual ----
    df["delta_sig_p1"] = (df["delta"].shift(1) * df["dir"]).fillna(0.0)
    df["rng_p1"] = df["rng"].shift(1).fillna(df["rng"].median())

    # ---- contexto de sessao ----
    df["dia"] = df["ts"].dt.normalize()
    gd = df.groupby("dia")
    hi = gd["high"].cummax()
    lo = gd["low"].cummin()
    pos = ((df["close"] - lo) / (hi - lo).replace(0, np.nan)).fillna(0.5)
    df["extremo_run"] = np.where(up, pos, 1.0 - pos)
    df["hora_dec"] = df["ts"].dt.hour + df["ts"].dt.minute / 60.0
    df["brick_do_dia"] = gd.cumcount() + 1

    return df


# --------------------------------------------------------------------------- #
# 3. ROTULOS
# --------------------------------------------------------------------------- #
def construir_rotulos(df):
    d0, d1, d2 = df["dir"], df["dir"].shift(-1), df["dir"].shift(-2)
    df["rev_next"] = (d1 != d0).astype(float)
    df["rev_conf"] = ((d1 != d0) & (d2 == d1)).astype(float)
    df.loc[df.index[-2:], ["rev_next", "rev_conf"]] = np.nan

    # tamanho do run seguinte (quantos bricks a virada anda) -> qualidade do sinal
    tam = df.groupby("run_id")["run_len"].max()
    prox = df["run_id"].map(lambda r: tam.get(r + 1, np.nan))
    ultimo_do_run = df["run_len"] == df["run_id"].map(tam)
    df["bricks_pos_virada"] = np.where(ultimo_do_run, prox, 0.0)
    return df


# --------------------------------------------------------------------------- #
# 4. ECONOMIA
# --------------------------------------------------------------------------- #
def expectativa(p, cfg, box):
    alvo = cfg["target_boxes"] * box - cfg["custo_pontos"]
    stop = cfg["stop_boxes"] * box + cfg["custo_pontos"]
    return p * alvo - (1 - p) * stop


def prob_breakeven(cfg, box):
    alvo = cfg["target_boxes"] * box - cfg["custo_pontos"]
    stop = cfg["stop_boxes"] * box + cfg["custo_pontos"]
    return stop / (alvo + stop)


# --------------------------------------------------------------------------- #
# 5. MODELOS
# --------------------------------------------------------------------------- #
def padronizar(Xtr, Xte):
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0).replace(0, 1.0)
    return (Xtr - mu) / sd, (Xte - mu) / sd, mu, sd


def treinar(Xtr, ytr, Xte, yte, Xtr_r, Xte_r, seed):
    """Xtr/Xte padronizados (logistica). Xtr_r/Xte_r crus (arvore e gbm:
    nao precisam de escala, e assim os cortes saem em unidade real,
    prontos para virar if/else no NTSL)."""
    res = {}

    melhor, melhor_auc = None, -1
    for C in [0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0]:
        aucs = []
        for itr, iva in TimeSeriesSplit(n_splits=4).split(Xtr):
            m = LogisticRegression(C=C, max_iter=3000, class_weight="balanced")
            m.fit(Xtr.iloc[itr], ytr.iloc[itr])
            if ytr.iloc[iva].nunique() < 2:
                continue
            aucs.append(roc_auc_score(ytr.iloc[iva], m.predict_proba(Xtr.iloc[iva])[:, 1]))
        a = np.mean(aucs) if aucs else 0.5
        if a > melhor_auc:
            melhor_auc, melhor = a, C

    log = LogisticRegression(C=melhor, max_iter=3000, class_weight="balanced").fit(Xtr, ytr)
    res["logistica"] = {"modelo": log, "C": melhor, "auc_cv": melhor_auc}

    arv = DecisionTreeClassifier(max_depth=3, min_samples_leaf=max(50, len(Xtr) // 40),
                                 class_weight="balanced", random_state=seed).fit(Xtr_r, ytr)
    res["arvore"] = {"modelo": arv, "cru": True}

    gb = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05,
                                        l2_regularization=1.0, random_state=seed).fit(Xtr_r, ytr)
    res["gbm"] = {"modelo": gb, "cru": True}

    for k, v in res.items():
        p = v["modelo"].predict_proba(Xte_r if v.get("cru") else Xte)[:, 1]
        v["p_test"] = p
        v["auc"] = roc_auc_score(yte, p) if yte.nunique() > 1 else np.nan
        v["brier"] = brier_score_loss(yte, p)
    return res


def tabela_decis(p, y, extra, cfg, box, n=10):
    d = pd.DataFrame({"p": p, "y": y.values, "bricks": extra.values})
    d["decil"] = pd.qcut(d["p"].rank(method="first"), n, labels=False) + 1
    t = d.groupby("decil").agg(n=("y", "size"), taxa=("y", "mean"),
                               p_med=("p", "mean"), bricks_med=("bricks", "median"))
    t["lift"] = t["taxa"] / d["y"].mean()
    t["exp_pts"] = expectativa(t["taxa"], cfg, box)
    return t


def curva_threshold(p, y, cfg, box):
    linhas = []
    for th in np.arange(0.05, 0.96, 0.025):
        sel = p >= th
        if sel.sum() < 20:
            continue
        taxa = y.values[sel].mean()
        linhas.append({"th": th, "n": int(sel.sum()), "cobertura": sel.mean(),
                       "acerto": taxa, "exp_pts": expectativa(taxa, cfg, box),
                       "total_pts": expectativa(taxa, cfg, box) * sel.sum()})
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------- #
# 6. GRAFICOS
# --------------------------------------------------------------------------- #
def salvar(fig, outdir, nome):
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, nome), dpi=120)
    plt.close(fig)


def graficos(df, ev, res, Xte, yte, tdec, tth, outdir, cfg, box, imps):
    lab = cfg["label"]

    # taxa base por comprimento do run
    t = df.dropna(subset=[lab]).groupby("run_len")[lab].agg(["mean", "size"])
    t = t[t["size"] >= 30]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(t.index, t["mean"], color="#4472c4")
    ax.axhline(prob_breakeven(cfg, box), color="crimson", ls="--",
               label=f"breakeven = {prob_breakeven(cfg, box):.1%}")
    for x, (m, s) in t.iterrows():
        ax.text(x, m, f"n={int(s)}", ha="center", va="bottom", fontsize=7)
    ax.set_xlabel("comprimento da sequencia (bricks)")
    ax.set_ylabel(f"P({lab})")
    ax.set_title("Taxa base de reversao por comprimento do run")
    ax.legend()
    salvar(fig, outdir, "01_taxa_base_por_runlen.png")

    # distribuicoes das features por classe
    top = imps.head(9).index.tolist()
    fig, axes = plt.subplots(3, 3, figsize=(13, 9))
    for a, f in zip(axes.ravel(), top):
        d0 = ev.loc[ev[lab] == 0, f].dropna()
        d1 = ev.loc[ev[lab] == 1, f].dropna()
        lo, hi = np.percentile(pd.concat([d0, d1]), [1, 99])
        bins = np.linspace(lo, hi, 40)
        a.hist(d0, bins=bins, alpha=.55, density=True, label="continua", color="#888")
        a.hist(d1, bins=bins, alpha=.55, density=True, label="reverte", color="#c0392b")
        u = stats.mannwhitneyu(d0, d1)[1] if len(d0) and len(d1) else np.nan
        a.set_title(f"{f}  (p={u:.1e})", fontsize=9)
        a.tick_params(labelsize=7)
    axes.ravel()[0].legend(fontsize=8)
    fig.suptitle("Distribuicao das features por classe (amostra completa)")
    salvar(fig, outdir, "02_features_por_classe.png")

    # ROC
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    for k, v in res.items():
        fpr, tpr, _ = roc_curve(yte, v["p_test"])
        ax.plot(fpr, tpr, label=f"{k}  AUC={v['auc']:.3f}")
    ax.plot([0, 1], [0, 1], "k--", lw=.8)
    ax.set_xlabel("FPR"); ax.set_ylabel("TPR"); ax.set_title("ROC - out-of-sample")
    ax.legend()
    salvar(fig, outdir, "03_roc.png")

    # calibracao
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    for k, v in res.items():
        try:
            pt, pp = calibration_curve(yte, v["p_test"], n_bins=8, strategy="quantile")
            ax.plot(pp, pt, "o-", label=k)
        except Exception:
            pass
    ax.plot([0, 1], [0, 1], "k--", lw=.8)
    ax.set_xlabel("prob. prevista"); ax.set_ylabel("frequencia real")
    ax.set_title("Calibracao - out-of-sample"); ax.legend()
    salvar(fig, outdir, "04_calibracao.png")

    # lift por decil
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    a1.bar(tdec.index, tdec["taxa"], color="#4472c4")
    a1.axhline(yte.mean(), color="k", ls="--", label="taxa base")
    a1.axhline(prob_breakeven(cfg, box), color="crimson", ls="--", label="breakeven")
    a1.set_xlabel("decil do score"); a1.set_ylabel("taxa de reversao"); a1.legend(fontsize=8)
    a1.set_title("Acerto por decil (logistica, OOS)")
    a2.bar(tdec.index, tdec["exp_pts"], color="#2e8b57")
    a2.axhline(0, color="k", lw=.8)
    a2.set_xlabel("decil do score"); a2.set_ylabel("expectativa (pontos/trade)")
    a2.set_title("Expectativa por decil")
    salvar(fig, outdir, "05_decis.png")

    # expectativa x threshold
    if len(tth):
        fig, a1 = plt.subplots(figsize=(8, 4.5))
        a1.plot(tth["th"], tth["exp_pts"], color="#2e8b57", label="pontos/trade")
        a1.axhline(0, color="k", lw=.8)
        a1.set_xlabel("threshold do score"); a1.set_ylabel("expectativa (pontos/trade)")
        a2 = a1.twinx()
        a2.plot(tth["th"], tth["cobertura"], color="#888", ls=":", label="cobertura")
        a2.set_ylabel("fracao de sinais disparados")
        a1.set_title("Expectativa e cobertura por threshold (OOS)")
        salvar(fig, outdir, "06_threshold.png")

    # correlacao
    fig, ax = plt.subplots(figsize=(9, 8))
    c = ev[FEATS].corr()
    im = ax.imshow(c, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(FEATS))); ax.set_xticklabels(FEATS, rotation=90, fontsize=7)
    ax.set_yticks(range(len(FEATS))); ax.set_yticklabels(FEATS, fontsize=7)
    fig.colorbar(im, shrink=.7); ax.set_title("Correlacao entre features")
    salvar(fig, outdir, "07_correlacao.png")

    # importancia
    fig, ax = plt.subplots(figsize=(7, 6))
    imps.sort_values().plot.barh(ax=ax, color="#4472c4")
    ax.set_xlabel("queda de AUC ao embaralhar (permutation importance, OOS)")
    ax.set_title("Importancia das features")
    salvar(fig, outdir, "08_importancia.png")

    # quantos bricks a virada anda, por decil
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(tdec.index, tdec["bricks_med"], color="#8e44ad")
    ax.set_xlabel("decil do score"); ax.set_ylabel("mediana de bricks apos a virada")
    ax.set_title("Qualidade do movimento por decil (0 = nao reverteu)")
    salvar(fig, outdir, "09_bricks_pos_virada.png")


# --------------------------------------------------------------------------- #
# 7. EXPORTACAO PARA NTSL
# --------------------------------------------------------------------------- #
NTSL_TMPL = """//////////////////////////////////////////////////////////////////////////////
// Score de reversao Renko -- constantes geradas por renko_reversao.py
// Gerado em {agora}
// Rotulo: {label} | box detectado: {box:g} | janela de normalizacao: {w} bricks
// AUC out-of-sample: {auc:.4f} | taxa base: {base:.4f}
//
// O score abaixo e o LOGITO (z). Probabilidade = 1/(1+exp(-z)).
// Para evitar depender de Exp() no NTSL, compare z direto com o limiar:
//   z >= {z_th:.4f}  <=>  p >= {p_th:.2f}
//
// Padronizacao: cada feature entra como (valor - MEDIA) / DESVIO,
// com MEDIA/DESVIO abaixo (calculados APENAS no periodo de treino).
//////////////////////////////////////////////////////////////////////////////

// intercepto
// z := {b0:.6f}
{linhas}

// ---- limiares sugeridos (out-of-sample) ----
{limiares}
"""


def exportar_ntsl(res, mu, sd, cfg, box, base, outdir, tth):
    regras = export_text(res["arvore"]["modelo"], feature_names=FEATS, decimals=4)
    log = res["logistica"]["modelo"]
    coef = pd.Series(log.coef_[0], index=FEATS)
    b0 = float(log.intercept_[0])

    linhas = []
    for f in FEATS:
        linhas.append(f"// z := z + {coef[f]: .6f} * (({f}) - {mu[f]:.6f}) / {sd[f]:.6f};")
    p_th = 0.5
    if len(tth):
        p_th = float(tth.loc[tth["total_pts"].idxmax(), "th"])
    z_th = float(np.log(p_th / (1 - p_th)))

    lim = []
    for th in [0.4, 0.5, 0.6, 0.7]:
        r = tth.loc[(tth["th"] - th).abs().idxmin()] if len(tth) else None
        if r is not None:
            lim.append(f"// p>={th:.2f} (z>={np.log(th/(1-th)):+.4f}): "
                       f"acerto={r['acerto']:.1%}, cobertura={r['cobertura']:.1%}, "
                       f"expectativa={r['exp_pts']:+.1f} pts")
    txt = NTSL_TMPL.format(agora=datetime.now().strftime("%d/%m/%Y %H:%M"),
                           label=cfg["label"], box=box, w=cfg["win_ma"],
                           auc=res["logistica"]["auc"], base=base,
                           z_th=z_th, p_th=p_th, b0=b0,
                           linhas="\n".join(linhas), limiares="\n".join(lim))
    txt += ("\n\n// ---- alternativa: arvore de decisao (cortes em unidade REAL,\n"
            "// nao padronizada -- da para transcrever direto como if/else) ----\n"
            + "\n".join("// " + l for l in regras.splitlines()) + "\n")
    with open(os.path.join(outdir, "modelo_ntsl.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)

    with open(os.path.join(outdir, "modelo.json"), "w", encoding="utf-8") as fh:
        json.dump({"config": cfg, "box": box, "intercepto": b0,
                   "coeficientes": coef.to_dict(),
                   "media": mu.to_dict(), "desvio": sd.to_dict(),
                   "auc_oos": float(res["logistica"]["auc"]),
                   "taxa_base": float(base),
                   "threshold_sugerido": p_th}, fh, indent=2, ensure_ascii=False)
    return coef, b0, p_th


# --------------------------------------------------------------------------- #
# 8. MAIN
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CFG["csv_path"])
    ap.add_argument("--outdir", default=CFG["outdir"])
    ap.add_argument("--label", default=CFG["label"], choices=["rev_conf", "rev_next"])
    ap.add_argument("--min-run", type=int, default=CFG["min_run_len"])
    ap.add_argument("--win", type=int, default=CFG["win_ma"])
    ap.add_argument("--custo", type=float, default=CFG["custo_pontos"])
    a = ap.parse_args()

    cfg = dict(CFG, csv_path=a.csv, outdir=a.outdir, label=a.label,
               min_run_len=a.min_run, win_ma=a.win, custo_pontos=a.custo)
    os.makedirs(cfg["outdir"], exist_ok=True)
    lab = cfg["label"]

    print("[1/6] carregando...")
    df = carregar(cfg["csv_path"], cfg["sep"], cfg["decimal"])
    box, frac = detectar_box(df)
    df.attrs["box"] = box
    print(f"      {len(df)} bricks | {df['ts'].dt.date.nunique()} pregoes | "
          f"box={box:g} ({frac:.1%} dos corpos)")

    print("[2/6] features e rotulos...")
    df = construir_features(df, cfg)
    df = construir_rotulos(df)
    df.to_csv(os.path.join(cfg["outdir"], "features.csv"), sep=";", decimal=",", index=False)

    ev = df[(df["run_len"] >= cfg["min_run_len"]) & df[lab].notna()].dropna(subset=FEATS).copy()
    if len(ev) < 300:
        sys.exit(f"[ERRO] apenas {len(ev)} eventos com run>={cfg['min_run_len']}. "
                 f"Reduza --min-run.")
    print(f"      {len(ev)} eventos | taxa base = {ev[lab].mean():.3f}")

    print("[3/6] split temporal...")
    dias = np.sort(ev["dia"].unique())
    corte = dias[int(len(dias) * (1 - cfg["test_frac_days"]))]
    tr, te = ev[ev["dia"] < corte], ev[ev["dia"] >= corte]
    Xtr_r, Xte_r = tr[FEATS], te[FEATS]
    ytr, yte = tr[lab], te[lab]
    Xtr, Xte, mu, sd = padronizar(Xtr_r, Xte_r)
    print(f"      treino: {len(tr)} ({tr['dia'].nunique()} pregoes)  "
          f"teste: {len(te)} ({te['dia'].nunique()} pregoes, a partir de {pd.Timestamp(corte).date()})")

    print("[4/6] modelos...")
    res = treinar(Xtr, ytr, Xte, yte, Xtr_r, Xte_r, cfg["seed"])
    for k, v in res.items():
        print(f"      {k:11s} AUC={v['auc']:.4f}  Brier={v['brier']:.4f}")

    pi = permutation_importance(res["logistica"]["modelo"], Xte, yte,
                                scoring="roc_auc", n_repeats=15, random_state=cfg["seed"])
    imps = pd.Series(pi.importances_mean, index=FEATS).sort_values(ascending=False)

    p = res["logistica"]["p_test"]
    tdec = tabela_decis(p, yte, te["bricks_pos_virada"], cfg, box)
    tth = curva_threshold(p, yte, cfg, box)

    print("[5/6] graficos...")
    graficos(df, ev, res, Xte, yte, tdec, tth, cfg["outdir"], cfg, box, imps)

    print("[6/6] relatorio + export NTSL...")
    coef, b0, p_th = exportar_ntsl(res, mu, sd, cfg, box, yte.mean(), cfg["outdir"], tth)
    escrever_relatorio(df, ev, tr, te, res, imps, coef, b0, tdec, tth,
                       cfg, box, frac, p_th)
    print(f"\nPronto. Saidas em: {os.path.abspath(cfg['outdir'])}")


def escrever_relatorio(df, ev, tr, te, res, imps, coef, b0, tdec, tth, cfg, box, frac, p_th):
    lab = cfg["label"]
    L = []
    A = L.append
    A(f"# Estudo de pontos de virada em Renko\n")
    A(f"Gerado em {datetime.now():%d/%m/%Y %H:%M} | rotulo `{lab}` | "
      f"formulacao B (antecipar a virada)\n")

    A("## 1. Base\n")
    A(f"- bricks validos: **{len(df)}**")
    A(f"- pregoes: **{df['ts'].dt.date.nunique()}** "
      f"({df['ts'].min():%d/%m/%Y} a {df['ts'].max():%d/%m/%Y})")
    A(f"- box detectado: **{box:g} pontos** (corpo constante em {frac:.1%} dos bricks)")
    A(f"- reversao no Renko custa **{2*box:g} pontos** de deslocamento real")
    A(f"- eventos com run >= {cfg['min_run_len']}: **{len(ev)}** "
      f"({len(ev)/len(df):.1%} dos bricks)")
    A(f"- taxa base de `{lab}` nesses eventos: **{ev[lab].mean():.3f}**")
    A(f"- probabilidade de breakeven (alvo {cfg['target_boxes']:g} box / "
      f"stop {cfg['stop_boxes']:g} box, custo {cfg['custo_pontos']:g} pts): "
      f"**{prob_breakeven(cfg, box):.3f}**\n")

    A("## 2. Taxa base por comprimento da sequencia\n")
    t = df.dropna(subset=[lab]).groupby("run_len")[lab].agg(["size", "mean"])
    t = t[t["size"] >= 30]
    A("| run_len | n | P(reversao) | IC95% |")
    A("|---|---|---|---|")
    for k, r in t.iterrows():
        lo, hi = stats.beta.interval(.95, r["mean"]*r["size"]+.5,
                                     (1-r["mean"])*r["size"]+.5)
        A(f"| {k} | {int(r['size'])} | {r['mean']:.3f} | {lo:.3f} – {hi:.3f} |")
    A("")

    A("## 3. Poder discriminante de cada feature (amostra completa)\n")
    A("Mann-Whitney entre os grupos reverte / continua. p pequeno = separa.\n")
    A("| feature | media (continua) | media (reverte) | p |")
    A("|---|---|---|---|")
    linhas = []
    for f in FEATS:
        d0 = ev.loc[ev[lab] == 0, f].dropna()
        d1 = ev.loc[ev[lab] == 1, f].dropna()
        pv = stats.mannwhitneyu(d0, d1)[1] if len(d0) and len(d1) else np.nan
        linhas.append((f, d0.mean(), d1.mean(), pv))
    for f, m0, m1, pv in sorted(linhas, key=lambda x: x[3]):
        A(f"| `{f}` | {m0:.4f} | {m1:.4f} | {pv:.2e} |")
    A("")

    A("## 4. Modelos (out-of-sample)\n")
    A(f"Treino: {tr['dia'].nunique()} pregoes / {len(tr)} eventos. "
      f"Teste: {te['dia'].nunique()} pregoes / {len(te)} eventos.\n")
    A("| modelo | AUC | Brier | exportavel p/ NTSL |")
    A("|---|---|---|---|")
    exp = {"logistica": "sim (soma linear)", "arvore": "sim (if/else)", "gbm": "nao"}
    for k, v in res.items():
        A(f"| {k} | {v['auc']:.4f} | {v['brier']:.4f} | {exp[k]} |")
    A("\nO GBM serve so de teto de referencia: se ele nao supera a logistica "
      "com folga, nao ha nao-linearidade relevante a capturar e a logistica "
      "e a escolha certa.\n")

    A("## 5. Coeficientes da logistica (features padronizadas)\n")
    A(f"intercepto = {b0:+.6f}\n")
    A("| feature | coef | importancia (perm.) |")
    A("|---|---|---|")
    for f in coef.abs().sort_values(ascending=False).index:
        A(f"| `{f}` | {coef[f]:+.4f} | {imps[f]:+.4f} |")
    A("\nCoeficiente positivo = valor alto da feature **aumenta** a chance de reversao.\n")

    A("## 6. Arvore de decisao (profundidade 3)\n")
    A("```")
    A(export_text(res["arvore"]["modelo"], feature_names=FEATS, decimals=3))
    A("```\n")

    A("## 7. Desempenho por decil do score\n")
    A("| decil | n | p media | acerto real | lift | expectativa (pts) | bricks pos-virada (mediana) |")
    A("|---|---|---|---|---|---|---|")
    for k, r in tdec.iterrows():
        A(f"| {k} | {int(r['n'])} | {r['p_med']:.3f} | {r['taxa']:.3f} | "
          f"{r['lift']:.2f}x | {r['exp_pts']:+.1f} | {r['bricks_med']:.1f} |")
    A("")

    A("## 8. Escolha do threshold\n")
    if len(tth):
        A("| threshold | sinais | cobertura | acerto | pts/trade | pts totais |")
        A("|---|---|---|---|---|---|")
        for _, r in tth.iterrows():
            A(f"| {r['th']:.3f} | {int(r['n'])} | {r['cobertura']:.1%} | "
              f"{r['acerto']:.3f} | {r['exp_pts']:+.1f} | {r['total_pts']:+.0f} |")
        A(f"\nThreshold que maximiza pontos totais no out-of-sample: **{p_th:.3f}**\n")
    else:
        A("Poucos eventos para varrer thresholds.\n")

    A("## 9. Leitura critica\n")
    A(f"- Se a AUC out-of-sample estiver abaixo de ~0.55, o sinal nao existe "
      f"nas features agregadas por brick e nao adianta insistir no modelo.")
    A(f"- O que decide nao e a AUC e sim se algum decil superior fica acima "
      f"de {prob_breakeven(cfg, box):.1%} de acerto com cobertura utilizavel.")
    A(f"- Todas as estatisticas moveis usam janela de {cfg['win_ma']} bricks "
      f"com `shift(1)`: nenhuma feature enxerga o proprio brick nem o futuro.")
    A(f"- A padronizacao usa media/desvio do **treino** e esta exportada em "
      f"`modelo_ntsl.txt`; o NTSL precisa usar exatamente esses numeros.")
    A(f"- Limite conhecido: o CSV agregado nao guarda a ORDEM da agressao "
      f"dentro do brick. Exaustao (compra no inicio, venda no fim) e "
      f"continuacao tem o mesmo `AgressionVolBuy`.\n")

    with open(os.path.join(cfg["outdir"], "relatorio.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


if __name__ == "__main__":
    main()