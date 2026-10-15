"""Estado do pregão de opções da B3 pelo relógio de Brasília (America/Sao_Paulo).

Fora do pregão (antes da abertura, depois do fechamento, fim de semana ou feriado) o book do
MT5 fica vazio ou distorcido; o app então usa as últimas cotações capturadas com o mercado
aberto (`QuoteStore`). Horários configuráveis em settings.yaml (`market_hours`).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from travas.calendar_b3 import B3Calendar

OPEN = "aberto"
PRE_OPEN = "pré-abertura"
CLOSED = "encerrado"
NO_SESSION = "sem pregão"


@dataclass(frozen=True, slots=True)
class MarketStatus:
    phase: str
    is_open: bool
    now: dt.datetime
    session_open: dt.time
    session_close: dt.time

    @property
    def label(self) -> str:
        return {
            OPEN: "Mercado aberto",
            PRE_OPEN: "Pré-abertura: mercado ainda fechado",
            CLOSED: "Pregão encerrado",
            NO_SESSION: "Sem pregão hoje (fim de semana ou feriado)",
        }[self.phase]

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "is_open": self.is_open,
            "label": self.label,
            "session_open": self.session_open.strftime("%H:%M"),
            "session_close": self.session_close.strftime("%H:%M"),
            "now": self.now.isoformat(timespec="seconds"),
        }


def parse_hhmm(text: str) -> dt.time:
    hours, minutes = text.split(":")
    return dt.time(int(hours), int(minutes))


def market_status(
    now: dt.datetime, calendar: B3Calendar, session_open: dt.time, session_close: dt.time
) -> MarketStatus:
    """`now` deve estar em America/Sao_Paulo."""
    if not calendar.is_session(now.date()):
        phase = NO_SESSION
    elif now.time() < session_open:
        phase = PRE_OPEN
    elif now.time() >= session_close:
        phase = CLOSED
    else:
        phase = OPEN
    return MarketStatus(phase, phase == OPEN, now, session_open, session_close)
