"""Publicação do relatório: lógica de envio, troca do nome público e retenção (sem rede)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from screener.publish import (
    PARTIAL_SUFFIX,
    REPORT_NAME,
    PublishError,
    obsolete_reports,
    publish_report,
    stale_uploads,
    upload_report,
)
from screener.report.render import REPORT_NAME_FORMAT
from screener.settings import DEFAULT_SETTINGS_PATH, PublishSettings, load_settings


class FakeRemote:
    """Dublê de `RemoteFiles` em memória: arquivos como conteúdo, links como alvo."""

    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.dirs: set[str] = set()
        self.files: dict[str, str] = dict(files or {})
        self.links: dict[str, str] = {}
        self.calls: list[str] = []

    def makedirs(self, path: str) -> None:
        self.calls.append(f"makedirs {path}")
        self.dirs.add(path)

    def put(self, local: Path, remote: str) -> None:
        self.calls.append(f"put {remote}")
        self.files[remote] = local.read_text(encoding="utf-8")

    def listdir(self, path: str) -> list[str]:
        prefix = path + "/"
        names = [
            name[len(prefix) :]
            for name in list(self.files) + list(self.links)
            if name.startswith(prefix) and "/" not in name[len(prefix) :]
        ]
        return sorted(names)

    def remove(self, path: str) -> None:
        self.calls.append(f"remove {path}")
        self.files.pop(path, None)
        self.links.pop(path, None)

    def symlink(self, target: str, path: str) -> None:
        self.calls.append(f"symlink {path} -> {target}")
        self.links[path] = target

    def replace(self, source: str, target: str) -> None:
        self.calls.append(f"replace {source} -> {target}")
        self.files.pop(target, None)
        self.links.pop(target, None)
        if source in self.links:
            self.links[target] = self.links.pop(source)
        else:
            self.files[target] = self.files.pop(source)


def _settings(**overrides: object) -> PublishSettings:
    base = load_settings(DEFAULT_SETTINGS_PATH).publish
    return base.model_copy(update=overrides)


def _report(tmp_path: Path, name: str = "relatorio_20260917_1331.html") -> Path:
    target = tmp_path / name
    target.write_text("<html>relatorio</html>", encoding="utf-8")
    return target


def test_report_name_pattern_matches_generated_names() -> None:
    generated = pd.Timestamp("2026-09-17 13:31", tz="America/Sao_Paulo").strftime(
        REPORT_NAME_FORMAT
    )
    assert REPORT_NAME.fullmatch(generated)


def test_upload_puts_report_in_history_and_points_public_name_to_it(tmp_path: Path) -> None:
    remote = FakeRemote()
    report = _report(tmp_path)

    result = upload_report(remote, report, _settings())

    assert remote.files["/srv/screener/relatorios/relatorio_20260917_1331.html"] == (
        "<html>relatorio</html>"
    )
    assert remote.links["/srv/screener/screening.html"] == (
        "relatorios/relatorio_20260917_1331.html"
    )
    assert result.url == "http://100.113.24.44/screening.html"
    assert result.size_bytes == report.stat().st_size
    assert result.removed == ()


def test_upload_only_exposes_the_report_after_it_is_complete(tmp_path: Path) -> None:
    remote = FakeRemote()
    report = _report(tmp_path)

    upload_report(remote, report, _settings())

    final = "/srv/screener/relatorios/relatorio_20260917_1331.html"
    assert remote.calls.index(f"put {final}{PARTIAL_SUFFIX}") < remote.calls.index(
        f"replace {final}{PARTIAL_SUFFIX} -> {final}"
    )
    # o link público só é trocado depois de o relatório estar no lugar definitivo
    assert remote.calls.index(f"replace {final}{PARTIAL_SUFFIX} -> {final}") < remote.calls.index(
        "replace /srv/screener/screening.html.partial -> /srv/screener/screening.html"
    )
    assert not [name for name in remote.files if name.endswith(PARTIAL_SUFFIX)]


def test_upload_replaces_a_public_name_that_is_a_regular_file(tmp_path: Path) -> None:
    remote = FakeRemote({"/srv/screener/screening.html": "<html>provisorio</html>"})

    upload_report(remote, _report(tmp_path), _settings())

    assert "/srv/screener/screening.html" not in remote.files
    assert remote.links["/srv/screener/screening.html"].endswith("relatorio_20260917_1331.html")


def test_upload_keeps_only_the_newest_reports(tmp_path: Path) -> None:
    history = "/srv/screener/relatorios"
    old = {f"{history}/relatorio_2026091{day}_1000.html": "x" for day in range(1, 5)}
    remote = FakeRemote({**old, f"{history}/relatorio_20260910_1000.html.partial": "x"})

    result = upload_report(remote, _report(tmp_path), _settings(keep_reports=3))

    assert result.removed == (
        "relatorio_20260911_1000.html",
        "relatorio_20260912_1000.html",
        "relatorio_20260910_1000.html.partial",
    )
    assert remote.listdir(history) == [
        "relatorio_20260913_1000.html",
        "relatorio_20260914_1000.html",
        "relatorio_20260917_1331.html",
    ]


def test_upload_never_removes_the_report_it_just_published(tmp_path: Path) -> None:
    history = "/srv/screener/relatorios"
    newer = {f"{history}/relatorio_20260918_{hhmm}.html": "x" for hhmm in ("1000", "1100")}
    remote = FakeRemote(newer)

    result = upload_report(remote, _report(tmp_path), _settings(keep_reports=1))

    assert "relatorio_20260917_1331.html" not in result.removed
    assert f"{history}/relatorio_20260917_1331.html" in remote.files
    assert remote.links["/srv/screener/screening.html"].endswith("relatorio_20260917_1331.html")


def test_obsolete_reports_ignores_names_that_are_not_reports() -> None:
    names = ["index.html", "relatorio_20260917_1331.html", "notas.txt", "relatorio_antigo.html"]
    assert obsolete_reports(names, keep=1) == []
    assert obsolete_reports([*names, "relatorio_20260916_1000.html"], keep=1) == [
        "relatorio_20260916_1000.html"
    ]


def test_obsolete_reports_keeps_at_least_one() -> None:
    names = ["relatorio_20260916_1000.html", "relatorio_20260917_1331.html"]
    assert obsolete_reports(names, keep=0) == ["relatorio_20260916_1000.html"]


def test_stale_uploads_finds_interrupted_transfers() -> None:
    names = ["relatorio_20260917_1331.html", "relatorio_20260917_1400.html.partial"]
    assert stale_uploads(names) == ["relatorio_20260917_1400.html.partial"]


def test_publish_report_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PublishError, match="não encontrado"):
        publish_report(tmp_path / "ausente.html", _settings())


def test_versioned_publish_settings_point_to_the_tailnet_server() -> None:
    publish = load_settings(DEFAULT_SETTINGS_PATH).publish
    assert publish.host == "100.113.24.44"
    assert publish.public_url == f"http://{publish.host}/{publish.latest_name}"
    assert publish.strict_host_key
