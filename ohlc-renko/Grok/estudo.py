#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detecção de Pivôs Renko (virada + ≥ 2 bricks) - Mini Índice (WIN)
Trigger exatamente no candle da virada.
Não espera confirmação além da regra dos 2 bricks.
Gera relatório + score + CSV detalhado.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURAÇÕES (ajuste se necessário)
# ============================================================
ARQUIVO_CSV = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WIN$N\Renko11R-limpo.csv"          # <-- coloque o nome do seu CSV
SEP = ";"
DECIMAL = ","
COL_DATA = "Data"
COL_ABERTURA = "Abertura"
COL_MAXIMA = "Maxima"
COL_MINIMA = "Minima"
COL_FECHAMENTO = "Fechamento"
COL_QTD = "Quantity"          # volume/quantidade
COL_TRADES = "Trades"

MIN_BRICKS_NOVA_DIR = 2       # regra: virada + pelo menos 1 = 2
LOOKAHEAD_MAX = 30            # quantos bricks olhamos à frente para métricas
SCORE_WEIGHTS = {             # pesos do score final (soma ~1.0)
    "freq": 0.15,
    "avg_continuation": 0.30,
    "pct_ge_3": 0.25,
    "pct_ge_5": 0.20,
    "stability": 0.10,
}

# ============================================================
# LEITURA E PREPARAÇÃO
# ============================================================
def carregar_dados(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(
        caminho,
        sep=SEP,
        decimal=DECIMAL,
        encoding="utf-8",
        low_memory=False
    )
    # limpeza básica de nomes de colunas
    df.columns = [c.strip() for c in df.columns]

    # parse de data (formato brasileiro com milissegundos)
    df[COL_DATA] = pd.to_datetime(df[COL_DATA], dayfirst=True, errors="coerce")
    df = df.dropna(subset=[COL_DATA, COL_ABERTURA, COL_FECHAMENTO]).reset_index(drop=True)

    # direção do brick: +1 alta, -1 baixa, 0 doji (raro)
    df["dir"] = np.sign(df[COL_FECHAMENTO] - df[COL_ABERTURA]).astype(int)
    df.loc[df["dir"] == 0, "dir"] = np.nan
    df["dir"] = df["dir"].ffill().fillna(0).astype(int)

    # tamanho aproximado do brick (para referência)
    df["brick_size"] = (df[COL_FECHAMENTO] - df[COL_ABERTURA]).abs()

    return df

# ============================================================
# DETECÇÃO DE SEQUÊNCIAS (STREAKS)
# ============================================================
def detectar_streaks(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de streak_id, streak_len, streak_start, etc."""
    # muda de direção
    change = df["dir"] != df["dir"].shift(1)
    streak_id = change.cumsum()

    df = df.copy()
    df["streak_id"] = streak_id
    df["streak_len"] = df.groupby("streak_id")["dir"].transform("size")
    df["streak_pos"] = df.groupby("streak_id").cumcount() + 1   # 1 = primeiro brick da sequência
    df["is_virada"] = df["streak_pos"] == 1
    df["prev_dir"] = df["dir"].shift(1)
    df["prev_streak_len"] = df.groupby("streak_id")["streak_len"].transform("first").shift(1)

    return df

# ============================================================
# EXTRAÇÃO DOS PIVÔS VÁLIDOS (virada + ≥ 2 bricks)
# ============================================================
def extrair_pivos(df: pd.DataFrame, min_bricks: int = 2) -> pd.DataFrame:
    """
    Retorna um DataFrame só com os pivôs que satisfazem a regra.
    O índice do pivô é o candle da virada (streak_pos == 1) e
    a sequência completa tem length >= min_bricks.
    """
    # só as viradas de sequências que tiveram tamanho suficiente
    mask = (df["is_virada"]) & (df["streak_len"] >= min_bricks) & (df["dir"] != 0)
    pivos = df.loc[mask].copy()

    # features úteis
    pivos["tipo"] = np.where(pivos["dir"] == 1, "Pivô de Baixa → Alta (compra)", "Pivô de Alta → Baixa (venda)")
    pivos["bricks_anteriores"] = pivos["prev_streak_len"].fillna(0).astype(int)
    pivos["bricks_novos"] = pivos["streak_len"]          # tamanho total da nova sequência
    pivos["continuacao_apos_2"] = pivos["bricks_novos"] - 2

    # preço de referência (fechamento da virada)
    pivos["preco_virada"] = pivos[COL_FECHAMENTO]

    return pivos

# ============================================================
# MÉTRICAS DE PERFORMANCE À FRENTE
# ============================================================
def calcular_metricas_lookahead(df: pd.DataFrame, pivos: pd.DataFrame, max_look: int = 30) -> pd.DataFrame:
    """
    Para cada pivô, olha quantos bricks na mesma direção ainda vieram
    e se a sequência seguinte (após o fim desta) foi favorável ou não.
    """
    results = []
    dirs = df["dir"].values
    closes = df[COL_FECHAMENTO].values
    n = len(df)

    for idx in pivos.index:
        i = df.index.get_loc(idx)          # posição inteira
        d = dirs[i]
        # já sabemos que a sequência tem >= 2; vamos achar o fim dela
        j = i
        while j + 1 < n and dirs[j + 1] == d:
            j += 1
        len_seq = j - i + 1

        # bricks restantes após o 2º
        cont_apos_2 = max(0, len_seq - 2)

        # próximo movimento (após o fim desta sequência)
        next_start = j + 1
        if next_start < n:
            next_dir = dirs[next_start]
            k = next_start
            while k + 1 < n and dirs[k + 1] == next_dir:
                k += 1
            next_len = k - next_start + 1
        else:
            next_dir = 0
            next_len = 0

        # movimento de preço aproximado (em pontos) da sequência
        price_move = closes[j] - closes[i] if d == 1 else closes[i] - closes[j]

        results.append({
            "idx": idx,
            "len_seq": len_seq,
            "cont_apos_2": cont_apos_2,
            "next_dir": next_dir,
            "next_len": next_len,
            "price_move_seq": price_move,
            "mesmo_sentido_next": 1 if next_dir == d else 0
        })

    meta = pd.DataFrame(results).set_index("idx")
    return pivos.join(meta)

# ============================================================
# SCORE E RELATÓRIO
# ============================================================
def calcular_score(pivos: pd.DataFrame) -> dict:
    if len(pivos) == 0:
        return {"score_final": 0, "detalhes": {}}

    total = len(pivos)
    avg_cont = pivos["cont_apos_2"].mean()
    pct_ge_3 = (pivos["bricks_novos"] >= 3).mean() * 100
    pct_ge_5 = (pivos["bricks_novos"] >= 5).mean() * 100
    # estabilidade: % de vezes que a sequência seguinte não reverteu imediatamente (next_len >= 2)
    stability = (pivos["next_len"] >= 2).mean() * 100 if "next_len" in pivos.columns else 50

    # normalizações simples (0-100)
    freq_score = min(100, total / 50)                    # 50 pivôs ≈ 100
    cont_score = min(100, avg_cont * 25)                 # 4 bricks extras ≈ 100
    ge3_score = pct_ge_3
    ge5_score = pct_ge_5
    stab_score = stability

    score = (
        SCORE_WEIGHTS["freq"] * freq_score +
        SCORE_WEIGHTS["avg_continuation"] * cont_score +
        SCORE_WEIGHTS["pct_ge_3"] * ge3_score +
        SCORE_WEIGHTS["pct_ge_5"] * ge5_score +
        SCORE_WEIGHTS["stability"] * stab_score
    )

    return {
        "score_final": round(score, 1),
        "detalhes": {
            "total_pivos": total,
            "avg_continuacao_apos_2": round(avg_cont, 2),
            "pct_sequencias_>=3": round(pct_ge_3, 1),
            "pct_sequencias_>=5": round(pct_ge_5, 1),
            "estabilidade_pct": round(stability, 1),
            "freq_score": round(freq_score, 1),
            "cont_score": round(cont_score, 1),
            "ge3_score": round(ge3_score, 1),
            "ge5_score": round(ge5_score, 1),
            "stab_score": round(stab_score, 1),
        }
    }

def gerar_relatorio(df: pd.DataFrame, pivos: pd.DataFrame, score_info: dict, saida_dir: Path):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_barras = len(df)
    total_pivos = len(pivos)

    # estatísticas por tipo
    por_tipo = pivos.groupby("tipo").agg(
        qtd=("tipo", "count"),
        avg_bricks=("bricks_novos", "mean"),
        avg_cont=("cont_apos_2", "mean"),
        med_bricks_ant=("bricks_anteriores", "median")
    ).round(2)

    # distribuição de tamanho das sequências
    dist = pivos["bricks_novos"].value_counts().sort_index()

    # volume médio na virada (se disponível)
    vol_info = ""
    if COL_QTD in pivos.columns:
        vol_medio = pivos[COL_QTD].mean()
        vol_info = f"\nVolume médio no candle da virada: {vol_medio:,.0f}"

    texto = f"""
================================================================================
RELATÓRIO DE PIVÔS RENKO – Mini Índice (WIN) 11R
Gerado em: {agora}
================================================================================

RESUMO GERAL
------------
Total de barras analisadas : {total_barras:,}
Total de pivôs válidos     : {total_pivos:,}
  (virada + pelo menos {MIN_BRICKS_NOVA_DIR} bricks na nova direção)
Score final (0-100)        : {score_info['score_final']}

DETALHES DO SCORE
-----------------
{chr(10).join(f'  {k}: {v}' for k,v in score_info['detalhes'].items())}

POR TIPO DE PIVÔ
----------------
{por_tipo.to_string()}

DISTRIBUIÇÃO DO TAMANHO DAS SEQUÊNCIAS APÓS A VIRADA
----------------------------------------------------
{dist.to_string()}
{vol_info}

INTERPRETAÇÃO RÁPIDA DO SCORE
-----------------------------
≥ 75  → padrão forte e frequente, boa continuação
50-74 → utilizável, filtrar por bricks anteriores ou volume
< 50  → muitos pivôs fracos ou pouca continuação; revisar regra ou filtros

RECOMENDAÇÕES DE USO DO TRIGGER
-------------------------------
1. Trigger no fechamento do candle da virada (streak_pos == 1).
2. Só considere o setup válido se o próximo brick confirmar a mesma direção
   (assim você garante os ≥ 2 bricks sem “esperar” visualmente demais).
3. Filtros opcionais que costumam melhorar o score:
   - bricks_anteriores ≥ 4 (tendência anterior mais estabelecida)
   - volume/quantidade acima da média das últimas N barras
   - horário (abertura / meio do pregão / final)
4. Gestão sugerida (teste no seu backtest):
   - Entrada: no 2º brick da nova direção (ou market no fechamento da virada)
   - Stop: 1–2 bricks contra a nova direção
   - Alvo parcial: 3–5 bricks / trailing de 1 brick

Arquivos gerados nesta pasta:
- relatorio_pivos_renko.txt  (este relatório)
- pivos_detalhados.csv       (todos os pivôs com features)
================================================================================
"""
    # salva relatório
    (saida_dir / "relatorio_pivos_renko.txt").write_text(texto, encoding="utf-8")
    print(texto)

    # salva CSV detalhado
    cols_uteis = [
        COL_DATA, "tipo", "dir", "preco_virada",
        "bricks_anteriores", "bricks_novos", "cont_apos_2",
        "len_seq", "next_len", "price_move_seq",
        COL_QTD, COL_TRADES
    ]
    cols_uteis = [c for c in cols_uteis if c in pivos.columns]
    pivos[cols_uteis].to_csv(saida_dir / "pivos_detalhados.csv", sep=";", decimal=",", index=False)
    print(f"\nCSV detalhado salvo em: {saida_dir / 'pivos_detalhados.csv'}")

# ============================================================
# MAIN
# ============================================================
def main():
    caminho = Path(ARQUIVO_CSV)
    if not caminho.exists():
        print(f"ERRO: arquivo '{ARQUIVO_CSV}' não encontrado.")
        print("Coloque o CSV na mesma pasta do script ou ajuste a variável ARQUIVO_CSV.")
        return

    print("Carregando dados...")
    df = carregar_dados(str(caminho))
    print(f"Barras carregadas: {len(df):,}")

    print("Detectando sequências...")
    df = detectar_streaks(df)

    print("Extraindo pivôs (virada + ≥ 2 bricks)...")
    pivos = extrair_pivos(df, min_bricks=MIN_BRICKS_NOVA_DIR)
    print(f"Pivôs encontrados: {len(pivos):,}")

    if len(pivos) == 0:
        print("Nenhum pivô atendeu o critério. Verifique o arquivo ou a regra MIN_BRICKS_NOVA_DIR.")
        return

    print("Calculando métricas de continuação...")
    pivos = calcular_metricas_lookahead(df, pivos, max_look=LOOKAHEAD_MAX)

    print("Calculando score...")
    score_info = calcular_score(pivos)

    saida = Path(".")
    gerar_relatorio(df, pivos, score_info, saida)

    print("\nConcluído.")

if __name__ == "__main__":
    main()