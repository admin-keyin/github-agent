import requests
import os

# 환경 변수에서 읽어오거나 비어있을 경우 안내
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
# 구글 콘솔에 등록된 리디렉션 URI
REDIRECT_URI = 'http://localhost:8080/'

def main():
    global CLIENT_ID, CLIENT_SECRET
    
    if not CLIENT_ID:
        CLIENT_ID = input("YOUTUBE_CLIENT_ID를 입력하세요: ").strip()
    if not CLIENT_SECRET:
        CLIENT_SECRET = input("YOUTUBE_CLIENT_SECRET를 입력하세요: ").strip()

    if not CLIENT_ID or not CLIENT_SECRET:
        print("오류: Client ID와 Secret이 필요합니다.")
        return

    print("\n" + "="*60)
    print("1. 아래 주소를 브라우저에 붙여넣고 로그인하세요:")
    print(f"\n{auth_url}\n")
    print("2. 로그인 후 주소창의 URL에서 'code=' 다음에 나오는 글자들을 복사하세요.")
    print("   예: code=4/0Aci98E... -> 4/0Aci98E... 부분만 복사")
    print("="*60)

    auth_code = input("\n복사한 code 값을 입력하세요: ").strip()
    
    # 2. 코드를 토큰으로 교환
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=data)
    tokens = response.json()
    
    if "refresh_token" in tokens:
        print("\n" + "="*60)
        print("성공! 아래의 Refresh Token을 GitHub Secrets에 등록하세요:")
        print(f"YOUTUBE_REFRESH_TOKEN: {tokens['refresh_token']}")
        print("="*60)
    else:
        print("\n에러 발생!")
        print(tokens)

if __name__ == "__main__":
    main()
