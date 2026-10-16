"""Rotas dos ativos com estrela (seguimento). Só leitura/gravação local; nada de ordens."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from travas.watchlist.store import NOTE_MAX, WatchlistError, WatchlistStore


class StarIn(BaseModel):
    price: float | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=NOTE_MAX)


def watchlist_router(store: WatchlistStore) -> APIRouter:
    router = APIRouter(prefix="/api/watchlist")

    @router.get("")
    def list_items() -> dict:
        return {"items": store.list()}

    @router.put("/{ticker}")
    def star(ticker: str, body: StarIn | None = None) -> dict:
        body = body or StarIn()
        try:
            return store.add(ticker, body.price, body.note)
        except WatchlistError as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.delete("/{ticker}")
    def unstar(ticker: str) -> dict:
        try:
            removed = store.remove(ticker)
        except WatchlistError as exc:
            raise HTTPException(422, str(exc)) from exc
        if not removed:
            raise HTTPException(404, f"{ticker} não está na lista")
        return {"ok": True}

    return router
