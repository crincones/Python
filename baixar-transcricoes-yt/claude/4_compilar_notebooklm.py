"""
4_compilar_notebooklm.py

Le os .srt baixados em <raw-dir>/<video_id>/ (gerado por 2_baixar_srt.py) e compila
tudo em no máximo N arquivos Markdown (default 20) para carregar como fontes no NotebookLM.

- Remove a duplicação das legendas automáticas do YouTube (efeito de rolagem).
- Agrupa o texto em parágrafos de ~60s, cada um iniciado por timestamp + link
  direto para o trecho no YouTube (https://youtu.be/<id>?t=<seg>), para que as
  citações do NotebookLM mostrem de qual vídeo/momento veio a informação.
- Distribui os vídeos (em ordem da playlist) entre os arquivos equilibrando o
  número de palavras; um vídeo nunca é dividido entre dois arquivos.

Uso:
    python 4_compilar_notebooklm.py --raw-dir Palmezani --out-dir Palmezani_notebooklm --prefixo Palmezani
"""

import argparse
import json
import re
from pathlib import Path

TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
LIMITE_PALAVRAS_NOTEBOOKLM = 500_000


def timestamp_para_segundos(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def formatar_tempo(segundos: float) -> str:
    s = int(segundos)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def parse_srt_sem_rolagem(caminho_srt: Path) -> list[tuple[float, str]]:
    """
    Retorna [(start, linha)] com cada linha de legenda uma única vez.

    Nas legendas automáticas do YouTube cada bloco repete a linha anterior e
    acrescenta uma nova; aqui só se mantém a linha na primeira vez que aparece.
    """
    conteudo = caminho_srt.read_text(encoding="utf-8", errors="ignore")
    blocos = re.split(r"\n\s*\n", conteudo.strip())

    linhas_saida = []
    ultimas = []  # linhas do bloco anterior
    for bloco in blocos:
        linhas = bloco.splitlines()
        idx = next((i for i, l in enumerate(linhas) if TIMESTAMP_RE.search(l)), None)
        if idx is None:
            continue
        start = timestamp_para_segundos(*TIMESTAMP_RE.search(linhas[idx]).groups()[0:4])
        texto = [re.sub(r"<[^>]+>", "", l).strip() for l in linhas[idx + 1:]]
        texto = [l for l in texto if l]
        for linha in texto:
            if linha not in ultimas and (not linhas_saida or linha != linhas_saida[-1][1]):
                linhas_saida.append((start, linha))
        if texto:
            ultimas = texto
    return linhas_saida


def montar_paragrafos(linhas: list[tuple[float, str]], janela_seg: int) -> list[tuple[float, str]]:
    """Agrupa as linhas em parágrafos de ~janela_seg, quebrando de preferência em fim de frase."""
    paragrafos = []
    inicio, atual = None, []
    for start, linha in linhas:
        if inicio is None:
            inicio = start
        atual.append(linha)
        passou = start - inicio >= janela_seg
        if passou and (linha.endswith((".", "?", "!")) or start - inicio >= janela_seg * 2):
            paragrafos.append((inicio, " ".join(atual)))
            inicio, atual = None, []
    if atual:
        paragrafos.append((inicio, " ".join(atual)))
    return paragrafos


def renderizar_video(meta: dict, paragrafos: list[tuple[float, str]]) -> str:
    vid = meta["video_id"]
    duracao = formatar_tempo(paragrafos[-1][0]) if paragrafos else "?"
    partes = [
        f"# {meta['titulo'].strip()}",
        "",
        f"- Vídeo: {meta['titulo'].strip()}",
        f"- URL: https://www.youtube.com/watch?v={vid}",
        f"- ID do vídeo: {vid}",
        f"- Publicado em: {meta.get('publicado_em', '')[:10]}",
        f"- Duração aprox.: {duracao}",
        "",
        "Cada parágrafo começa com [tempo | vídeo | link] indicando o trecho exato no YouTube.",
        "",
    ]
    rotulo = re.sub(r"\s+", " ", meta["titulo"]).strip()
    for inicio, texto in paragrafos:
        t = int(inicio)
        partes.append(f"[{formatar_tempo(t)} | {rotulo} | https://youtu.be/{vid}?t={t}] {texto}")
        partes.append("")
    return "\n".join(partes)


def particionar(pesos: list[int], k: int) -> list[list[int]]:
    """Divide pesos (em ordem) em até k grupos contíguos minimizando o maior grupo."""
    k = min(k, len(pesos))

    def cabe(limite: int) -> bool:
        grupos, soma = 1, 0
        for p in pesos:
            if soma + p > limite:
                grupos, soma = grupos + 1, p
            else:
                soma += p
        return grupos <= k

    lo, hi = max(pesos), sum(pesos)
    while lo < hi:
        meio = (lo + hi) // 2
        if cabe(meio):
            hi = meio
        else:
            lo = meio + 1

    grupos, atual, soma = [], [], 0
    for i, p in enumerate(pesos):
        # também força a abertura de novos grupos se sobrarem itens suficientes para usar os k arquivos
        restantes = len(pesos) - i
        faltam = k - len(grupos) - 1
        if atual and (soma + p > lo or restantes <= faltam):
            grupos.append(atual)
            atual, soma = [], 0
        atual.append(i)
        soma += p
    grupos.append(atual)
    return grupos


def main():
    parser = argparse.ArgumentParser(description="Compila .srt em arquivos Markdown para o NotebookLM")
    parser.add_argument("--raw-dir", default="raw_srt", help="Pasta com os .srt baixados (default: raw_srt)")
    parser.add_argument("--out-dir", default="notebooklm", help="Pasta de saída (default: notebooklm)")
    parser.add_argument("--max-fontes", type=int, default=20, help="Número máximo de arquivos (default: 20)")
    parser.add_argument("--janela-seg", type=int, default=60, help="Duração aprox. de cada parágrafo (default: 60)")
    parser.add_argument("--prefixo", default="transcricoes", help="Prefixo dos arquivos gerados")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    videos = []
    for pasta in [p for p in raw_dir.iterdir() if p.is_dir()]:
        srts = sorted(pasta.glob("*.srt"))
        if not srts:
            print(f"sem .srt: {pasta.name}")
            continue
        caminho_meta = pasta / "metadata.json"
        meta = json.loads(caminho_meta.read_text(encoding="utf-8")) if caminho_meta.exists() else {}
        meta.setdefault("video_id", pasta.name)
        meta.setdefault("titulo", pasta.name)
        paragrafos = montar_paragrafos(parse_srt_sem_rolagem(srts[0]), args.janela_seg)
        if not paragrafos:
            print(f"sem conteúdo válido: {pasta.name}")
            continue
        texto = renderizar_video(meta, paragrafos)
        videos.append({"meta": meta, "texto": texto, "palavras": len(texto.split())})

    videos.sort(key=lambda v: (v["meta"].get("posicao_playlist", 1_000_000), v["meta"]["titulo"]))
    grupos = particionar([v["palavras"] for v in videos], args.max_fontes)

    for arq in out_dir.glob(f"{args.prefixo}_*.md"):
        arq.unlink()

    indice = []
    for n, grupo in enumerate(grupos, 1):
        itens = [videos[i] for i in grupo]
        titulos = [re.sub(r"\s+", " ", v["meta"]["titulo"]).strip() for v in itens]
        cabecalho = [
            f"# {args.prefixo} — parte {n:02d} de {len(grupos):02d}",
            "",
            "Transcrições automáticas de vídeos do YouTube. Vídeos nesta fonte:",
            "",
            *[f"- {t} — https://www.youtube.com/watch?v={v['meta']['video_id']}" for t, v in zip(titulos, itens)],
            "",
            "---",
            "",
        ]
        conteudo = "\n".join(cabecalho) + "\n\n---\n\n".join(v["texto"] for v in itens)
        nome = f"{args.prefixo}_{n:02d}.md"
        (out_dir / nome).write_text(conteudo, encoding="utf-8")
        palavras = len(conteudo.split())
        aviso = "  <-- ACIMA DO LIMITE DO NOTEBOOKLM" if palavras > LIMITE_PALAVRAS_NOTEBOOKLM else ""
        print(f"{nome}: {len(itens)} vídeo(s), {palavras:,} palavras{aviso}")
        indice.append({"arquivo": nome, "palavras": palavras, "videos": [v["meta"] for v in itens]})

    with open(out_dir / "indice.json", "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"\nConcluído: {len(videos)} vídeos em {len(grupos)} arquivo(s) em {out_dir}/")


if __name__ == "__main__":
    main()
