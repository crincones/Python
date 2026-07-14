"""
2_baixar_srt.py

Le o manifest.json (gerado por 1_listar_playlist.py) e baixa a legenda (.srt)
de cada vídeo usando yt-dlp, salvando numa pasta por vídeo:

    raw_srt/
        <video_id>/
            <video_id>.pt.srt
            metadata.json      (copia dos dados do manifest para esse vídeo)

Requisitos:
    pip install yt-dlp
    ffmpeg instalado no sistema (necessário para converter legendas para .srt)
        - Ubuntu/Debian: sudo apt install ffmpeg
        - Mac: brew install ffmpeg

Uso:
    python 2_baixar_srt.py --manifest manifest.json --out-dir raw_srt --langs "pt,pt-BR,pt-orig"

Observações:
    - Tenta primeiro legenda manual (--write-subs), depois legenda automática
      (--write-auto-subs) no(s) idioma(s) informado(s).
    - Pula vídeos que já têm .srt baixado (retomável: pode rodar de novo sem repetir).
    - Gera um log de falhas em falhas.json ao final.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def video_ja_baixado(pasta_video: Path) -> bool:
    return any(pasta_video.glob("*.srt")) if pasta_video.exists() else False


def baixar_srt_video(video: dict, out_dir: Path, langs: str) -> bool:
    video_id = video["video_id"]
    pasta_video = out_dir / video_id
    pasta_video.mkdir(parents=True, exist_ok=True)

    if video_ja_baixado(pasta_video):
        print(f"  [pulado] {video_id} já tem .srt")
        return True

    saida_template = str(pasta_video / f"{video_id}")

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", langs,
        "--convert-subs", "srt",
        "-o", saida_template,
        video["url"],
    ]

    resultado = subprocess.run(cmd, capture_output=True, text=True)

    if resultado.returncode != 0:
        print(f"  [ERRO] {video_id}: {resultado.stderr.strip()[-300:]}")
        return False

    if not video_ja_baixado(pasta_video):
        print(f"  [sem legenda] {video_id} — nenhuma legenda disponível no(s) idioma(s) pedido(s)")
        return False

    # salva metadata junto, útil para a etapa de processamento
    with open(pasta_video / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(video, f, ensure_ascii=False, indent=2)

    print(f"  [ok] {video_id}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Baixa legendas .srt de todos os vídeos de um manifest")
    parser.add_argument("--manifest", default="manifest.json", help="Arquivo manifest.json de entrada")
    parser.add_argument("--out-dir", default="raw_srt", help="Pasta de saída (default: raw_srt)")
    parser.add_argument(
        "--langs",
        default="pt,pt-BR,pt-orig",
        help="Idiomas de legenda a tentar, em ordem de preferência (default: pt,pt-BR,pt-orig)",
    )
    args = parser.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        videos = json.load(f)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    falhas = []
    print(f"Baixando legendas de {len(videos)} vídeos...")

    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video['video_id']} - {video['titulo'][:60]}")
        ok = baixar_srt_video(video, out_dir, args.langs)
        if not ok:
            falhas.append(video)

    if falhas:
        with open("falhas.json", "w", encoding="utf-8") as f:
            json.dump(falhas, f, ensure_ascii=False, indent=2)
        print(f"\n{len(falhas)} vídeo(s) sem legenda ou com erro. Detalhes em falhas.json")

    sucesso = len(videos) - len(falhas)
    print(f"\nConcluído: {sucesso}/{len(videos)} vídeos com legenda baixada.")


if __name__ == "__main__":
    main()
