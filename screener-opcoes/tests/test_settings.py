from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from screener.settings import DEFAULT_SETTINGS_PATH, PROJECT_ROOT, load_settings


def _write_variant(tmp_path: Path, mutate) -> Path:
    raw = yaml.safe_load(DEFAULT_SETTINGS_PATH.read_text(encoding="utf-8"))
    mutate(raw)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    target = config_dir / "settings.yaml"
    target.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return target


def test_versioned_settings_are_valid() -> None:
    settings = load_settings()
    assert settings.spreads.lot_size == 100
    assert settings.paths.snapshots_dir == PROJECT_ROOT / "data" / "snapshots"


def test_paths_resolve_relative_to_config_parent(tmp_path: Path) -> None:
    settings = load_settings(_write_variant(tmp_path, lambda raw: None))
    assert settings.paths.logs_dir == tmp_path / "logs"


def test_liquidity_weights_must_sum_to_one(tmp_path: Path) -> None:
    def mutate(raw: dict) -> None:
        raw["series_liquidity"]["weights"]["spread"] = 0.9

    with pytest.raises(ValidationError, match="somar 1"):
        load_settings(_write_variant(tmp_path, mutate))


def test_unknown_keys_are_rejected(tmp_path: Path) -> None:
    def mutate(raw: dict) -> None:
        raw["spreads"]["largura"] = 1

    with pytest.raises(ValidationError):
        load_settings(_write_variant(tmp_path, mutate))


def test_bias_accepts_only_alta_or_baixa(tmp_path: Path) -> None:
    def mutate(raw: dict) -> None:
        raw["bias"] = {"PETR4": "lateral"}

    with pytest.raises(ValidationError):
        load_settings(_write_variant(tmp_path, mutate))
