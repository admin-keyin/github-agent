import os
import time
import subprocess
import sys

def load_env_local():
    env_path = os.path.join(os.getcwd(), ".env.local")
    if os.path.exists(env_path):
        print(f"정보: {env_path} 파일에서 설정값을 읽어옵니다.")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False

def run_task():
    # .env.local 로드
    load_env_local()

    # 필수 변수 확인
    required_vars = ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"!! 오류: 필수 변수가 없습니다: {', '.join(missing)}")
        print(".env.local 파일을 확인해 주세요.")
        return

    try:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 새로운 루프 시작...")

        # 1. 영상 생성 스크립트 실행
        print(">> 영상 제작 중 (scripts/generate_music_video.py)...")
        subprocess.run([sys.executable, "scripts/generate_music_video.py"], check=True)

        # 2. 유튜브 업로드 스크립트 실행
        print(">> 유튜브 업로드 중 (scripts/upload_to_youtube.py)...")
        # 제목과 설명도 환경변수로 전달 (이미 .env.local에 있을 수 있음)
        env = os.environ.copy()
        if "VIDEO_TITLE" not in env:
            env["VIDEO_TITLE"] = "음량에 따라 잘때도, 공부할때도 좋은 백색소음"
        if "VIDEO_DESCRIPTION" not in env:
            env["VIDEO_DESCRIPTION"] = "made by keyin."

        subprocess.run([sys.executable, "scripts/upload_to_youtube.py", "output_music_video.mp4"], env=env, check=True)

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 모든 작업이 성공적으로 끝났습니다. 5분 대기합니다.")

    except subprocess.CalledProcessError as e:
        print(f"!! 스크립트 실행 중 에러 발생: {e}")
    except Exception as e:
        print(f"!! 알 수 없는 에러: {e}")

def main():
    print("="*60)
    print(" [Keyin] 로컬 유튜브 자동화 러너 (5분 주기)")
    print(" - .env.local 파일을 자동으로 감지합니다.")
    print(" - 종료하려면 Ctrl+C 를 누르세요.")
    print("="*60)

    while True:
        run_task()
        time.sleep(300) # 300초 = 5분

if __name__ == "__main__":
    main()
