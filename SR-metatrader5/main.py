"""
Detector automatico de niveis importantes -- saida para MetaTrader 5.

Le o CSV de 1 minuto mantido pelo projeto baixar-ohlc-fx, roda o mesmo motor do
SR-profitchart3 (Renko -> giros -> clustering -> score) e grava um CSV por
simbolo na pasta MQL5/Files do terminal. O indicador SR_Levels.mq5 le esse
arquivo e desenha as linhas no grafico.

DISTANCIAS EM PONTOS DO MT5
    --sep, --vao-max, --faixa e --box-ticks sao dados em PONTOS (1 ponto =
    1 tick = 10^-digits). Para o USDJPY (digits=3) 1 ponto = 0.001, ou seja
    10 pontos = 1 pip. Assim os valores da linha de comando nao mudam quando
    voce troca de par.

Uso tipico:
    python main.py
    python main.py --symbol USDJPY --box-ticks 50 --sep 100 --top 25
    python main.py --desde 2026-06-01 --vao-max 400 --faixa 4000
    python main.py --instalar          # copia o SR_Levels.mq5 para Indicators
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BASE_DIR, MQL5_FILES_DIR, MQL5_INDICATORS_DIR, Config
from export.mql5 import install_indicator, write_csv
from models.level import levels_to_frame
from pipeline import detect_events, load_and_prepare, renko_box, run_pipeline
from visualization.charts import plot_levels

INDICADOR = os.path.join(BASE_DIR, "mql5", "SR_Levels.mq5")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detector de niveis importantes com saida para MetaTrader 5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    d = Config()

    p.add_argument("--symbol", default=d.symbol,
                   help=f"simbolo do MT5 (padrao: {d.symbol}); define o CSV de "
                        "entrada e o nome do arquivo de saida")
    p.add_argument("--csv", default=None,
                   help="CSV de 1 minuto (padrao: <baixar-ohlc-fx>/<SYMBOL>_M1.csv)")
    p.add_argument("--modo", default=d.mode, choices=["renko", "mtf"],
                   help="renko: analisa so o grafico Renko; mtf: multi-timeframe")
    p.add_argument("--box-ticks", type=int, default=d.renko_box_ticks,
                   help="tamanho da caixa do Renko, em pontos do MT5 "
                        "(USDJPY: 50 = 0.050 = 5 pips)")
    p.add_argument("--box-preco", type=float, default=None,
                   help="tamanho da caixa em unidades de preco (sobrepoe --box-ticks)")
    p.add_argument("--ancora", type=float, default=d.renko_anchor,
                   help="ancora da grade do Renko")
    p.add_argument("--desde", default=None, help="limite inicial do historico (AAAA-MM-DD)")
    p.add_argument("--ate", default=None, help="limite final do historico (AAAA-MM-DD)")
    p.add_argument("--digits", type=int, default=None,
                   help="casas decimais do simbolo (padrao: derivado do tick inferido)")

    p.add_argument("--sep", type=float, default=None,
                   help="separacao minima entre linhas, em pontos (padrao: a caixa)")
    p.add_argument("--top", type=int, default=d.top_n, help="numero maximo de linhas")
    p.add_argument("--min-score", type=float, default=d.min_score)
    p.add_argument("--ref", type=float, default=None,
                   help="PRECO de referencia que centra as linhas "
                        "(padrao: ultimo fechamento do historico)")
    p.add_argument("--vao-max", type=float, default=None,
                   help="vao maximo entre linhas vizinhas, em pontos; vaos maiores "
                        "sao preenchidos com o melhor candidato (pode passar de --top)")
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

    p.add_argument("--out", default=d.out_dir)
    p.add_argument("--files", default=d.mql5_files_dir,
                   help="pasta MQL5/Files do terminal (padrao: config.py)")
    p.add_argument("--sem-mt5", action="store_true",
                   help="nao copia o CSV para a pasta Files; grava so em --out")
    p.add_argument("--instalar", action="store_true",
                   help="copia o SR_Levels.mq5 para a pasta Indicators do terminal")
    p.add_argument("--sem-grafico", action="store_true")
    p.add_argument("--dias-grafico", type=int, default=d.chart_last_days,
                   help="janela do grafico de inspecao, em dias (0 = todo o historico)")
    p.add_argument("--sem-cache", action="store_true")
    p.add_argument("--walk-forward", action="store_true",
                   help="roda a validacao fora da amostra (mais lento)")
    return p.parse_args(argv)


def build_config(a: argparse.Namespace) -> Config:
    """Config sem as distancias: elas so podem ser convertidas depois do tick."""
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
        symbol=a.symbol, csv_path=a.csv, date_from=a.desde, date_to=a.ate,
        digits=a.digits,
        mode=a.modo,
        renko_box_ticks=a.box_ticks, renko_box_points=a.box_preco, renko_anchor=a.ancora,
        cluster_method=a.metodo,
        event_price_method=price_method if not renko else d.event_price_method,
        renko_price_method=price_method if renko else d.renko_price_method,
        cluster_space="linear" if renko else "log",
        level_price_method=a.preco_nivel, min_events=a.min_eventos,
        cluster_atr_factor=a.fator_cluster, cluster_box_factor=a.fator_caixa,
        renko_min_strength=forca if (renko and forca is not None) else d.renko_min_strength,
        min_reaction_strength=forca if (not renko and forca is not None) else d.min_reaction_strength,
        recency_half_life_days=a.meia_vida, top_n=a.top, min_score=a.min_score,
        reference_price=a.ref,
        out_dir=a.out,
        mql5_files_dir=None if a.sem_mt5 else a.files,
        cache=not a.sem_cache,
    )


def aplicar_pontos(cfg: Config, a: argparse.Namespace, tick: float) -> Config:
    """Converte as distancias da linha de comando (pontos) em unidades de preco."""
    def px(valor):
        return None if valor is None else float(valor) * tick

    return replace(cfg,
                   level_separation=px(a.sep),
                   window_points=px(a.faixa),
                   max_gap=px(a.vao_max))


def digits_do_tick(tick: float) -> int:
    """Casas decimais implicadas pelo tick (0.001 -> 3, 1 -> 0, 5 -> 0)."""
    if tick <= 0:
        return 0
    return max(0, int(round(-math.log10(tick))))


def main(argv=None) -> int:
    a = parse_args(argv)
    cfg = build_config(a)
    os.makedirs(cfg.out_dir, exist_ok=True)
    t0 = time.time()

    if a.instalar:
        alvo = install_indicator(cfg, INDICADOR, MQL5_INDICATORS_DIR)
        print(f"indicador instalado -> {alvo}")
        print("      abra o MetaEditor e compile (F7) antes de usar.\n")

    # ------------------------------------------------------------ 1. dados
    print(f"[1/5] carregando {cfg.historico} ...")
    if not os.path.exists(cfg.historico):
        raise SystemExit(
            f"historico nao encontrado: {cfg.historico}\n"
            f"Rode primeiro: python atualiza-historico.py --symbol {cfg.symbol}\n"
            f"(no projeto baixar-ohlc-fx)"
        )
    df, tick, report = load_and_prepare(cfg)
    digits = cfg.digits if cfg.digits is not None else digits_do_tick(tick)
    cfg = aplicar_pontos(cfg, a, tick)

    def pf(x) -> str:                      # preco
        return f"{x:,.{digits}f}"

    def df_(x) -> str:                     # distancia: preco + pontos
        return f"{x:,.{digits}f} ({x / tick:,.0f} pts)"

    print(f"      {report['linhas_validas']:,} candles validos "
          f"({report['descartadas_invalidas']} descartados) | "
          f"{report['inicio']} -> {report['fim']}")
    print(f"      simbolo = {cfg.symbol} | tick = {tick:g} | digits = {digits} | "
          f"continuidade 1m = {report['pct_continuidade_1m']}% | gaps = {report['gaps']} | "
          f"volume = {'disponivel' if report['volume_disponivel'] else 'ausente'}")

    # -------------------------------------------------- 2. eventos + niveis
    if cfg.mode == "renko":
        box = renko_box(cfg, tick)
        print(f"[2/5] construindo o Renko (caixa {df_(box)}) e detectando giros ...")
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
              f"para cobrir vaos maiores que {df_(cfg.max_gap)}")
    print(f"      {res.info['n_niveis']} candidatos -> {len(res.selected)} linhas | "
          f"separacao minima {df_(res.separation)} | media obtida {df_(sep_media)} | "
          f"maior vao {df_(gaps.max() if gaps.size else 0.0)}")
    if res.info.get("maior_cluster", 0) > 0.20:
        print(f"      AVISO: o maior cluster concentra "
              f"{100 * res.info['maior_cluster']:.0f}% dos eventos agrupados "
              f"(encadeamento). Use --metodo kde/hierarchical ou reduza --fator-cluster.")

    # ----------------------------------------------------------- 4. saidas
    print("[4/5] gravando saidas ...")
    frame = levels_to_frame(res.selected)
    frame.to_csv(os.path.join(cfg.out_dir, "niveis.csv"), index=False, float_format="%.6f")

    ev_path = os.path.join(cfg.out_dir, "eventos.csv.gz")
    res.events.assign(cluster=res.labels, weight=res.weights).to_csv(
        ev_path, index=False, compression="gzip", float_format="%.6f")

    meta = {
        "symbol": cfg.symbol, "historico": cfg.historico,
        "inicio": df.index[0], "fim": df.index[-1], "n_candles": len(df),
        "tick": tick, "digits": digits,
        "modo": cfg.mode, "box_ticks": cfg.renko_box_ticks, "caixa": res.detection.box,
        "n_tijolos": len(res.detection.bricks) if res.detection.bricks is not None else 0,
        "n_eventos": len(res.events), "metodo": cfg.cluster_method,
        "banda": res.info["band_pts"], "referencia": res.info.get("ref_price"),
        "separacao": res.separation, "sep_media": sep_media,
        "n_niveis_totais": res.info["n_niveis"], "n_linhas": len(res.selected),
    }
    saidas = write_csv(res.selected, cfg, digits, meta)

    png_path = None
    if not a.sem_grafico:
        dens = (res.info["grid"], res.info["density"]) if "grid" in res.info else None
        escala = (f"Renko {cfg.renko_box_ticks} pts ({res.detection.box:g})"
                  if cfg.mode == "renko" else "multi-timeframe")
        png_path = plot_levels(
            df, res.selected, os.path.join(cfg.out_dir, "niveis.png"),
            chart_tf=cfg.chart_tf,
            title=f"{cfg.symbol} | {escala} | analisado {df.index[0]:%d/%m/%Y} a "
                  f"{df.index[-1]:%d/%m/%Y} | {cfg.cluster_method} | "
                  f"top {len(res.selected)} | grafico: ultimos {a.dias_grafico} dias",
            density=dens,
            last_days=a.dias_grafico,
            bricks=res.detection.bricks,
            digits=digits,
        )

    # ----------------------------------------------------- 5. tabela final
    largura = max(9, digits + 8)
    print(f"\n  #    {'Preco':>{largura}}   Score   Ev  Dias  Meses  Span(d)  Esc  Ultimo evento")
    print("  " + "-" * (62 + largura))
    for i, lv in enumerate(res.selected, 1):
        print(f"  {i:<4} {pf(lv.price):>{largura}}  {lv.score:>6.1f}  {lv.n_events:>3}  "
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
    if saidas["mt5"]:
        print(f"  MT5    -> {saidas['mt5']}")
        print(f"            adicione o indicador SR_Levels no grafico de {cfg.symbol}")
    else:
        print(f"  CSV    -> {saidas['local']}  (copie para {MQL5_FILES_DIR})")
    print(f"  local  -> {saidas['local']}")
    print(f"  meta   -> {saidas['meta']}")
    print(f"  eventos-> {ev_path}")
    if png_path:
        print(f"  grafico-> {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
