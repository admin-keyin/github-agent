import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth.exceptions

def get_authenticated_service():
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("Error: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN must be set.")
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    try:
        print("Attempting to refresh access token...")
        creds.refresh(Request())
        print("Token refresh successful.")
    except google.auth.exceptions.RefreshError as e:
        print("\n" + "="*60)
        print("Authentication Error: Failed to refresh the access token.")
        print(f"Details: {e}")
        print("="*60 + "\n")
        sys.exit(1)

    return build("youtube", "v3", credentials=creds)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_to_youtube.py <video_file_path>")
        sys.exit(1)

    video_file = sys.argv[1]
    
    # 생성 스크립트에서 저장한 곡 메타데이터 읽기
    json_path = "temp/video_info.json"
    txt_path = "temp/video_info.txt"
    title_part = ""
    desc_part = ""
    artist_name = "K-Pop Piano"
    song_title = "멜론 인기곡"

    if os.path.exists(json_path):
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            title_part = meta.get("title", "")
            desc_part = meta.get("description", "")
            artist_name = meta.get("artist", artist_name)
            song_title = meta.get("song_title", song_title)
    elif os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            raw_info = f.read().strip()
            parts = raw_info.split('|')
            if len(parts) >= 2:
                title_part = parts[0].strip()
                desc_part = parts[1].strip()
            if len(parts) >= 4:
                artist_name = parts[2].strip()
                song_title = parts[3].strip()

    if title_part:
        title = f"[8 Hours] {title_part}"
        description = desc_part
    else:
        title = os.getenv("VIDEO_TITLE", "[8 Hours] 멜론 TOP 100 인기곡 감성 피아노 연주곡 모음 (Sleep & Study)")
        description = os.getenv("VIDEO_DESCRIPTION", "멜론 실시간 인기곡들을 감미로운 피아노 연주로 감상하는 8시간 연속 재생 플레이리스트입니다.")

    description += f"\n\n#{artist_name.replace(' ', '')} #{song_title.replace(' ', '')} #멜론TOP100 #피아노플레이리스트 #수면음악 #공부음악 #힐링피아노 #KPopPiano #PianoCover #SleepMusic #StudyMusic"

    # 태그 최적화
    tags = [artist_name, song_title, f"{song_title} 피아노", 'K-Ballad Piano', '피아노 커버', '수면음악', '공부할때듣는음악', '힐링음악', 'Piano Cover', 'Sleep Aid']

    youtube_service = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title[:100], # 유튜브 제목 100자 제한
            'description': description,
            'tags': tags,
            'categoryId': '10' # Music
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube_service.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"Uploading {video_file} to YouTube with title: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response.get('id')
    print(f"Upload complete! Video ID: {video_id}")

    # 썸네일 자동 설정
    thumb_path = "temp/bg.jpg"
    if os.path.exists(thumb_path) and video_id:
        try:
            print("Setting custom thumbnail for the video...")
            youtube_service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path, mimetype='image/jpeg')
            ).execute()
            print("Custom thumbnail set successfully!")
        except Exception as e:
            print(f"Notice: Custom thumbnail could not be set automatically: {e}")
