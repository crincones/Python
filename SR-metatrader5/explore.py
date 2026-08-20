"""
Script exploratorio (secao 40 do descritivo).

Roda o pipeline em uma AMOSTRA do historico, imprimindo o que cada etapa
produziu, para que a definicao matematica de "nivel importante" possa ser
inspecionada antes de qualquer otimizacao:

  1. carrega uma amostra dos dados
  2. calcula ATR
  3. detecta eventos
  4. visualiza os eventos sobre os candles
  5. faz clustering
  6. visualiza as linhas resultantes
  7. permite inspecionar manualmente os niveis
  8. mede estatisticamente as reacoes posteriores

Uso:
    python explore.py --meses 12
    python explore.py --meses 24 --metodo hierarchical
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from data.resampling import atr, resample_ohlcv
from pipeline import load_and_prepare, run_pipeline
from validation.backtest import baseline_prices, compare, evaluate_prices
from visualization.charts import plot_levels


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Exploracao passo a passo do detector")
    p.add_argument("--symbol", default=Config().symbol)
    p.add_argument("--csv", default=None,
                   help="CSV de 1 minuto (padrao: derivado de --symbol)")
    p.add_argument("--meses", type=int, default=12, help="tamanho da amostra")
    p.add_argument("--metodo", default="kde", choices=["kde", "grade", "dbscan", "hierarchical"])
    p.add_argument("--modo", default="renko", choices=["renko", "mtf"])
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--out", default="output/explore")
    a = p.parse_args(argv)

    cfg = replace(Config(), symbol=a.symbol, csv_path=a.csv, cluster_method=a.metodo,
                  top_n=a.top, out_dir=a.out, cache=False, mode=a.modo,
                  cluster_space="linear" if a.modo == "renko" else "log")
    os.makedirs(cfg.out_dir, exist_ok=True)

    # ------------------------------------------------- 1. amostra dos dados
    df_full, tick, rep = load_and_prepare(cfg)
    cut = df_full.index[-1] - pd.DateOffset(months=a.meses)
    df = df_full.loc[df_full.index >= cut]
    print(f"1) amostra: {len(df):,} candles de 1m | {df.index[0]} -> {df.index[-1]} "
          f"| tick={tick:g}")

    # ------------------------------------------- 2. volatilidade / estrutura
    for rule in ("15min", "1h", "1D"):
        bars = resample_ohlcv(df, rule)
        a_ = atr(bars, cfg.atr_period).dropna()
        # tudo em PONTOS DO MT5 (1 ponto = 1 tick), para nao depender das casas
        # decimais do simbolo
        print(f"2) ATR {rule:>5}: mediano={a_.median() / tick:8.0f} pts | "
              f"p10={a_.quantile(.10) / tick:7.0f} | p90={a_.quantile(.90) / tick:7.0f} "
              f"| barras={len(bars):,}")

    # ------------------------------------------- 3. eventos + 5. clustering
    res = run_pipeline(df, cfg, tick, use_cache=False)
    ev = res.events
    if res.detection.bricks is not None:
        b = res.detection.bricks
        print(f"   Renko caixa {cfg.renko_box_ticks} pts = {res.detection.box:g} | "
              f"{len(b):,} tijolos | {len(b) / max((df.index[-1] - df.index[0]).days, 1):.1f} "
              f"tijolos/dia")
    print(f"3) eventos independentes: {len(ev):,}")
    print(ev.groupby(["scale", "source"]).agg(
        n=("price", "size"), forca_media=("strength", "mean")).round(2).to_string())
    print(f"   forca da reacao: mediana={ev['strength'].median():.2f} "
          f"| p90={ev['strength'].quantile(.9):.2f} | max={ev['strength'].max():.2f}")

    print(f"5) clustering ({cfg.cluster_method}, espaco {res.info['space']}): "
          f"{res.info['n_clusters']} clusters | banda={res.info['band_pts'] / tick:.0f} pts | "
          f"eventos sem cluster={res.info['n_ruido']:,}")

    # --------------------------------- 4. eventos sobre os candles (grafico)
    bars = resample_ohlcv(df, "1D")
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(bars.index, bars["close"], color="#555", linewidth=0.7, zorder=1)
    sc = ax.scatter(ev["timestamp"], ev["price"], s=6,
                    c=np.clip(ev["strength"], 0, 5),
                    cmap="viridis", alpha=0.6, zorder=2)
    fig.colorbar(sc, ax=ax, label="forca da reacao")
    ax.set_title(f"4) eventos detectados sobre o preco -- amostra de {a.meses} meses")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    p4 = os.path.join(cfg.out_dir, "eventos.png")
    fig.savefig(p4, dpi=120)
    plt.close(fig)

    # ---------------------------------------- 6. linhas resultantes (grafico)
    dens = (res.info["grid"], res.info["density"]) if "grid" in res.info else None
    p6 = plot_levels(df, res.selected, os.path.join(cfg.out_dir, "niveis.png"),
                     chart_tf="1D", density=dens, bricks=res.detection.bricks,
                     title=f"6) niveis -- {cfg.mode} / {cfg.cluster_method} -- "
                           f"amostra de {a.meses} meses")

    # ------------------------------------------------- 7. inspecao manual
    print("\n7) niveis selecionados (inspecao manual):")
    frame = pd.DataFrame([{
        "preco": lv.price, "score": lv.score, "eventos": lv.n_events,
        "dias": lv.unique_days, "meses": lv.unique_months,
        "span_d": round(lv.span_days), "escalas": lv.n_scales,
        "forca_media": round(lv.mean_strength, 2),
        "reacao_pts": round(lv.mean_reaction / tick),
        "ultimo": lv.last_event.strftime("%d/%m/%Y"),
    } for lv in res.selected])
    print(frame.to_string(index=False))

    # ------------------------------------- 8. estatisticas das reacoes
    print("\n8) reacoes posteriores medidas NA PROPRIA amostra (in-sample, "
          "apenas para inspecao -- o teste honesto e o walk-forward):")
    prices = [lv.price for lv in res.selected]
    lv_eval = evaluate_prices(df, prices, cfg, horizon=60)
    bs_eval = evaluate_prices(df, baseline_prices(df, df, len(prices) * 10, tick, cfg.seed),
                              cfg, horizon=60)
    cmp = compare(lv_eval, bs_eval)
    print(f"   niveis   : {cmp['niveis']}")
    print(f"   controle : {cmp['aleatorio']}")
    print(f"   razao de forca = {cmp['razao_forca']} | razao de toques = {cmp['razao_toques']}")

    print(f"\n   graficos -> {p4}\n              {p6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
