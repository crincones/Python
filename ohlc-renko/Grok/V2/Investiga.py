import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

# ============================================================
# 1. CARREGAMENTO E CÁLCULO DAS EMAS (17 e 34 PERÍODOS)
# ============================================================
def load_and_preprocess_win(filepath):
    df = pd.read_csv(filepath, sep=";", decimal=",")
    df = df.iloc[::-1].reset_index(drop=True)  # Ordem cronológica

    df["dir"] = np.where(df["Fechamento"] >= df["Abertura"], 1, -1)
    df["wick"] = np.where(
        df["dir"] == 1, df["Abertura"] - df["Mínima"], df["Máxima"] - df["Abertura"]
    )

    data = pd.DataFrame(
        {
            "close": df["Fechamento"],
            "high": df["Máxima"],
            "low": df["Mínima"],
            "dir": df["dir"],
            "wick": df["wick"],
            "buy_agg": df["AgressionVolBuy"],
            "sell_agg": df["AgressionVolSell"],
            "lots": df["Quantity"],
            "n_trades": df["Trades"],
            "duration": df["BarDurationF"].clip(lower=0.1),
        }
    )

    data["delta"] = data["buy_agg"] - data["sell_agg"]

    # Caso 1: EMA 17
    data["ema_17"] = data["close"].ewm(span=17, adjust=False).mean()
    data["ema_17_slope"] = data["ema_17"].diff()

    # Caso 2: EMA 34
    data["ema_34"] = data["close"].ewm(span=34, adjust=False).mean()
    data["ema_34_slope"] = data["ema_34"].diff()

    # Normalização por Z-score
    for col in ["lots", "duration", "delta", "wick"]:
        mean = data[col].rolling(window=20, min_periods=5).mean()
        std = data[col].rolling(window=20, min_periods=5).std().replace(0, 1)
        data[f"{col}_z"] = (data[col] - mean) / std

    return data.fillna(0)

# ============================================================
# 2. FILTRO DE EVENTOS (STREAK >= 3 + POSIÇÃO DA PERNA + EMA <= 25 PTS)
# ============================================================
def get_ema_distance_points(high, low, ema_val):
    """Calcula a distância em pontos do tijolo até a EMA."""
    if low <= ema_val <= high:
        return 0.0  # Houve colisão/cruzamento
    return min(abs(high - ema_val), abs(low - ema_val))

def create_pullback_ema_events(df, ema_col, max_dist_pts=25.0, min_streak=3, target_bricks=2, stop_bricks=2):
    events = []
    n = len(df)
    i = 0

    while i < n - (min_streak + 5):
        streak_dir = df.loc[i, "dir"]
        streak_len = 1
        j = i + 1

        while j < n and df.loc[j, "dir"] == streak_dir:
            streak_len += 1
            j += 1

        if streak_len >= min_streak and j < n:
            rev_idx = j
            rev_dir = df.loc[rev_idx, "dir"]
            
            high = df.loc[rev_idx, "high"]
            low = df.loc[rev_idx, "low"]
            ema_val = df.loc[rev_idx, ema_col]
            
            # Distância do tijolo de reversão até a EMA
            dist_pts = get_ema_distance_points(high, low, ema_val)

            # Validação do Posição dos Tijolos Anteriores (Streak) em Relação à Média
            streak_lows = df.loc[rev_idx - streak_len : rev_idx - 1, "low"]
            streak_highs = df.loc[rev_idx - streak_len : rev_idx - 1, "high"]
            streak_emas = df.loc[rev_idx - streak_len : rev_idx - 1, ema_col]

            if rev_dir == 1:
                # COMPRA: Perna de queda anterior devia estar ACIMA da média
                valid_position = (streak_lows >= streak_emas).all()
            else:
                # VENDA: Perna de alta anterior devia estar ABAIXO da média
                valid_position = (streak_highs <= streak_emas).all()

            # REGRA COMBINADA: Posição válida + Colisão/Aproximação em até 25 pontos (5 ticks)
            if valid_position and dist_pts <= max_dist_pts:
                # Label: Barreira Tripla (+2 tijolos a favor antes de -2 tijolos contra)
                win = False
                pos_count, neg_count = 0, 0
                
                for k in range(rev_idx + 1, min(rev_idx + 25, n)):
                    if df.loc[k, "dir"] == rev_dir:
                        pos_count += 1
                    else:
                        neg_count += 1
                    
                    if pos_count >= target_bricks:
                        win = True
                        break
                    if neg_count >= stop_bricks:
                        win = False
                        break

                events.append({
                    "event_idx": rev_idx,
                    "streak_len": streak_len,
                    "dist_ema_pts": dist_pts,
                    "label": 1 if win else 0
                })

            i = rev_idx + 1
        else:
            i = j if j > i else i + 1

    return pd.DataFrame(events)

# ============================================================
# 3. FEATURE ENGINEERING
# ============================================================
def engineer_ema_features(df, events, ema_col, slope_col):
    rows = []

    for _, ev in events.iterrows():
        idx = int(ev["event_idx"])
        streak_len = int(ev["streak_len"])

        if idx < 40 or (idx - streak_len) < 0:
            continue

        row = {"label": int(ev["label"])}
        rev = df.loc[idx]

        # Features da Reversão
        row["rev_lots_z"] = float(rev["lots_z"])
        row["rev_duration_z"] = float(rev["duration_z"])
        row["rev_wick_z"] = float(rev["wick_z"])
        row["rev_delta_z"] = float(rev["delta_z"])

        # Métricas em PONTOS e TICKS do WIN (1 tick = 5 pts)
        row["dist_ema_pts"] = float(ev["dist_ema_pts"])
        row["dist_ema_ticks"] = float(ev["dist_ema_pts"] / 5.0)
        row["ema_slope"] = float(rev[slope_col])

        # Alinhamento da reversão com a inclinação da EMA
        aligned = (rev["dir"] == 1 and rev[slope_col] > 0) or (rev["dir"] == -1 and rev[slope_col] < 0)
        row["reversal_aligned_with_ema"] = 1 if aligned else -1

        # Contexto da Perna de Pullback (3+ tijolos)
        streak_df = df.loc[idx - streak_len : idx - 1]
        row["streak_len"] = int(streak_len)
        row["streak_cum_delta"] = float(streak_df["delta"].sum())
        row["streak_cum_volume"] = float(streak_df["lots"].sum())

        last_brick = df.loc[idx - 1]
        row["streak_exhaustion_ratio"] = float(
            last_brick["duration"] / (streak_df["duration"].mean() + 1e-6)
        )

        rows.append(row)

    return pd.DataFrame(rows)

# ============================================================
# 4. EXECUÇÃO E AVALIAÇÃO
# ============================================================
def evaluate_case(df, case_name, ema_col, slope_col):
    print(f"\n==================================================")
    print(f"AVALIANDO {case_name}")
    print(f"==================================================")
    
    events = create_pullback_ema_events(df, ema_col=ema_col, max_dist_pts=25.0, min_streak=3)
    features_df = engineer_ema_features(df, events, ema_col=ema_col, slope_col=slope_col)

    print(f"Eventos validados no filtro: {len(features_df)}")
    if len(features_df) < 30:
        print("Amostra muito reduzida para validar via TimeSeriesSplit.")
        return

    print(f"Taxa de sucesso base (Win Rate): {features_df['label'].mean():.2%}")

    X = features_df.drop(columns=["label"])
    y = features_df["label"]

    tscv = TimeSeriesSplit(n_splits=5)
    auc_scores = []
    importances = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
        X_train, X_test = X.iloc[train_idx[:-5]], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx[:-5]], y.iloc[test_idx]

        model = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.03,
            max_depth=3,
            num_leaves=7,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1,
        )

        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
        auc_scores.append(auc)

        imp = pd.Series(model.feature_importances_, index=X.columns)
        importances.append(imp)

        print(f"Fold {fold} - AUC: {auc:.4f}")

    print(f"\nAUC Médio ({case_name}): {np.mean(auc_scores):.4f} ± {np.std(auc_scores):.4f}")
    
    mean_imp = pd.concat(importances, axis=1).mean(axis=1).sort_values(ascending=False)
    print("\nTop 5 Features Mais Importantes:")
    print(mean_imp.head(5).round(2))

# --- Execução Principal ---
CSV_PATH = r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv"  # <--- Altere para o seu arquivo CSV

df = load_and_preprocess_win(CSV_PATH)

# Testar Caso 1: EMA 17
evaluate_case(df, "CASO 1: EMA 17 Períodos (Pullback Puro)", "ema_17", "ema_17_slope")

# Testar Caso 2: EMA 34
evaluate_case(df, "CASO 2: EMA 34 Períodos (Pullback Puro)", "ema_34", "ema_34_slope")