"""
1_listar_playlist.py

Lista todos os vídeos de uma playlist do YouTube usando a YouTube Data API v3,
autenticando via OAuth com client_secret.json (mesmo arquivo usado para upload
em lote), e salva um manifest.json com id, título, url e data de publicação
de cada vídeo.

Requisitos:
    pip install google-api-python-client google-auth-oauthlib google-auth

Como conseguir o client_secret.json:
    1. Google Cloud Console > APIs & Services > Credentials
    2. Create Credentials > OAuth client ID > tipo "Desktop app"
    3. Baixa o JSON e salva como client_secret.json

Uso:
    python 1_listar_playlist.py --playlist-id PL_XXXXXXXX --client-secret client_secret.json --out manifest.json

Na primeira execução, abre o navegador para autorizar o acesso à sua conta do
YouTube. Depois disso, as credenciais ficam salvas em token.json e são
reutilizadas automaticamente (não pede login de novo, a menos que expirem ou
o arquivo seja apagado).

Como pegar o playlist-id:
    Na URL da playlist: https://www.youtube.com/playlist?list=PLxxxxxxxxxxxx
    O playlist-id é o valor depois de "list=".
"""

import argparse
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# readonly é suficiente para listar playlists e vídeos, inclusive privados/não listados
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def obter_credenciais(client_secret_path: str, token_path: str) -> Credentials:
    """
    Obtém credenciais OAuth, reutilizando token salvo se existir e ainda for válido.
    Na primeira vez (ou se o token expirar sem refresh possível), abre o navegador
    para autorização manual.
    """
    creds = None
    token_file = Path(token_path)

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secret_path).exists():
                print(f"Erro: arquivo '{client_secret_path}' não encontrado.", file=sys.stderr)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json(), encoding="utf-8")

    return creds


def listar_videos_playlist(creds: Credentials, playlist_id: str) -> list[dict]:
    youtube = build("youtube", "v3", credentials=creds)
    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = item["contentDetails"]["videoId"]

            # Vídeos removidos/privados aparecem com título genérico; pula esses
            if snippet.get("title") in ("Private video", "Deleted video"):
                continue

            videos.append(
                {
                    "video_id": video_id,
                    "titulo": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "publicado_em": snippet.get("publishedAt", ""),
                    "posicao_playlist": snippet.get("position"),
                }
            )

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def main():
    parser = argparse.ArgumentParser(description="Lista vídeos de uma playlist do YouTube (autenticado via OAuth)")
    parser.add_argument("--playlist-id", required=True, help="ID da playlist do YouTube")
    parser.add_argument(
        "--client-secret",
        default="client_secret.json",
        help="Caminho do arquivo client_secret.json (default: client_secret.json)",
    )
    parser.add_argument(
        "--token",
        default="token.json",
        help="Caminho onde salvar/reutilizar o token OAuth (default: token.json)",
    )
    parser.add_argument("--out", default="manifest.json", help="Arquivo de saída (default: manifest.json)")
    args = parser.parse_args()

    creds = obter_credenciais(args.client_secret, args.token)

    print(f"Buscando vídeos da playlist {args.playlist_id}...")
    videos = listar_videos_playlist(creds, args.playlist_id)

    if not videos:
        print("Nenhum vídeo encontrado. Verifique o playlist-id e as permissões da conta autenticada.", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(videos)} vídeos salvos em {args.out}")


if __name__ == "__main__":
    main()
