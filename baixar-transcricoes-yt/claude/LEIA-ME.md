# Pipeline de transcrição de playlist do YouTube

## Instalação
```
pip install -r requirements.txt
```
Também precisa do **ffmpeg** instalado no sistema (usado pelo yt-dlp para converter legendas para .srt):
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Mac: `brew install ffmpeg`

## Uso (em ordem)

### 1. Listar vídeos da playlist
```
python 1_listar_playlist.py --playlist-id PLxxxxxxxxxxxx --client-secret client_secret.json
```
Gera `manifest.json` com id, título, url e data de publicação de cada vídeo.

Autentica via OAuth (mesmo `client_secret.json` que você já usa para upload em lote), o que
também permite listar playlists privadas/não listadas. Na primeira execução abre o navegador
para autorizar; depois disso reutiliza `token.json` automaticamente sem pedir login de novo.

### 2. Baixar as legendas (.srt)
```
python 2_baixar_srt.py --manifest manifest.json --out-dir raw_srt
```
Baixa para `raw_srt/<video_id>/`. É retomável: se parar no meio, rode de novo e ele pula os já baixados.
Vídeos sem legenda disponível ficam listados em `falhas.json`.

### 3. Processar para JSON estruturado
```
python 3_processar_srt.py --raw-dir raw_srt --out-dir transcricoes_processadas
```
Gera `transcricoes_processadas/<video_id>/transcricao.json` (timestamps em segundos, prontos para
enviar a uma IA) e um `indice.json` com a lista de todos os vídeos processados.

## Próximo passo
Os arquivos em `transcricoes_processadas/` já estão no formato certo para o script de
extração de pontos-chave via API da Anthropic (chunking + geração de capítulos com timestamp).
