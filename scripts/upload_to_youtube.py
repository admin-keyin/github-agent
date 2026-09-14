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
        # Refresh the token if it's expired
        print("Attempting to refresh access token...")
        creds.refresh(Request())
        print("Token refresh successful.")
    except google.auth.exceptions.RefreshError as e:
        print("\n" + "="*60)
        print("Authentication Error: Failed to refresh the access token.")
        print(f"Details: {e}")
        print("\nThis typically happens due to one of the following reasons:")
        print("1. The OAuth Consent Screen in Google Cloud Console is set to 'Testing' status.")
        print("   -> In 'Testing' mode, refresh tokens expire after 7 days.")
        print("   -> Solution: Change the Publishing Status to 'In production' (Go to Google Cloud Console -> APIs & Services -> OAuth consent screen).")
        print("2. The user has revoked access or changed their Google password.")
        print("3. YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, or YOUTUBE_REFRESH_TOKEN is invalid.")
        print("Please check your GitHub Repository Secrets and regenerate OAuth credentials if necessary.")
        print("="*60 + "\n")
        sys.exit(1)

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

    # 제목 및 설명 설정
    if freq_info and '|' in freq_info:
        info_part, desc_part = freq_info.split('|', 1)
        info_part = info_part.strip()
        desc_part = desc_part.strip()
        title = f"[8 Hours] {info_part}"
        description = f"{desc_part}\n\nMade by AI Sound Generator (Keyin)."
    else:
        title = os.getenv("VIDEO_TITLE", "[8 Hours] 편안한 감성 피아노 연주곡 (Sleep & Study Piano)")
        description = os.getenv("VIDEO_DESCRIPTION", "편안한 휴식과 수면, 집중을 돕는 감성 피아노 연주곡입니다.")

    description += "\n\n#피아노 #수면음악 #공부음악 #힐링피아노 #로파이 #K발라드 #뉴에이지 #LofiPiano #BalladPiano #SleepMusic #StudyMusic"

    # 태그 최적화
    tags = ['Piano', 'Sleep Music', 'Study Aid', 'Meditation', 'AI Music', 'Ambient Piano', 'Lofi Hip Hop', 'New Age Piano', 'K-Ballad Piano']

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

    video_id = response.get('id')
    print(f"Upload complete! Video ID: {video_id}")

    # 썸네일 이미지(temp/bg.jpg)가 존재하면 공식 썸네일로 등록
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
            print(f"Notice: Custom thumbnail could not be set automatically (e.g. channel phone verification required): {e}")


