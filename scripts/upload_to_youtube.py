import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

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
    
    # Refresh the token if it's expired
    creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, file_path, title, description, category="10", privacy="public"):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['AI', 'Music', 'GitHubAction'],
            'categoryId': category
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"Uploading {file_path} to YouTube...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"Upload complete! Video ID: {response.get('id')}")
    return response.get('id')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_to_youtube.py <video_file_path>")
        sys.exit(1)

    video_file = sys.argv[1]
    
    # 주파수 정보 읽기
    info_path = "temp/video_info.txt"
    freq_info = ""
    if os.path.exists(info_path):
        with open(info_path, "r") as f:
            freq_info = f.read().strip()

    # 기본 제목 및 설명 설정
    base_title = os.getenv("VIDEO_TITLE", "음량에 따라 잘때도, 공부할때도 좋은 백색소음")
    if freq_info:
        # 제목 최적화: [8 Hours] 주파수Hz | 효과 | 백색소음
        title = f"[8 Hours] {freq_info} | {base_title}"
    else:
        title = f"[8 Hours] {base_title}"

    description = os.getenv("VIDEO_DESCRIPTION", "이 영상은 AI를 통해 생성된 최적의 수면 및 집중용 백색소음입니다.")
    if freq_info:
        description += f"\n\n적용된 주파수: {freq_info}"
        description += "\n\n솔페지오 주파수와 바이노럴 비트가 적용되어 깊은 휴식과 집중을 도와줍니다."
    
    description += "\n\n#백색소음 #수면음악 #집중력 #Solfeggio #BinauralBeats #WhiteNoise"

    # 태그 최적화
    tags = ['White Noise', 'Sleep Music', 'Study Aid', 'Meditation', 'AI']
    if freq_info:
        tags.extend([freq_info.split('|')[0].strip(), 'Solfeggio', 'Binaural Beats', 'Healing Tone'])

    youtube_service = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title[:100], # 제목 100자 제한
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

    print(f"Upload complete! Video ID: {response.get('id')}")

