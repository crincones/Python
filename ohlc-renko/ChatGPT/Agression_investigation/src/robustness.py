"""
Etapa 09 — testes de robustez e estabilidade (secoes 23 e 24)
mais um TESTE NULO de selecao (adicional, nao pedido explicitamente,
mas necessario para responder a secao 41.1 com honestidade).

Teste nulo
----------
O melhor AUC de uma busca de N configuracoes e um MAXIMO amostral, nao uma
estimativa nao-enviesada. Para saber se 0.55 e um resultado real ou o topo
do ruido, embaralhamos o target DENTRO de blocos temporais (preservando a
taxa-base e a estrutura de blocos) e repetimos o mesmo procedimento de
selecao. A distribuicao dos "melhores AUC" sob a hipotese nula fornece o
p-valor correto para o procedimento inteiro.
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_dataset import load_dataset
from config import DEFAULT_LAGS, FIGURES_DIR, REPORTS_DIR, RESULTS_DIR, SEED
from evaluate import classification_metrics, metrics_by_group
from train_catboost import feature_columns
from walk_forward import holdout_split, run_walk_forward


# ------------------------------------------------------- cortes de regime
def regime_columns(ds: pd.DataFrame) -> pd.DataFrame:
    """Regimes construidos SOMENTE com informacao ate t."""
    r = pd.DataFrame(index=ds.index)
    r["month"] = ds["Date"].dt.to_period("M").astype(str)
    r["week"] = ds["Date"].dt.to_period("W").astype(str)
    r["hour"] = ds["Date"].dt.hour

    # duracao: tercis calculados sobre a mediana movel causal
    dur_rank = ds["LogDurationResidual20"]
    q = dur_rank.expanding(min_periods=200).quantile(0.33)
    q2 = dur_rank.expanding(min_periods=200).quantile(0.67)
    r["duration_regime"] = np.select(
        [dur_rank <= q, dur_rank >= q2], ["rapida", "lenta"], default="normal")

    # volatilidade: range medio de 20 barras (causal), tercis expansivos
    vol = ds["Range"].rolling(20, min_periods=20).mean()
    v1 = vol.expanding(min_periods=200).quantile(0.33)
    v2 = vol.expanding(min_periods=200).quantile(0.67)
    r["vol_regime"] = np.select([vol <= v1, vol >= v2],
                                ["baixa", "alta"], default="media")
    return r


def by_regime(target_suffix="p2c2", feature_set="BASE", params=None,
              n_lags=DEFAULT_LAGS, threshold=0.5) -> dict:
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)))
    cols = feature_columns(ds, feature_set, n_lags)
    wf = run_walk_forward(ds, cols, f"y_{target_suffix}",
                          f"cand_{target_suffix}", "catboost", params,
                          bar_pool=dev, collect_importance=False)
    if wf.oof.empty:
        return {}
    reg = regime_columns(ds)
    o = wf.oof.merge(
        reg.assign(BarIndex=ds["BarIndex"]), on="BarIndex", how="left")

    out = {}
    for col in ("month", "week", "hour", "side", "duration_regime",
                "vol_regime"):
        m = metrics_by_group(o, col, threshold)
        if len(m):
            m.to_csv(RESULTS_DIR / f"09_regime_{col}_{target_suffix}.csv",
                     index=False)
            out[col] = m[[col, "n", "base_rate", "roc_auc", "precision",
                          "n_signals", "edge_vs_base"]].to_dict("records")
    return out


# --------------------------------------------------------- teste nulo
def _block_permute(y: np.ndarray, block: int, rng) -> np.ndarray:
    """Embaralha blocos contiguos de rotulos, preservando autocorrelacao."""
    n = len(y)
    blocks = [y[i:i + block] for i in range(0, n, block)]
    order = rng.permutation(len(blocks))
    return np.concatenate([blocks[i] for i in order])[:n]


def null_test(target_suffix="p2c2", feature_sets=("STRUCT+AGG",),
              param_grid=None, n_perm=30, block=40,
              n_lags=DEFAULT_LAGS, seed=SEED, embargo=None) -> dict:
    """Distribuicao nula do MELHOR AUC do procedimento de selecao."""
    param_grid = param_grid or [
        dict(depth=d, learning_rate=lr, l2_leaf_reg=l2)
        for d in (3, 4) for lr in (0.02, 0.05) for l2 in (3.0, 10.0)
    ]
    from config import EMBARGO_BARS
    embargo = EMBARGO_BARS if embargo is None else embargo
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)), embargo=embargo)
    tcol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"

    def best_auc(dset) -> float:
        best = -np.inf
        for fs in feature_sets:
            cols = feature_columns(dset, fs, n_lags)
            for p in param_grid:
                r = run_walk_forward(dset, cols, tcol, ccol, "catboost", p,
                                     bar_pool=dev, embargo=embargo,
                                     collect_importance=False)
                if r.oof.empty:
                    continue
                a = classification_metrics(r.oof["y"], r.oof["prob"])["roc_auc"]
                best = max(best, a)
        return best

    observed = best_auc(ds)

    rng = np.random.default_rng(seed)
    usable = ((ds[ccol] == 1) & ds[tcol].notna()).to_numpy()
    pos = np.where(usable)[0]
    nulls = []
    for i in range(n_perm):
        d2 = ds.copy()
        y = d2[tcol].to_numpy()[pos].astype(int)
        d2.loc[pos, tcol] = _block_permute(y, block, rng).astype(float)
        nulls.append(best_auc(d2))
        print(f"    perm {i + 1}/{n_perm}: melhor AUC nulo = {nulls[-1]:.4f}")

    nulls = np.asarray(nulls)
    p = float((nulls >= observed).mean())
    out = {"observed_best_auc": float(observed),
           "n_permutations": int(n_perm), "block_size": int(block),
           "n_configs_per_search": len(feature_sets) * len(param_grid),
           "null_mean": float(nulls.mean()), "null_std": float(nulls.std()),
           "null_p95": float(np.percentile(nulls, 95)),
           "null_max": float(nulls.max()),
           "p_value": p,
           "nulls": nulls.tolist()}

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(nulls, bins=15, color="#B0B0B0", label="melhor AUC sob H0")
    ax.axvline(observed, color="#E45756", lw=2,
               label=f"observado = {observed:.4f}")
    ax.axvline(np.percentile(nulls, 95), color="#4C78A8", ls="--",
               label="p95 nulo")
    ax.set_xlabel("melhor AUC da busca"); ax.set_ylabel("frequencia")
    ax.set_title(f"Teste nulo do procedimento de selecao — {target_suffix}\n"
                 f"p = {p:.3f}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"09_null_test_{target_suffix}.png", dpi=110)
    plt.close(fig)
    return out


# ------------------------------------------------- estabilidade do desenho
def target_variant_stability(feature_set="BASE", params=None,
                             n_lags=DEFAULT_LAGS) -> pd.DataFrame:
    """Secao 24: 2 vs 3 candles de pre-sequencia e de continuacao."""
    params = params or dict(depth=4, learning_rate=0.05, l2_leaf_reg=10.0)
    ds = load_dataset()
    dev, _ = holdout_split(np.arange(len(ds)))
    cols = feature_columns(ds, feature_set, n_lags)
    rows = []
    for suf in ("p2c2", "p2c3", "p3c2", "p3c3", "p2c2e", "p3c2e"):
        r = run_walk_forward(ds, cols, f"y_{suf}", f"cand_{suf}", "catboost",
                             params, bar_pool=dev, collect_importance=False)
        if r.oof.empty:
            continue
        m = classification_metrics(r.oof["y"], r.oof["prob"], 0.5)
        fm = pd.DataFrame(r.fold_metrics)
        rows.append({"target": suf, "n": m["n"], "base_rate": m["base_rate"],
                     "roc_auc": m["roc_auc"], "pr_auc": m["pr_auc"],
                     "precision": m["precision"],
                     "edge_vs_base": m["edge_vs_base"],
                     "auc_fold_mean": float(fm["roc_auc"].mean()),
                     "auc_fold_std": float(fm["roc_auc"].std()),
                     "folds_above_05": int((fm["roc_auc"] > 0.5).sum()),
                     "n_folds": len(fm)})
        print(f"  {suf:6s} AUC={m['roc_auc']:.4f} base={m['base_rate']:.4f} "
              f"folds>0.5={rows[-1]['folds_above_05']}/{rows[-1]['n_folds']}")
    res = pd.DataFrame(rows)
    res.to_csv(RESULTS_DIR / "09_target_variant_stability.csv", index=False)
    return res


def run(target_suffix="p2c2", n_perm=30) -> dict:
    print("=== regimes ===")
    reg = by_regime(target_suffix)
    print("=== estabilidade do desenho do target ===")
    tv = target_variant_stability()
    print("=== teste nulo (pode demorar) ===")
    nt = null_test(target_suffix, n_perm=n_perm)

    out = {"regimes": reg, "target_variants": tv.to_dict("records"),
           "null_test": {k: v for k, v in nt.items() if k != "nulls"},
           "null_distribution": nt["nulls"]}
    (RESULTS_DIR / f"09_robustness_{target_suffix}.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    _write_md(out, target_suffix)
    return out


def _write_md(out: dict, suf: str) -> None:
    L = [f"# 09 — Robustez e estabilidade (`{suf}`)", "",
         "## Teste nulo do procedimento de selecao", ""]
    nt = out["null_test"]
    L += [f"- melhor AUC observado: **{nt['observed_best_auc']:.4f}**",
          f"- configuracoes por busca: {nt['n_configs_per_search']}",
          f"- permutacoes em bloco (bloco={nt['block_size']}): "
          f"{nt['n_permutations']}",
          f"- melhor AUC sob H0: media {nt['null_mean']:.4f}, "
          f"desvio {nt['null_std']:.4f}, p95 {nt['null_p95']:.4f}, "
          f"max {nt['null_max']:.4f}",
          f"- **p-valor = {nt['p_value']:.4f}**", "",
          "![teste nulo](figures/09_null_test_%s.png)" % suf, ""]

    L += ["## Estabilidade do desenho do target", "",
          "| target | n | taxa-base | AUC | precision | edge | AUC/fold | desvio | folds>0.5 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in out["target_variants"]:
        L.append(f"| `{r['target']}` | {r['n']} | {r['base_rate']:.4f} | "
                 f"{r['roc_auc']:.4f} | {r['precision']:.4f} | "
                 f"{r['edge_vs_base']:+.4f} | {r['auc_fold_mean']:.4f} | "
                 f"{r['auc_fold_std']:.4f} | "
                 f"{r['folds_above_05']}/{r['n_folds']} |")

    for name, title in (("side", "direcao"), ("month", "mes"),
                        ("hour", "horario"), ("duration_regime", "duracao"),
                        ("vol_regime", "volatilidade")):
        rows = out["regimes"].get(name)
        if not rows:
            continue
        L += ["", f"## Desempenho por {title}", "",
              f"| {name} | n | taxa-base | AUC | precision | sinais | edge |",
              "|---|---|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {r[name]} | {r['n']} | {r['base_rate']:.4f} | "
                     f"{r['roc_auc']:.4f} | {r['precision']:.4f} | "
                     f"{r['n_signals']} | {r['edge_vs_base']:+.4f} |")
    (REPORTS_DIR / f"09_robustness_{suf}.md").write_text("\n".join(L),
                                                         encoding="utf-8")


if __name__ == "__main__":
    run()
