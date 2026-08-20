"""
Testes automatizados de vazamento temporal (secao 26 do CLAUDE.md).

Rodar com:  python -m pytest tests -q      (a partir da raiz do projeto)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import features as F           # noqa: E402
import targets as T            # noqa: E402
from build_dataset import load_dataset, split_columns   # noqa: E402
from leakage_test import run_perturbation_test          # noqa: E402
from walk_forward import holdout_split, make_folds      # noqa: E402
from config import EMBARGO_BARS                          # noqa: E402


@pytest.fixture(scope="module")
def ds():
    return load_dataset()


def test_features_do_not_depend_on_future():
    """Corromper t+1.. nao pode alterar nenhuma feature em t' <= t."""
    rep = run_perturbation_test()
    assert rep["feature_failures"] == [], rep["feature_failures"]
    assert rep["candidate_mask_failures"] == []
    assert rep["passed"]


def test_leakage_detector_actually_works():
    """Controle positivo: o teste precisa PEGAR um vazamento injetado."""
    rep = run_perturbation_test(cuts=(7000,))
    assert rep["positive_control_detects_injected_leak"] is True


def _code_only(path: Path) -> str:
    """Fonte sem comentarios nem strings — para procurar codigo de verdade."""
    import io
    import tokenize

    out = []
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    return " ".join(out)


def test_no_negative_shift_in_features_module():
    """Nenhum shift(-k) no modulo de features — futuro so em targets.py."""
    code = _code_only(SRC / "features.py")
    assert "shift ( -" not in code
    assert "shift(-" not in code.replace(" ", "")[:0] or True
    # forma robusta: nenhum argumento negativo literal em shift/rolling
    import re
    assert re.search(r"shift\s*\(\s*-", code) is None


def test_only_whitelisted_modules_use_future():
    """Somente tres modulos podem olhar para frente, cada um por um motivo
    explicito. Qualquer outro arquivo com shift negativo e vazamento.

      targets.py      — constroi o rotulo (uso legitimo e unico do futuro)
      eda.py          — probabilidades incondicionais de continuacao, que
                        sao estatistica descritiva, nunca feature
      leakage_test.py — INJETA um vazamento de proposito, como controle
                        positivo do proprio detector
    """
    import re
    allowed = {"targets.py", "eda.py", "leakage_test.py"}
    offenders = []
    for p in SRC.glob("*.py"):
        if p.name in allowed:
            continue
        if re.search(r"shift\s*\(\s*-", _code_only(p)):
            offenders.append(p.name)
    assert offenders == [], offenders


def test_target_columns_are_not_features(ds):
    cols = split_columns(ds)
    for c in cols["features"]:
        assert not c.startswith(T.TARGET_PREFIXES), c


def test_candidate_mask_is_causal(ds):
    """cand_* usa apenas direcao de t-pre_seq..t."""
    for pre in (2, 3):
        m, side = T.candidate_mask(ds, pre)
        d = np.sign(ds["Close"] - ds["Open"]).astype(int)
        sel = m & m.notna()
        # onde ha candidato, t inverte a direcao de t-1
        assert (d[sel] == -d.shift(1)[sel]).all()
        # e as pre_seq barras anteriores tinham a mesma direcao entre si
        for k in range(1, pre):
            assert (d.shift(k)[sel] == d.shift(k + 1)[sel]).all()


def test_target_uses_future_only_in_target(ds):
    """y_* = candidato AND continuacao futura confirmada."""
    for pre, cont in ((2, 2), (3, 3)):
        suf = T.target_suffix(pre, cont)
        d = np.sign(ds["Close"] - ds["Open"]).astype(int)
        y = ds[f"y_{suf}"]
        pos = y == 1
        for k in range(1, cont + 1):
            assert (d.shift(-k)[pos] == d[pos]).all()


def test_walk_forward_has_embargo_and_no_overlap():
    bars = np.arange(20000)
    folds = make_folds(bars)
    for f in folds:
        assert f.valid_bars.min() - f.train_bars.max() >= EMBARGO_BARS
        assert len(np.intersect1d(f.train_bars, f.valid_bars)) == 0
    # janela expansiva: o treino so cresce
    for a, b in zip(folds, folds[1:]):
        assert len(b.train_bars) > len(a.train_bars)


def test_holdout_is_disjoint_and_last():
    bars = np.arange(20000)
    dev, test = holdout_split(bars)
    assert len(np.intersect1d(dev, test)) == 0
    assert test.min() > dev.max()
    assert test.min() - dev.max() >= EMBARGO_BARS


def test_no_shuffling_anywhere():
    """Nenhum train_test_split com shuffle no codigo-fonte."""
    for p in SRC.glob("*.py"):
        s = p.read_text(encoding="utf-8")
        assert "shuffle=True" not in s, p.name
        assert "train_test_split" not in s, p.name


def test_rolling_windows_are_causal(ds):
    """Media movel de t nao pode usar t+1: recomputar so com o passado da."""
    dur = ds["Duration"]
    manual = dur.rolling(20, min_periods=20).mean()
    assert np.allclose(manual.dropna(), ds["DurationMA20"].dropna())
    # e a de t coincide com a media dos ultimos 20 valores ate t
    i = 5000
    assert abs(ds["DurationMA20"].iloc[i]
               - dur.iloc[i - 19:i + 1].mean()) < 1e-9
