import os
import time
import requests
import sys

def load_env_local():
    env_path = os.path.join(os.getcwd(), ".env.local")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

def trigger_workflow():
    load_env_local()
    
    # 설정 값 (본인의 것으로 변경 가능)
    GITHUB_PAT = os.getenv("GITHUB_PAT")
    REPO_OWNER = "admin-keyin" # GitHub 아이디
    REPO_NAME = "github-agent"   # 리포지토리 이름
    WORKFLOW_ID = "youtube-music-video.yml" # 워크플로우 파일명
    
    if not GITHUB_PAT:
        print("!! 오류: .env.local 에 GITHUB_PAT 가 설정되어 있지 않습니다.")
        return

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # workflow_dispatch 는 'ref' (브랜치) 가 필수입니다.
    data = {
        "ref": "main" 
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            print(f"[{time.strftime('%H:%M:%S')}] GitHub Action 트리거 성공! (204 No Content)")
        else:
            print(f"!! 트리거 실패: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"!! API 호출 중 에러: {e}")

def main():
    print("="*60)
    print(" [Keyin] GitHub Actions 원격 트리거 러너 (5분 주기)")
    print(" - .env.local 의 GITHUB_PAT 를 사용합니다.")
    print(" - 종료하려면 Ctrl+C 를 누르세요.")
    print("="*60)

    while True:
        trigger_workflow()
        print("다음 실행까지 30분 대기합니다...")
        time.sleep(1800) # 30분 대기

if __name__ == "__main__":
    main()
