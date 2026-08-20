"""Validacao walk-forward (secoes 28 e 29).

Cada dobra constroi os niveis usando exclusivamente o periodo de treino e mede
o desempenho no ano seguinte, que o algoritmo nunca viu. A janela de treino e
expansiva: 2021-2023 -> testa 2024; 2021-2024 -> testa 2025; e assim por diante.
"""

from __future__ import annotations

from dataclasses import replace
from typing import List, Tuple

import numpy as np
import pandas as pd

from pipeline import run_pipeline
from validation.backtest import baseline_prices, compare, evaluate_prices


def make_folds(df: pd.DataFrame, min_train_years: int = 2) -> List[Tuple[pd.Timestamp, pd.Timestamp, int]]:
    """(inicio_treino, fim_treino, ano_de_teste) para cada dobra."""
    years = sorted(df.index.year.unique())
    start = df.index[0]
    folds = []
    for y in years[min_train_years:]:
        train_end = pd.Timestamp(year=y, month=1, day=1) - pd.Timedelta(minutes=1)
        if train_end <= start:
            continue
        folds.append((start, train_end, int(y)))
    return folds


def run(df: pd.DataFrame, cfg, tick: float, min_train_years: int = 2,
        horizon: int = 60, verbose: bool = True) -> pd.DataFrame:
    # Em cada dobra as linhas tem que ser centradas no preco vigente no FIM do
    # treino -- um preco de referencia fixo do usuario nao vale para 2023.
    cfg = replace(cfg, reference_price=None)
    rows = []
    for train_start, train_end, test_year in make_folds(df, min_train_years):
        train = df.loc[train_start:train_end]
        test = df.loc[str(test_year)]
        if len(train) < 5000 or len(test) < 1000:
            continue

        res = run_pipeline(train, cfg, tick, use_cache=False)
        if not res.selected:
            continue

        prices = [lv.price for lv in res.selected]
        scores = np.array([lv.score for lv in res.selected])

        lv_eval = evaluate_prices(test, prices, cfg, horizon=horizon)
        bs_eval = evaluate_prices(test, baseline_prices(train, test, len(prices) * 10, tick, cfg.seed),
                                  cfg, horizon=horizon)
        cmp = compare(lv_eval, bs_eval)

        # o score tambem precisa valer alguma coisa: niveis melhor pontuados
        # deveriam reagir mais fora da amostra
        s = lv_eval["mean_strength"].to_numpy()
        ok = np.isfinite(s)
        corr = float(np.corrcoef(scores[ok], s[ok])[0, 1]) if ok.sum() > 2 else np.nan

        row = {
            "teste": test_year,
            "treino_ate": train_end.date(),
            "n_niveis": len(prices),
            "pct_tocados": cmp["niveis"]["pct_tocados"],
            "toques_niveis": cmp["niveis"]["toques_medios"],
            "toques_controle": cmp["aleatorio"]["toques_medios"],
            "forca_niveis": cmp["niveis"]["forca_media"],
            "forca_controle": cmp["aleatorio"]["forca_media"],
            "razao": cmp["razao_forca"],
            "razao_toques": cmp["razao_toques"],
            "corr_score_forca": round(corr, 3) if np.isfinite(corr) else np.nan,
            "reacao_media_pts": cmp["niveis"]["reacao_media"],
            "min_ate_movimento": cmp["niveis"]["min_ate_movimento"],
            "min_ate_movimento_controle": cmp["aleatorio"]["min_ate_movimento"],
        }
        rows.append(row)
        if verbose:
            print(f"  [{test_year}] niveis={row['n_niveis']:>3} "
                  f"tocados={row['pct_tocados']:>5}% "
                  f"toques={row['toques_niveis']:>6} vs {row['toques_controle']:>6} | "
                  f"forca={row['forca_niveis']} vs {row['forca_controle']} "
                  f"(razao {row['razao']}) | corr(score,forca)={row['corr_score_forca']}")

    return pd.DataFrame(rows)
