import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ARQUIVO = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WIN$N\Renko11R-limpo.csv"

# Quantas barras olhar para trás ao estudar um pivô
LOOKBACK = 8

# Quantas barras depois do pivô observar
LOOKFORWARD = 10

# Número mínimo de barras consecutivas para considerar uma tendência
MIN_TREND = 2


# ============================================================
# LEITURA
# ============================================================

df = pd.read_csv(
    ARQUIVO,
    sep=";",
    decimal=",",
    encoding="utf-8"
)

# Limpa nomes
df.columns = [c.strip().replace("**", "") for c in df.columns]

print("Colunas:")
print(df.columns.tolist())

# Data
df["Data"] = pd.to_datetime(
    df["Data"],
    dayfirst=True,
    errors="coerce"
)

# Numéricos
for col in [
    "Abertura",
    "Maxima",
    "Minima",
    "Fechamento",
    "BarDurationF",
    "Quantity",
    "Trades"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna().reset_index(drop=True)


# ============================================================
# CARACTERÍSTICAS DA BARRA
# ============================================================

df["direction"] = np.sign(
    df["Fechamento"] - df["Abertura"]
).astype(int)

# Corpo
df["body"] = (
    df["Fechamento"] - df["Abertura"]
).abs()

# Amplitude
df["range"] = (
    df["Maxima"] - df["Minima"]
)

# Pavios
df["upper_wick"] = (
    df["Maxima"] -
    df[["Abertura", "Fechamento"]].max(axis=1)
)

df["lower_wick"] = (
    df[["Abertura", "Fechamento"]].min(axis=1) -
    df["Minima"]
)

# Normalização dos pavios
df["upper_wick_ratio"] = (
    df["upper_wick"] /
    df["range"].replace(0, np.nan)
)

df["lower_wick_ratio"] = (
    df["lower_wick"] /
    df["range"].replace(0, np.nan)
)

# Corpo relativo
df["body_ratio"] = (
    df["body"] /
    df["range"].replace(0, np.nan)
)


# ============================================================
# SEQUÊNCIA DE DIREÇÃO
# ============================================================

run = []

count = 0
previous = 0

for direction in df["direction"]:

    if direction == previous:
        count += 1
    else:
        count = 1

    run.append(count)
    previous = direction

df["run_length"] = run


# ============================================================
# ACELERAÇÃO / DESACELERAÇÃO
# ============================================================

df["quantity_change"] = (
    df["Quantity"].pct_change()
)

df["trades_change"] = (
    df["Trades"].pct_change()
)

df["duration_change"] = (
    df["BarDurationF"].pct_change()
)


# ============================================================
# IDENTIFICAÇÃO DOS PIVÔS
# ============================================================

# Um pivô de alta:
#
# várias barras de baixa
# seguidas por uma barra de alta
#
# Um pivô de baixa:
#
# várias barras de alta
# seguidas por uma barra de baixa

df["pivot_high"] = False
df["pivot_low"] = False

for i in range(1, len(df)):

    prev_dir = df.loc[i - 1, "direction"]
    curr_dir = df.loc[i, "direction"]

    # Virada de baixa -> alta
    if prev_dir < 0 and curr_dir > 0:

        if df.loc[i - 1, "run_length"] >= MIN_TREND:
            df.loc[i, "pivot_low"] = True

    # Virada de alta -> baixa
    elif prev_dir > 0 and curr_dir < 0:

        if df.loc[i - 1, "run_length"] >= MIN_TREND:
            df.loc[i, "pivot_high"] = True


# ============================================================
# ESTATÍSTICAS DOS PIVÔS
# ============================================================

pivots = []

for i in range(LOOKBACK, len(df) - LOOKFORWARD):

    if not (df.loc[i, "pivot_high"] or df.loc[i, "pivot_low"]):
        continue

    pivot_type = (
        "LOW" if df.loc[i, "pivot_low"]
        else "HIGH"
    )

    # Movimento futuro
    entry = df.loc[i, "Fechamento"]

    future = df.iloc[
        i + 1:
        i + 1 + LOOKFORWARD
    ]

    if pivot_type == "LOW":

        future_move = (
            future["Maxima"].max() - entry
        )

        adverse_move = (
            entry - future["Minima"].min()
        )

    else:

        future_move = (
            entry - future["Minima"].min()
        )

        adverse_move = (
            future["Maxima"].max() - entry
        )

    row = {

        "index": i,

        "date": df.loc[i, "Data"],

        "pivot": pivot_type,

        "entry": entry,

        # Características da barra do pivô
        "body": df.loc[i, "body"],

        "range": df.loc[i, "range"],

        "upper_wick": df.loc[i, "upper_wick"],

        "lower_wick": df.loc[i, "lower_wick"],

        "upper_wick_ratio":
            df.loc[i, "upper_wick_ratio"],

        "lower_wick_ratio":
            df.loc[i, "lower_wick_ratio"],

        "quantity":
            df.loc[i, "Quantity"],

        "trades":
            df.loc[i, "Trades"],

        "duration":
            df.loc[i, "BarDurationF"],

        # Características da tendência anterior
        "run_length":
            df.loc[i - 1, "run_length"],

        "prev_quantity":
            df.loc[i - 1, "Quantity"],

        "prev_trades":
            df.loc[i - 1, "Trades"],

        "prev_duration":
            df.loc[i - 1, "BarDurationF"],

        # Resultado
        "future_move":
            future_move,

        "adverse_move":
            adverse_move,

        "net_move":
            future_move - adverse_move
    }

    pivots.append(row)


pivots = pd.DataFrame(pivots)


# ============================================================
# RESULTADOS BÁSICOS
# ============================================================

print("\n========================================")
print("ESTATÍSTICAS DOS PIVÔS")
print("========================================")

print(
    pivots.groupby("pivot")[
        [
            "future_move",
            "adverse_move",
            "net_move"
        ]
    ].agg(
        [
            "count",
            "mean",
            "median",
            "std"
        ]
    )
)


# ============================================================
# ESTATÍSTICAS POR NÚMERO DE BARRAS ANTERIORES
# ============================================================

print("\n========================================")
print("PIVÔ x SEQUÊNCIA ANTERIOR")
print("========================================")

seq_stats = (
    pivots
    .groupby(["pivot", "run_length"])
    .agg(
        occurrences=("pivot", "size"),

        future_mean=("future_move", "mean"),

        future_median=("future_move", "median"),

        adverse_mean=("adverse_move", "mean"),

        net_mean=("net_move", "mean")
    )
    .reset_index()
)

print(seq_stats.to_string(index=False))


# ============================================================
# QUANTIDADE / TRADES
# ============================================================

print("\n========================================")
print("PIVÔ x QUANTITY")
print("========================================")

pivots["quantity_percentile"] = (
    pivots["quantity"]
    .rank(pct=True)
)

pivots["trades_percentile"] = (
    pivots["trades"]
    .rank(pct=True)
)

pivots["wick_imbalance"] = (
    pivots["lower_wick"] -
    pivots["upper_wick"]
)


# ============================================================
# QUARTIS
# ============================================================

pivots["quantity_q"] = pd.qcut(
    pivots["quantity"],
    4,
    labels=False,
    duplicates="drop"
)

pivots["trades_q"] = pd.qcut(
    pivots["trades"],
    4,
    labels=False,
    duplicates="drop"
)

pivots["wick_q"] = pd.qcut(
    pivots["wick_imbalance"],
    4,
    labels=False,
    duplicates="drop"
)


print("\n========================================")
print("QUANTIDADE")
print("========================================")

print(
    pivots
    .groupby(["pivot", "quantity_q"])
    .agg(
        occurrences=("pivot", "size"),
        future_mean=("future_move", "mean"),
        adverse_mean=("adverse_move", "mean"),
        net_mean=("net_move", "mean")
    )
)


print("\n========================================")
print("TRADES")
print("========================================")

print(
    pivots
    .groupby(["pivot", "trades_q"])
    .agg(
        occurrences=("pivot", "size"),
        future_mean=("future_move", "mean"),
        adverse_mean=("adverse_move", "mean"),
        net_mean=("net_move", "mean")
    )
)


print("\n========================================")
print("PAVIOS")
print("========================================")

print(
    pivots
    .groupby(["pivot", "wick_q"])
    .agg(
        occurrences=("pivot", "size"),
        future_mean=("future_move", "mean"),
        adverse_mean=("adverse_move", "mean"),
        net_mean=("net_move", "mean")
    )
)


# ============================================================
# SALVAR
# ============================================================

pivots.to_csv(
    "pivots_analysis.csv",
    index=False,
    sep=";",
    decimal=","
)

print("\nArquivo gerado:")
print("pivots_analysis.csv")