"""Google Drive: o que enviar, corpo do upload e recuperação (Drive falso em memória, sem rede)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json

import pytest
from conftest import SETTINGS

from travas.tracking import gdrive
from travas.tracking.gcal import DRIVE_SCOPE, SCOPE
from travas.tracking.gdrive import (
    DriveBackup,
    GoogleDriveError,
    daily_name,
    multipart_body,
    plan_uploads,
    restore_target,
    validate_backup,
)

DAY = dt.date(2026, 10, 28)
CARTEIRA = b'{"positions": []}'


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_drive_scope_is_requested_and_disabled_in_tests():
    assert DRIVE_SCOPE in SCOPE.split()
    assert SETTINGS.google_drive.enabled is False


def test_daily_name_keeps_extension():
    assert daily_name("acompanhamento.json", DAY) == "acompanhamento_2026-10-28.json"


def test_first_sync_sends_current_and_daily_copy():
    plan = plan_uploads({"acompanhamento.json": CARTEIRA}, {}, DAY, history=True)
    assert [(u.key, u.name, u.history) for u in plan] == [
        ("atual/acompanhamento.json", "acompanhamento.json", False),
        ("historico/acompanhamento_2026-10-28.json", "acompanhamento_2026-10-28.json", True),
    ]
    assert all(u.content == CARTEIRA and u.sha256 == _sha(CARTEIRA) for u in plan)


def test_unchanged_content_is_not_sent_again():
    uploaded = {
        "atual/acompanhamento.json": {"id": "a", "sha256": _sha(CARTEIRA)},
        "historico/acompanhamento_2026-10-28.json": {"id": "b", "sha256": _sha(CARTEIRA)},
    }
    assert plan_uploads({"acompanhamento.json": CARTEIRA}, uploaded, DAY, history=True) == []


def test_new_day_creates_new_daily_copy_only():
    uploaded = {
        "atual/acompanhamento.json": {"id": "a", "sha256": _sha(CARTEIRA)},
        "historico/acompanhamento_2026-10-27.json": {"id": "b", "sha256": _sha(CARTEIRA)},
    }
    plan = plan_uploads({"acompanhamento.json": CARTEIRA}, uploaded, DAY, history=True)
    assert [u.key for u in plan] == ["historico/acompanhamento_2026-10-28.json"]


def test_changed_content_without_history():
    uploaded = {"atual/acompanhamento.json": {"id": "a", "sha256": _sha(b"antigo")}}
    plan = plan_uploads({"acompanhamento.json": CARTEIRA}, uploaded, DAY, history=False)
    assert [u.key for u in plan] == ["atual/acompanhamento.json"]


def test_multipart_body_has_metadata_and_content():
    body, ctype = multipart_body(
        {"name": "Carteira ç.json", "parents": ["p"]}, CARTEIRA, "application/json"
    )
    assert ctype.startswith("multipart/related; boundary=")
    boundary = ctype.split("boundary=")[1].encode()
    parts = body.split(b"--" + boundary)
    assert parts[-1] == b"--\r\n"
    meta = json.loads(parts[1].split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n").decode("utf-8"))
    assert meta == {"name": "Carteira ç.json", "parents": ["p"]}
    assert parts[2].split(b"\r\n\r\n", 1)[1] == CARTEIRA + b"\r\n"


def test_restore_target_maps_current_and_history_names():
    names = ["acompanhamento.json", "favoritos.json"]
    assert restore_target("acompanhamento.json", names) == "acompanhamento.json"
    assert restore_target("acompanhamento_2026-10-28.json", names) == "acompanhamento.json"
    assert restore_target("favoritos_2026-10-27.json", names) == "favoritos.json"
    assert restore_target("outro.json", names) is None
    assert restore_target("acompanhamento_2026-10-28.txt", names) is None


def test_validate_backup_rejects_foreign_content():
    assert validate_backup(CARTEIRA) == {"positions": []}
    assert validate_backup(b'{"items": []}') == {"items": []}
    with pytest.raises(GoogleDriveError):
        validate_backup(b"nao e json")
    with pytest.raises(GoogleDriveError):
        validate_backup(b'{"outra": 1}')


# ---- Drive falso -------------------------------------------------------------------------------
class FakeDrive:
    """Drive em memória com a mesma interface de `DriveApi` (pasta = arquivo sem conteúdo)."""

    def __init__(self) -> None:
        self.files: dict[str, dict] = {}
        self.calls: list[str] = []
        self._n = 0

    def add(self, name: str, parent: str | None, content: bytes | None = None) -> str:
        self._n += 1
        fid = f"f{self._n}"
        self.files[fid] = {
            "name": name,
            "parents": [parent] if parent else [],
            "content": content,
            "trashed": False,
            "modified": f"2026-10-{self._n:02d}T10:00:00Z",
        }
        return fid

    def alive(self, fid):
        return fid in self.files and not self.files[fid]["trashed"]

    def find_folder(self, name, parent=None):
        for fid, f in reversed(self.files.items()):
            folder = f["content"] is None and f["name"] == name and not f["trashed"]
            if folder and (parent is None or parent in f["parents"]):
                return fid
        return None

    def children(self, folder):
        return [
            {
                "id": fid,
                "name": f["name"],
                "md5Checksum": hashlib.md5(f["content"]).hexdigest(),  # noqa: S324
                "modifiedTime": f["modified"],
                "size": str(len(f["content"])),
                "mimeType": "application/json",
            }
            for fid, f in self.files.items()
            if folder in f["parents"] and not f["trashed"] and f["content"] is not None
        ]

    def metadata(self, fid):
        f = self.files[fid]
        return {"id": fid, "name": f["name"], "parents": f["parents"], "trashed": f["trashed"]}

    def download(self, fid):
        return self.files[fid]["content"]

    def copy(self, fid, name, parent):
        self.calls.append(f"copy {name}")
        return self.add(name, parent, self.files[fid]["content"])

    def create_folder(self, name, parent=None):
        self.calls.append(f"folder {name}")
        return self.add(name, parent)

    def upload(self, name, content, parent, file_id):
        self.calls.append(f"upload {name}")
        if file_id:
            self.files[file_id]["content"] = content
            return file_id
        return self.add(name, parent, content)


class FakeGoogle:
    def connected(self):
        return True

    def drive_ready(self):
        return True

    def access_token(self):
        return "token"


@pytest.fixture
def drive(monkeypatch):
    fake = FakeDrive()
    monkeypatch.setattr(gdrive, "DriveApi", lambda _token: fake)
    return fake


def _backup(tmp_path):
    cfg = SETTINGS.google_drive.model_copy(update={"enabled": True, "daily_history": False})
    restored = []
    backup = DriveBackup(
        cfg,
        tmp_path / "google_drive.json",
        [tmp_path / "acompanhamento.json", tmp_path / "favoritos.json"],
        FakeGoogle(),
        on_restored=lambda: restored.append(True),
    )
    return backup, restored


def _existing_drive(drive) -> tuple[str, str, str]:
    """Pasta já criada pelo app numa instalação anterior."""
    folder = drive.add("Dash CIRP – Carteira", None)
    history = drive.add("Histórico", folder)
    current = drive.add("acompanhamento.json", folder, b'{"positions": [{"id": "a"}]}')
    return folder, history, current


def test_first_install_creates_folders_and_uploads(drive, tmp_path):
    (tmp_path / "acompanhamento.json").write_bytes(CARTEIRA)
    backup, _ = _backup(tmp_path)
    result = backup.sync()
    assert drive.calls == [
        "folder Dash CIRP – Carteira",
        "folder Histórico",
        "upload acompanhamento.json",
    ]
    assert result["uploaded"] == ["acompanhamento.json"] and result["restored"] == []
    drive.calls.clear()
    assert backup.sync()["uploaded"] == []  # nada mudou
    assert drive.calls == []


def test_formatted_pc_reuses_folder_and_restores_missing_file(drive, tmp_path):
    _, _, current = _existing_drive(drive)
    backup, restored = _backup(tmp_path)
    result = backup.sync()
    assert result["restored"] == ["acompanhamento.json"]
    assert result["uploaded"] == []  # restaurado = igual ao Drive, nada a enviar
    assert (tmp_path / "acompanhamento.json").read_bytes() == drive.files[current]["content"]
    assert not any(c.startswith("folder") for c in drive.calls)  # não criou pasta nova
    assert restored == [True]


def test_different_local_file_keeps_drive_version_before_overwrite(drive, tmp_path):
    _, history, current = _existing_drive(drive)
    old = drive.files[current]["content"]
    (tmp_path / "acompanhamento.json").write_bytes(CARTEIRA)
    backup, restored = _backup(tmp_path)
    result = backup.sync()
    assert result["restored"] == [] and result["uploaded"] == ["acompanhamento.json"]
    kept = [f for f in drive.files.values() if "_substituido_" in f["name"]]
    assert len(kept) == 1 and kept[0]["content"] == old and kept[0]["parents"] == [history]
    assert drive.files[current]["content"] == CARTEIRA
    assert restored == []


def test_same_local_content_is_adopted_without_upload(drive, tmp_path):
    _, _, current = _existing_drive(drive)
    (tmp_path / "acompanhamento.json").write_bytes(drive.files[current]["content"])
    backup, _ = _backup(tmp_path)
    assert backup.sync()["uploaded"] == []
    assert drive.calls == []


def test_restore_history_version_keeps_local_copy(drive, tmp_path):
    _, history, _ = _existing_drive(drive)
    older = drive.add("acompanhamento_2026-10-20.json", history, b'{"positions": [{"id": "x"}]}')
    local = tmp_path / "acompanhamento.json"
    local.write_bytes(CARTEIRA)
    backup, restored = _backup(tmp_path)
    names = [v["name"] for v in backup.versions()]
    assert names[0] == "acompanhamento.json" and "acompanhamento_2026-10-20.json" in names
    result = backup.restore(older)
    assert result == {
        "restored": "acompanhamento_2026-10-20.json",
        "target": "acompanhamento.json",
        "backup": "acompanhamento.pre-restauracao.bak",
    }
    assert local.read_bytes() == b'{"positions": [{"id": "x"}]}'
    assert (tmp_path / "acompanhamento.pre-restauracao.bak").read_bytes() == CARTEIRA
    assert restored == [True]


def test_restore_rejects_files_outside_app_folder_and_invalid_content(drive, tmp_path):
    folder, _, _ = _existing_drive(drive)
    stranger = drive.add("acompanhamento.json", "outra-pasta", CARTEIRA)
    broken = drive.add("acompanhamento_2026-10-21.json", folder, b"quebrado")
    local = tmp_path / "acompanhamento.json"
    local.write_bytes(CARTEIRA)
    backup, _ = _backup(tmp_path)
    with pytest.raises(GoogleDriveError):
        backup.restore(stranger)
    with pytest.raises(GoogleDriveError):
        backup.restore(broken)
    assert local.read_bytes() == CARTEIRA
