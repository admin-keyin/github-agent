import os
import sys
import glob
import random
import subprocess
import json
import requests
from pydub import AudioSegment

# --- 1. 테마 및 메타데이터 설정 ---

THEME_CONFIG = {
    "piano": {
        "title": "잠잘 때나 공부할 때 듣기 좋은 편안한 감성 피아노 연주곡 (8 Hours Piano)",
        "desc": "마음이 편안해지는 고품질 감성 피아노 연주곡입니다. 수면, 공부, 집중, 카페, 휴식 시간에 편안하게 감상하세요.",
        "tags": ["#피아노연주", "#수면음악", "#공부음악", "#힐링피아노", "#PianoMusic", "#SleepAid", "#StudyMusic"],
        "images": [
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "lofi": {
        "title": "새벽에 듣기 좋은 감성 로파이 칠합 비트 (8 Hours Lo-Fi Chill Beats)",
        "desc": "따뜻하고 아늑한 로파이(Lo-Fi) 칠합 음악입니다. 코딩, 과제, 야간 작업, 휴식에 최적화된 연속 재생 플레이리스트입니다.",
        "tags": ["#로파이", "#LofiBeats", "#칠합", "#코딩음악", "#공부할때듣는음악", "#LofiChill", "#NightVibe"],
        "images": [
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "sleep": {
        "title": "불면증을 위한 깊은 수면 유도 힐링 음악 (8 Hours Deep Sleep Music)",
        "desc": "복잡한 생각을 비우고 깊은 잠에 빠져들 수 있도록 도와주는 수면 유도 음악입니다. 편안한 밤 되세요.",
        "tags": ["#수면음악", "#불면증치료", "#딥슬립", "#힐링음악", "#SleepMusic", "#DeepSleep", "#Relaxing"],
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "study": {
        "title": "집중력 향상과 몰입을 위한 차분한 연주곡 (8 Hours Study & Focus)",
        "desc": "집중이 필요할 때 뇌파를 안정시키고 몰입을 도와주는 BGM입니다. 독서, 공부, 작업용으로 추천합니다.",
        "tags": ["#공부음악", "#집중력음악", "#몰입음악", "#작업용BGM", "#StudyBGM", "#FocusMusic"],
        "images": [
            "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    }
}

# --- 2. 완성형 고음질 MP3 음원 가져오기 & 8시간 루프 준비 ---

def get_audio_track(theme_key):
    """assets/audio 디렉토리의 완성형 고음질 MP3를 읽어와 5분 루프 준비"""
    audio_dir = "assets/audio"
    valid_exts = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg")
    audio_files = []
    for ext in valid_exts:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))
        
    os.makedirs("temp", exist_ok=True)
    output_mp3 = "temp/base.mp3"

    if not audio_files:
        print("[Error] assets/audio 폴더에 음원이 없습니다. 기본 고음질 음원을 다운로드합니다.")
        default_url = "https://cdn.pixabay.com/download/audio/2022/05/16/audio_db6591201e.mp3?filename=piano-moment-110241.mp3"
        dl = requests.get(default_url, headers={'User-Agent': 'Mozilla/5.0'})
        with open("assets/audio/Piano_Moment_Calm_Relaxing.mp3", "wb") as f:
            f.write(dl.content)
        audio_files = ["assets/audio/Piano_Moment_Calm_Relaxing.mp3"]

    chosen = random.choice(audio_files)
    filename = os.path.basename(chosen)
    name_no_ext = os.path.splitext(filename)[0]
    print(f"[Selected High-Quality Audio] {chosen}")

    # 원본 음원을 훼손하지 않고 볼륨 정규화 & 매끄러운 5분 루프 생성
    audio = AudioSegment.from_file(chosen)
    audio = audio.normalize(headroom=0.5)
    
    target_ms = 300 * 1000 # 5분
    if len(audio) < target_ms:
        repeats = int(target_ms // len(audio)) + 1
        looped = audio
        for _ in range(repeats):
            looped = looped.append(audio, crossfade=1500)
        audio = looped[:target_ms]
    else:
        audio = audio[:target_ms]
        
    audio = audio.fade_in(2000).fade_out(3000)
    audio.export(output_mp3, format="mp3", bitrate="320k")

    clean_name = name_no_ext.replace("_", " ").strip()
    if " - " in clean_name:
        parts = clean_name.split(" - ", 1)
        return {"artist": parts[0].strip(), "title": parts[1].strip(), "path": output_mp3}
    return {"artist": "Relaxing Piano Studio", "title": clean_name, "path": output_mp3}

# --- 3. 고화질 감성 배경 이미지 다운로드 ---

def fetch_hd_background(theme_key, filename):
    cfg = THEME_CONFIG.get(theme_key, THEME_CONFIG["piano"])
    chosen_url = random.choice(cfg["images"])
    print(f"Fetching HD background image ({theme_key}): {chosen_url}")
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
    theme = os.getenv("INPUT_THEME", "piano").strip().lower()
    if theme not in THEME_CONFIG:
        theme = "piano"
        
    cfg = THEME_CONFIG[theme]
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. assets/audio/의 실제 완성형 고음질 MP3 트랙 선택
    audio_info = get_audio_track(theme)

    # 2. 테마별 고화질 감성 배경 이미지 다운로드
    fetch_hd_background(theme, bg_image)

    # 3. 8시간 무손실 연속 재생 비디오 초고속 생성
    create_8h_video(bg_image, audio_info["path"], final_video)

    # 4. 유튜브 메타데이터 JSON 저장
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    if custom_title:
        title = custom_title
    else:
        title = f"[8 Hours] {audio_info['title']} - 편안한 피아노 연주곡"

    tags_str = " ".join(cfg["tags"])
    desc = (
        f"{cfg['desc']}\n\n"
        f"Track: {audio_info['title']}\n"
        f"Artist: {audio_info['artist']}\n\n"
        f"{tags_str}\n\n"
        f"Produced & Provided by Keyin Studio."
    )

    meta_info = {
        "title": title[:100],
        "description": desc,
        "artist": audio_info["artist"],
        "song_title": audio_info["title"]
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print("Video metadata saved successfully.")
