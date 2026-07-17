#!/usr/bin/env python3

import os
import json
import pickle
import argparse

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timezone

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".m4v"
)

REGISTRY_FILE = "uploaded_videos.json"


def load_registry(registry_path):
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_registry(registry_path, registry):
    # grava em arquivo temporário e substitui, para evitar corromper
    # o registro caso o processo seja interrompido no meio da escrita
    tmp_path = registry_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, registry_path)


def make_key(filename, playlist_id):
    abs_path = os.path.abspath(filename)
    return f"{abs_path}::{playlist_id or ''}"


def get_authenticated_service():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, filename, playlist_id, registry, registry_path):

    key = make_key(filename, playlist_id)
    title = os.path.splitext(os.path.basename(filename))[0]

    entry = registry.get(key)

    # já foi enviado e (se havia playlist) já foi adicionado a ela
    if entry and entry.get("status") == "done":
        print(f"Já enviado, pulando: {title}")
        print("-" * 40)
        return

    video_id = entry.get("video_id") if entry else None

    if video_id:
        print(f"Upload já feito anteriormente (video_id={video_id}), retomando etapa de playlist: {title}")
    else:
        body = {
            "snippet": {
                "title": title,
                "description": "",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "unlisted",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            filename,
            chunksize=8 * 1024 * 1024,
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        print(f"Enviando: {title}")

        response = None

        while response is None:
            status, response = request.next_chunk()

            if status:
                print(f"{title}: {int(status.progress()*100)}%")

        video_id = response["id"]

        print("Upload concluído.")

        # salva o registro imediatamente após o upload, antes de mexer
        # na playlist, para não reenviar o vídeo caso a etapa seguinte falhe
        registry[key] = {
            "filename": os.path.abspath(filename),
            "title": title,
            "playlist_id": playlist_id or None,
            "video_id": video_id,
            "status": "uploaded",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        save_registry(registry_path, registry)

    if playlist_id:

        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()

        print("Adicionado à playlist.")

    registry[key]["status"] = "done"
    save_registry(registry_path, registry)

    print("-" * 40)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--folder",
        required=True,
        help="Pasta contendo os vídeos"
    )

    parser.add_argument(
        "--playlist",
        default="",
        help="ID da playlist"
    )

    parser.add_argument(
        "--registry",
        default=REGISTRY_FILE,
        help="Caminho do arquivo de registro de uploads (padrão: uploaded_videos.json)"
    )

    args = parser.parse_args()

    youtube = get_authenticated_service()

    registry = load_registry(args.registry)

    videos = []

    for f in sorted(os.listdir(args.folder)):
        if f.lower().endswith(VIDEO_EXTENSIONS):
            videos.append(os.path.join(args.folder, f))

    print(f"{len(videos)} vídeo(s) encontrado(s).")

    for video in videos:
        upload_video(
            youtube,
            video,
            args.playlist,
            registry,
            args.registry
        )

    print("Todos os uploads finalizaram.")


if __name__ == "__main__":
    main()