"""
Etapa 12 — treina o modelo EXPORTAVEL e gera o indicador NTSL,
depois audita o NTSL contra as previsoes Python (secoes 27-29 e 44.19).

O modelo exportado difere do modelo de pesquisa em dois pontos, ambos
deliberados e documentados:

  1. usa apenas features calculaveis em NTSL (ver ``ntsl_features.py``);
     em particular, nada derivado de ``Trades``;
  2. e propositalmente pequeno (poucas arvores, profundidade baixa) para
     que o codigo gerado seja auditavel a olho, como exige a secao 29.

A auditoria tem duas camadas:
  A. ``model_to_ntsl.verify_python_reimplementation`` — a aritmetica de
     arvores que o NTSL executa reproduz o CatBoost;
  B. ``audit_against_ntsl_semantics`` — as FEATURES recalculadas do jeito
     que o NTSL as calcula (a partir de OHLC/agressao brutos, com as
     mesmas medias moveis causais) reproduzem as features do pipeline,
     e o sinal final coincide barra a barra.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import model_to_ntsl as M
from build_dataset import load_dataset
from config import EPSILON, MA_PERIOD, MODELS_DIR, RESULTS_DIR
from evaluate import classification_metrics
from final_model import choose_threshold, economic_summary
from ntsl_features import ntsl_feature_set
from walk_forward import fit_predict, holdout_split, run_walk_forward

EXPORT_PARAMS = dict(depth=3, learning_rate=0.05, l2_leaf_reg=10.0,
                     iterations=40)
N_LAGS_EXPORT = 3


# ------------------------------------------------ semantica do NTSL
def ntsl_recompute_features(ds: pd.DataFrame, cols: list[str],
                            ma_period: int = MA_PERIOD) -> pd.DataFrame:
    """Recalcula as features do zero, imitando o NTSL.

    Escrito propositalmente de forma independente de ``features.py``:
    parte de Open/High/Low/Close/AggBuy/AggSell/Quantity/Duration e usa
    exatamente as mesmas operacoes que o indicador executa. Se os dois
    caminhos concordarem, o NTSL calcula o que o modelo espera.
    """
    o, h, l, c = ds["Open"], ds["High"], ds["Low"], ds["Close"]
    agrB, agrS = ds["AggBuy"], ds["AggSell"]
    qtd, dur = ds["Quantity"], ds["Duration"]

    rng = h - l
    rng_safe = rng.clip(lower=EPSILON)          # 'if rngSafe < 1 then := 1'
    corpo = (c - o).abs()
    tot = agrB + agrS

    dirn = np.sign(c - o).astype(int)
    run = dirn.groupby((dirn != dirn.shift(1)).cumsum()).cumcount() + 1

    m_dur = dur.rolling(ma_period, min_periods=ma_period).mean()
    m_rng = rng.rolling(ma_period, min_periods=ma_period).mean().clip(lower=1)
    m_tot = tot.rolling(ma_period, min_periods=ma_period).mean().clip(lower=1)
    m_qtd = qtd.rolling(ma_period, min_periods=ma_period).mean().clip(lower=1)

    bal_norm = (agrB - agrS) / rng_safe
    imbal = np.where(tot > 0, (agrB - agrS) / tot.replace(0, np.nan), 0.0)

    base = {
        "AggBuyNorm": agrB / rng_safe,
        "AggSellNorm": agrS / rng_safe,
        "AggBalanceNorm": bal_norm,
        "AggTotalNorm": tot / rng_safe,
        "QuantityNorm": qtd / rng_safe,
        "DurationResidual": dur - m_dur,
        "Range": rng,
        "BodyNorm": corpo / rng_safe,
        "Direction": dirn,
        "RunLength": run,
        "AggImbalance": pd.Series(imbal, index=ds.index),
        "AggBalanceChange": bal_norm - bal_norm.shift(1),
        "RangeRatio20": rng / m_rng,
        "AggTotalRatio20": tot / m_tot,
        "QuantityRatio20": qtd / m_qtd,
    }
    out = {}
    for col in cols:
        if "_lag" in col:
            b, k = col.split("_lag")
            out[col] = base[b].shift(int(k))
        else:
            out[col] = base[col]
    return pd.DataFrame(out, index=ds.index)


def audit_against_ntsl_semantics(ds, cols, model, spec, threshold,
                                 idx: np.ndarray) -> dict:
    """Camada B: features do NTSL == features do pipeline == mesmo sinal."""
    ntsl_feats = ntsl_recompute_features(ds, cols).iloc[idx]
    pipe_feats = ds.iloc[idx][cols].replace([np.inf, -np.inf], np.nan)

    diff = (ntsl_feats.to_numpy(float) - pipe_feats.to_numpy(float))
    both_nan = np.isnan(ntsl_feats.to_numpy(float)) & np.isnan(
        pipe_feats.to_numpy(float))
    diff = np.where(both_nan, 0.0, diff)
    max_diff = float(np.nanmax(np.abs(diff))) if diff.size else 0.0

    p_pipe = model.predict_proba(pipe_feats)[:, 1]
    p_ntsl = M.probability(spec, ntsl_feats.to_numpy(float))
    sig_pipe = (p_pipe >= threshold).astype(int)
    sig_ntsl = (p_ntsl >= threshold).astype(int)

    return {
        "n_bars_audited": int(len(idx)),
        "max_abs_feature_diff": max_diff,
        "features_match": bool(max_diff < 1e-9),
        "max_abs_prob_diff": float(np.nanmax(np.abs(p_pipe - p_ntsl))),
        "n_signal_disagreements": int((sig_pipe != sig_ntsl).sum()),
        "signals_match": bool((sig_pipe == sig_ntsl).all()),
        "n_signals_pipeline": int(sig_pipe.sum()),
        "n_signals_ntsl": int(sig_ntsl.sum()),
    }


# ---------------------------------------------------- no-repaint check
def assert_signal_uses_only_past(ds, cols, spec, threshold,
                                 cuts=(2000, 9000, 15000)) -> dict:
    """O sinal da barra t muda se o futuro mudar? (nao pode mudar)"""
    rng = np.random.default_rng(0)
    base_feats = ntsl_recompute_features(ds, cols)
    base_p = M.probability(spec, base_feats.to_numpy(float))
    base_sig = (base_p >= threshold).astype(int)

    fails = []
    for cut in cuts:
        d2 = ds.copy()
        fut = d2.index > cut
        n = int(fut.sum())
        for col in ("Open", "High", "Low", "Close", "AggBuy", "AggSell",
                    "Duration", "Quantity"):
            d2[col] = d2[col].astype(float)
            d2.loc[fut, col] = (d2.loc[fut, col].to_numpy(float)
                                * rng.uniform(0.1, 10, n))
        f2 = ntsl_recompute_features(d2, cols)
        p2 = M.probability(spec, f2.to_numpy(float))
        s2 = (p2 >= threshold).astype(int)
        n_diff = int((base_sig[:cut + 1] != s2[:cut + 1]).sum())
        if n_diff:
            fails.append({"cut": cut, "n_changed_signals": n_diff})
    return {"cuts": list(cuts), "failures": fails, "passed": not fails}


# ------------------------------------------------------------------ run
def run(target_suffix="p2c2", pre_seq=2) -> dict:
    ds = load_dataset()
    bars = np.arange(len(ds))
    dev, test = holdout_split(bars)
    tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"
    cols = ntsl_feature_set(N_LAGS_EXPORT)
    cols = [c for c in cols if c in ds.columns]

    # ---- walk-forward em DEV: define o threshold ------------------------
    wf = run_walk_forward(ds, cols, tcol, ccol, "catboost", EXPORT_PARAMS,
                          bar_pool=dev, collect_importance=False)
    dev_m = classification_metrics(wf.oof["y"], wf.oof["prob"], 0.5)
    dev_days = ds.iloc[dev]["Session"].nunique()
    th = choose_threshold(wf.oof, dev_days)
    t = th["threshold"]

    # ---- retreino em todo o DEV -----------------------------------------
    usable = ((ds[ccol] == 1) & ds[tcol].notna()).to_numpy()
    tr = np.intersect1d(dev, np.where(usable)[0])
    te = np.intersect1d(test, np.where(usable)[0])
    ytr = ds[tcol].to_numpy()[tr].astype(int)
    yte = ds[tcol].to_numpy()[te].astype(int)

    prob_te, model = fit_predict("catboost", EXPORT_PARAMS,
                                 ds.iloc[tr][cols], ytr, ds.iloc[te][cols],
                                 use_early_stopping=False)
    model.save_model(str(MODELS_DIR / "catboost_ntsl_export.cbm"))

    test_days = ds.iloc[test]["Session"].nunique()
    hold_m = classification_metrics(yte, prob_te, t, n_days=test_days)
    econ = economic_summary(ds, te, prob_te >= t)
    econ_all = economic_summary(ds, te, np.ones(len(te), bool))

    # ---- exportacao + auditoria -----------------------------------------
    spec = M.parse_model(model)
    verif = M.verify_python_reimplementation(model, spec, ds.iloc[te][cols])
    audit = audit_against_ntsl_semantics(ds, cols, model, spec, t, te)
    norep = assert_signal_uses_only_past(ds, cols, spec, t)

    note = _honesty_note(dev_m, hold_m, econ, econ_all)
    info = M.export(model, cols, t, ds.iloc[te][cols],
                    name="ReversalDetectorClaude", pre_seq=pre_seq,
                    honesty_note=note)

    out = {
        "target": target_suffix, "params": EXPORT_PARAMS,
        "n_lags": N_LAGS_EXPORT, "features": cols, "n_features": len(cols),
        "threshold": t,
        "dev_walkforward": dev_m,
        "holdout": hold_m,
        "economics_signals": econ,
        "economics_all_candidates": econ_all,
        "tree_arithmetic_verification": verif,
        "ntsl_semantics_audit": audit,
        "no_repaint_test": norep,
        "export": info,
    }
    (RESULTS_DIR / "12_ntsl_export_audit.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    return out


def _honesty_note(dev_m, hold_m, econ, econ_all) -> str:
    lines = [
        "// RESULTADO DA VALIDACAO — ESTE INDICADOR NAO ATINGIU O CRITERIO",
        "// DE SUCESSO DA SECAO 41 DO CLAUDE.md. Ele e entregue porque foi",
        "// pedido como entregavel, e para servir de arcabouco auditavel,",
        "// NAO porque a pesquisa recomendou opera-lo.",
        "//",
        f"//   AUC walk-forward (desenvolvimento) : {dev_m['roc_auc']:.4f}",
        f"//   AUC holdout (out-of-sample)        : {hold_m['roc_auc']:.4f}",
        f"//   taxa-base do evento                : {hold_m['base_rate']:.4f}",
        f"//   precision no threshold escolhido   : {hold_m['precision']:.4f}",
        f"//   ganho sobre a taxa-base            : {hold_m['edge_vs_base']:+.4f}",
        f"//   sinais por pregao                  : {hold_m.get('signals_per_day', 0):.1f}",
        "//",
        f"//   deslocamento medio 12 barras, SINAIS      : "
        f"{econ.get('mean_move_12_bars_pts', float('nan')):+.1f} pts",
        f"//   deslocamento medio 12 barras, TODOS CAND. : "
        f"{econ_all.get('mean_move_12_bars_pts', float('nan')):+.1f} pts",
        "//",
        "// Ou seja: filtrar os candidatos com o modelo nao melhorou o",
        "// resultado economico em relacao a simplesmente aceitar todas as",
        "// viradas estruturais. Ver reports/final_report.md.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: v for k, v in r.items()
                      if k not in ("features",)}, indent=2, default=float))
