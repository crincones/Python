"""
Detector automatico de niveis importantes -- ponto de entrada.

Uso tipico:
    python main.py
    python main.py --sep 400 --top 15
    python main.py --ate 2025-12-31 --walk-forward
    python main.py --metodo hierarchical --cor 200 0 0 --espessura 2 --estilo 0
    ---- CONFIG 1 MINI INDICE FUTURO
    python main.py --ref 172000 --sep 100  --desde 2021-01-01 --ate 2026-08-08 --box-ticks 50 --top 50 --faixa 10000 --vao-max 500 --metodo grade --min-eventos 2 --cor 90 90 150 --espessura 2 --estilo 1

A saida principal e output/niveis.ntsl (ProfitChart). Tambem sao gravados o CSV
dos niveis, o CSV dos eventos e um PNG de inspecao.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from export.ntsl import write_ntsl
from models.level import levels_to_frame
from pipeline import detect_events, load_and_prepare, renko_box, run_pipeline
from visualization.charts import plot_levels


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Detector automatico de niveis importantes")
    d = Config()

    p.add_argument("--csv", default=d.csv_path, help="arquivo de candles de 1 minuto")
    p.add_argument("--modo", default=d.mode, choices=["renko", "mtf"],
                   help="renko: analisa so o grafico Renko; mtf: multi-timeframe")
    p.add_argument("--box-ticks", type=int, default=d.renko_box_ticks,
                   help="tamanho da caixa do Renko em ticks, como no ProfitChart "
                        "(50R = 50 ticks = 245 pts no WIN)")
    p.add_argument("--box-pontos", type=float, default=None,
                   help="tamanho da caixa em pontos (sobrepoe --box-ticks)")
    p.add_argument("--ancora", type=float, default=d.renko_anchor,
                   help="ancora da grade do Renko (o ProfitChart usa 0)")
    p.add_argument("--desde", default=None, help="limite inicial do historico (AAAA-MM-DD)")
    p.add_argument("--ate", default=None, help="limite final do historico (AAAA-MM-DD)")

    p.add_argument("--sep", type=float, default=None,
                   help="separacao media desejada entre linhas, em pontos "
                        "(padrao: 0.75 x ATR de referencia mediano)")
    p.add_argument("--top", type=int, default=d.top_n, help="numero maximo de linhas")
    p.add_argument("--min-score", type=float, default=d.min_score)
    p.add_argument("--ref", type=float, default=None,
                   help="preco de referencia que centra as linhas "
                        "(padrao: ultimo fechamento do historico)")
    p.add_argument("--vao-max", type=float, default=None,
                   help="vao maximo entre linhas vizinhas, em pontos; vaos maiores "
                        "sao preenchidos com o melhor candidato disponivel "
                        "(pode passar de --top)")
    p.add_argument("--faixa", type=float, default=None,
                   help="janela de desenho: +-X pontos em torno da referencia "
                        "(padrao: top x separacao / 2; use 0 para nao limitar)")

    p.add_argument("--metodo", default=d.cluster_method,
                   choices=["kde", "grade", "dbscan", "hierarchical"],
                   help="grade: uma linha por nivel da grade do Renko (so no modo renko)")
    p.add_argument("--preco-evento", default=None,
                   choices=["renko", "extreme", "close", "mid", "reaction_price"],
                   help="renko|extreme|close no modo renko; "
                        "extreme|close|mid|reaction_price no modo mtf")
    p.add_argument("--preco-nivel", default=d.level_price_method,
                   choices=["weighted_median", "median", "mean", "weighted_mean", "density"])
    p.add_argument("--min-eventos", type=int, default=d.min_events)
    p.add_argument("--fator-cluster", type=float, default=d.cluster_atr_factor)
    p.add_argument("--forca-min", type=float, default=None,
                   help="reacao minima do evento: em caixas (renko) ou em "
                        "movimentos esperados (mtf)")
    p.add_argument("--fator-caixa", type=float, default=d.cluster_box_factor,
                   help="banda de agrupamento, em caixas (modo renko)")
    p.add_argument("--meia-vida", type=float, default=d.recency_half_life_days)

    p.add_argument("--cor", nargs=3, type=int, default=list(d.ntsl_color_rgb),
                   metavar=("R", "G", "B"), help="cor padrao das linhas no NTSL")
    p.add_argument("--espessura", type=int, default=d.ntsl_width)
    p.add_argument("--estilo", type=int, default=d.ntsl_style,
                   help="0=solida 1=tracejada 2=pontilhada 3=traco-ponto 4=traco-ponto-ponto")

    p.add_argument("--out", default=d.out_dir)
    p.add_argument("--sem-grafico", action="store_true")
    p.add_argument("--dias-grafico", type=int, default=d.chart_last_days,
                   help="janela do grafico de inspecao, em dias (0 = todo o historico)")
    p.add_argument("--sem-cache", action="store_true")
    p.add_argument("--walk-forward", action="store_true",
                   help="roda a validacao fora da amostra (mais lento)")
    return p.parse_args(argv)


def build_config(a: argparse.Namespace) -> Config:
    d = Config()
    renko = a.modo == "renko"

    price_method = a.preco_evento or (d.renko_price_method if renko else d.event_price_method)
    if renko and price_method not in ("renko", "extreme", "close"):
        raise SystemExit(f"--preco-evento {price_method} nao existe no modo renko")
    if not renko and price_method == "renko":
        raise SystemExit("--preco-evento renko so existe no modo renko")

    forca = a.forca_min
    return replace(
        d,
        mode=a.modo, csv_path=a.csv, date_from=a.desde, date_to=a.ate,
        renko_box_ticks=a.box_ticks, renko_box_points=a.box_pontos, renko_anchor=a.ancora,
        cluster_method=a.metodo,
        event_price_method=price_method if not renko else d.event_price_method,
        renko_price_method=price_method if renko else d.renko_price_method,
        cluster_space="linear" if renko else "log",
        level_price_method=a.preco_nivel, min_events=a.min_eventos,
        cluster_atr_factor=a.fator_cluster, cluster_box_factor=a.fator_caixa,
        renko_min_strength=forca if (renko and forca is not None) else d.renko_min_strength,
        min_reaction_strength=forca if (not renko and forca is not None) else d.min_reaction_strength,
        recency_half_life_days=a.meia_vida, top_n=a.top, min_score=a.min_score,
        level_separation=a.sep, window_points=a.faixa, reference_price=a.ref,
        max_gap=a.vao_max,
        out_dir=a.out,
        ntsl_color_rgb=tuple(a.cor), ntsl_width=a.espessura, ntsl_style=a.estilo,
        cache=not a.sem_cache,
    )


def main(argv=None) -> int:
    a = parse_args(argv)
    cfg = build_config(a)
    os.makedirs(cfg.out_dir, exist_ok=True)
    t0 = time.time()

    # ------------------------------------------------------------ 1. dados
    print(f"[1/5] carregando {cfg.csv_path} ...")
    df, tick, report = load_and_prepare(cfg)
    print(f"      {report['linhas_validas']:,} candles validos "
          f"({report['descartadas_invalidas']} descartados) | "
          f"{report['inicio']} -> {report['fim']}")
    print(f"      tick size = {tick:g} | continuidade 1m = {report['pct_continuidade_1m']}% | "
          f"gaps = {report['gaps']} | volume = "
          f"{'disponivel' if report['volume_disponivel'] else 'ausente'}")

    # -------------------------------------------------- 2. eventos + niveis
    if cfg.mode == "renko":
        box = renko_box(cfg, tick)
        print(f"[2/5] construindo o Renko ({cfg.renko_box_ticks}R = {box:g} pts) "
              f"e detectando giros ...")
    else:
        print("[2/5] detectando eventos (swings, niveis de referencia, reacoes) ...")
    det = detect_events(df, cfg, tick, use_cache=cfg.cache)
    if det.bricks is not None:
        print(f"      {len(det.bricks):,} tijolos | {len(det.events):,} giros "
              f"independentes (forca >= {cfg.renko_min_strength:g})")
    else:
        print(f"      {len(det.events):,} eventos independentes")

    print(f"[3/5] clustering ({cfg.cluster_method}) e scoring ...")
    res = run_pipeline(df, cfg, tick, use_cache=cfg.cache, precomputed=det)
    if not res.selected:
        print("      nenhum nivel selecionado -- afrouxe --min-eventos ou --forca-min")
        return 1

    prices = np.array([lv.price for lv in res.selected])
    gaps = np.abs(np.diff(np.sort(prices)))
    sep_media = float(gaps.mean()) if gaps.size else 0.0
    if cfg.max_gap and len(res.selected) > cfg.top_n:
        print(f"      {len(res.selected) - cfg.top_n} linhas alem do --top {cfg.top_n} "
              f"para cobrir vaos maiores que {cfg.max_gap:.0f} pts")
    print(f"      {res.info['n_niveis']} candidatos -> {len(res.selected)} linhas | "
          f"separacao minima {res.separation:.0f} pts | media obtida {sep_media:.0f} pts"
          f" | maior vao {gaps.max() if gaps.size else 0:.0f} pts")
    if res.info.get("maior_cluster", 0) > 0.20:
        print(f"      AVISO: o maior cluster concentra "
              f"{100 * res.info['maior_cluster']:.0f}% dos eventos agrupados "
              f"(encadeamento). Use --metodo kde/hierarchical ou reduza --fator-cluster.")

    # ----------------------------------------------------------- 4. saidas
    print("[4/5] gravando saidas ...")
    frame = levels_to_frame(res.selected)
    csv_path = os.path.join(cfg.out_dir, "niveis.csv")
    frame.to_csv(csv_path, index=False, float_format="%.4f")

    ev_path = os.path.join(cfg.out_dir, "eventos.csv.gz")
    res.events.assign(cluster=res.labels, weight=res.weights).to_csv(
        ev_path, index=False, compression="gzip", float_format="%.4f")

    meta = {
        "inicio": df.index[0], "fim": df.index[-1], "n_candles": len(df), "tick": tick,
        "n_eventos": len(res.events), "metodo": cfg.cluster_method,
        "banda_pts": res.info["band_pts"], "modo": cfg.mode,
        "box_ticks": cfg.renko_box_ticks, "referencia": res.info.get("ref_price"),
        "caixa": res.detection.box, "n_tijolos": len(res.detection.bricks)
        if res.detection.bricks is not None else 0,
        "separacao": res.separation, "sep_media": sep_media,
        "n_niveis_totais": res.info["n_niveis"],
    }
    ntsl_path = write_ntsl(res.selected, cfg, meta, os.path.join(cfg.out_dir, "niveis.ntsl"))

    png_path = None
    if not a.sem_grafico:
        dens = (res.info["grid"], res.info["density"]) if "grid" in res.info else None
        escala = (f"Renko {cfg.renko_box_ticks}R ({res.detection.box:g} pts)"
                  if cfg.mode == "renko" else "multi-timeframe")
        png_path = plot_levels(
            df, res.selected, os.path.join(cfg.out_dir, "niveis.png"),
            chart_tf=cfg.chart_tf,
            title=f"Niveis importantes | {escala} | analisado {df.index[0]:%d/%m/%Y} a "
                  f"{df.index[-1]:%d/%m/%Y} | {cfg.cluster_method} | "
                  f"top {len(res.selected)} | grafico: ultimos {a.dias_grafico} dias",
            density=dens,
            last_days=a.dias_grafico,
            bricks=res.detection.bricks,
        )

    # ----------------------------------------------------- 5. tabela final
    print("\n  #    Preco      Score   Ev  Dias  Meses  Span(d)  Esc  Ultimo evento")
    print("  " + "-" * 70)
    for i, lv in enumerate(res.selected, 1):
        print(f"  {i:<4} {lv.price:>9,.0f}  {lv.score:>6.1f}  {lv.n_events:>3}  "
              f"{lv.unique_days:>4}  {lv.unique_months:>5}  {lv.span_days:>7.0f}  "
              f"{lv.n_scales:>3}  {lv.last_event:%d/%m/%Y}")

    if a.walk_forward:
        from validation.walk_forward import run as wf_run
        print("\n[5/5] validacao walk-forward (constroi no passado, mede no futuro) ...")
        wf = wf_run(df, cfg, tick)
        if not wf.empty:
            wf_path = os.path.join(cfg.out_dir, "walk_forward.csv")
            wf.to_csv(wf_path, index=False)
            print(f"\n      razao media niveis/aleatorio = {wf['razao'].mean():.3f} "
                  f"(>1 indica poder preditivo fora da amostra)")
            print(f"      -> {wf_path}")

    print(f"\nOK em {time.time() - t0:.1f}s")
    print(f"  NTSL   -> {ntsl_path}")
    print(f"  CSV    -> {csv_path}")
    print(f"  eventos-> {ev_path}")
    if png_path:
        print(f"  grafico-> {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
