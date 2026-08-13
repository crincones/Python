"""
Modelo neutro de nivel (secoes 25 e 26 do descritivo).

Um nivel e SEMPRE um unico preco. Nao existe classificacao suporte/resistencia
e nao existe zona (price_low / price_high / zone_width).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

# Colunas do DataFrame de eventos produzido pela etapa de deteccao.
EVENT_COLUMNS = [
    "timestamp",     # instante do evento (fim da interacao, inicio da reacao)
    "pos",           # posicao correspondente na serie de 1 minuto
    "price",         # preco representativo do evento
    "scale",         # escala/estrutura de origem (timeframe ou profundidade do pivo)
    "source",        # 'swing' ou 'ref_<kind>' -- apenas proveniencia
    "reaction",      # maior deslocamento absoluto posterior, em pontos
    "strength",      # reacao normalizada pela volatilidade esperada
    "rel_volume",    # volume relativo no instante do evento (NaN se ausente)
    "atr",           # ATR de referencia vigente
]


@dataclass
class Level:
    """Uma linha horizontal de preco com um score de relevancia historica."""

    price: float
    score: float = 0.0

    # ---- estatisticas de suporte factual do nivel -------------------------
    n_events: int = 0
    unique_days: int = 0
    unique_weeks: int = 0
    unique_months: int = 0
    span_days: float = 0.0
    first_event: Optional[pd.Timestamp] = None
    last_event: Optional[pd.Timestamp] = None
    mean_strength: float = 0.0
    median_strength: float = 0.0
    max_strength: float = 0.0
    mean_reaction: float = 0.0
    n_scales: int = 0
    n_sources: int = 0
    mean_rel_volume: float = float("nan")
    decayed_touches: float = 0.0

    # ---- decomposicao do score (0..1 cada) --------------------------------
    components: Dict[str, float] = field(default_factory=dict)

    def as_row(self) -> dict:
        row = {
            "price": self.price,
            "score": self.score,
            "n_events": self.n_events,
            "unique_days": self.unique_days,
            "unique_weeks": self.unique_weeks,
            "unique_months": self.unique_months,
            "span_days": self.span_days,
            "first_event": self.first_event,
            "last_event": self.last_event,
            "mean_strength": self.mean_strength,
            "median_strength": self.median_strength,
            "max_strength": self.max_strength,
            "mean_reaction": self.mean_reaction,
            "n_scales": self.n_scales,
            "n_sources": self.n_sources,
            "mean_rel_volume": self.mean_rel_volume,
            "decayed_touches": self.decayed_touches,
        }
        row.update({f"c_{k}": v for k, v in self.components.items()})
        return row


def levels_to_frame(levels) -> pd.DataFrame:
    if not levels:
        return pd.DataFrame(columns=[c for c in Level(0.0).as_row()])
    return pd.DataFrame([lv.as_row() for lv in levels])
