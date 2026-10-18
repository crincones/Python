"""Ícones dos ativos (PNG 128×128) baixados sob demanda e guardados em disco.

Fonte configurável (padrão: repositório público thefintz/icones-b3, sem licença declarada; os
logos são marcas das empresas). Os arquivos ficam em `data/icones/` (fora do git) e não são
redistribuídos. Tenta o ticker completo (ex.: BOVA11) e depois a raiz de 4 letras (PETR).
Ausências ficam registradas por 7 dias para não repetir a busca a cada tela.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 512_000
MISSING_TTL_SECONDS = 7 * 86_400
TICKER_RE = re.compile(r"^[A-Z0-9]{4,12}$")


class IconCache:
    def __init__(self, directory: Path, url_template: str, timeout: float, enabled: bool) -> None:
        self._dir = directory
        self._url = url_template
        self._timeout = timeout
        self._enabled = enabled
        self._lock = threading.Lock()

    def path(self, ticker: str) -> Path | None:
        ticker = ticker.strip().upper()
        if not TICKER_RE.match(ticker):
            return None
        local = self._dir / f"{ticker}.png"
        if local.exists():
            return local
        marker = self._dir / f"{ticker}.missing"
        if marker.exists() and time.time() - marker.stat().st_mtime < MISSING_TTL_SECONDS:
            return None
        if not self._enabled:
            return None
        with self._lock:
            if local.exists():
                return local
            for name in dict.fromkeys((ticker, ticker[:4])):
                data = self._download(name)
                if data is not None:
                    self._dir.mkdir(parents=True, exist_ok=True)
                    tmp = local.with_suffix(".tmp")
                    tmp.write_bytes(data)
                    os.replace(tmp, local)
                    return local
            self._dir.mkdir(parents=True, exist_ok=True)
            marker.touch()
            return None

    def _download(self, name: str) -> bytes | None:
        url = self._url.format(name=name)
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resp:  # noqa: S310
                data = resp.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                log.warning("Ícone %s: HTTP %s", name, exc.code)
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            log.warning("Ícone %s indisponível: %s", name, exc)
            return None
        if len(data) > MAX_BYTES or not data.startswith(PNG_SIGNATURE):
            log.warning("Ícone %s ignorado: não é PNG válido ou grande demais", name)
            return None
        return data
