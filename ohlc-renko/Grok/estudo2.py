#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise de características do brick de VIRADA
Objetivo: encontrar padrões de volume, negócios, wicks, duração e sequência anterior
que diferenciem viradas que continuam ≥ 2 bricks das que falham (só 1 brick).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURAÇÃO
# ============================================================
ARQUIVO_CSV = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WIN$N\Renko11R-limpo.csv"          # <-- coloque o nome do seu CSV
SEP = ";"
DECIMAL = ","

COL_DATA = "Data"
COL_OPEN = "Abertura"
COL_HIGH = "Maxima"
COL_LOW  = "Minima"
COL_CLOSE = "Fechamento"
COL_DUR  = "BarDurationF"
COL_QTD  = "Quantity"
COL_TRADES = "Trades"

# ============================================================
# FUNÇÕES
# ============================================================
def carregar(caminho):
    df = pd.read_csv(caminho, sep=SEP, decimal=DECIMAL, encoding="utf-8", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    
    df[COL_DATA] = pd.to_datetime(df[COL_DATA], dayfirst=True, errors="coerce")
    df = df.dropna(subset=[COL_DATA, COL_OPEN, COL_CLOSE]).reset_index(drop=True)
    
    # Direção
    df["dir"] = np.sign(df[COL_CLOSE] - df[COL_OPEN]).astype(int)
    df.loc[df["dir"] == 0, "dir"] = np.nan
    df["dir"] = df["dir"].ffill().fillna(0).astype(int)
    
    # Wicks
    body_top = df[[COL_OPEN, COL_CLOSE]].max(axis=1)
    body_bot = df[[COL_OPEN, COL_CLOSE]].min(axis=1)
    df["wick_upper"] = df[COL_HIGH] - body_top
    df["wick_lower"] = body_bot - df[COL_LOW]
    df["wick_total"] = df["wick_upper"] + df["wick_lower"]
    df["body"] = (df[COL_CLOSE] - df[COL_OPEN]).abs()
    
    # Duração (já vem como float com vírgula, pandas trata)
    if COL_DUR in df.columns:
        df[COL_DUR] = pd.to_numeric(df[COL_DUR], errors="coerce")
    
    return df

def detectar_viradas(df):
    df = df.copy()
    change = df["dir"] != df["dir"].shift(1)
    df["streak_id"] = change.cumsum()
    df["streak_len"] = df.groupby("streak_id")["dir"].transform("size")
    df["streak_pos"] = df.groupby("streak_id").cumcount() + 1
    df["is_virada"] = (df["streak_pos"] == 1) & (df["dir"] != 0)
    
    # tamanho da sequência anterior
    df["prev_streak_len"] = df.groupby("streak_id")["streak_len"].transform("first").shift(1)
    
    return df

def extrair_features_virada(df):
    """Extrai features de cada virada e rotula se continuou ≥ 2 bricks"""
    viradas = df[df["is_virada"]].copy()
    
    # Label: sucesso se a nova sequência teve ≥ 2 bricks
    viradas["sucesso"] = viradas["streak_len"] >= 2
    viradas["len_nova"] = viradas["streak_len"]
    
    # Features do brick da virada
    viradas["vol"] = viradas[COL_QTD]
    viradas["negocios"] = viradas[COL_TRADES]
    viradas["duracao"] = viradas[COL_DUR] if COL_DUR in viradas.columns else np.nan
    viradas["wick_up"] = viradas["wick_upper"]
    viradas["wick_dn"] = viradas["wick_lower"]
    viradas["wick_tot"] = viradas["wick_total"]
    viradas["body"] = viradas["body"]
    
    # Volume e negócios relativos (vs média das últimas 10 barras)
    for col, new in [(COL_QTD, "vol_rel"), (COL_TRADES, "neg_rel")]:
        if col in df.columns:
            media = df[col].rolling(10, min_periods=3).mean()
            viradas[new] = viradas[col] / media.loc[viradas.index]
    
    # Features da barra anterior (última da tendência antiga)
    viradas["vol_ant"] = df[COL_QTD].shift(1).loc[viradas.index]
    viradas["neg_ant"] = df[COL_TRADES].shift(1).loc[viradas.index]
    viradas["wick_ant"] = df["wick_total"].shift(1).loc[viradas.index]
    
    # Tamanho da tendência que está sendo quebrada
    viradas["bricks_ant"] = viradas["prev_streak_len"].fillna(0).astype(int)
    
    # Direção da virada
    viradas["tipo"] = np.where(viradas["dir"] == 1, "Compra (baixa→alta)", "Venda (alta→baixa)")
    
    return viradas

def comparar_grupos(viradas):
    """Compara estatísticas entre sucesso (≥2) e falha (=1)"""
    cols = [
        "vol", "negocios", "duracao", "wick_up", "wick_dn", "wick_tot", "body",
        "vol_rel", "neg_rel", "vol_ant", "neg_ant", "wick_ant", "bricks_ant"
    ]
    cols = [c for c in cols if c in viradas.columns]
    
    res = []
    for c in cols:
        s = viradas.loc[viradas["sucesso"], c].dropna()
        f = viradas.loc[~viradas["sucesso"], c].dropna()
        if len(s) < 5 or len(f) < 5:
            continue
        res.append({
            "feature": c,
            "media_sucesso": s.mean(),
            "media_falha": f.mean(),
            "mediana_sucesso": s.median(),
            "mediana_falha": f.median(),
            "diff_media_%": (s.mean() - f.mean()) / (f.mean() + 1e-9) * 100,
            "diff_mediana_%": (s.median() - f.median()) / (f.median() + 1e-9) * 100,
            "n_sucesso": len(s),
            "n_falha": len(f)
        })
    return pd.DataFrame(res).sort_values("diff_mediana_%", key=abs, ascending=False)

def regras_simples(viradas):
    """Testa algumas regras simples de filtro e mostra lift"""
    total = len(viradas)
    base_rate = viradas["sucesso"].mean()
    
    regras = []
    
    # Exemplos de regras (você pode expandir)
    candidatos = [
        ("vol_rel > 1.5", viradas["vol_rel"] > 1.5),
        ("vol_rel > 2.0", viradas["vol_rel"] > 2.0),
        ("neg_rel > 1.5", viradas["neg_rel"] > 1.5),
        ("bricks_ant >= 4", viradas["bricks_ant"] >= 4),
        ("bricks_ant >= 5", viradas["bricks_ant"] >= 5),
        ("wick_tot == 0", viradas["wick_tot"] == 0),          # brick limpo
        ("wick_tot > 0", viradas["wick_tot"] > 0),
        ("vol > vol.median()", viradas["vol"] > viradas["vol"].median()),
        ("negocios > negocios.median()", viradas["negocios"] > viradas["negocios"].median()),
    ]
    
    for nome, mask in candidatos:
        if mask.sum() < 20:
            continue
        rate = viradas.loc[mask, "sucesso"].mean()
        lift = rate / base_rate
        regras.append({
            "regra": nome,
            "qtd": mask.sum(),
            "taxa_sucesso": rate,
            "taxa_base": base_rate,
            "lift": lift
        })
    
    return pd.DataFrame(regras).sort_values("lift", ascending=False)

# ============================================================
# MAIN
# ============================================================
def main():
    caminho = Path(ARQUIVO_CSV)
    if not caminho.exists():
        print(f"Arquivo '{ARQUIVO_CSV}' não encontrado.")
        return
    
    print("Carregando...")
    df = carregar(str(caminho))
    print(f"Barras: {len(df):,}")
    
    df = detectar_viradas(df)
    viradas = extrair_features_virada(df)
    
    n_total = len(viradas)
    n_sucesso = viradas["sucesso"].sum()
    n_falha = n_total - n_sucesso
    taxa = n_sucesso / n_total
    
    print(f"\nViradas totais: {n_total:,}")
    print(f"  Sucesso (≥2 bricks): {n_sucesso:,} ({taxa:.1%})")
    print(f"  Falha (só 1 brick) : {n_falha:,} ({1-taxa:.1%})")
    
    print("\n" + "="*70)
    print("COMPARAÇÃO DE FEATURES (Sucesso vs Falha)")
    print("="*70)
    comp = comparar_grupos(viradas)
    print(comp.to_string(index=False, float_format="%.2f"))
    
    print("\n" + "="*70)
    print("TESTE DE REGRAS SIMPLES (Lift sobre a taxa base)")
    print("="*70)
    regras = regras_simples(viradas)
    print(regras.to_string(index=False, float_format="%.3f"))
    
    # Salva tudo
    viradas.to_csv("viradas_com_features.csv", sep=";", decimal=",", index=False)
    comp.to_csv("comparacao_features.csv", sep=";", decimal=",", index=False)
    regras.to_csv("regras_lift.csv", sep=";", decimal=",", index=False)
    
    print("\nArquivos gerados:")
    print("  - viradas_com_features.csv")
    print("  - comparacao_features.csv")
    print("  - regras_lift.csv")
    
    print("\n" + "="*70)
    print("INTERPRETAÇÃO RÁPIDA")
    print("="*70)
    print("Procure features com |diff_mediana_%| grande e lift > 1.2")
    print("Essas são as melhores candidatas para filtrar no NTSL.")
    print("Exemplos comuns que costumam aparecer:")
    print("  - Volume relativo alto na virada")
    print("  - Tendência anterior longa (bricks_ant >= 4 ou 5)")
    print("  - Wick pequeno ou zero (brick limpo)")
    print("  - Negócios relativos elevados")

if __name__ == "__main__":
    main()