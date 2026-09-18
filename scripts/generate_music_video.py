import os
import sys
import glob
import random
import subprocess
import json
import requests
from pydub import AudioSegment

# --- 1. 유튜브 URL 또는 assets/audio/ 에서 오디오 소스 준비 ---

def download_youtube_audio(youtube_url, output_path):
    """지정된 유튜브 URL에서 최고음질 오디오(MP3) 및 메타데이터 추출"""
    print(f"[YouTube Download] URL 다운로드 시작: {youtube_url}")
    
    # 1. 메타데이터(제목, 업로더) 추출
    info_cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        youtube_url
    ]
    title = "힐링 피아노 연주곡"
    artist = "Piano Music"
    
    try:
        res = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 0 and res.stdout.strip():
            meta = json.loads(res.stdout.strip())
            title = meta.get("title", title)
            artist = meta.get("uploader", meta.get("channel", artist))
            print(f"[YouTube Info] Title: {title}, Uploader: {artist}")
    except Exception as e:
        print(f"[YouTube Info Warning] 메타데이터 추출 오류 ({e}), 기본값 사용")

    # 2. 오디오 다운로드 (MP3)
    out_template = output_path.replace(".mp3", "")
    dl_cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", f"{out_template}.%(ext)s",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        youtube_url
    ]
    
    try:
        subprocess.run(dl_cmd, check=True, timeout=120)
        # 생성된 파일 확인
        if os.path.exists(output_path):
            return {"path": output_path, "artist": artist, "title": title}
        
        for ext in [".mp3", ".m4a", ".wav", ".opus", ".webm"]:
            alt = out_template + ext
            if os.path.exists(alt):
                os.rename(alt, output_path)
                return {"path": output_path, "artist": artist, "title": title}
    except Exception as e:
        print(f"[YouTube Download Error] 다운로드 실패: {e}")
        
    return None

def get_audio_source():
    """입력받은 유튜브 URL 또는 assets/audio/ 에서 오디오 가져오기"""
    os.makedirs("temp", exist_ok=True)
    custom_url = os.getenv("INPUT_YOUTUBE_URL", "").strip()
    
    # 1. GitHub Actions 수동 실행 시 입력받은 유튜브 URL이 있는 경우
    if custom_url:
        yt_target = "temp/youtube_source.mp3"
        result = download_youtube_audio(custom_url, yt_target)
        if result and os.path.exists(result["path"]) and os.path.getsize(result["path"]) > 10000:
            print(f"[Audio Source] 유튜브 URL에서 성공적으로 추출 완료: {result['title']}")
            return result
        else:
            print("[Audio Source] 유튜브 다운로드 실패, 로컬 assets 폴더 탐색으로 전환합니다.")

    # 2. assets/audio/ 폴더에서 로컬 음원 탐색
    audio_dir = "assets/audio"
    valid_exts = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg")
    audio_files = []
    for ext in valid_exts:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))
        
    if audio_files:
        chosen_file = random.choice(audio_files)
        filename = os.path.basename(chosen_file)
        name_without_ext = os.path.splitext(filename)[0]

        if " - " in name_without_ext:
            parts = name_without_ext.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Piano Music"
            title = name_without_ext.strip()

        print(f"[Audio Source] 로컬 에셋 선택: {chosen_file} ({artist} - {title})")
        return {"path": chosen_file, "artist": artist, "title": title}

    # 3. Fallback 기본 톤
    print(f"[Warning] 음원이 없어 기본 톤을 생성합니다.")
    fallback_path = "temp/default_piano.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "sine=frequency=523.25:duration=60",
        fallback_path
    ], check=True)
    return {
        "path": fallback_path,
        "artist": "Keyin Studio",
        "title": "편안한 힐링 피아노 연주곡"
    }

# --- 2. 오디오 5분 루프 준비 및 노멀라이징 ---

def prepare_base_audio(input_path, output_path, target_duration=300):
    """실제 MP3를 볼륨 최적화 및 5분(300초) 단위로 매끄럽게 연결"""
    print(f"Processing and normalizing audio track: {input_path}...")
    audio = AudioSegment.from_file(input_path)
    
    # 볼륨 노멀라이즈
    audio = audio.normalize(headroom=0.5)
    
    # 5분(300초) 이상으로 루프 확장
    target_ms = target_duration * 1000
    if len(audio) < target_ms:
        repeats = int(target_ms // len(audio)) + 1
        looped = audio
        for _ in range(repeats):
            looped = looped.append(audio, crossfade=1500)
        audio = looped[:target_ms]
    else:
        audio = audio[:target_ms]
        
    audio = audio.fade_in(2000).fade_out(3000)
    audio.export(output_path, format="mp3", bitrate="320k")
    print(f"Base audio ready: {output_path} (Duration: {len(audio)/1000}s)")

# --- 3. 감성 고화질 배경 이미지 다운로드 ---

def fetch_hd_background(filename):
    image_pool = [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
    ]
    chosen_url = random.choice(image_pool)
    print(f"Fetching HD background image: {chosen_url}")
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            print("Background image saved.")
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")

    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a2130:s=1280x720:d=1", "-vframes", "1", filename], check=True)

# --- 4. 8시간 비디오 초고속 무손실 렌더링 ---

def create_8h_video(image_path, audio_path, output_path):
    print("Creating 8-hour video via ultra-fast concat...")
    short_video = "temp/short.mp4"
    cmd_short = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", "300", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "192k", short_video
    ]
    subprocess.run(cmd_short, check=True)

    with open("temp/concat.txt", "w") as f:
        for _ in range(96): # 5분 x 96 = 8시간 (480분)
            f.write("file 'short.mp4'\n")
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"Final 8-hour video created: {output_path}")

# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 오디오 소스 선택 (유튜브 URL 또는 assets/audio/)
    source = get_audio_source()

    # 2. 오디오 노멀라이징 및 5분 단위 기본 트랙 준비
    prepare_base_audio(source["path"], base_audio, target_duration=300)

    # 3. 고화질 감성 배경 이미지 다운로드
    fetch_hd_background(bg_image)

    # 4. 8시간 비디오 렌더링
    create_8h_video(bg_image, base_audio, final_video)

    # 5. 유튜브 메타데이터 JSON 저장
    custom_title_input = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    if custom_title_input:
        title = custom_title_input
    else:
        title = f"{source['artist']} - {source['title']} (8 Hours Piano)"

    desc = (
        f"감미로운 [{source['artist']} - {source['title']}] 음악입니다.\n"
        f"수면, 공부, 집중, 카페, 편안한 휴식 시간에 듣기 좋은 8시간 연속 재생 영상입니다.\n\n"
        f"Track: {source['title']}\n"
        f"Artist: {source['artist']}\n\n"
        f"Uploaded via Keyin Studio."
    )
    
    meta_info = {
        "title": title,
        "description": desc,
        "artist": source["artist"],
        "song_title": source["title"]
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print("Video metadata saved successfully.")
