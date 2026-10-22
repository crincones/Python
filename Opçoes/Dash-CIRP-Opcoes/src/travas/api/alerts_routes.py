"""Rotas dos alertas de stop 1:1 (estado e teste de envio). Nenhuma ordem é enviada."""

from __future__ import annotations

from fastapi import APIRouter

from travas.alerts.service import StopAlerts


def alerts_router(alerts: StopAlerts) -> APIRouter:
    router = APIRouter(prefix="/api/alerts")

    @router.get("/status")
    def status() -> dict:
        return alerts.status()

    @router.post("/test")
    def test() -> dict:
        """Mensagem de teste (Telegram + e-mail) pelo app e pelo servidor de alertas."""
        return alerts.test()

    return router
