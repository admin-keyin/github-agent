import os
import sys
import glob
import random
import subprocess
import json
import requests
from pydub import AudioSegment

# --- 1. assets/audio/ 폴더에서 MP3 음원 선곡 및 메타데이터 파싱 ---

def get_audio_source():
    """assets/audio 디렉토리에서 음원 파일 탐색 및 정보 추출"""
    audio_dir = "assets/audio"
    valid_exts = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg")
    audio_files = []
    for ext in valid_exts:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))
        
    if not audio_files:
        print(f"[Warning] '{audio_dir}' 폴더에 MP3 파일이 없습니다.")
        print("기본 힐링 피아노 톤을 생성하여 진행합니다. (assets/audio/ 에 MP3를 업로드해주세요)")
        fallback_path = "temp/default_piano.mp3"
        os.makedirs("temp", exist_ok=True)
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

    # 여러 파일이 있을 경우 무작위 1곡 선택
    chosen_file = random.choice(audio_files)
    filename = os.path.basename(chosen_file)
    name_without_ext = os.path.splitext(filename)[0]

    # 파일명 형식 분석 ("가수 - 곡명" 또는 일반 파일명)
    if " - " in name_without_ext:
        parts = name_without_ext.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        artist = "Piano Music"
        title = name_without_ext.strip()

    print(f"[Audio Selected] {chosen_file}")
    print(f"-> Artist: {artist}, Title: {title}")
    
    return {
        "path": chosen_file,
        "artist": artist,
        "title": title
    }

# --- 2. 오디오 5분 루프 준비 및 노멀라이징 ---

def prepare_base_audio(input_path, output_path, target_duration=300):
    """실제 MP3를 볼륨 최적화 및 5분(300초) 단위로 매끄럽게 연결"""
    print("Processing and normalizing audio track...")
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

    # 1. assets/audio/ 폴더에서 실제 MP3 선택
    source = get_audio_source()

    # 2. 오디오 노멀라이징 및 5분 단위 기본 트랙 준비
    prepare_base_audio(source["path"], base_audio, target_duration=300)

    # 3. 고화질 감성 배경 이미지 다운로드
    fetch_hd_background(bg_image)

    # 4. 8시간 비디오 렌더링
    create_8h_video(bg_image, base_audio, final_video)

    # 5. 유튜브 메타데이터 JSON 저장
    title = f"{source['artist']} - {source['title']} 피아노 연주 (8 Hours Piano)"
    desc = (
        f"감미로운 [{source['artist']} - {source['title']}] 피아노 연주곡입니다.\n"
        f"수면, 공부, 집중, 카페, 편안한 휴식 시간에 듣기 좋은 8시간 연속 재생 음악입니다.\n\n"
        f"Song: {source['title']}\n"
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
