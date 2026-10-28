"""Rotas da cópia da Carteira no Google Drive. A conexão é a mesma do Google Agenda."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from travas.tracking.gcal import GoogleCalendarError
from travas.tracking.gdrive import DriveBackup, GoogleDriveError
from travas.tracking.secure_store import SecureStoreError


def drive_router(drive: DriveBackup) -> APIRouter:
    router = APIRouter(prefix="/api/drive")

    @router.get("/status")
    def status() -> dict:
        return drive.status()

    @router.post("/sync")
    def sync() -> dict:
        try:
            return drive.sync()
        except (GoogleDriveError, GoogleCalendarError, OSError, SecureStoreError) as exc:
            drive.last_error = str(exc)
            raise HTTPException(502, str(exc)) from exc

    @router.get("/versions")
    def versions() -> list[dict]:
        try:
            return drive.versions()
        except (GoogleDriveError, GoogleCalendarError, OSError, SecureStoreError) as exc:
            raise HTTPException(502, str(exc)) from exc

    @router.post("/restore/{file_id}")
    def restore(file_id: str) -> dict:
        """Troca o arquivo local pela cópia escolhida (o local vai para .pre-restauracao.bak)."""
        try:
            return drive.restore(file_id)
        except (GoogleDriveError, GoogleCalendarError, OSError, SecureStoreError) as exc:
            raise HTTPException(502, str(exc)) from exc

    return router
