"""
Motor de validacao temporal (secao 18).

Garantias:
  - nenhum embaralhamento;
  - janela expansiva (expanding window);
  - embargo de EMBARGO_BARS barras entre fim do treino e inicio da validacao,
    dimensionado para cobrir o horizonte futuro do target;
  - scaler/imputador ajustados EXCLUSIVAMENTE no treino de cada fold;
  - o holdout final (ultimos FINAL_TEST_FRACTION da serie em barras) e
    removido antes de qualquer walk-forward, e nunca participa de escolha de
    hiperparametro ou threshold.

Os splits sao definidos sobre o indice de BARRAS (nao de candidatos), para
que o embargo tenha significado temporal correto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from config import (CATBOOST_BASE_PARAMS, EMBARGO_BARS, FINAL_TEST_FRACTION,
                    MIN_TRAIN_FRACTION, N_FOLDS, SEED)


# ------------------------------------------------------------------- splits
@dataclass
class Fold:
    idx: int
    train_bars: np.ndarray
    valid_bars: np.ndarray
    train_end_bar: int
    valid_start_bar: int
    valid_end_bar: int


def holdout_split(bar_index: np.ndarray,
                  test_fraction: float = FINAL_TEST_FRACTION,
                  embargo: int = EMBARGO_BARS) -> tuple[np.ndarray, np.ndarray]:
    """Divide a serie em (desenvolvimento, holdout final) com embargo."""
    n = len(bar_index)
    cut = int(n * (1 - test_fraction))
    dev = bar_index[:cut]
    test = bar_index[cut + embargo:]
    return dev, test


def make_folds(bar_index: np.ndarray, n_folds: int = N_FOLDS,
               min_train_fraction: float = MIN_TRAIN_FRACTION,
               embargo: int = EMBARGO_BARS) -> list[Fold]:
    """Walk-forward com janela expansiva sobre o indice de barras."""
    n = len(bar_index)
    start = int(n * min_train_fraction)
    step = (n - start) // n_folds
    if step <= embargo + 10:
        raise ValueError("serie curta demais para o numero de folds pedido")

    folds = []
    for i in range(n_folds):
        train_end = start + i * step
        valid_start = train_end + embargo
        valid_end = min(valid_start + step, n) if i < n_folds - 1 else n
        if valid_start >= n:
            break
        folds.append(Fold(
            idx=i,
            train_bars=bar_index[:train_end],
            valid_bars=bar_index[valid_start:valid_end],
            train_end_bar=int(bar_index[train_end - 1]),
            valid_start_bar=int(bar_index[valid_start]),
            valid_end_bar=int(bar_index[valid_end - 1]),
        ))
    return folds


# ------------------------------------------------------------------ modelos
def make_model(name: str, params: dict | None = None):
    """Fabrica de modelos. Scaler/imputer ficam DENTRO do pipeline,
    logo sao ajustados apenas no treino de cada fold."""
    params = dict(params or {})
    if name == "always_signal":
        return DummyClassifier(strategy="constant", constant=1)
    if name == "prior":
        return DummyClassifier(strategy="prior")
    if name == "logistic":
        return Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, C=params.pop("C", 0.1),
                                       random_state=SEED, **params)),
        ])
    if name == "tree":
        return Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", DecisionTreeClassifier(
                max_depth=params.pop("max_depth", 4),
                min_samples_leaf=params.pop("min_samples_leaf", 50),
                random_state=SEED, **params)),
        ])
    if name == "random_forest":
        return Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=params.pop("n_estimators", 400),
                max_depth=params.pop("max_depth", 6),
                min_samples_leaf=params.pop("min_samples_leaf", 30),
                n_jobs=-1, random_state=SEED, **params)),
        ])
    if name == "catboost":
        from catboost import CatBoostClassifier
        p = dict(CATBOOST_BASE_PARAMS)
        p.update(params)
        return CatBoostClassifier(**p)
    raise ValueError(f"modelo desconhecido: {name}")


def _clean(X: pd.DataFrame) -> pd.DataFrame:
    return X.replace([np.inf, -np.inf], np.nan)


def fit_predict(model_name: str, params: dict, Xtr: pd.DataFrame,
                ytr: np.ndarray, Xva: pd.DataFrame,
                use_early_stopping: bool = True) -> tuple[np.ndarray, object]:
    """Treina no fold e devolve probabilidades de validacao.

    Para o CatBoost, o early stopping usa um recorte TEMPORAL FINAL do
    proprio treino (ultimos 20% das linhas de treino, que ja estao em ordem
    cronologica), nunca o conjunto de validacao — caso contrario a validacao
    deixaria de ser out-of-sample.
    """
    Xtr, Xva = _clean(Xtr), _clean(Xva)
    model = make_model(model_name, params)

    if model_name == "catboost" and use_early_stopping and len(Xtr) > 300:
        k = int(len(Xtr) * 0.8)
        Xa, ya = Xtr.iloc[:k], ytr[:k]
        Xb, yb = Xtr.iloc[k:], ytr[k:]
        if len(np.unique(yb)) < 2 or len(np.unique(ya)) < 2:
            model.fit(Xtr, ytr)
        else:
            model.fit(Xa, ya, eval_set=(Xb, yb), use_best_model=True)
    else:
        model.fit(Xtr, ytr)

    if hasattr(model, "predict_proba"):
        p = model.predict_proba(Xva)
        prob = p[:, 1] if p.ndim == 2 and p.shape[1] > 1 else np.ravel(p)
    else:
        prob = model.predict(Xva).astype(float)
    return np.asarray(prob, float), model


# ---------------------------------------------------------------- execucao
@dataclass
class WFResult:
    experiment: str
    model: str
    feature_set: str
    params: dict
    oof: pd.DataFrame                      # predicoes out-of-fold
    fold_metrics: list = field(default_factory=list)
    importances: pd.DataFrame | None = None


def run_walk_forward(ds: pd.DataFrame, feature_cols: list[str],
                     target_col: str, cand_col: str,
                     model_name: str, params: dict | None = None,
                     bar_pool: np.ndarray | None = None,
                     experiment: str = "EXP", feature_set: str = "?",
                     n_folds: int = N_FOLDS, embargo: int = EMBARGO_BARS,
                     collect_importance: bool = True) -> WFResult:
    """Walk-forward completo restrito ao universo de candidatos."""
    from evaluate import classification_metrics

    params = dict(params or {})
    bars = np.arange(len(ds)) if bar_pool is None else np.asarray(bar_pool)
    folds = make_folds(bars, n_folds=n_folds, embargo=embargo)

    cand = (ds[cand_col] == 1).to_numpy()
    labeled = ds[target_col].notna().to_numpy()
    usable = cand & labeled

    oof_parts, fold_metrics, imps = [], [], []
    for fold in folds:
        tr = np.intersect1d(fold.train_bars, np.where(usable)[0])
        va = np.intersect1d(fold.valid_bars, np.where(usable)[0])
        if len(tr) < 100 or len(va) < 30:
            continue
        ytr = ds[target_col].to_numpy()[tr].astype(int)
        yva = ds[target_col].to_numpy()[va].astype(int)
        if len(np.unique(ytr)) < 2:
            continue

        prob, model = fit_predict(model_name, params,
                                  ds.iloc[tr][feature_cols], ytr,
                                  ds.iloc[va][feature_cols])

        part = pd.DataFrame({
            "BarIndex": ds["BarIndex"].to_numpy()[va],
            "Date": ds["Date"].to_numpy()[va],
            "fold": fold.idx,
            "y": yva,
            "prob": prob,
            "side": ds[cand_col.replace("cand_", "side_")].to_numpy()[va],
        })
        oof_parts.append(part)

        m = classification_metrics(yva, prob, 0.5)
        m.update(fold=fold.idx, n_train=len(tr), n_valid=len(va),
                 train_end_bar=fold.train_end_bar,
                 valid_start_bar=fold.valid_start_bar,
                 valid_end_bar=fold.valid_end_bar,
                 train_base_rate=float(ytr.mean()))
        fold_metrics.append(m)

        if collect_importance:
            fi = _importance(model, feature_cols)
            if fi is not None:
                fi["fold"] = fold.idx
                imps.append(fi)

    oof = (pd.concat(oof_parts, ignore_index=True) if oof_parts
           else pd.DataFrame(columns=["BarIndex", "Date", "fold", "y", "prob", "side"]))
    imp = pd.concat(imps, ignore_index=True) if imps else None
    return WFResult(experiment, model_name, feature_set, params, oof,
                    fold_metrics, imp)


def _importance(model, cols) -> pd.DataFrame | None:
    est = model
    if isinstance(model, Pipeline):
        est = model.named_steps.get("clf")
    if hasattr(est, "get_feature_importance"):
        v = est.get_feature_importance()
    elif hasattr(est, "feature_importances_"):
        v = est.feature_importances_
    elif hasattr(est, "coef_"):
        v = np.abs(np.ravel(est.coef_))
    else:
        return None
    return pd.DataFrame({"feature": cols, "importance": np.asarray(v, float)})
