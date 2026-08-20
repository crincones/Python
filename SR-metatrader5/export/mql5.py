"""Saida principal do projeto: CSV lido pelo indicador SR_Levels.mq5.

Um arquivo por simbolo, gravado na pasta MQL5/Files do terminal (a unica pasta
que o MQL5 enxerga em FileOpen sem FILE_COMMON):

    SR_USDJPY.csv

Formato -- texto ANSI, uma linha por nivel, campos separados por ';' e ponto
decimal (independente do locale da maquina):

    symbol;price;score;n_events;unique_days;unique_months;span_days;first_event;last_event

A primeira linha e o cabecalho, que o indicador pula. A coluna `symbol` e
redundante (ja esta no nome do arquivo) de proposito: e ela que o indicador
confere contra o _Symbol do grafico antes de desenhar qualquer coisa.

As datas saem como AAAA.MM.DD HH:MM, o formato que StringToTime() do MQL5 le
sem conversao.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

from models.level import Level

COLUNAS = [
    "symbol", "price", "score", "n_events", "unique_days",
    "unique_months", "span_days", "first_event", "last_event",
]


def _data(ts) -> str:
    """Timestamp no formato que o StringToTime() do MQL5 aceita."""
    return "" if ts is None else f"{ts:%Y.%m.%d %H:%M}"


def build_csv(levels: List[Level], symbol: str, digits: int, sep: str = ";") -> str:
    """Monta o conteudo do CSV, ja ordenado do preco mais alto para o mais baixo."""
    linhas = [sep.join(COLUNAS)]
    for lv in sorted(levels, key=lambda x: x.price, reverse=True):
        linhas.append(sep.join([
            symbol,
            f"{lv.price:.{digits}f}",
            f"{lv.score:.1f}",
            str(lv.n_events),
            str(lv.unique_days),
            str(lv.unique_months),
            f"{lv.span_days:.1f}",
            _data(lv.first_event),
            _data(lv.last_event),
        ]))
    return "\n".join(linhas) + "\n"


def write_csv(
    levels: List[Level],
    cfg,
    digits: int,
    meta: Optional[Dict] = None,
) -> Dict[str, Optional[str]]:
    """Grava o CSV em out_dir e copia para a pasta Files do terminal.

    Devolve {'local': ..., 'mt5': ..., 'meta': ...}; 'mt5' vem None quando
    cfg.mql5_files_dir esta desligado ou a pasta nao existe.
    """
    os.makedirs(cfg.out_dir, exist_ok=True)
    conteudo = build_csv(levels, cfg.symbol, digits, cfg.csv_sep)

    local = os.path.join(cfg.out_dir, cfg.csv_name)
    tmp = local + ".tmp"
    # newline="" + \r\n: o MQL5 le os dois finais de linha, mas o CRLF mantem o
    # arquivo legivel no Bloco de Notas e igual ao resto do ecossistema MT5.
    with open(tmp, "w", encoding="ascii", errors="replace", newline="\r\n") as fh:
        fh.write(conteudo)
    os.replace(tmp, local)

    # ---- metadados da rodada: ficam FORA da pasta Files, para nao poluir a
    # sandbox do terminal com arquivo que o indicador nao usa.
    meta_path = None
    if meta is not None:
        meta_path = os.path.join(cfg.out_dir, f"{cfg.csv_name[:-4]}_meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump({"gerado_em": datetime.now().isoformat(timespec="seconds"),
                       **{k: str(v) for k, v in meta.items()}},
                      fh, indent=2, ensure_ascii=False)

    destino = None
    if cfg.mql5_files_dir:
        if os.path.isdir(cfg.mql5_files_dir):
            destino = os.path.join(cfg.mql5_files_dir, cfg.csv_name)
            # copia atomica: o indicador pode estar lendo o arquivo agora
            tmp_mt5 = destino + ".tmp"
            shutil.copyfile(local, tmp_mt5)
            os.replace(tmp_mt5, destino)
        else:
            raise FileNotFoundError(
                f"pasta Files do terminal nao encontrada: {cfg.mql5_files_dir}\n"
                "Ajuste MQL5_FILES_DIR no config.py (Arquivo > Abrir pasta de "
                "dados > MQL5 > Files) ou rode com --sem-mt5."
            )

    return {"local": local, "mt5": destino, "meta": meta_path}


def install_indicator(cfg, source: str, destino_dir: str) -> str:
    """Copia o SR_Levels.mq5 para a pasta Indicators do terminal."""
    if not os.path.exists(source):
        raise FileNotFoundError(source)
    if not os.path.isdir(destino_dir):
        raise FileNotFoundError(f"pasta Indicators nao encontrada: {destino_dir}")
    destino = os.path.join(destino_dir, os.path.basename(source))
    shutil.copyfile(source, destino)
    return destino
