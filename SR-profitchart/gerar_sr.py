# -*- coding: utf-8 -*-
"""
Gerador automatico de zonas de Suporte/Resistencia a partir de historico OHLC
(Renko 50R do WIN) + emissao de codigo NTSL para o ProfitChart.

Uso basico:
    python gerar_sr.py
    python gerar_sr.py --csv historico.csv --data-fim 01/06/2026 --max-niveis 10
    python gerar_sr.py --grafico

Saidas:
    niveis_sr.csv        -> tabela com todos os niveis aprovados e suas metricas
    niveis_sr_ntsl.txt   -> codigo NTSL pronto para colar no Editor de Estrategias
    niveis_sr.png        -> (opcional, --grafico) previa visual dos niveis
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
#  CONFIGURACAO
# =============================================================================
CONFIG = {
    # ---------------------------------------------------------------- entrada
    "csv": "historico.csv",
    "tick": 5.0,              # incremento minimo de preco do ativo (WIN = 5 pts)

    # ------------------------------------------------------- limites de data
    # Formato aceito: "dd/mm/aaaa" ou "dd/mm/aaaa HH:MM". None = sem limite.
    # Somente as barras dentro da janela [data_inicio, data_fim] sao usadas
    # para detectar os niveis. Ex.: para NAO usar nada de 01/06/2026 ate hoje,
    # basta definir data_fim = "01/06/2026".
    "data_inicio": None,
    "data_fim": "07/08/2026",

    # --------------------------------------------------- detecao de pivos
    # Um topo/fundo e confirmado quando e o extremo de uma janela de
    # pivo_n barras para cada lado (fractal de Williams generalizado).
    # 2-3 e o padrao consagrado; em Renko 3 filtra bem o ruido.
    "pivo_n": 3,
    "pivo_proeminencia_min": 2.0,   # em "caixas" de renko; descarta pivos rasos

    # ------------------------------------------------------- zona / tolerancia
    # Meia-largura da zona, medida em CAIXAS do renko (a caixa e fixa em pontos,
    # por isso a referencia e ela, e nao um % do preco). A zona precisa caber
    # dentro do espacamento entre niveis, senao elas se sobrepoem:
    # 0.5 => zona de 1 caixa (~245 pts), compativel com separacao de 250 pts.
    "tolerancia_caixas": 0.50,
    "tolerancia_pct_min": 0.0,      # piso opcional em % do preco (0 = desligado)
    "cluster_largura_max": 2.0,     # largura total do cluster, em multiplos da tolerancia

    # ------------------------------------------------------------- toques
    # Um toque so e contado de novo depois que o preco ABANDONA a zona por
    # `saida_min_caixas` caixas — e o criterio de "teste distinto", que evita
    # contar 30 vezes a mesma congestao.
    "toques_min": 2,                # criterio classico: >= 3 toques valida o nivel
    "saida_min_caixas": 2.0,
    "rejeicao_janela": 30,          # barras olhadas apos o toque para medir a reacao
    "rejeicao_min_caixas": 4.0,     # afastamento minimo (caixas) para contar rejeicao

    # ------------------------------------------------------------- pontuacao
    "peso_pivos": 0.26,             # densidade de topos/fundos que formam a zona
    "peso_rejeicoes": 0.22,         # quantas vezes o nivel efetivamente segurou
    "peso_taxa_rejeicao": 0.16,     # segurou em que % das aproximacoes
    "peso_recencia": 0.14,
    "peso_toques": 0.08,
    "peso_abrangencia": 0.08,       # ha quanto tempo o nivel e respeitado
    "peso_proeminencia": 0.03,
    "peso_flip": 0.03,              # nivel que ja foi suporte E resistencia
    "taxa_rejeicao_min": 0.30,      # abaixo disso o preco so atravessa: nao e nivel
    "rejeicoes_min": 2,             # nº minimo de reacoes validadas
    "recencia_meia_vida": 3000,     # barras; peso cai pela metade a cada X barras

    # ------------------------------------------------------------- selecao
    "relevancia_min": 25.0,         # nota 0-100 minima para o nivel entrar

    # Preco de ancoragem: os niveis sao escolhidos em torno dele, N acima e
    # N abaixo. None = usa o fechamento da ultima barra da janela.
    "preco_referencia": 172000.0,
    "niveis_acima": 10,
    "niveis_abaixo": 10,
    # "proximidade" = escada densa em volta do preco de referencia (varre de
    # dentro para fora). "relevancia" = os melhores niveis da janela, onde
    # quer que estejam — mais espalhados.
    "selecao": "proximidade",

    # Separacao minima entre niveis exibidos, EM PONTOS.
    # None => cai para `distancia_min_caixas` * tamanho da caixa.
    "distancia_min_pontos": 150.0,
    "distancia_min_caixas": 3.0,

    "faixa_preco_pct": None,        # so niveis a ate X% do preco de referencia

    # ------------------------------------------------------------- NTSL
    "ntsl_nome": "SR Automatico",
    "ntsl_estilo": "dash",          # solid | dash | dot | dashdot | dashdotdot
    "ntsl_cor": "clBlue",           # "#RRGGBB", "clRed", ou (r, g, b)
    "ntsl_espessura": 1,            # 1..5
    "ntsl_cor_por_relevancia": False,
    "ntsl_cores_tiers": ["#FF3B30", "#FFA000", "#8E8E93"],  # alta / media / baixa
    "ntsl_espessura_por_relevancia": False,
    "ntsl_espessuras_tiers": [3, 2, 1],
    "ntsl_tier_alta": 70.0,         # relevancia >= 70 -> tier alta
    "ntsl_tier_media": 50.0,        # relevancia >= 50 -> tier media

    # ------------------------------------------------------------ assinatura
    # Ordem confirmada de HorizontalLineCustom:
    #   valor, cor, espessura, estilo, texto, tamanhoTexto, localTexto, 0, 0, 0
    # Os tres ultimos sao os limites opcionais de data/hora do desenho; 0 = a
    # linha cobre o grafico inteiro. Se precisar recortar, edite AQUI.
    "ntsl_template": ("HorizontalLineCustom( {preco}, {cor}, {espessura}, "
                      "{estilo}, \"{texto}\", {tamanho_texto}, {local_texto}, "
                      "0, 0, 0 )"),

    # rotulo embutido na propria linha (parametro nativo da funcao)
    "ntsl_texto": True,
    "ntsl_texto_relevancia": True,
    "ntsl_texto_toques": True,
    "ntsl_texto_preco": False,
    "ntsl_texto_tamanho": 9,
    # Posicao do texto sobre a linha. Vira input no NTSL: ajuste direto nas
    # propriedades do indicador ate cair acima/a direita, sem regerar o codigo.
    "ntsl_texto_local": 0,

    # ------------------------------------------------------------- saidas
    "saida_csv": "niveis_sr.csv",
    "saida_ntsl": "niveis_sr_ntsl.txt",
    "saida_png": "niveis_sr.png",
}

ESTILOS_NTSL = {
    "solid": "psSolid",
    "dash": "psDash",
    "dot": "psDot",
    "dashdot": "psDashDot",
    "dashdotdot": "psDashDotDot",
}


# =============================================================================
#  1. LEITURA DOS DADOS
# =============================================================================
def carregar_dados(caminho: str) -> pd.DataFrame:
    """Le o CSV/TSV exportado do ProfitChart e devolve OHLC em ordem cronologica."""
    caminho = Path(caminho)
    if not caminho.exists():
        sys.exit(f"[erro] arquivo nao encontrado: {caminho}")

    with caminho.open("r", encoding="utf-8-sig", errors="replace") as fh:
        cabecalho = fh.readline()
    sep = max(["\t", ";", ","], key=cabecalho.count)

    df = pd.read_csv(caminho, sep=sep, decimal=",", encoding="utf-8-sig",
                     engine="python")
    df.columns = [c.strip().lower() for c in df.columns]

    mapa = {}
    for col in df.columns:
        if col.startswith("data") or col.startswith("date"):
            mapa[col] = "data"
        elif col.startswith("abert") or col.startswith("open"):
            mapa[col] = "abertura"
        elif col.startswith("m") and "x" in col[:5] or col.startswith("high"):
            mapa[col] = "maxima"
        elif col.startswith("m") and "n" in col[:5] or col.startswith("low"):
            mapa[col] = "minima"
        elif col.startswith("fech") or col.startswith("close"):
            mapa[col] = "fechamento"
    df = df.rename(columns=mapa)

    faltando = {"data", "abertura", "maxima", "minima", "fechamento"} - set(df.columns)
    if faltando:
        sys.exit(f"[erro] colunas nao identificadas no CSV: {faltando}\n"
                 f"       colunas lidas: {list(df.columns)}")

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, format="mixed")
    for c in ("abertura", "maxima", "minima", "fechamento"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["data", "maxima", "minima", "fechamento"])
    df = df.sort_values("data", kind="stable").reset_index(drop=True)
    return df[["data", "abertura", "maxima", "minima", "fechamento"]]


def aplicar_janela(df: pd.DataFrame, ini: str | None, fim: str | None) -> pd.DataFrame:
    """Recorta o historico ao intervalo de datas configurado."""
    def _parse(txt):
        if not txt:
            return None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(txt, fmt)
            except ValueError:
                continue
        sys.exit(f"[erro] data invalida: {txt!r} (use dd/mm/aaaa)")

    d0, d1 = _parse(ini), _parse(fim)
    if d0 is not None:
        df = df[df["data"] >= d0]
    if d1 is not None:
        df = df[df["data"] <= d1]
    if len(df) < 100:
        sys.exit(f"[erro] apenas {len(df)} barras na janela — amplie o intervalo de datas.")
    return df.reset_index(drop=True)


def detectar_caixa_renko(df: pd.DataFrame) -> float:
    """Estima o tamanho da caixa (box) do renko pela mediana do corpo das barras."""
    corpo = (df["fechamento"] - df["abertura"]).abs()
    corpo = corpo[corpo > 0]
    if corpo.empty:
        return float((df["maxima"] - df["minima"]).median())
    return float(corpo.median())


# =============================================================================
#  2. PIVOS (topos e fundos)
# =============================================================================
def detectar_pivos(hi: np.ndarray, lo: np.ndarray, n: int, caixa: float,
                   prom_min: float):
    """
    Fractal generalizado: barra i e topo se sua maxima e o maior valor da
    janela [i-n, i+n]; fundo, analogamente, com a minima.
    Devolve (precos, indices, proeminencia_em_caixas, tipo) com tipo 1=topo, -1=fundo.
    """
    tam = len(hi)
    precos, indices, proems, tipos = [], [], [], []

    for i in range(n, tam - n):
        esq_hi, dir_hi = hi[i - n:i], hi[i + 1:i + n + 1]
        if hi[i] >= esq_hi.max() and hi[i] > dir_hi.max():
            prom = (hi[i] - lo[i - n:i + n + 1].min()) / caixa
            if prom >= prom_min:
                precos.append(hi[i]); indices.append(i)
                proems.append(prom); tipos.append(1)

        esq_lo, dir_lo = lo[i - n:i], lo[i + 1:i + n + 1]
        if lo[i] <= esq_lo.min() and lo[i] < dir_lo.min():
            prom = (hi[i - n:i + n + 1].max() - lo[i]) / caixa
            if prom >= prom_min:
                precos.append(lo[i]); indices.append(i)
                proems.append(prom); tipos.append(-1)

    return (np.array(precos), np.array(indices),
            np.array(proems), np.array(tipos))


# =============================================================================
#  3. AGRUPAMENTO EM ZONAS
# =============================================================================
def tolerancia(preco: float, cfg: dict, caixa: float) -> float:
    return max(caixa * cfg["tolerancia_caixas"],
               preco * cfg["tolerancia_pct_min"] / 100.0)


def agrupar(precos, indices, proems, cfg, caixa):
    """
    Encadeamento por proximidade sobre os pivos ordenados por preco, com trava
    de largura maxima do cluster (evita 'deriva' de niveis muito extensos).
    """
    ordem = np.argsort(precos)
    p, ix, pr = precos[ordem], indices[ordem], proems[ordem]

    clusters, atual = [], [0]
    for k in range(1, len(p)):
        centro = np.average(p[atual], weights=pr[atual])
        tol = tolerancia(centro, cfg, caixa)
        largura = p[k] - p[atual[0]]
        if (p[k] - centro) <= tol and largura <= tol * cfg["cluster_largura_max"]:
            atual.append(k)
        else:
            clusters.append(atual)
            atual = [k]
    clusters.append(atual)

    saida = []
    for cl in clusters:
        w = pr[cl]
        nivel = float(np.average(p[cl], weights=w))
        saida.append({
            "nivel": nivel,
            "n_pivos": len(cl),
            "proem_media": float(np.average(pr[cl], weights=w)),
            "idx_pivos": ix[cl],
            "proem_pivos": pr[cl],
        })
    return saida


def arredondar_tick(preco: float, tick: float) -> float:
    return round(round(preco / tick) * tick, 6)


# =============================================================================
#  4. TOQUES, REJEICOES E RELEVANCIA
# =============================================================================
def medir_toques(hi, lo, fech, nivel, tol, cfg, caixa):
    """
    Conta TESTES DISTINTOS da zona por maquina de estados:

      OUT --(barra intersecta a zona)--> IN        -> conta 1 toque
      IN  --(preco se afasta `saida_min_caixas` caixas alem da borda)--> OUT

    Assim uma congestao longa vale 1 toque, e so um novo aproach depois de um
    afastamento real vale outro. E o criterio que da sentido ao "numero de
    toques" como medida de relevancia.
    """
    n = len(hi)
    borda = tol + cfg["saida_min_caixas"] * caixa
    dentro = (lo <= nivel + tol) & (hi >= nivel - tol)
    fora = (lo > nivel + borda) | (hi < nivel - borda)
    idx_fora = np.flatnonzero(fora)

    eventos = []          # (i_inicio, i_fim) de cada toque
    estado_in = False
    ini = fim = 0
    for i in range(n):
        if dentro[i]:
            if not estado_in:
                estado_in = True
                ini = i
            fim = i
        elif estado_in and fora[i]:
            eventos.append((ini, fim))
            estado_in = False
    if estado_in:
        eventos.append((ini, fim))

    vazio = dict(toques=0, rejeicoes=0, travessias=0, taxa_rejeicao=0.0,
                 toques_pond=0.0, rejeicoes_pond=0.0, primeiro=None,
                 ultimo=None, flip=False, forca_rej=0.0)
    if not eventos:
        return vazio

    rej_cima = rej_baixo = travessias = 0
    forca = []
    rej_idx = []          # barra em que cada rejeicao validada ocorreu
    alvo = cfg["rejeicao_min_caixas"] * caixa

    for a, f in eventos:
        # Lado de onde o preco veio e para onde foi, medidos nas ultimas/primeiras
        # barras confirmadamente FORA da zona (afastadas de `saida_min_caixas`).
        ant = idx_fora[idx_fora < a]
        dep = idx_fora[idx_fora > f]
        if ant.size == 0 or dep.size == 0:
            continue                       # evento nas pontas da serie: nao classifica
        entrada = 1 if fech[ant[-1]] > nivel else -1
        saida = 1 if fech[dep[0]] > nivel else -1

        if saida != entrada:
            travessias += 1                # rompeu o nivel
            continue

        # Voltou pelo mesmo lado: mede o tamanho da reacao para validar.
        ate = min(f + cfg["rejeicao_janela"], n - 1)
        reacao = (hi[f:ate + 1].max() - (nivel + tol) if entrada > 0
                  else (nivel - tol) - lo[f:ate + 1].min())
        if reacao < alvo:
            continue                       # reacao fraca demais: nao conta
        forca.append(reacao / caixa)
        rej_idx.append(f)
        if entrada > 0:
            rej_cima += 1                  # veio de cima e voltou: segurou como suporte
        else:
            rej_baixo += 1                 # veio de baixo e voltou: segurou como resistencia

    rejeicoes = rej_cima + rej_baixo
    classificados = rejeicoes + travessias

    # Contagens ponderadas por recencia: um teste de 2022 nao vale o mesmo que
    # um teste do mes passado. Decaimento exponencial por meia-vida em barras.
    def decai(i):
        return 0.5 ** ((n - 1 - i) / cfg["recencia_meia_vida"])

    return dict(
        toques=len(eventos),
        rejeicoes=rejeicoes,
        travessias=travessias,
        taxa_rejeicao=(rejeicoes / classificados) if classificados else 0.0,
        toques_pond=float(sum(decai(f) for _, f in eventos)),
        rejeicoes_pond=float(sum(decai(i) for i in rej_idx)),
        primeiro=int(eventos[0][0]),
        ultimo=int(eventos[-1][1]),
        # Flip = ja segurou nos dois sentidos (mudanca de polaridade).
        flip=bool(rej_cima >= 1 and rej_baixo >= 1),
        forca_rej=float(np.mean(forca)) if forca else 0.0,
    )


def pontuar(cand: pd.DataFrame, cfg: dict) -> pd.Series:
    """
    Relevancia 0-100. As metricas de contagem sao normalizadas por PERCENTIL
    dentro do conjunto de candidatos (nao por teto absoluto): assim a nota
    sempre separa os niveis entre si, em vez de saturar todo mundo em 100.
    As metricas que ja sao naturalmente 0-1 (taxa, recencia, flip) entram
    com o proprio valor.
    """
    def pct(col: pd.Series) -> pd.Series:
        return (col.rank(pct=True) if col.nunique() > 1
                else pd.Series(1.0, index=col.index))

    componentes = {
        "peso_pivos": pct(cand["pivos_pond"]),
        "peso_rejeicoes": pct(cand["rejeicoes_pond"]),
        "peso_toques": pct(cand["toques_pond"]),
        "peso_taxa_rejeicao": cand["taxa_rejeicao"].clip(0.0, 1.0),
        "peso_recencia": 0.5 ** (cand["barras_desde_toque"] / cfg["recencia_meia_vida"]),
        "peso_abrangencia": pct(cand["abrangencia"]),
        "peso_proeminencia": pct(cand["proeminencia"]),
        "peso_flip": cand["flip"].astype(float),
    }
    nota = sum(cfg[k] * v for k, v in componentes.items())
    total = sum(cfg[k] for k in componentes)
    return (100.0 * nota / total).round(1)


# =============================================================================
#  5. PIPELINE
# =============================================================================
def calcular_niveis(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, float]:
    hi = df["maxima"].to_numpy(float)
    lo = df["minima"].to_numpy(float)
    fe = df["fechamento"].to_numpy(float)
    n_barras = len(df)

    caixa = detectar_caixa_renko(df)
    precos, indices, proems, _ = detectar_pivos(
        hi, lo, cfg["pivo_n"], caixa, cfg["pivo_proeminencia_min"])
    if precos.size == 0:
        sys.exit("[erro] nenhum pivo encontrado — reduza pivo_n ou pivo_proeminencia_min.")

    linhas = []
    for cl in agrupar(precos, indices, proems, cfg, caixa):
        nivel = arredondar_tick(cl["nivel"], cfg["tick"])
        tol = tolerancia(nivel, cfg, caixa)
        m = medir_toques(hi, lo, fe, nivel, tol, cfg, caixa)
        if (m["toques"] < cfg["toques_min"]
                or m["rejeicoes"] < cfg["rejeicoes_min"]
                or m["taxa_rejeicao"] < cfg["taxa_rejeicao_min"]):
            continue
        linhas.append({
            "nivel": nivel,
            "zona_min": arredondar_tick(nivel - tol, cfg["tick"]),
            "zona_max": arredondar_tick(nivel + tol, cfg["tick"]),
            "toques": m["toques"],
            "rejeicoes": m["rejeicoes"],
            "travessias": m["travessias"],
            "taxa_rejeicao": round(m["taxa_rejeicao"], 2),
            "toques_pond": round(m["toques_pond"], 3),
            "rejeicoes_pond": round(m["rejeicoes_pond"], 3),
            "pivos": cl["n_pivos"],
            # Densidade de pivos que formou a zona, ponderada por recencia e
            # pela proeminencia de cada topo/fundo. E o que distingue um nivel
            # estrutural de um preco qualquer dentro de uma congestao.
            "pivos_pond": round(float(np.sum(
                np.minimum(cl["proem_pivos"] / 4.0, 1.0) *
                0.5 ** ((n_barras - 1 - cl["idx_pivos"]) / cfg["recencia_meia_vida"])
            )), 3),
            "proeminencia": round(cl["proem_media"], 2),
            "forca_rejeicao": round(m["forca_rej"], 2),
            "flip": m["flip"],
            "abrangencia": m["ultimo"] - m["primeiro"],
            "primeiro_toque": df["data"].iloc[m["primeiro"]],
            "ultimo_toque": df["data"].iloc[m["ultimo"]],
            "barras_desde_toque": n_barras - 1 - m["ultimo"],
        })

    if not linhas:
        sys.exit("[erro] nenhum nivel passou nos filtros de toque/rejeicao — "
                 "reduza toques_min, rejeicoes_min ou taxa_rejeicao_min.")

    niveis = pd.DataFrame(linhas)
    niveis["relevancia"] = pontuar(niveis, cfg)
    print(f"[ok] {len(precos)} pivos -> {len(linhas)} zonas candidatas")

    # ---- ancoragem no preco de referencia -----------------------------------
    ref = float(cfg["preco_referencia"] or fe[-1])
    print(f"[ok] preco de referencia: {ref:,.0f}")

    if cfg["faixa_preco_pct"]:
        margem = ref * cfg["faixa_preco_pct"] / 100.0
        niveis = niveis[(niveis["nivel"] >= ref - margem) &
                        (niveis["nivel"] <= ref + margem)]

    niveis = niveis[niveis["relevancia"] >= cfg["relevancia_min"]]

    # ---- N acima e N abaixo, respeitando a separacao minima ------------------
    dmin = (cfg["distancia_min_pontos"] if cfg["distancia_min_pontos"]
            else cfg["distancia_min_caixas"] * caixa)
    escolhidos = []

    if cfg["selecao"] == "proximidade":
        # Varre do preco de referencia para fora, em faixas de `dmin`, e em cada
        # faixa fica o nivel de maior relevancia. Resultado: escada densa em
        # volta do preco de trabalho, em vez dos melhores niveis espalhados.
        niveis = niveis.assign(
            _faixa=(niveis["nivel"] - ref).abs().floordiv(dmin)
        ).sort_values(["_faixa", "relevancia"], ascending=[True, False])
    else:
        niveis = niveis.sort_values("relevancia", ascending=False)

    def _preencher(candidatos: pd.DataFrame, limite: int) -> int:
        n = 0
        for _, lin in candidatos.iterrows():
            if n >= limite:
                break
            if all(abs(lin["nivel"] - e["nivel"]) >= dmin for e in escolhidos):
                escolhidos.append(lin.to_dict())
                n += 1
        return n

    n_cima = _preencher(niveis[niveis["nivel"] > ref], cfg["niveis_acima"])
    n_baixo = _preencher(niveis[niveis["nivel"] <= ref], cfg["niveis_abaixo"])

    if not escolhidos:
        sys.exit("[erro] nenhum nivel sobreviveu aos filtros — afrouxe relevancia_min "
                 "ou reduza distancia_min_pontos.")
    if n_cima < cfg["niveis_acima"] or n_baixo < cfg["niveis_abaixo"]:
        print(f"[aviso] pedidos {cfg['niveis_acima']} acima / "
              f"{cfg['niveis_abaixo']} abaixo, encontrados {n_cima} / {n_baixo} "
              f"(separacao minima de {dmin:.0f} pts limita a quantidade)")

    final = pd.DataFrame(escolhidos).sort_values("nivel", ascending=False)
    return final.reset_index(drop=True), caixa


# =============================================================================
#  6. GERADOR DE CODIGO NTSL
# =============================================================================
def cor_ntsl(cor) -> str:
    """Converte '#RRGGBB' / (r,g,b) / 'clRed' na expressao de cor do NTSL."""
    if isinstance(cor, (tuple, list)) and len(cor) == 3:
        return f"RGB({int(cor[0])}, {int(cor[1])}, {int(cor[2])})"
    txt = str(cor).strip()
    if txt.startswith("#"):
        txt = txt[1:]
        if len(txt) != 6:
            sys.exit(f"[erro] cor hex invalida: {cor!r}")
        r, g, b = (int(txt[i:i + 2], 16) for i in (0, 2, 4))
        return f"RGB({r}, {g}, {b})"
    if txt.lower().startswith("cl"):
        return txt
    sys.exit(f"[erro] cor nao reconhecida: {cor!r} (use '#RRGGBB', (r,g,b) ou 'clRed')")


def _tier(relevancia: float, cfg: dict) -> int:
    if relevancia >= cfg["ntsl_tier_alta"]:
        return 0
    if relevancia >= cfg["ntsl_tier_media"]:
        return 1
    return 2


def gerar_ntsl(niveis: pd.DataFrame, cfg: dict, df: pd.DataFrame, caixa: float) -> str:
    estilo = ESTILOS_NTSL.get(str(cfg["ntsl_estilo"]).lower())
    if estilo is None:
        sys.exit(f"[erro] estilo invalido: {cfg['ntsl_estilo']!r} "
                 f"(use {', '.join(ESTILOS_NTSL)})")

    espessura_base = int(cfg["ntsl_espessura"])
    fmt_data = "%d/%m/%Y %H:%M"
    L = []
    add = L.append

    add("//" + "=" * 70)
    add(f"// {cfg['ntsl_nome']}")
    add(f"// Gerado automaticamente por gerar_sr.py em "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")
    add(f"// Janela analisada : {df['data'].iloc[0].strftime(fmt_data)}"
        f"  ->  {df['data'].iloc[-1].strftime(fmt_data)}")
    add(f"// Barras / caixa   : {len(df)} barras | box renko ~ {caixa:.0f} pts")
    add(f"// Criterios        : >= {cfg['toques_min']} toques distintos, "
        f"relevancia >= {cfg['relevancia_min']:.0f}, pivo n={cfg['pivo_n']}, "
        f"zona +-{cfg['tolerancia_caixas'] * caixa:.0f} pts")
    dmin = (cfg["distancia_min_pontos"] if cfg["distancia_min_pontos"]
            else cfg["distancia_min_caixas"] * caixa)
    ref = cfg["preco_referencia"] or df["fechamento"].iloc[-1]
    add(f"// Referencia       : {ref:,.0f} "
        f"({cfg['niveis_acima']} acima / {cfg['niveis_abaixo']} abaixo)")
    add(f"// Niveis           : {len(niveis)} "
        f"(separacao min. {dmin:.0f} pts)")
    add("//" + "-" * 70)
    add("// #   Preco        Zona                  Toques  Rej  Flip  Relev")
    for i, lin in niveis.iterrows():
        add(f"// {i + 1:<3} {lin['nivel']:<12,.0f} "
            f"{lin['zona_min']:,.0f} - {lin['zona_max']:<12,.0f} "
            f"{lin['toques']:^6} {lin['rejeicoes']:^4} "
            f"{'S' if lin['flip'] else '-':^5} {lin['relevancia']:>5.1f}")
    add("//" + "=" * 70)
    add("")

    def rotulo(lin) -> str:
        if not cfg["ntsl_texto"]:
            return ""
        partes = []
        if cfg["ntsl_texto_preco"]:
            partes.append(f"{lin['nivel']:.0f}")
        if cfg["ntsl_texto_relevancia"]:
            partes.append(f"R{lin['relevancia']:.0f}")
        if cfg["ntsl_texto_toques"]:
            partes.append(f"T{lin['toques']}")
        return " ".join(partes)

    add("input")
    add(f"  TamanhoTexto ( {int(cfg['ntsl_texto_tamanho'])} );")
    add(f"  LocalTexto   ( {int(cfg['ntsl_texto_local'])} );  "
        f"// posicao do rotulo sobre a linha")
    add("")
    add("begin")
    add("")
    add("  // Desenha UMA unica vez, na ultima barra do grafico. Sem esta guarda")
    add("  // a NTSL repetiria as chamadas em todas as barras da serie.")
    add("  if LastBarOnChart then")
    add("  begin")
    add("")

    for i, lin in niveis.iterrows():
        tier = _tier(lin["relevancia"], cfg)
        cor = (cor_ntsl(cfg["ntsl_cores_tiers"][tier])
               if cfg["ntsl_cor_por_relevancia"] else cor_ntsl(cfg["ntsl_cor"]))
        esp = (int(cfg["ntsl_espessuras_tiers"][tier])
               if cfg["ntsl_espessura_por_relevancia"] else espessura_base)

        add(f"    // Nivel {i + 1}: toques={lin['toques']} "
            f"| rejeicoes={lin['rejeicoes']} | relevancia={lin['relevancia']:.1f} "
            f"| ultimo toque {lin['ultimo_toque'].strftime('%d/%m/%Y')}")
        add("    " + cfg["ntsl_template"].format(
            preco=f"{lin['nivel']:.2f}", cor=cor, espessura=esp, estilo=estilo,
            texto=rotulo(lin), tamanho_texto="TamanhoTexto",
            local_texto="LocalTexto") + ";")
        add("")

    add("  end;")
    add("")
    add("end;")
    return "\n".join(L) + "\n"


# =============================================================================
#  7. GRAFICO OPCIONAL
# =============================================================================
def salvar_grafico(df: pd.DataFrame, niveis: pd.DataFrame, caminho: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[aviso] matplotlib nao instalado — grafico ignorado.")
        return False

    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot(df["data"], df["fechamento"], lw=0.6, color="#3A3A3A", label="Fechamento")
    for _, lin in niveis.iterrows():
        ax.axhspan(lin["zona_min"], lin["zona_max"], color="#FFA000", alpha=0.15)
        ax.axhline(lin["nivel"], color="#FF6F00", lw=1.0, ls="--")
        ax.text(df["data"].iloc[-1], lin["nivel"],
                f"  {lin['nivel']:,.0f}  R{lin['relevancia']:.0f} T{lin['toques']}",
                va="center", fontsize=8, color="#B34700")
    ax.set_title("Zonas de suporte/resistencia detectadas")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)
    return True


# =============================================================================
#  8. CLI
# =============================================================================
def montar_cli(cfg: dict) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera zonas de suporte/resistencia e o codigo NTSL do ProfitChart.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--csv", default=cfg["csv"])
    p.add_argument("--data-inicio", default=cfg["data_inicio"],
                   help="dd/mm/aaaa — ignora barras anteriores a esta data")
    p.add_argument("--data-fim", default=cfg["data_fim"],
                   help="dd/mm/aaaa — ignora barras posteriores a esta data")
    p.add_argument("--preco-ref", type=float, default=cfg["preco_referencia"],
                   help="preco de ancoragem; 0 usa o fechamento da ultima barra")
    p.add_argument("--acima", type=int, default=cfg["niveis_acima"])
    p.add_argument("--abaixo", type=int, default=cfg["niveis_abaixo"])
    p.add_argument("--distancia", type=float, default=cfg["distancia_min_pontos"],
                   help="separacao minima entre niveis, em pontos")
    p.add_argument("--selecao", default=cfg["selecao"],
                   choices=["proximidade", "relevancia"])
    p.add_argument("--toques-min", type=int, default=cfg["toques_min"])
    p.add_argument("--relevancia-min", type=float, default=cfg["relevancia_min"])
    p.add_argument("--tolerancia-caixas", type=float, default=cfg["tolerancia_caixas"],
                   help="meia-largura da zona, em caixas do renko")
    p.add_argument("--faixa-preco-pct", type=float, default=cfg["faixa_preco_pct"],
                   help="0 desativa o filtro de proximidade do preco atual")
    p.add_argument("--cor", default=cfg["ntsl_cor"])
    p.add_argument("--estilo", default=cfg["ntsl_estilo"], choices=list(ESTILOS_NTSL))
    p.add_argument("--espessura", type=int, default=cfg["ntsl_espessura"])
    p.add_argument("--sem-texto", action="store_true", help="nao gerar os rotulos")
    p.add_argument("--grafico", action="store_true", help="salva previa em PNG")
    return p.parse_args()


def main() -> None:
    cfg = dict(CONFIG)
    a = montar_cli(cfg)
    cfg.update({
        "csv": a.csv,
        "data_inicio": a.data_inicio,
        "data_fim": a.data_fim,
        "preco_referencia": a.preco_ref or None,
        "niveis_acima": a.acima,
        "niveis_abaixo": a.abaixo,
        "distancia_min_pontos": a.distancia,
        "selecao": a.selecao,
        "toques_min": a.toques_min,
        "relevancia_min": a.relevancia_min,
        "tolerancia_caixas": a.tolerancia_caixas,
        "faixa_preco_pct": a.faixa_preco_pct or None,
        "ntsl_cor": a.cor,
        "ntsl_estilo": a.estilo,
        "ntsl_espessura": a.espessura,
        "ntsl_texto": cfg["ntsl_texto"] and not a.sem_texto,
    })

    df = carregar_dados(cfg["csv"])
    print(f"[ok] {len(df)} barras lidas: "
          f"{df['data'].iloc[0]:%d/%m/%Y} -> {df['data'].iloc[-1]:%d/%m/%Y}")

    df = aplicar_janela(df, cfg["data_inicio"], cfg["data_fim"])
    print(f"[ok] janela de analise: {df['data'].iloc[0]:%d/%m/%Y %H:%M} -> "
          f"{df['data'].iloc[-1]:%d/%m/%Y %H:%M} ({len(df)} barras)")

    niveis, caixa = calcular_niveis(df, cfg)
    print(f"[ok] caixa renko estimada: {caixa:.0f} pts")
    print(f"[ok] {len(niveis)} niveis selecionados\n")

    tabela = niveis[["nivel", "zona_min", "zona_max", "toques", "rejeicoes",
                     "travessias", "taxa_rejeicao", "flip", "relevancia",
                     "ultimo_toque"]].copy()
    tabela["ultimo_toque"] = tabela["ultimo_toque"].dt.strftime("%d/%m/%Y")
    print(tabela.to_string(index=False))

    niveis.to_csv(cfg["saida_csv"], index=False, sep=";", decimal=",",
                  encoding="utf-8-sig")
    Path(cfg["saida_ntsl"]).write_text(
        gerar_ntsl(niveis, cfg, df, caixa), encoding="utf-8")

    print(f"\n[ok] tabela -> {cfg['saida_csv']}")
    print(f"[ok] NTSL   -> {cfg['saida_ntsl']}")

    if a.grafico and salvar_grafico(df, niveis, cfg["saida_png"]):
        print(f"[ok] grafico -> {cfg['saida_png']}")


if __name__ == "__main__":
    main()
