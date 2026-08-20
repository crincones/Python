import sys
import json
import re
from yt_dlp import YoutubeDL
# IMPORTAÇÃO DIRETA DA FUNÇÃO: Evita problemas de escopo/versão do objeto de classe
from youtube_transcript_api import YouTubeTranscriptApi

def extrair_dados_playlist(url_playlist):
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
    }
    
    print("📌 Buscando vídeos da playlist... Aguarde.")
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url_playlist, download=False)
        except Exception as e:
            print(f"❌ Erro ao acessar a playlist. Verifique se a URL está correta.\nDetalhes: {e}")
            return
        
        if 'entries' not in info_dict:
            print("❌ Não foi possível encontrar vídeos nesta playlist.")
            return
            
        videos = info_dict['entries']
        print(f"✅ Encontrados {len(videos)} vídeos na playlist.\n")

    for idx, video in enumerate(videos, start=1):
        video_id = video.get('id')
        titulo = video.get('title')
        
        if not video_id:
            continue
            
        nome_arquivo_limpo = re.sub(r'[\\/*?:"<>|]', "", titulo).replace(" ", "_")
        nome_final_arquivo = f"{video_id}_{nome_arquivo_limpo[:30]}.json"
        
        print(f"[{idx}/{len(videos)}] Processando: {titulo} (ID: {video_id})")
        
        try:
            # Forçando a execução do método mais básico que existe na biblioteca original
            # usando parâmetros posicionais simples para evitar quebras
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, ['pt', 'en'])
            
            falas_formatadas = []
            for fala in transcript_list:
                segundos = int(fala['start'])
                texto = fala['text'].replace("\n", " ")
                falas_formatadas.append([segundos, texto])
            
            json_final = {
                "id": video_id,
                "titulo": titulo,
                "falas": falas_formatadas
            }
            
            with open(nome_final_arquivo, 'w', encoding='utf-8') as f:
                json.dump(json_final, f, ensure_ascii=False, indent=2)
                
            print(f"   💾 Salvo com sucesso: {nome_final_arquivo}")
            
        except Exception as e:
            print(f"   ❌ Erro no vídeo {video_id}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Erro: Você precisa passar a URL da playlist como argumento.")
        print("\nUso correto:")
        print('  python baixar-transcript.py "SUA_URL_DA_PLAYLIST_AQUI"\n')
        sys.exit(1)
        
    url_argumento = sys.argv[1]
    extrair_dados_playlist(url_argumento)