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
    title = os.getenv("VIDEO_TITLE", "AI Generated Music Video")
    description = os.getenv("VIDEO_DESCRIPTION", "This video was automatically generated and uploaded using GitHub Actions.")

    youtube_service = get_authenticated_service()
    upload_video(youtube_service, video_file, title, description)
