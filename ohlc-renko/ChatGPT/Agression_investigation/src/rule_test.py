"""
Etapa 13 — teste de REGRAS ISOLADAS sobre os candidatos estruturais.

Motivacao: antes de qualquer modelo, uma hipotese operacional explicita
deve ser medida sozinha, sem mistura. Aqui a hipotese do usuario:

    "quando (AggBuy+AggSell)/(High-Low) e maior no brick de virada do que
     no anterior, tende a dar bons resultados"

vira a regra booleana ``AggTotalNorm_gt_prev = 1`` e e comparada
diretamente contra a taxa-base dos candidatos.

Tambem varre TODAS as comparacoes t vs t-1 recem-criadas, reportando
precision, lift e expectativa em R, com correcao para multiplos testes.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import features as F
from build_dataset import load_dataset
from config import REPORTS_DIR, RESULTS_DIR, SEED


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson para proporcao — correto com n pequeno."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def evaluate_rule(ds: pd.DataFrame, mask_rule: pd.Series, y: pd.Series,
                  rmult: pd.Series, universe: pd.Series, name: str,
                  n_days: int) -> dict:
    sel = universe & mask_rule.fillna(False).astype(bool)
    n = int(sel.sum())
    if n == 0:
        return {"rule": name, "n": 0}
    k = int(y[sel].sum())
    base = float(y[universe].mean())
    prec = k / n
    lo, hi = _wilson(k, n)
    exp_r = float(rmult[sel].mean())
    exp_r_base = float(rmult[universe].mean())
    return {
        "rule": name, "n": n, "n_per_day": round(n / n_days, 2),
        "precision": prec, "wilson_lo": lo, "wilson_hi": hi,
        "base_rate": base, "edge": prec - base, "lift": prec / base,
        "beats_base_at_95": bool(lo > base),
        "expectancy_R": exp_r, "expectancy_R_base": exp_r_base,
        "expectancy_R_delta": exp_r - exp_r_base,
        "coverage": n / int(universe.sum()),
    }


def run(target_suffix: str = "pts100p2", dev_only: bool = True) -> dict:
    from walk_forward import holdout_split

    ds = load_dataset()
    ycol, ccol = f"y_{target_suffix}", f"cand_{target_suffix}"
    rcol = f"fwd_rmultiple_{target_suffix}"

    universe = (ds[ccol] == 1) & ds[ycol].notna()
    if dev_only:
        dev, _ = holdout_split(np.arange(len(ds)))
        in_dev = pd.Series(False, index=ds.index)
        in_dev.iloc[dev] = True
        universe = universe & in_dev

    y = ds[ycol].fillna(0).astype(int)
    rmult = pd.to_numeric(ds[rcol], errors="coerce").fillna(0.0)
    n_days = ds.loc[universe, "Session"].nunique()

    rows = []

    # ---- 1. a hipotese do usuario, isolada ------------------------------
    rows.append(evaluate_rule(ds, ds["AggTotalNorm_gt_prev"] == 1, y, rmult,
                              universe, "HIPOTESE: AggTotalNorm[t] > [t-1]",
                              n_days))
    rows.append(evaluate_rule(ds, ds["AggTotalNorm_lt_prev"] == 1, y, rmult,
                              universe, "controle: AggTotalNorm[t] < [t-1]",
                              n_days))
    # versoes por magnitude
    for q in (0.5, 0.7, 0.9):
        thr = ds.loc[universe, "AggTotalNorm_ratio1"].quantile(q)
        rows.append(evaluate_rule(
            ds, ds["AggTotalNorm_ratio1"] > thr, y, rmult, universe,
            f"AggTotalNorm_ratio1 > q{int(q * 100)} ({thr:.2f})", n_days))

    # ---- 2. varredura de TODAS as comparacoes t vs t-1 -----------------
    scan = []
    for col in F.prev_comparison_names():
        if col not in ds.columns:
            continue
        s = ds[col]
        if col.endswith(("_gt_prev", "_lt_prev")):
            cand_masks = [(col, s == 1)]
        else:
            thr = s[universe].median()
            cand_masks = [(f"{col} > mediana", s > thr),
                          (f"{col} < mediana", s < thr)]
        for nm, mk in cand_masks:
            r = evaluate_rule(ds, mk, y, rmult, universe, nm, n_days)
            if r.get("n", 0) >= 100:
                scan.append(r)

    sc = pd.DataFrame(scan).sort_values("edge", ascending=False)
    sc.to_csv(RESULTS_DIR / f"13_rule_scan_{target_suffix}.csv", index=False)

    out = {
        "target": target_suffix,
        "dev_only": dev_only,
        "n_universe": int(universe.sum()),
        "n_days": int(n_days),
        "base_rate": float(y[universe].mean()),
        "expectancy_R_base": float(rmult[universe].mean()),
        "hypothesis": rows,
        "scan_top10": sc.head(10).to_dict("records"),
        "scan_bottom5": sc.tail(5).to_dict("records"),
        "n_rules_scanned": len(sc),
        "n_rules_beating_base_at_95": int(sc["beats_base_at_95"].sum()),
        "expected_false_positives_at_95": round(0.05 * len(sc), 1),
    }
    (RESULTS_DIR / f"13_rule_test_{target_suffix}.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    _write_md(out, sc, target_suffix)
    return out


def _write_md(out: dict, sc: pd.DataFrame, suf: str) -> None:
    L = [f"# 13 — Teste de regras isoladas (`{suf}`)", "",
         f"Universo: {out['n_universe']} candidatos em {out['n_days']} "
         f"pregoes (apenas DESENVOLVIMENTO).  ",
         f"Taxa-base: **{out['base_rate']:.4f}** · "
         f"expectativa base: **{out['expectancy_R_base']:+.4f} R**", "",
         "## Hipotese do usuario, isolada", "",
         "| regra | n | /dia | precision | IC95 Wilson | taxa-base | edge | "
         "expectativa R | Δ vs base | bate a base? |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in out["hypothesis"]:
        if not r.get("n"):
            continue
        L.append(
            f"| {r['rule']} | {r['n']} | {r['n_per_day']} | "
            f"{r['precision']:.4f} | [{r['wilson_lo']:.4f}, {r['wilson_hi']:.4f}] | "
            f"{r['base_rate']:.4f} | {r['edge']:+.4f} | "
            f"{r['expectancy_R']:+.4f} | {r['expectancy_R_delta']:+.4f} | "
            f"{'SIM' if r['beats_base_at_95'] else 'nao'} |")
    L += ["", "## Varredura de todas as comparacoes t vs t-1", "",
          f"- regras testadas (n >= 100): **{out['n_rules_scanned']}**",
          f"- regras cujo IC95 fica acima da taxa-base: "
          f"**{out['n_rules_beating_base_at_95']}**",
          f"- falsos positivos esperados por acaso a 95%: "
          f"**{out['expected_false_positives_at_95']}**", "",
          "| regra | n | precision | IC95 | edge | expectativa R | Δ vs base |",
          "|---|---|---|---|---|---|---|"]
    for _, r in sc.head(15).iterrows():
        L.append(f"| `{r['rule']}` | {r['n']} | {r['precision']:.4f} | "
                 f"[{r['wilson_lo']:.4f}, {r['wilson_hi']:.4f}] | "
                 f"{r['edge']:+.4f} | {r['expectancy_R']:+.4f} | "
                 f"{r['expectancy_R_delta']:+.4f} |")
    (REPORTS_DIR / f"13_rule_test_{suf}.md").write_text("\n".join(L),
                                                        encoding="utf-8")


if __name__ == "__main__":
    for t in ("pts100p2", "pts100p3"):
        o = run(t)
        print(f"\n=== {t} ===  base={o['base_rate']:.4f}  "
              f"expR={o['expectancy_R_base']:+.4f}  n={o['n_universe']}")
        for r in o["hypothesis"]:
            if r.get("n"):
                print(f"  {r['rule']:44s} n={r['n']:5d} prec={r['precision']:.4f} "
                      f"[{r['wilson_lo']:.4f},{r['wilson_hi']:.4f}] "
                      f"edge={r['edge']:+.4f} expR={r['expectancy_R']:+.4f} "
                      f"{'BATE' if r['beats_base_at_95'] else ''}")
        print(f"  regras varridas: {o['n_rules_scanned']}, "
              f"batendo a base a 95%: {o['n_rules_beating_base_at_95']} "
              f"(esperado por acaso: {o['expected_false_positives_at_95']})")
