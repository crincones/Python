"""Rotas do Google Agenda (eventos de vencimento do Acompanhamento). Nada de ordens."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from travas.tracking.gcal import CalendarSync, GoogleCalendarError
from travas.tracking.secure_store import SecureStoreError


def calendar_router(gcal: CalendarSync) -> APIRouter:
    router = APIRouter(prefix="/api/calendar")

    @router.get("/status")
    def status() -> dict:
        return gcal.status()

    @router.post("/connect")
    def connect() -> dict:
        """URL de consentimento do Google; o usuário faz login e autoriza no navegador."""
        try:
            return {"auth_url": gcal.begin_connect()}
        except (GoogleCalendarError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.post("/sync")
    def sync() -> dict:
        try:
            return gcal.sync()
        except (GoogleCalendarError, OSError, SecureStoreError) as exc:
            gcal.last_error = str(exc)
            raise HTTPException(502, str(exc)) from exc

    @router.post("/disconnect")
    def disconnect() -> dict:
        gcal.disconnect()
        return {"ok": True}

    return router
