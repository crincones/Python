"""Saida principal do projeto: codigo NTSL para o ProfitChart (secao 32).

Gera uma chamada HorizontalLineCustom() por nivel selecionado, com parametros
de cor (R, G, B), espessura e tipo de linha configuraveis pelo usuario dentro
do proprio indicador (secao 39.1).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List

from models.level import Level

_STYLE_HELP = "0=solida 1=tracejada 2=pontilhada 3=traco-ponto 4=traco-ponto-ponto"


def _header(levels: List[Level], meta: Dict) -> str:
    sep = "//" + "=" * 72
    lines = [
        sep,
        "// Niveis importantes (preco + relevancia) -- sem suporte/resistencia, sem zonas",
        f"// Gerado automaticamente por main.py em {datetime.now():%d/%m/%Y %H:%M}",
        f"// Historico       : {meta.get('inicio')}  ->  {meta.get('fim')}",
        f"// Candles 1m      : {meta.get('n_candles'):,}".replace(",", "."),
        f"// Tick size       : {meta.get('tick')}",
        (f"// Grafico         : Renko {meta.get('box_ticks')}R = {meta.get('caixa'):g} pts "
         f"| {meta.get('n_tijolos'):,} tijolos".replace(",", ".")
         if meta.get("modo") == "renko" else
         "// Grafico         : multi-timeframe (5m, 15m, 1h, 4h, diario, semanal)"),
        f"// Eventos         : {meta.get('n_eventos'):,}".replace(",", "."),
        f"// Clustering      : {meta.get('metodo')} | banda {meta.get('banda_pts'):.0f} pts",
        f"// Separacao linhas: {meta.get('separacao'):.0f} pts (media obtida {meta.get('sep_media'):.0f} pts)",
        f"// Niveis          : {len(levels)} de {meta.get('n_niveis_totais')} candidatos",
        "//" + "-" * 72,
        "// Se a sua versao do ProfitChart nao aceitar RGB(), troque a linha",
        "//   Cor := RGB( CorR, CorG, CorB );   por   Cor := clBlue;",
        "//" + "-" * 72,
        "// #    Preco        Score  Ev   Dias  Meses  Span(d)  Esc  Ultimo evento",
    ]
    for i, lv in enumerate(levels, 1):
        lines.append(
            f"// {i:<4} {lv.price:>10,.0f}  {lv.score:>5.1f}  {lv.n_events:>3}  "
            f"{lv.unique_days:>4}  {lv.unique_months:>5}  {lv.span_days:>7.0f}  "
            f"{lv.n_scales:>3}  {lv.last_event:%d/%m/%Y}".replace(",", ".")
        )
    lines.append(sep)
    return "\n".join(lines)


def build_ntsl(levels: List[Level], cfg, meta: Dict) -> str:
    r, g, b = cfg.ntsl_color_rgb
    out = [_header(levels, meta), "", "input", ]
    out += [
        f"  CorR         ( {r} );",
        f"  CorG         ( {g} );",
        f"  CorB         ( {b} );",
        f"  Espessura    ( {cfg.ntsl_width} );",
        f"  TipoLinha    ( {cfg.ntsl_style} );   // {_STYLE_HELP}",
        f"  TamanhoTexto ( {cfg.ntsl_text_size} );",
        f"  LocalTexto   ( {cfg.ntsl_text_pos} );",
        "",
        "var",
        "  Cor    : Integer;",
        "  Estilo : Integer;",
        "",
        "begin",
        "",
        "  Cor := RGB( CorR, CorG, CorB );",
        "",
        f"  // {_STYLE_HELP}",
        "  if      TipoLinha = 0 then Estilo := psSolid",
        "  else if TipoLinha = 2 then Estilo := psDot",
        "  else if TipoLinha = 3 then Estilo := psDashDot",
        "  else if TipoLinha = 4 then Estilo := psDashDotDot",
        "  else                       Estilo := psDash;",
        "",
        "  // Desenha uma unica vez, na ultima barra do grafico.",
        "  if LastBarOnChart then",
        "  begin",
        "",
    ]

    for i, lv in enumerate(levels, 1):
        label = f"R{lv.score:.0f} T{lv.n_events}"
        out.append(
            f"    // Nivel {i}: score={lv.score:.1f} | eventos={lv.n_events} | "
            f"dias={lv.unique_days} | meses={lv.unique_months} | "
            f"ultimo evento {lv.last_event:%d/%m/%Y}"
        )
        out.append(
            f"    HorizontalLineCustom( {lv.price:.2f}, Cor, Espessura, Estilo, "
            f'"{label}", TamanhoTexto, LocalTexto, 0, 0, 0 );'
        )
        out.append("")

    out += ["  end;", "", "end;", ""]
    return "\n".join(out)


def write_ntsl(levels: List[Level], cfg, meta: Dict, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="latin-1", errors="replace") as fh:
        fh.write(build_ntsl(levels, cfg, meta))
    return path
