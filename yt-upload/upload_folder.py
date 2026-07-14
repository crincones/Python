#!/usr/bin/env python3

import os
import pickle
import argparse

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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


def upload_video(youtube, filename, playlist_id):

    title = os.path.splitext(os.path.basename(filename))[0]

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

    print("-"*40)


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

    args = parser.parse_args()

    youtube = get_authenticated_service()

    videos = []

    for f in sorted(os.listdir(args.folder)):
        if f.lower().endswith(VIDEO_EXTENSIONS):
            videos.append(os.path.join(args.folder, f))

    print(f"{len(videos)} vídeo(s) encontrado(s).")

    for video in videos:
        upload_video(
            youtube,
            video,
            args.playlist
        )

    print("Todos os uploads finalizaram.")


if __name__ == "__main__":
    main()