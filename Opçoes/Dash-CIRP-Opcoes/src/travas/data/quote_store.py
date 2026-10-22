"""Últimas cotações capturadas com o mercado ABERTO, por ativo-objeto (disco local).

Cada coleta durante o pregão (cadeia da análise ou pernas da carteira) atualiza as séries
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


def reference_capture(captured: pd.Series) -> pd.Timestamp:
    """Captura com mais séries (empate: a mais recente)."""
    counts = pd.to_datetime(captured).value_counts()
    return max(counts[counts == counts.max()].index)


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
        Séries já vencidas são descartadas. As idades são as da captura de cada série: alinhe
        o recorte usado com `align_captures` antes de combinar séries."""
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

    @staticmethod
    def align_captures(frame: pd.DataFrame) -> tuple[pd.DataFrame, float | None]:
        """Alinha um recorte de cotações salvas à sua captura principal.

        Cada coleta salva só o seu escopo, então o recorte pode misturar capturas de horários
        diferentes. A referência é a captura com mais séries no recorte (empate: a mais recente)
        — nunca simplesmente a última do arquivo, que pode ser uma atualização de 2 pernas do
        carteira e tornaria "antiga" a cadeia inteira. As demais séries somam à idade a
        distância (antes ou depois) até a referência: uma perna de horas antes vira "cotação
        antiga" em vez de ser combinada como atual com outra perna e com outro preço do ativo.
        Devolve o recorte e o preço do ativo lido na captura de referência."""
        if frame.empty:
            return frame, None
        captured = pd.to_datetime(frame["captured_at"])
        reference = reference_capture(captured)
        gap = (captured - reference).abs().dt.total_seconds()
        aligned = frame.assign(quote_age_seconds=frame["quote_age_seconds"] + gap)
        prices = frame.loc[captured == reference, "underlying_price"].dropna()
        return aligned, (float(prices.iloc[-1]) if len(prices) else None)

    def spot(self, underlying: str) -> tuple[float | None, pd.Timestamp | None]:
        """Último preço do ativo registrado junto das séries e o horário da captura."""
        with self._lock:
            stored = self._load_raw(underlying)
        if stored is None or stored.empty:
            return None, None
        latest = stored.sort_values("captured_at").iloc[-1]
        price = latest["underlying_price"]
        return (None if pd.isna(price) else float(price)), latest["captured_at"]
