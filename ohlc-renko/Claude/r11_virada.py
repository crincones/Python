#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r11_virada.py -- Estudo preditivo de pontos de virada em Renko R11 (WINFUT / ProfitChart)

FORMULACAO A (a mesma do estudo MQL5, e a que da entrada operavel):
  No FECHAMENTO de um brick CONTRARIO a uma sequencia de >= MIN_SEQ bricks
  (o "brick elegivel"), estimar a probabilidade de que ele inicie uma PERNA de
  K bricks na nova direcao ANTES que o preco devolva 2 corpos.

  Entrada: no fechamento do brick elegivel, na direcao dele.
  Alvo   : (K-1) corpos a favor.     Stop: 2 corpos contra.
  => breakeven = 2/(K-1+2). Para K=4: 0.400.

Restricao de projeto: TODA feature tem de ser recalculavel em NTSL em tempo real.
  - nenhuma mediana (NTSL nao tem; media de janela do MESMO TIPO de brick)
  - nenhum log (razoes entram como (v-m)/(v+m), monotona em log(v/m) e limitada)
  - todo rolling caminha para tras e para no proprio brick: zero lookahead

Saidas em OUTDIR:
  relatorio.md        estudo completo
  modelo_ntsl.txt     constantes do modelo
  RenkoViradaR11.src  indicador NTSL pronto
  features.csv        dataset
  *.png               graficos
"""

import argparse
import json
import os
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss, roc_curve
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")

CSV_DEFAULT = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv"

TICK = 5.0          # tick do WIN em pontos
BODY_TICKS = 10     # corpo do brick R11 (R-1, padrao Nelogica)
BODY_PTS = BODY_TICKS * TICK
REF_N = 20          # bricks do MESMO TIPO na janela de referencia
REG_N = 40          # janela de regime
LOOKBACK_CAP = 400  # teto de varredura para tras (limite duro no NTSL tambem)
DUR_FLOOR = 0.01    # BarDurationF e quantizado em 0.01 min (0.6 s)


# --------------------------------------------------------------------------- #
# 1. CARGA E SANEAMENTO
# --------------------------------------------------------------------------- #
def carregar(csv):
    raw = pd.read_csv(csv, sep=";", decimal=",", encoding="utf-8-sig",
                      engine="python", on_bad_lines="skip")
    raw.columns = [c.strip() for c in raw.columns]
    ren = {}
    for c in raw.columns:
        cl = c.lower()
        if cl.startswith("data"):
            ren[c] = "dt"
        elif cl.startswith("abert"):
            ren[c] = "o"
        elif "xima" in cl and cl[1] == "\u00e1" or cl.startswith("m\u00e1x") or cl.startswith("max"):
            ren[c] = "h"
        elif cl.startswith("m\u00edn") or cl.startswith("min"):
            ren[c] = "l"
        elif cl.startswith("fech"):
            ren[c] = "c"
        elif cl == "agressionvolbuy":
            ren[c] = "agb"
        elif cl == "agressionvolsell":
            ren[c] = "ags"
        elif cl.startswith("bardur"):
            ren[c] = "dur"
        elif cl == "quantity":
            ren[c] = "qt"
        elif cl == "trades":
            ren[c] = "trd"
    raw = raw.rename(columns=ren)
    cols = ["dt", "o", "h", "l", "c", "agb", "ags", "dur", "qt", "trd"]
    raw = raw[[c for c in cols if c in raw.columns]].dropna(subset=["dt", "o", "c"])
    raw["dt"] = pd.to_datetime(raw["dt"], format="%d/%m/%Y %H:%M:%S.%f", errors="coerce")
    raw = raw.dropna(subset=["dt"])
    for k in cols[1:]:
        raw[k] = pd.to_numeric(raw[k], errors="coerce")
    raw = raw.dropna().sort_values("dt", kind="stable").reset_index(drop=True)

    # a ultima barra do arquivo esta EM FORMACAO (corpo incompleto) -> fora
    body = (raw.c - raw.o).abs()
    while len(raw) and abs(body.iloc[-1] - BODY_PTS) > 1e-9:
        raw = raw.iloc[:-1].reset_index(drop=True)
        body = (raw.c - raw.o).abs()
    return raw


def geometria(df):
    n = len(df)
    o, c, h, l = df.o.values, df.c.values, df.h.values, df.l.values
    dirn = np.where(c > o, 1, -1)
    df["dirn"] = dirn

    is_rev = np.zeros(n, dtype=int)
    is_rev[1:] = (dirn[1:] != dirn[:-1]).astype(int)
    df["is_rev"] = is_rev

    seq = np.ones(n, dtype=int)
    for i in range(1, n):
        seq[i] = seq[i - 1] + 1 if dirn[i] == dirn[i - 1] else 1
    df["seq_before"] = np.r_[0, seq[:-1]]

    # pavio do lado da origem, em ticks
    df["wick"] = np.where(dirn > 0, (o - l) / TICK, (h - o) / TICK)
    # excedente sobre o piso estrutural: reversao carrega 10 ticks de construcao
    df["wick_net"] = df.wick - np.where(is_rev == 1, BODY_TICKS, 0)
    df["trav"] = np.where(is_rev == 1, 2 * BODY_TICKS, BODY_TICKS) + df.wick_net.clip(lower=0)

    # encadeamento quebrado: o brick nao abre nem no close nem no open do anterior
    okc = np.r_[True, np.abs(o[1:] - c[:-1]) < 1e-9]
    oko = np.r_[True, np.abs(o[1:] - o[:-1]) < 1e-9]
    df["brk"] = (~(okc | oko)).astype(int)

    newday = df.dt.dt.date.values
    df["newday"] = np.r_[True, newday[1:] != newday[:-1]].astype(int)

    # brick "sujo": sem volume, ou rajada de preenchimento de gap, ou virada de pregao
    df["sujo"] = ((df.qt <= 0) | (df.brk == 1) | (df.newday == 1) |
                  (df.dur > 60)).astype(int)
    df["ok"] = 1 - df.sujo

    df["dur_eff"] = df.dur.clip(lower=DUR_FLOOR)
    df["agtot"] = df.agb + df.ags
    df["unk_share"] = np.where(df.qt > 0, (df.qt - df.agtot).clip(lower=0) / df.qt, 0.0)
    df["avg_trd"] = np.where(df.trd > 0, df.qt / df.trd, 0.0)
    df["hora"] = df.dt.dt.hour + df.dt.dt.minute / 60.0
    return df


# --------------------------------------------------------------------------- #
# 2. FEATURES  (caminhada para tras, identica a que o NTSL vai fazer)
# --------------------------------------------------------------------------- #
def nz(v, m):
    """razao limitada em (-1,1), monotona em log(v/m). NTSL: so aritmetica."""
    s = v + m
    return np.where(s > 1e-12, (v - m) / s, 0.0)


def media_mesmo_tipo(vals, ok, is_rev, i, tipo, n_ref, cap=LOOKBACK_CAP):
    """media dos n_ref bricks OK anteriores a i com is_rev == tipo. -1 se nao houver."""
    s, k, j = 0.0, 0, i - 1
    lim = max(0, i - cap)
    while j >= lim and k < n_ref:
        if ok[j] and is_rev[j] == tipo:
            s += vals[j]
            k += 1
        j -= 1
    return s / k if k == n_ref else -1.0


def construir_features(df):
    n = len(df)
    ok = df.ok.values.astype(bool)
    isr = df.is_rev.values
    dirn = df.dirn.values
    qt, trd, dur, agb, ags = (df.qt.values, df.trd.values, df.dur_eff.values,
                              df.agb.values, df.ags.values)
    agtot = df.agtot.values
    trav = df.trav.values
    wick = df.wick.values
    wick_net = df.wick_net.values
    unk = df.unk_share.values
    avg_trd = df.avg_trd.values
    c, h, l, o = df.c.values, df.h.values, df.l.values, df.o.values
    seq_b = df.seq_before.values
    hora = df.hora.values
    dayid = pd.factorize(df.dt.dt.date)[0]

    cost = qt / trav                 # contratos por tick percorrido
    pace = trav / dur                # ticks por minuto
    F = {k: np.full(n, np.nan) for k in [
        "cost_nz", "dur_nz", "trd_nz", "size_nz", "pace_nz",
        "delta_cl", "delta_raw", "unk_nz", "wick_net_n", "seq_len",
        "rev_dens", "eff_ratio", "pace_reg", "pos_rng", "day_pos", "hora_dec",
        "cost_seq", "dur_seq", "delta_seq", "wick_seq", "ref_ok"]}

    for i in range(n):
        if not ok[i] or isr[i] != 1:
            continue
        t = 1  # brick elegivel e sempre reversao -> referencia so de reversoes
        m_cost = media_mesmo_tipo(cost, ok, isr, i, t, REF_N)
        m_dur = media_mesmo_tipo(dur, ok, isr, i, t, REF_N)
        m_trd = media_mesmo_tipo(trd, ok, isr, i, t, REF_N)
        m_siz = media_mesmo_tipo(avg_trd, ok, isr, i, t, REF_N)
        m_pac = media_mesmo_tipo(pace, ok, isr, i, t, REF_N)
        m_unk = media_mesmo_tipo(unk, ok, isr, i, t, REF_N)
        if min(m_cost, m_dur, m_trd, m_siz, m_pac) <= 0:
            F["ref_ok"][i] = 0
            continue
        F["ref_ok"][i] = 1

        F["cost_nz"][i] = nz(cost[i], m_cost)
        F["dur_nz"][i] = nz(dur[i], m_dur)
        F["trd_nz"][i] = nz(trd[i], m_trd)
        F["size_nz"][i] = nz(avg_trd[i], m_siz)
        F["pace_nz"][i] = nz(pace[i], m_pac)
        F["unk_nz"][i] = nz(unk[i], m_unk) if m_unk > 0 else 0.0

        d = dirn[i]
        F["delta_cl"][i] = d * (agb[i] - ags[i]) / agtot[i] if agtot[i] > 0 else 0.0
        F["delta_raw"][i] = d * (agb[i] - ags[i]) / qt[i] if qt[i] > 0 else 0.0
        F["wick_net_n"][i] = wick_net[i] / BODY_TICKS
        F["seq_len"][i] = seq_b[i]
        F["hora_dec"][i] = hora[i]

        # ---- regime: ultimos REG_N bricks anteriores ----
        lo = max(0, i - REG_N)
        if i - lo >= REG_N:
            sl = slice(lo, i)
            F["rev_dens"][i] = isr[sl].mean()
            desl = abs(c[i - 1] - o[lo]) / BODY_PTS
            F["eff_ratio"][i] = desl / REG_N
            hi_r, lo_r = h[sl].max(), l[sl].min()
            F["pos_rng"][i] = (d * (c[i] - (hi_r + lo_r) / 2.0)) / max(hi_r - lo_r, BODY_PTS)
            # pace do regime: ticks/min dos REG_N contra a referencia longa
            tt = trav[sl].sum()
            dd = max(dur[sl].sum(), DUR_FLOOR)
            lo2 = max(0, i - 4 * REG_N)
            tt2 = trav[lo2:i].sum()
            dd2 = max(dur[lo2:i].sum(), DUR_FLOOR)
            F["pace_reg"][i] = nz(tt / dd, tt2 / dd2)

        # ---- posicao no dia ----
        d0 = np.searchsorted(dayid, dayid[i], side="left")
        if i - d0 >= 5:
            hi_d, lo_d = h[d0:i + 1].max(), l[d0:i + 1].min()
            rng = max(hi_d - lo_d, BODY_PTS)
            F["day_pos"][i] = d * (c[i] - (hi_d + lo_d) / 2.0) / rng

        # ---- exaustao da perna contrariada (os seq_b bricks anteriores) ----
        k = int(seq_b[i])
        if 2 <= k <= 30 and i - k >= 0:
            sl = slice(i - k, i)
            half = max(1, k // 2)
            c1, c2 = cost[i - k:i - k + half], cost[i - half:i]
            d1, d2 = dur[i - k:i - k + half], dur[i - half:i]
            F["cost_seq"][i] = nz(c2.mean(), c1.mean())
            F["dur_seq"][i] = nz(d2.mean(), d1.mean())
            sg = -d  # a perna ia na direcao contraria a deste brick
            den = agtot[sl].sum()
            F["delta_seq"][i] = sg * (agb[sl].sum() - ags[sl].sum()) / den if den > 0 else 0.0
            F["wick_seq"][i] = wick[sl].mean() / BODY_TICKS

    for k, v in F.items():
        df[k] = v
    return df


# --------------------------------------------------------------------------- #
# 3. ROTULOS -- primeiro toque, stop testado ANTES do alvo (pessimista)
# --------------------------------------------------------------------------- #
def rotular(df, K, stop_bodies=2.0):
    n = len(df)
    c, h, l, dirn = df.c.values, df.h.values, df.l.values, df.dirn.values
    lab = np.full(n, np.nan)
    bars = np.full(n, np.nan)
    elig = df.elig.values.astype(bool)
    for i in np.where(elig)[0]:
        d = dirn[i]
        tgt = c[i] + d * (K - 1) * BODY_PTS
        stp = c[i] - d * stop_bodies * BODY_PTS
        for j in range(i + 1, n):
            if d > 0:
                if l[j] <= stp:
                    lab[i], bars[i] = 0.0, j - i
                    break
                if h[j] >= tgt:
                    lab[i], bars[i] = 1.0, j - i
                    break
            else:
                if h[j] >= stp:
                    lab[i], bars[i] = 0.0, j - i
                    break
                if l[j] <= tgt:
                    lab[i], bars[i] = 1.0, j - i
                    break
    return lab, bars


# --------------------------------------------------------------------------- #
# 4. MAIN
# --------------------------------------------------------------------------- #
FEATS = ["cost_nz", "dur_nz", "trd_nz", "size_nz", "pace_nz",
         "delta_cl", "delta_raw", "unk_nz", "wick_net_n", "seq_len",
         "rev_dens", "eff_ratio", "pace_reg", "pos_rng", "day_pos", "hora_dec",
         "cost_seq", "dur_seq", "delta_seq", "wick_seq"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--outdir", default="saida_r11")
    ap.add_argument("-K", type=int, default=4)
    ap.add_argument("--min-seq", type=int, default=3)
    ap.add_argument("--test-frac", type=float, default=0.30)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    R = []       # linhas do relatorio

    def say(s=""):
        print(s)
        R.append(s)

    df = carregar(args.csv)
    df = geometria(df)
    df["elig"] = ((df.is_rev == 1) & (df.seq_before >= args.min_seq) &
                  (df.ok == 1)).astype(int)
    df = construir_features(df)

    say("# Estudo preditivo de pontos de virada -- Renko R11 (WINFUT / ProfitChart)")
    say()
    say("Gerado em %s | K=%d | min_seq=%d | janela ref=%d bricks do mesmo tipo"
        % (pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"), args.K, args.min_seq, REF_N))
    say()
    say("## 1. Base e geometria")
    say()
    say("- bricks: **%d** | pregoes: **%d** | %s a %s" %
        (len(df), df.dt.dt.date.nunique(), df.dt.iloc[0].strftime("%d/%m/%Y"),
         df.dt.iloc[-1].strftime("%d/%m/%Y")))
    say("- corpo constante de **%d pts (%d ticks)** em %.2f%% dos bricks"
        % (BODY_PTS, BODY_TICKS, 100 * ((df.c - df.o).abs() == BODY_PTS).mean()))
    say("- continuacao abre no close anterior; reversao abre no **open** anterior "
        "(confirmado em %.1f%% / %.1f%%)" % (
            100 * (np.abs(df.o.values[1:] - df.c.values[:-1]) < 1e-9)[df.is_rev.values[1:] == 0].mean(),
            100 * (np.abs(df.o.values[1:] - df.o.values[:-1]) < 1e-9)[df.is_rev.values[1:] == 1].mean()))
    say("- `Data` e o instante de **abertura**; `BarDurationF` esta em **minutos**, "
        "quantizado em 0,01 min (0,6 s) -- %.1f%% dos bricks marcam 0,00"
        % (100 * (df.dur == 0).mean()))
    say("- bricks descartados (`sujo`): **%d (%.2f%%)** -- %d quebras de encadeamento, "
        "%d viradas de pregao, %d sem volume, %d com dur > 60 min"
        % (df.sujo.sum(), 100 * df.sujo.mean(), df.brk.sum(), df.newday.sum(),
           (df.qt <= 0).sum(), (df.dur > 60).sum()))
    say()
    say("### Reversao e continuacao sao populacoes distintas")
    say()
    g = df[df.ok == 1].groupby("is_rev").agg(
        n=("qt", "size"), dur=("dur", "median"), qt=("qt", "median"),
        trd=("trd", "median"), wick=("wick", "median"), unk=("unk_share", "median"))
    say("| | n | dur (min) | Quantity | Trades | pavio (ticks) | vol s/ agressor |")
    say("|---|---|---|---|---|---|---|")
    for t, nome in [(0, "continuacao"), (1, "reversao")]:
        r = g.loc[t]
        say("| %s | %d | %.2f | %.0f | %.0f | %.0f | %.1f%% |" %
            (nome, r.n, r.dur, r.qt, r.trd, r.wick, 100 * r.unk))
    say("| **razao rev/cont** | | **%.2fx** | **%.2fx** | **%.2fx** | **%.2fx** | |" %
        (g.dur[1] / g.dur[0], g.qt[1] / g.qt[0], g.trd[1] / g.trd[0], g.wick[1] / g.wick[0]))
    say()
    say("E por isso que a janela de referencia so contem bricks do **mesmo tipo**. "
        "Comparar um brick de reversao contra uma janela dominada por continuacoes "
        "infla a razao por construcao, sem informacao dentro.")
    say()
    say("### O volume sem agressor")
    say()
    say("`Quantity - (AgressionVolBuy + AgressionVolSell)` responde por **%.1f%%** do "
        "volume total e correlaciona **+%.2f** com `log(Quantity)`. E o negocio direto / RLP, "
        "que o ProfitChart nao classifica. Consequencia: `(agb-ags)/Quantity` vem diluido "
        "nos bricks grandes. O estudo usa **`(agb-ags)/(agb+ags)`** como delta, e trata "
        "a fracao sem agressor como feature separada (`unk_nz`)."
        % (100 * (df.qt - df.agtot).clip(lower=0).sum() / df.qt.sum(),
           np.corrcoef(df.unk_share[df.qt > 0], np.log(df.qt[df.qt > 0]))[0, 1]))
    say()

    # ---------------- taxa base -------------------------------------------- #
    say("## 2. A taxa base -- o numero a bater")
    say()
    dirn = df.dirn.values
    nxt_same = (dirn[1:] == dirn[:-1])
    say("| condicao | P(proximo brick na mesma direcao) | n |")
    say("|---|---|---|")
    say("| qualquer brick | %.2f%% | %d |" % (100 * nxt_same.mean(), len(nxt_same)))
    m = df.is_rev.values[:-1] == 1
    say("| brick contrario a qualquer sequencia | %.2f%% | %d |" %
        (100 * nxt_same[m].mean(), m.sum()))
    me = df.elig.values[:-1] == 1
    say("| brick contrario a seq >= %d (**elegivel**) | **%.2f%%** | %d |" %
        (args.min_seq, 100 * nxt_same[me].mean(), me.sum()))
    say()
    say("A pre-condicao inteira vale **%+.2f p.p.** A assimetria vem da mecanica do Renko: "
        "reverter custa o corpo do tijolo anterior **mais** o novo (20 ticks), continuar "
        "custa so o novo (10). Depois de pagar uma reversao, continuar e mecanicamente "
        "duas vezes mais barato. Isso nao e informacao de fluxo."
        % (100 * (nxt_same[me].mean() - nxt_same.mean())))
    say()

    say("### Escolha do alvo")
    say()
    say("Entrada no fechamento do brick elegivel, na direcao dele. "
        "Alvo (K-1) corpos a favor, stop 2 corpos contra (= o brick de reversao fechando). "
        "Stop testado **antes** do alvo dentro do mesmo brick (pessimista).")
    say()
    say("| K | alvo (pts) | stop (pts) | breakeven | taxa base | n | expectativa na taxa base |")
    say("|---|---|---|---|---|---|---|")
    labs = {}
    for K in [2, 3, 4, 5, 6]:
        lab, _ = rotular(df, K)
        labs[K] = lab
        v = lab[~np.isnan(lab)]
        alvo, stop = (K - 1) * BODY_PTS, 2 * BODY_PTS
        be = stop / (alvo + stop)
        exp = v.mean() * alvo - (1 - v.mean()) * stop
        say("| %d | %d | %d | %.3f | **%.4f** | %d | %+.1f pts |" %
            (K, alvo, stop, be, v.mean(), len(v), exp))
    say()
    say("K=%d e o alvo do estudo: e o mais proximo do breakeven, portanto o que mais "
        "depende do modelo, e uma perna de %d tijolos = %d pts no WIN."
        % (args.K, args.K, (args.K - 1) * BODY_PTS))
    say()

    df["y"] = labs[args.K]
    # ---------------- amostra ---------------------------------------------- #
    d = df[(df.elig == 1) & (df.ref_ok == 1) & df.y.notna()].copy()
    d = d.dropna(subset=FEATS)
    say("## 3. Amostra")
    say()
    say("- elegiveis: **%d** (%.2f%% dos bricks)" % (df.elig.sum(), 100 * df.elig.mean()))
    say("- com janela de referencia completa e rotulo definido: **%d**" % len(d))
    say("- taxa base na amostra: **%.4f**" % d.y.mean())
    say()

    dias = np.sort(d.dt.dt.date.unique())
    corte = dias[int(len(dias) * (1 - args.test_frac))]
    tr = d[d.dt.dt.date < corte]
    te = d[d.dt.dt.date >= corte]
    say("Split cronologico por pregao: treino %d eventos (%d pregoes, ate %s), "
        "teste %d eventos (%d pregoes, de %s)."
        % (len(tr), tr.dt.dt.date.nunique(), (corte - pd.Timedelta(days=1)).strftime("%d/%m"),
           len(te), te.dt.dt.date.nunique(), corte.strftime("%d/%m/%Y")))
    say()

    # ---------------- AUC univariada --------------------------------------- #
    say("## 4. Poder discriminante isolado de cada feature")
    say()
    say("AUC sobre a amostra inteira. 0,50 = nada. Valor **abaixo** de 0,50 significa "
        "que a feature separa com o **sinal invertido** em relacao a intuicao.")
    say()
    uni = []
    for f in FEATS:
        a = roc_auc_score(d.y, d[f])
        ate = roc_auc_score(te.y, te[f]) if te.y.nunique() > 1 else np.nan
        uni.append((f, a, abs(a - .5), ate))
    uni.sort(key=lambda x: -x[2])
    say("| feature | AUC (tudo) | AUC (teste) | |AUC-0,5| |")
    say("|---|---|---|---|")
    for f, a, dd, ate in uni:
        say("| `%s` | %.4f | %.4f | %.4f |" % (f, a, ate, dd))
    say()

    # ---------------- modelos ---------------------------------------------- #
    Xtr, ytr = tr[FEATS].values, tr.y.values
    Xte, yte = te[FEATS].values, te.y.values
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-12] = 1.0
    Ztr, Zte = (Xtr - mu) / sd, (Xte - mu) / sd

    say("## 5. Modelos")
    say()
    base_te = ytr.mean()   # previsao constante calibrada no treino
    res = []
    for nome, mdl, exp_ntsl in [
        ("logistica L2 (C=0.1)", LogisticRegression(C=0.1, max_iter=2000), "sim"),
        ("logistica L1 (C=0.1)", LogisticRegression(C=0.1, penalty="l1",
                                                    solver="liblinear", max_iter=2000), "sim"),
        ("GBM (teto de referencia)", HistGradientBoostingClassifier(
            max_depth=3, max_iter=200, learning_rate=0.05,
            min_samples_leaf=60, l2_regularization=1.0, random_state=7), "nao"),
    ]:
        mdl.fit(Ztr, ytr)
        p = mdl.predict_proba(Zte)[:, 1]
        res.append((nome, roc_auc_score(yte, p), log_loss(yte, p),
                    brier_score_loss(yte, p), exp_ntsl, mdl, p))
    say("| modelo | AUC teste | log-loss | Brier | exportavel NTSL |")
    say("|---|---|---|---|---|")
    for nome, auc, ll, br, ex, _, _ in res:
        say("| %s | %.4f | %.4f | %.4f | %s |" % (nome, auc, ll, br, ex))
    pb = np.full(len(yte), base_te)
    say("| *constante = taxa base do treino* | 0.5000 | %.4f | %.4f | - |" %
        (log_loss(yte, pb, labels=[0, 1]), brier_score_loss(yte, pb)))
    say()

    # CV temporal no treino
    tss = TimeSeriesSplit(n_splits=5)
    aucs = []
    for itr, iva in tss.split(Ztr):
        m2 = LogisticRegression(C=0.1, max_iter=2000).fit(Ztr[itr], ytr[itr])
        if len(np.unique(ytr[iva])) > 1:
            aucs.append(roc_auc_score(ytr[iva], m2.predict_proba(Ztr[iva])[:, 1]))
    say("Validacao cruzada temporal (5 dobras expansivas, so no treino): "
        "AUC **%.3f +/- %.3f**." % (np.mean(aucs), np.std(aucs)))
    say()

    logit = res[0][5]
    p_te = res[0][6]
    say("### Coeficientes da logistica L2 (features padronizadas)")
    say()
    say("intercepto = %+.6f" % logit.intercept_[0])
    say()
    say("| feature | coef | AUC isolada | leitura |")
    say("|---|---|---|---|")
    order = np.argsort(-np.abs(logit.coef_[0]))
    ua = {f: a for f, a, _, _ in uni}
    for k in order:
        f = FEATS[k]
        cf = logit.coef_[0][k]
        say("| `%s` | %+.4f | %.4f | %s |" %
            (f, cf, ua[f], "valor alto -> **mais** chance de perna" if cf > 0
             else "valor alto -> **menos** chance de perna"))
    say()

    # ---------------- decis e limiar --------------------------------------- #
    say("## 6. Desempenho por decil do score (out-of-sample)")
    say()
    dt2 = te.copy()
    dt2["p"] = p_te
    dt2["dec"] = pd.qcut(dt2.p, 10, labels=False, duplicates="drop") + 1
    alvo, stop = (args.K - 1) * BODY_PTS, 2 * BODY_PTS
    say("| decil | n | p media | acerto real | lift | expectativa (pts/trade) |")
    say("|---|---|---|---|---|---|")
    for q, gq in dt2.groupby("dec"):
        acc = gq.y.mean()
        say("| %d | %d | %.3f | %.3f | %.2fx | %+.1f |" %
            (q, len(gq), gq.p.mean(), acc, acc / yte.mean(),
             acc * alvo - (1 - acc) * stop))
    say()

    say("## 7. Escolha do limiar (out-of-sample)")
    say()
    say("| p >= | z >= | sinais | por pregao | acerto | lift | pts/trade | pts totais |")
    say("|---|---|---|---|---|---|---|---|")
    npregoes = te.dt.dt.date.nunique()
    grid = []
    for th in np.arange(0.30, 0.75, 0.025):
        m = p_te >= th
        if m.sum() < 5:
            continue
        acc = yte[m].mean()
        ppt = acc * alvo - (1 - acc) * stop
        z = np.log(th / (1 - th))
        grid.append((th, z, int(m.sum()), m.sum() / npregoes, acc,
                     acc / yte.mean(), ppt, ppt * m.sum()))
        say("| %.3f | %+.4f | %d | %.1f | %.3f | %.2fx | %+.1f | %+.0f |" % grid[-1])
    say()

    # ---------------- graficos --------------------------------------------- #
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    fpr, tpr, _ = roc_curve(yte, p_te)
    ax[0, 0].plot(fpr, tpr, lw=2, label="logistica AUC=%.4f" % res[0][1])
    ax[0, 0].plot([0, 1], [0, 1], "k--", lw=1)
    ax[0, 0].set_title("ROC out-of-sample"); ax[0, 0].legend()
    pt, pp = calibration_curve(yte, p_te, n_bins=8, strategy="quantile")
    ax[0, 1].plot(pp, pt, "o-"); ax[0, 1].plot([0, 1], [0, 1], "k--", lw=1)
    ax[0, 1].axhline(yte.mean(), color="r", ls=":", label="taxa base")
    ax[0, 1].set_title("Calibracao"); ax[0, 1].legend()
    ax[0, 1].set_xlabel("p previsto"); ax[0, 1].set_ylabel("frequencia real")
    dd = dt2.groupby("dec").y.mean()
    ax[1, 0].bar(dd.index, dd.values)
    ax[1, 0].axhline(yte.mean(), color="r", ls="--", label="taxa base")
    ax[1, 0].axhline(stop / (alvo + stop), color="g", ls=":", label="breakeven")
    ax[1, 0].set_title("Acerto por decil do score"); ax[1, 0].legend()
    ax[1, 0].set_xlabel("decil")
    if grid:
        gg = np.array(grid, dtype=float)
        ax[1, 1].plot(gg[:, 0], gg[:, 6], "o-")
        ax[1, 1].axhline(0, color="k", lw=1)
        ax[1, 1].set_title("Expectativa (pts/trade) x limiar")
        ax[1, 1].set_xlabel("p minimo")
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "01_diagnostico.png"), dpi=110)
    plt.close()

    nf = len(FEATS)
    fig, axs = plt.subplots((nf + 4) // 5, 5, figsize=(19, 3.1 * ((nf + 4) // 5)))
    for k, f in enumerate(FEATS):
        a = axs.flat[k]
        for yv, cor, lb in [(0, "tab:red", "sem perna"), (1, "tab:blue", "perna")]:
            s = d.loc[d.y == yv, f]
            a.hist(s, bins=40, alpha=.5, density=True, color=cor, label=lb)
        a.set_title("%s (AUC %.3f)" % (f, ua[f]), fontsize=9)
        if k == 0:
            a.legend(fontsize=7)
    for k in range(nf, axs.size):
        axs.flat[k].axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "02_features.png"), dpi=100)
    plt.close()

    # ---------------- export ----------------------------------------------- #
    d.to_csv(os.path.join(args.outdir, "features.csv"), sep=";", decimal=",", index=False)
    json.dump({"feats": FEATS, "mu": mu.tolist(), "sd": sd.tolist(),
               "coef": logit.coef_[0].tolist(), "intercept": float(logit.intercept_[0]),
               "K": args.K, "min_seq": args.min_seq, "ref_n": REF_N, "reg_n": REG_N,
               "auc_test": float(res[0][1]), "base_rate": float(d.y.mean())},
              open(os.path.join(args.outdir, "modelo.json"), "w"), indent=2)

    with open(os.path.join(args.outdir, "relatorio.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(R) + "\n")
    print("\n>>> escrito em", args.outdir)
    return d, tr, te, logit, mu, sd, FEATS, res, grid, uni


if __name__ == "__main__":
    main()
