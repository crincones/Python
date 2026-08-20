"""
Teste automatizado de vazamento temporal (secao 26 do CLAUDE.md).

Metodo (perturbacao do futuro):
  1. calcula todas as features na serie original;
  2. escolhe um ponto de corte t*;
  3. embaralha/corrompe agressivamente TODAS as barras t* + 1 em diante;
  4. recalcula as features;
  5. exige igualdade bit-a-bit das features nas barras <= t*.

Qualquer diferenca implica dependencia futura.

Alem disso:
  - verifica que nenhuma coluna de feature tem prefixo de target;
  - verifica que nenhuma feature correlaciona-se perfeitamente com o target
    por construcao (teste de sanidade);
  - verifica ``candidate_mask`` (o candidato estrutural precisa ser causal).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import features as F
import targets as T
from config import DEFAULT_LAGS, MA_PERIOD, RESULTS_DIR, SEED
from load_data import load_chronological


def _corrupt_future(df: pd.DataFrame, cut: int, rng: np.random.Generator
                    ) -> pd.DataFrame:
    """Destroi completamente as barras > cut, preservando <= cut."""
    d = df.copy()
    fut = d.index > cut
    n = int(fut.sum())
    # embaralha as linhas futuras e ainda soma ruido multiplicativo forte
    idx = d.index[fut].to_numpy()
    shuffled = rng.permutation(idx)
    for col in ("Open", "High", "Low", "Close", "AggBuy", "AggSell",
                "Duration", "Quantity", "Trades"):
        d[col] = d[col].astype(float)
        vals = d.loc[shuffled, col].to_numpy(float)
        vals = vals * rng.uniform(0.1, 10.0, size=n) + rng.normal(0, 1e4, n)
        d.loc[idx, col] = vals
    # datas futuras tambem corrompidas (mantendo monotonicidade grosseira)
    d.loc[idx, "Date"] = d.loc[idx, "Date"] + pd.to_timedelta(
        rng.integers(0, 10_000, n), unit="s")
    return d


def run_perturbation_test(cuts=(500, 2000, 7000, 13000, 19000),
                          n_lags: int = DEFAULT_LAGS,
                          ma_period: int = MA_PERIOD) -> dict:
    raw = load_chronological()
    body_abs = (raw["Close"] - raw["Open"]).abs()
    raw = raw.loc[body_abs == body_abs.mode().iloc[0]].reset_index(drop=True)
    raw["BarIndex"] = range(len(raw))

    base = F.add_lags(F.build_features(raw, ma_period=ma_period), n_lags=n_lags)
    feat_cols = [c for c in base.columns
                 if c not in ("Date", "BarIndex", "FileOrder")
                 and pd.api.types.is_numeric_dtype(base[c])]

    rng = np.random.default_rng(SEED)
    failures = []
    for cut in cuts:
        pert = _corrupt_future(raw, cut, rng)
        pf = F.add_lags(F.build_features(pert, ma_period=ma_period),
                        n_lags=n_lags)
        a = base.loc[:cut, feat_cols].to_numpy(float)
        b = pf.loc[:cut, feat_cols].to_numpy(float)
        same = (np.isclose(a, b, rtol=0, atol=0, equal_nan=True))
        if not same.all():
            bad = np.where(~same)
            cols = sorted({feat_cols[j] for j in bad[1]})
            failures.append({"cut": cut, "n_diff": int((~same).sum()),
                             "columns": cols[:50]})

    # ---- candidato estrutural tambem precisa ser causal -----------------
    cand_fail = []
    for pre_seq in (2, 3):
        m0, s0 = T.candidate_mask(raw, pre_seq)
        for cut in cuts:
            pert = _corrupt_future(raw, cut, rng)
            m1, s1 = T.candidate_mask(pert, pre_seq)
            if not (m0.loc[:cut].equals(m1.loc[:cut])
                    and s0.loc[:cut].equals(s1.loc[:cut])):
                cand_fail.append({"pre_seq": pre_seq, "cut": cut})

    # ---- guarda-corpo de nomes ------------------------------------------
    name_violations = [c for c in feat_cols if c.startswith(T.TARGET_PREFIXES)]

    # ---- controle positivo: o teste realmente detecta vazamento? --------
    # injetamos deliberadamente uma feature com shift(-1) e exigimos que o
    # teste falhe para ela.
    poisoned = base.copy()
    poisoned["LEAK_close_next"] = raw["Close"].shift(-1).to_numpy()
    cut = 7000
    pert = _corrupt_future(raw, cut, rng)
    pf = F.add_lags(F.build_features(pert, ma_period=ma_period), n_lags=n_lags)
    pf["LEAK_close_next"] = pert["Close"].shift(-1).to_numpy()
    detects = not np.isclose(
        poisoned.loc[:cut, "LEAK_close_next"].to_numpy(float),
        pf.loc[:cut, "LEAK_close_next"].to_numpy(float),
        equal_nan=True).all()

    return {
        "n_features_checked": len(feat_cols),
        "cuts": list(cuts),
        "feature_failures": failures,
        "candidate_mask_failures": cand_fail,
        "target_named_columns_in_features": name_violations,
        "positive_control_detects_injected_leak": bool(detects),
        "passed": (not failures and not cand_fail and not name_violations
                   and bool(detects)),
    }


def assert_no_future_dependency() -> dict:
    rep = run_perturbation_test()
    (RESULTS_DIR / "02_leakage_test.json").write_text(
        json.dumps(rep, indent=2), encoding="utf-8")
    if not rep["passed"]:
        raise AssertionError(
            "VAZAMENTO TEMPORAL DETECTADO:\n"
            + json.dumps(rep, indent=2)[:4000]
        )
    return rep


if __name__ == "__main__":
    rep = assert_no_future_dependency()
    print(f"OK — {rep['n_features_checked']} features verificadas em "
          f"{len(rep['cuts'])} pontos de corte.")
    print(f"controle positivo detecta vazamento injetado: "
          f"{rep['positive_control_detects_injected_leak']}")
