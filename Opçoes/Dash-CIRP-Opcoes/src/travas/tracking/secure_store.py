"""Proteção de segredos locais com a DPAPI do Windows (CryptProtectData).

O conteúdo só pode ser decifrado pela mesma conta de usuário do Windows nesta máquina: o arquivo
gravado em disco não contém o segredo em texto puro. Usado para o token do Google Agenda.
"""

from __future__ import annotations

import base64
import ctypes
import sys

CRYPTPROTECT_UI_FORBIDDEN = 0x1
DESCRIPTION = "Dash CIRP Opcoes"


class SecureStoreError(RuntimeError):
    pass


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _call(function, data: bytes, *middle) -> bytes:
    buffer = ctypes.create_string_buffer(data, len(data))
    source = _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    target = _Blob()
    ok = function(
        ctypes.byref(source), *middle, None, None, None, CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(target),
    )
    if not ok:
        raise SecureStoreError(f"DPAPI falhou (erro {ctypes.GetLastError()})")
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def _require_windows() -> None:
    if sys.platform != "win32":
        raise SecureStoreError("armazenamento protegido disponível só no Windows (DPAPI)")


def protect(text: str) -> str:
    """Texto → base64 do blob cifrado pela DPAPI (conta de usuário atual)."""
    _require_windows()
    blob = _call(ctypes.windll.crypt32.CryptProtectData, text.encode("utf-8"), DESCRIPTION)
    return base64.b64encode(blob).decode("ascii")


def unprotect(encoded: str) -> str:
    _require_windows()
    blob = _call(ctypes.windll.crypt32.CryptUnprotectData, base64.b64decode(encoded), None)
    return blob.decode("utf-8")
