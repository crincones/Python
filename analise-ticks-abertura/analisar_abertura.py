"""
analisar_abertura.py
=====================

Analisa o CSV de ticks (formato de exportação MT5: DATE, TIME, BID, ASK, LAST,
VOLUME, FLAGS) capturado na abertura do mercado e responde a uma pergunta
prática de execução:

    "Em que momento / sob qual condição dá para colocar uma ordem SELL STOP
     abaixo do preço LAST, ou é preciso esperar bid/ask se formarem?"

O script:
  1. Carrega o(s) CSV da pasta (ou um caminho passado por argumento).
  2. Reconstrói, tick a tick, o estado de bid/ask/last (forward-fill).
  3. Detecta quotes "lixo" (spread negativo ou absurdamente largo) - comuns
     no primeiro instante do leilão de abertura.
  4. Mede a cadência de atualização do bid/ask vs. a cadência do LAST
     (quantos negócios acontecem "no escuro", sem bid/ask novo).
  5. Calcula a distribuição do spread (ask-bid) válido e sugere uma
     distância mínima de segurança para o stop, em pontos e em ticks.
  6. Aponta o timestamp/índice a partir do qual o book já está "confiável"
     (primeiro bid&ask sensato, e o instante em que o spread deixa de
     apresentar outliers).
  7. Gera um relatório em texto e um gráfico (PNG) com last/bid/ask/spread
     ao longo do tempo, marcando os pontos relevantes.

Uso:
    python analisar_abertura.py                     # pega o único CSV da pasta
    python analisar_abertura.py caminho\arquivo.csv  # CSV específico
    python analisar_abertura.py --spread-max 100 --buffer-ticks 2

Saída:
    - Relatório impresso no console
    - relatorio_abertura.txt (mesmo relatório, salvo)
    - grafico_abertura.png (gráfico)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # não depende de display para gerar o PNG
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Carregamento
# --------------------------------------------------------------------------- #

def localizar_csv(pasta: Path) -> Path:
    """Se nenhum caminho for passado, usa o único CSV da pasta do script."""
    candidatos = sorted(pasta.glob("*.csv"))
    if not candidatos:
        raise FileNotFoundError(f"Nenhum .csv encontrado em {pasta}")
    if len(candidatos) > 1:
        print("[aviso] mais de um CSV na pasta, usando o mais recente:")
        for c in candidatos:
            print("   -", c.name)
        candidatos.sort(key=lambda p: p.stat().st_mtime)
    return candidatos[-1]


def carregar_ticks(caminho: Path) -> pd.DataFrame:
    """
    Lê o export de ticks do MT5 (separado por TAB, cabeçalho <DATE> <TIME> ...).
    Retorna um DataFrame indexado por datetime, com colunas bid/ask/last/volume/flags
    já convertidas para número (NaN onde o campo veio vazio).
    """
    df = pd.read_csv(
        caminho,
        sep="\t",
        header=0,
        names=["date", "time", "bid", "ask", "last", "volume", "flags"],
        dtype={"date": str, "time": str},
        na_values=["", " "],
        keep_default_na=True,
    )

    dt = pd.to_datetime(
        df["date"] + " " + df["time"],
        format="%Y.%m.%d %H:%M:%S.%f",
    )
    df["datetime"] = dt
    df = df.set_index("datetime").sort_index()

    for col in ("bid", "ask", "last", "volume", "flags"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Classifica cada linha pelo que ela realmente traz de novo
    tem_bid = df["bid"].notna()
    tem_ask = df["ask"].notna()
    tem_last = df["last"].notna()

    condicoes = [
        tem_bid & tem_ask,
        tem_bid & ~tem_ask,
        ~tem_bid & tem_ask,
        tem_last,
    ]
    categorias = ["BID+ASK", "BID", "ASK", "LAST"]
    df["tipo"] = np.select(condicoes, categorias, default="OUTRO")

    return df


# --------------------------------------------------------------------------- #
# Reconstrução do estado de book (forward-fill) e limpeza de quotes-lixo
# --------------------------------------------------------------------------- #

def reconstruir_estado(df: pd.DataFrame, spread_max: float) -> pd.DataFrame:
    """
    Propaga bid/ask/last para frente (o valor "vigente" em cada instante é o
    último publicado) e marca como inválida qualquer combinação bid/ask cujo
    spread seja negativo ou maior que `spread_max` pontos - sintoma clássico
    de quote de abertura ainda não normalizado.
    """
    out = df.copy()
    out["bid_ff"] = out["bid"].ffill()
    out["ask_ff"] = out["ask"].ffill()
    out["last_ff"] = out["last"].ffill()

    out["spread_ff"] = out["ask_ff"] - out["bid_ff"]
    out["spread_valido"] = out["spread_ff"].between(0, spread_max)

    return out


def detectar_tick_size(last: pd.Series) -> float:
    """Tick size = menor variação positiva mais frequente do LAST."""
    diffs = last.dropna().diff().abs()
    diffs = diffs[diffs > 0]
    if diffs.empty:
        return 5.0
    return float(diffs.mode().iloc[0])


def agrupar_ciclos_de_quote(df: pd.DataFrame, gap_cluster_ms: float = 50.0) -> pd.DataFrame:
    """
    O book normalmente publica BID e ASK como DOIS ticks separados (não
    atômicos), poucos milissegundos um do outro (ex.: BID às 09:03:05.123 e
    ASK às 09:03:05.123-05.126). Olhando linha a linha, existe uma janela
    curtíssima em que o lado ainda não atualizado está "velho" - o que pode
    gerar spread aparentemente negativo ou anormalmente largo sem que o
    mercado tenha, de fato, ficado cruzado.

    Esta função agrupa ticks de bid/ask que chegam próximos no tempo
    (gap <= gap_cluster_ms) em "ciclos de atualização" e devolve apenas o
    estado final (assentado/"settled") de cada ciclo - a leitura correta de
    bid&ask depois que os dois lados já se atualizaram.
    """
    q = df[df["tipo"].isin(["BID", "ASK", "BID+ASK"])].copy()
    if q.empty:
        return q.assign(spread_settled=pd.Series(dtype=float))

    gap_ms = q.index.to_series().diff().dt.total_seconds() * 1000
    cluster_id = (gap_ms > gap_cluster_ms).cumsum()
    q["ciclo"] = cluster_id.values

    settled = q.groupby("ciclo").tail(1).copy()
    settled["spread_settled"] = settled["ask_ff"] - settled["bid_ff"]
    return settled


# --------------------------------------------------------------------------- #
# Métricas
# --------------------------------------------------------------------------- #

def calcular_metricas(df: pd.DataFrame, spread_max: float, gap_cluster_ms: float = 50.0) -> dict:
    inicio = df.index[0]
    fim = df.index[-1]

    quotes = df[(df["tipo"] == "BID+ASK") | (df["tipo"] == "BID") | (df["tipo"] == "ASK")]
    trades = df[df["tipo"] == "LAST"]

    # --- ciclos "assentados" (bid&ask já ambos atualizados) -------------- #
    settled = agrupar_ciclos_de_quote(df, gap_cluster_ms=gap_cluster_ms)
    settled_valido = settled["spread_settled"].between(0, spread_max)

    primeiro_quote_valido = (
        settled.index[settled_valido][0] if settled_valido.any() else None
    )
    n_ciclos_lixo = int((~settled_valido).sum())

    gaps_ciclos_ms = settled.index.to_series().diff().dt.total_seconds().dropna() * 1000

    # cadência bruta de ticks de bid/ask individuais (para contraste)
    t_quotes = quotes.index.to_series()
    gaps_quotes_ms = t_quotes.diff().dt.total_seconds().dropna() * 1000

    # cadência do LAST
    t_trades = trades.index.to_series()
    gaps_trades_ms = t_trades.diff().dt.total_seconds().dropna() * 1000

    # quantos negócios (LAST) acontecem dentro de cada ciclo de quote
    trades_por_ciclo = []
    ciclo_idx = list(settled.index)
    if len(ciclo_idx) > 1:
        for a, b in zip(ciclo_idx[:-1], ciclo_idx[1:]):
            n = int(((df.index > a) & (df.index <= b) & (df["tipo"] == "LAST")).sum())
            trades_por_ciclo.append(n)

    # quanto de "cruzamento" (spread negativo) some quando olhamos o ciclo
    # assentado em vez do tick cru intermediário
    brutos_duplos = df[df["bid_ff"].notna() & df["ask_ff"].notna()]
    n_neg_bruto = int(((brutos_duplos["ask_ff"] - brutos_duplos["bid_ff"]) < 0).sum())
    n_neg_settled = int((settled["spread_settled"] < 0).sum())

    spread_valido_serie = settled.loc[settled_valido, "spread_settled"]

    tick_size = detectar_tick_size(df["last"])

    return dict(
        inicio=inicio,
        fim=fim,
        duracao_s=(fim - inicio).total_seconds(),
        n_ticks=len(df),
        n_trades=len(trades),
        n_quotes=len(quotes),
        n_ciclos=len(settled),
        primeiro_quote_valido=primeiro_quote_valido,
        latencia_primeiro_quote_ms=(
            (primeiro_quote_valido - inicio).total_seconds() * 1000
            if primeiro_quote_valido is not None else None
        ),
        n_ciclos_lixo=n_ciclos_lixo,
        n_neg_bruto=n_neg_bruto,
        n_neg_settled=n_neg_settled,
        gap_quotes_mediano_ms=float(gaps_quotes_ms.median()) if not gaps_quotes_ms.empty else None,
        gap_ciclos_mediano_ms=float(gaps_ciclos_ms.median()) if not gaps_ciclos_ms.empty else None,
        gap_ciclos_p90_ms=float(gaps_ciclos_ms.quantile(0.90)) if not gaps_ciclos_ms.empty else None,
        gap_trades_mediano_ms=float(gaps_trades_ms.median()) if not gaps_trades_ms.empty else None,
        trades_por_ciclo_mediana=float(np.median(trades_por_ciclo)) if trades_por_ciclo else None,
        trades_por_ciclo_max=int(np.max(trades_por_ciclo)) if trades_por_ciclo else None,
        spread_min=float(spread_valido_serie.min()) if not spread_valido_serie.empty else None,
        spread_mediano=float(spread_valido_serie.median()) if not spread_valido_serie.empty else None,
        spread_p90=float(spread_valido_serie.quantile(0.90)) if not spread_valido_serie.empty else None,
        spread_p99=float(spread_valido_serie.quantile(0.99)) if not spread_valido_serie.empty else None,
        spread_max=float(spread_valido_serie.max()) if not spread_valido_serie.empty else None,
        tick_size=tick_size,
        settled=settled,
    )


# --------------------------------------------------------------------------- #
# Relatório
# --------------------------------------------------------------------------- #

def montar_relatorio(m: dict, buffer_ticks: int) -> str:
    linhas = []
    add = linhas.append

    add("=" * 78)
    add("RELATÓRIO - TICKS DE ABERTURA")
    add("=" * 78)
    add(f"Janela analisada : {m['inicio']} -> {m['fim']}  ({m['duracao_s']:.1f} s)")
    add(f"Total de ticks   : {m['n_ticks']}  (LAST: {m['n_trades']}, ticks BID/ASK: {m['n_quotes']}, "
        f"ciclos de quote assentados: {m['n_ciclos']})")
    add(f"Tick size detectado (LAST): {m['tick_size']:.0f} pontos")
    add("")

    add("-" * 78)
    add("1) QUANDO SURGE O PRIMEIRO BID/ASK UTILIZÁVEL")
    add("-" * 78)
    if m["primeiro_quote_valido"] is not None:
        add(f"Primeiro bid&ask ASSENTADO (ambos já atualizados) com spread coerente:")
        add(f"    {m['primeiro_quote_valido']}")
        add(f"  -> {m['latencia_primeiro_quote_ms']:.0f} ms depois do primeiro tick do arquivo.")
    else:
        add("Nenhum bid/ask com spread coerente foi encontrado na janela.")
    add(f"Ciclos de quote (bid+ask já assentados): {m['n_ciclos']}  "
        f"(dos quais {m['n_ciclos_lixo']} são 'lixo': spread negativo ou > limite)")
    if m["n_ciclos_lixo"]:
        add("  -> O(s) primeiro(s) ciclo(s) do leilão podem vir com spread absurdo")
        add("     (preço ainda formando). Não confie no primeiro BID+ASK sem checar")
        add("     a sanidade do spread.")
    add("")

    add("-" * 78)
    add("2) BID E ASK NÃO CHEGAM ATÔMICOS (cuidado ao ler tick a tick)")
    add("-" * 78)
    add(f"Olhando tick a tick (estado bruto após cada linha), {m['n_neg_bruto']} instantes")
    add(f"mostram spread NEGATIVO (book aparentemente cruzado).")
    add(f"Agrupando bid+ask que chegam a poucos ms de distância no mesmo 'ciclo' de")
    add(f"atualização e olhando só o estado final de cada ciclo, sobram apenas")
    add(f"{m['n_neg_settled']} spread(s) negativo(s) reais.")
    add("  -> Ou seja: quase todo 'spread negativo' é artefato de ler o book no meio")
    add("     de uma atualização (BID já chegou, ASK ainda não, ou vice-versa) - não")
    add("     é o mercado cruzando de verdade. Se o seu código decide o stop olhando")
    add("     o bid/ask tick a tick, ele pode reagir a um cruzamento que não existiu.")
    add("     Sempre use o par bid&ask já assentado (mesmo timestamp/poucos ms).")
    add("")

    add("-" * 78)
    add("3) BID/ASK É RARO PERTO DO LAST: CADÊNCIA DE ATUALIZAÇÃO")
    add("-" * 78)
    if m["gap_ciclos_mediano_ms"] is not None:
        add(f"Intervalo mediano entre ciclos de bid/ask assentados: {m['gap_ciclos_mediano_ms']:.0f} ms "
            f"(p90: {m['gap_ciclos_p90_ms']:.0f} ms)")
    if m["gap_trades_mediano_ms"] is not None:
        add(f"Intervalo mediano entre negócios (LAST)              : {m['gap_trades_mediano_ms']:.1f} ms")
    if m["trades_por_ciclo_mediana"] is not None:
        add(f"Negócios (LAST) executados dentro de cada ciclo de quote: "
            f"mediana {m['trades_por_ciclo_mediana']:.0f}, máx {m['trades_por_ciclo_max']}")
        add("  -> Entre um refresh de bid/ask e o próximo, o preço já andou várias")
        add("     vezes no LAST. Um stop referenciado só no LAST reage mais rápido,")
        add("     mas 'no escuro' quanto ao book; um stop que depende de BID/ASK só")
        add("     vê o mercado em fotos espaçadas por esse intervalo.")
    add("")

    add("-" * 78)
    add("4) SPREAD (ASK - BID) DOS CICLOS ASSENTADOS, JÁ SEM OUTLIERS")
    add("-" * 78)
    if m["spread_mediano"] is not None:
        add(f"mínimo : {m['spread_min']:.0f} pontos")
        add(f"mediana: {m['spread_mediano']:.0f} pontos")
        add(f"p90    : {m['spread_p90']:.0f} pontos")
        add(f"p99    : {m['spread_p99']:.0f} pontos")
        add(f"máximo : {m['spread_max']:.0f} pontos")
    add("")

    add("-" * 78)
    add("5) RECOMENDAÇÃO PRÁTICA PARA A SELL STOP")
    add("-" * 78)
    if m["spread_p99"] is not None:
        distancia_min = m["spread_p99"] + buffer_ticks * m["tick_size"]
        add(f"Distância mínima sugerida abaixo do preço de referência:")
        add(f"    spread_p99 ({m['spread_p99']:.0f}) + {buffer_ticks} tick(s) de folga "
            f"({buffer_ticks * m['tick_size']:.0f} pts) = {distancia_min:.0f} pontos")
        add("")
    add("Conclusão sobre 'esperar bid/ask ou usar LAST':")
    add("  - Bid/ask aparece cedo (poucas centenas de ms), mas ATUALIZA POUCO")
    add("    (a cada ~%.0f ms), enquanto o LAST tickeia dezenas/centenas de vezes"
        % (m["gap_ciclos_mediano_ms"] or 0))
    add("    por segundo. Esperar 'o' bid/ask se formar não resolve sozinho, pois")
    add("    ele fica 'desatualizado' entre os próprios refreshes.")
    add("  - Regra prática: só considere o book confiável a partir do primeiro")
    add("    bid&ask ASSENTADO com spread dentro do range normal (itens 1/4 acima)")
    add("    - e sempre leia o par bid&ask já assentado (item 2), nunca um tick")
    add("    isolado no meio de uma atualização.")
    add("  - Coloque a sell stop com folga >= (spread_p99 + alguns ticks) abaixo")
    add("    do LAST/BID vigente para não ser 'varrida' pelo próprio spread indo")
    add("    e voltando nos primeiros segundos.")
    add("  - Se a plataforma valida/dispara a stop contra o BID (padrão comum em")
    add("    MT5 para ordens de venda), o gatilho efetivo só é confiável a partir")
    add("    do primeiro-quote-válido apontado no item 1 - antes disso o BID pode")
    add("    nem existir ou estar 'descolado' do LAST. Confirme no seu corretor")
    add("    qual preço (bid/ask/last) ele usa para checar o disparo da pendente.")
    add("=" * 78)

    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Gráfico
# --------------------------------------------------------------------------- #

def gerar_grafico(df: pd.DataFrame, m: dict, caminho_saida: Path, spread_max: float) -> None:
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    # Para o gráfico, oculta os instantes em que bid/ask formam spread-lixo
    # (ex.: o primeiro quote do leilão), senão a escala do eixo Y é dominada
    # por um único ponto espúrio. Esses pontos continuam contabilizados nas
    # métricas/relatório - aqui é só uma questão de legibilidade visual.
    mascara_lixo = df["bid_ff"].notna() & df["ask_ff"].notna() & ~df["spread_valido"]
    bid_plot = df["bid_ff"].mask(mascara_lixo)
    ask_plot = df["ask_ff"].mask(mascara_lixo)

    ax1.plot(df.index, df["last_ff"], color="#2563eb", linewidth=0.8, label="LAST")
    ax1.step(df.index, bid_plot, color="#16a34a", linewidth=0.9, where="post", label="BID")
    ax1.step(df.index, ask_plot, color="#dc2626", linewidth=0.9, where="post", label="ASK")

    if m["primeiro_quote_valido"] is not None:
        ax1.axvline(m["primeiro_quote_valido"], color="#6b7280", linestyle="--", linewidth=1)
        ax1.text(
            m["primeiro_quote_valido"], ax1.get_ylim()[1], " 1º quote válido",
            rotation=90, va="top", ha="right", fontsize=8, color="#6b7280",
        )

    ax1.set_ylabel("Preço (pontos)")
    ax1.set_title("Abertura: LAST vs BID/ASK reconstruídos")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(alpha=0.25)

    # Painel de baixo: spread dos CICLOS ASSENTADOS (bid&ask já ambos
    # atualizados) - é a leitura que importa na prática. O spread lido tick a
    # tick tem artefatos transitórios (ver item 2 do relatório) que não valem
    # a pena poluir o gráfico.
    settled = m["settled"]
    validos = settled["spread_settled"].between(0, spread_max)
    ax2.plot(
        settled.index[validos], settled.loc[validos, "spread_settled"],
        color="#7c3aed", linewidth=0.8, marker="o", markersize=2, label="spread (ciclo assentado)",
    )
    ax2.scatter(
        settled.index[~validos], settled.loc[~validos, "spread_settled"],
        color="#dc2626", s=14, label="ciclo outlier", zorder=5,
    )
    if m["spread_p99"] is not None:
        ax2.axhline(m["spread_p99"], color="#f59e0b", linestyle=":", linewidth=1, label="p99")
    ax2.set_ylabel("Spread (pts)")
    ax2.set_xlabel("Horário")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(alpha=0.25)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()

    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=140)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", default=None, help="Caminho do CSV de ticks")
    parser.add_argument("--spread-max", type=float, default=150.0,
                         help="Spread (pontos) acima do qual um quote é considerado lixo/outlier (default: 150)")
    parser.add_argument("--buffer-ticks", type=int, default=2,
                         help="Ticks extras de folga somados ao spread_p99 na recomendação de distância (default: 2)")
    parser.add_argument("--gap-cluster-ms", type=float, default=50.0,
                         help="Ticks de bid/ask a até esse intervalo (ms) um do outro são tratados como o mesmo "
                              "ciclo de atualização/'settled' (default: 50)")
    parser.add_argument("--saida-dir", default=None, help="Pasta onde salvar relatório e gráfico (default: pasta do CSV)")
    args = parser.parse_args()

    pasta_script = Path(__file__).resolve().parent
    caminho_csv = Path(args.csv) if args.csv else localizar_csv(pasta_script)
    if not caminho_csv.exists():
        print(f"Arquivo não encontrado: {caminho_csv}", file=sys.stderr)
        sys.exit(1)

    saida_dir = Path(args.saida_dir) if args.saida_dir else caminho_csv.parent

    print(f"Lendo {caminho_csv} ...")
    df = carregar_ticks(caminho_csv)
    df = reconstruir_estado(df, spread_max=args.spread_max)
    m = calcular_metricas(df, spread_max=args.spread_max, gap_cluster_ms=args.gap_cluster_ms)

    relatorio = montar_relatorio(m, buffer_ticks=args.buffer_ticks)
    print()
    print(relatorio)

    caminho_txt = saida_dir / "relatorio_abertura.txt"
    caminho_txt.write_text(relatorio, encoding="utf-8")
    print(f"\nRelatório salvo em: {caminho_txt}")

    caminho_png = saida_dir / "grafico_abertura.png"
    gerar_grafico(df, m, caminho_png, spread_max=args.spread_max)
    print(f"Gráfico salvo em:   {caminho_png}")


if __name__ == "__main__":
    main()
