"""
3_processar_srt.py

Le os .srt baixados em raw_srt/<video_id>/ (gerado por 2_baixar_srt.py) e gera,
para cada vídeo, um JSON estruturado com timestamps em segundos, pronto para
ser usado em análise por IA. Também gera um índice geral.

Estrutura de saída:
    transcricoes_processadas/
        <video_id>/
            transcricao.json
        indice.json          (lista de todos os vídeos processados, com metadados)

Formato de transcricao.json:
    {
      "video_id": "...",
      "titulo": "...",
      "url": "...",
      "publicado_em": "...",
      "duracao_seg": 16234.32,
      "segmentos": [
        {"start": 0.0, "end": 4.32, "texto": "..."},
        ...
      ]
    }

Uso:
    python 3_processar_srt.py --raw-dir raw_srt --out-dir transcricoes_processadas
"""

import argparse
import json
import re
from pathlib import Path

TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def timestamp_para_segundos(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(caminho_srt: Path) -> list[dict]:
    """Parseia um arquivo .srt em uma lista de segmentos {start, end, texto}."""
    conteudo = caminho_srt.read_text(encoding="utf-8", errors="ignore")
    blocos = re.split(r"\n\s*\n", conteudo.strip())

    segmentos = []
    for bloco in blocos:
        linhas = [l for l in bloco.splitlines() if l.strip()]
        if not linhas:
            continue

        # encontra a linha de timestamp dentro do bloco (pode vir antes ou depois do índice numérico)
        idx_timestamp = None
        match = None
        for i, linha in enumerate(linhas):
            m = TIMESTAMP_RE.search(linha)
            if m:
                idx_timestamp = i
                match = m
                break

        if match is None:
            continue

        start = timestamp_para_segundos(*match.groups()[0:4])
        end = timestamp_para_segundos(*match.groups()[4:8])
        texto = " ".join(linhas[idx_timestamp + 1:]).strip()

        # remove tags de formatação residuais (ex: <c>, </c> de legendas auto-geradas)
        texto = re.sub(r"<[^>]+>", "", texto).strip()

        if texto:
            segmentos.append({"start": round(start, 2), "end": round(end, 2), "texto": texto})

    return mesclar_segmentos_duplicados(segmentos)


def mesclar_segmentos_duplicados(segmentos: list[dict]) -> list[dict]:
    """
    Legendas automáticas do YouTube costumam repetir o mesmo texto em segmentos
    consecutivos sobrepostos (efeito de rolagem). Esta função remove repetições
    exatas consecutivas e funde segmentos idênticos adjacentes.
    """
    if not segmentos:
        return segmentos

    limpos = [segmentos[0]]
    for seg in segmentos[1:]:
        anterior = limpos[-1]
        if seg["texto"] == anterior["texto"]:
            anterior["end"] = seg["end"]
        else:
            limpos.append(seg)
    return limpos


def processar_video(pasta_video: Path, out_dir: Path) -> dict | None:
    arquivos_srt = list(pasta_video.glob("*.srt"))
    if not arquivos_srt:
        return None

    # se houver mais de um .srt (idiomas diferentes), pega o primeiro por ordem alfabética
    caminho_srt = sorted(arquivos_srt)[0]

    caminho_metadata = pasta_video / "metadata.json"
    metadata = {}
    if caminho_metadata.exists():
        metadata = json.loads(caminho_metadata.read_text(encoding="utf-8"))

    segmentos = parse_srt(caminho_srt)
    if not segmentos:
        return None

    video_id = pasta_video.name
    resultado = {
        "video_id": video_id,
        "titulo": metadata.get("titulo", ""),
        "url": metadata.get("url", f"https://www.youtube.com/watch?v={video_id}"),
        "publicado_em": metadata.get("publicado_em", ""),
        "duracao_seg": segmentos[-1]["end"] if segmentos else 0,
        "segmentos": segmentos,
    }

    pasta_saida = out_dir / video_id
    pasta_saida.mkdir(parents=True, exist_ok=True)
    with open(pasta_saida / "transcricao.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return {
        "video_id": video_id,
        "titulo": resultado["titulo"],
        "url": resultado["url"],
        "duracao_seg": resultado["duracao_seg"],
        "n_segmentos": len(segmentos),
        "arquivo": str((pasta_saida / "transcricao.json").as_posix()),
    }


def main():
    parser = argparse.ArgumentParser(description="Processa .srt baixados em JSON estruturado")
    parser.add_argument("--raw-dir", default="raw_srt", help="Pasta com os .srt baixados (default: raw_srt)")
    parser.add_argument(
        "--out-dir", default="transcricoes_processadas", help="Pasta de saída (default: transcricoes_processadas)"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pastas_video = sorted([p for p in raw_dir.iterdir() if p.is_dir()])
    print(f"Processando {len(pastas_video)} vídeos...")

    indice = []
    sem_legenda = []

    for i, pasta_video in enumerate(pastas_video, 1):
        entrada = processar_video(pasta_video, out_dir)
        if entrada:
            indice.append(entrada)
            print(f"[{i}/{len(pastas_video)}] ok: {pasta_video.name} ({entrada['n_segmentos']} segmentos)")
        else:
            sem_legenda.append(pasta_video.name)
            print(f"[{i}/{len(pastas_video)}] sem conteúdo válido: {pasta_video.name}")

    with open(out_dir / "indice.json", "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"\nConcluído: {len(indice)} vídeos processados em {out_dir}/")
    if sem_legenda:
        print(f"{len(sem_legenda)} vídeo(s) sem conteúdo válido: {sem_legenda}")


if __name__ == "__main__":
    main()
