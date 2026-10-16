"""Últimas cotações capturadas com o mercado ABERTO, por ativo-objeto (disco local).

Cada coleta durante o pregão (cadeia da análise ou pernas do acompanhamento) atualiza as séries
lidas (a mais recente de cada símbolo prevalece). Fora do pregão, o app lê daqui em vez de
consultar o MT5, cujo book fica vazio/distorcido. Arquivos em `data/cotacoes/` (fora do git),
gravados e lidos só por este aplicativo.
"""

from __future__ import annotations

import datetime as dt
import os
import threading
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar


class QuoteStore:
    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._lock = threading.Lock()

    def _path(self, underlying: str) -> Path:
        return self._dir / f"{underlying.upper()}.pkl"

    def save(self, underlying: str, chain: pd.DataFrame, captured_at: pd.Timestamp) -> None:
        """Mescla `chain` (normalizada) às cotações salvas do ativo."""
        if chain.empty:
            return
        with self._lock:
            stored = self._load_raw(underlying)
            fresh = chain.assign(captured_at=captured_at)
            merged = (
                pd.concat([stored, fresh], ignore_index=True)
                if stored is not None and not stored.empty
                else fresh
            )
            merged = merged.drop_duplicates("symbol", keep="last").reset_index(drop=True)
            self._dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path(underlying).with_suffix(".tmp")
            merged.to_pickle(tmp)
            os.replace(tmp, self._path(underlying))

    def _load_raw(self, underlying: str) -> pd.DataFrame | None:
        path = self._path(underlying)
        return pd.read_pickle(path) if path.exists() else None

    def load(self, underlying: str, today: dt.date, calendar: B3Calendar) -> pd.DataFrame | None:
        """Cotações salvas, com prazos (dias úteis/corridos) recalculados para `today`.
        Séries já vencidas são descartadas."""
        with self._lock:
            stored = self._load_raw(underlying)
        if stored is None or stored.empty:
            return None
        frame = stored[stored["expiration_date"] >= today].copy()
        if frame.empty:
            return None
        expirations = pd.Series(frame["expiration_date"].to_numpy(), index=frame.index)
        frame["dte_business_days"] = calendar.sessions_until(today, expirations)
        frame["dte_calendar_days"] = (pd.to_datetime(expirations) - pd.Timestamp(today)).dt.days
        return frame.reset_index(drop=True)

    def spot(self, underlying: str) -> tuple[float | None, pd.Timestamp | None]:
        """Último preço do ativo registrado junto das séries e o horário da captura."""
        with self._lock:
            stored = self._load_raw(underlying)
        if stored is None or stored.empty:
            return None, None
        latest = stored.sort_values("captured_at").iloc[-1]
        price = latest["underlying_price"]
        return (None if pd.isna(price) else float(price)), latest["captured_at"]
