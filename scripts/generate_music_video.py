import os
import sys
import glob
import random
import subprocess
import json
import requests
import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile

# --- 1. 테마별 메타데이터 및 배경 이미지 설정 ---

THEME_CONFIG = {
    "piano": {
        "title": "잠잘 때나 공부할 때 듣기 좋은 편안한 감성 피아노 연주곡 (8 Hours Piano)",
        "desc": "마음이 편안해지는 감성 피아노 연주곡입니다. 수면, 공부, 집중, 카페, 휴식 시간에 편안하게 감상하세요.",
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

# --- 2. 오디오 소스 준비 (assets/audio/ 우선 또는 고품질 앰비언트 엔진) ---

def generate_ambient_piano_melody(output_wav, duration=300):
    """assets 폴더에 파일이 없을 경우 풍성한 배음과 리버브가 적용된 5분 힐링 피아노 멜로디 생성"""
    print("Generating high-quality ambient piano track...")
    fs = 44100
    total_samples = int(fs * duration)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    # 편안한 코드 진행 (Cmaj7 - Am7 - Fmaj7 - G7sus4)
    chords = [
        [48, 52, 55, 59, 64], # Cmaj7
        [45, 48, 52, 55, 60], # Am7
        [41, 45, 48, 52, 57], # Fmaj7
        [43, 48, 50, 55, 59]  # G7sus4
    ]
    
    melody_scale = [60, 62, 64, 67, 69, 72, 74, 76, 79] # 펜타토닉 힐링 스케일
    
    def synth_note(midi_pitch, note_dur, vel):
        freq = 440.0 * (2.0 ** ((midi_pitch - 69.0) / 12.0))
        t = np.linspace(0, note_dur, int(fs * note_dur), False)
        # 배음 감쇠
        w = np.sin(2 * np.pi * freq * t) * np.exp(-t * 0.8)
        w += np.sin(2 * np.pi * (freq * 2) * t) * 0.4 * np.exp(-t * 1.6)
        w += np.sin(2 * np.pi * (freq * 3) * t) * 0.2 * np.exp(-t * 2.8)
        w *= vel
        attack = int(fs * 0.005)
        if len(w) > attack:
            w[:attack] *= np.linspace(0, 1, attack)
        return w

    cur_sample = 0
    chord_dur_sec = 4.0
    chord_samples = int(fs * chord_dur_sec)
    
    while cur_sample < total_samples:
        chord = chords[(cur_sample // chord_samples) % len(chords)]
        
        # 코드 아르페지오 (왼손)
        for i, pitch in enumerate(chord):
            offset = int(i * 0.6 * fs)
            note_start = cur_sample + offset
            if note_start < total_samples:
                w = synth_note(pitch, 3.8, 0.45)
                end = min(total_samples, note_start + len(w))
                buffer_l[note_start:end] += w[:end-note_start] * 0.6
                buffer_r[note_start:end] += w[:end-note_start] * 0.4
                
        # 서정적 멜로디 (오른손)
        for m_step in range(4):
            if random.random() > 0.3:
                m_pitch = random.choice(melody_scale)
                m_offset = int(m_step * 1.0 * fs + random.uniform(0.1, 0.4) * fs)
                m_start = cur_sample + m_offset
                if m_start < total_samples:
                    m_dur = random.choice([1.2, 1.8, 2.5])
                    w = synth_note(m_pitch, m_dur, 0.6)
                    end = min(total_samples, m_start + len(w))
                    pan = random.uniform(0.4, 0.6)
                    buffer_l[m_start:end] += w[:end-m_start] * (1.0 - pan)
                    buffer_r[m_start:end] += w[:end-m_start] * pan

        cur_sample += chord_samples

    # 리버브 (공간감 잔향)
    reverb_delay = int(fs * 0.25)
    if reverb_delay < total_samples:
        buffer_l[reverb_delay:] += buffer_r[:-reverb_delay] * 0.3
        buffer_r[reverb_delay:] += buffer_l[:-reverb_delay] * 0.3

    # 노멀라이징
    max_val = max(np.max(np.abs(buffer_l)), np.max(np.abs(buffer_r)))
    if max_val > 0:
        buffer_l = (buffer_l / max_val) * 0.88
        buffer_r = (buffer_r / max_val) * 0.88

    stereo = np.vstack(((buffer_l * 32767).astype(np.int16), (buffer_r * 32767).astype(np.int16))).T
    wavfile.write(output_wav, fs, stereo)

def get_audio_track(theme_key):
    """assets/audio 디렉토리의 실제 MP3 탐색 (없으면 자동 앰비언트 트랙 생성)"""
    audio_dir = "assets/audio"
    valid_exts = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg")
    audio_files = []
    for ext in valid_exts:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))
        
    os.makedirs("temp", exist_ok=True)
    temp_wav = "temp/generated_base.wav"
    output_mp3 = "temp/base.mp3"

    if audio_files:
        chosen = random.choice(audio_files)
        filename = os.path.basename(chosen)
        name_no_ext = os.path.splitext(filename)[0]
        print(f"[Audio] assets/audio/ 로컬 파일 사용: {filename}")
        
        audio = AudioSegment.from_file(chosen)
        audio = audio.normalize(headroom=0.5)
        target_ms = 300 * 1000
        if len(audio) < target_ms:
            repeats = int(target_ms // len(audio)) + 1
            looped = audio
            for _ in range(repeats):
                looped = looped.append(audio, crossfade=1500)
            audio = looped[:target_ms]
        else:
            audio = audio[:target_ms]
        audio.fade_in(2000).fade_out(3000).export(output_mp3, format="mp3", bitrate="320k")
        
        if " - " in name_no_ext:
            parts = name_no_ext.split(" - ", 1)
            return {"artist": parts[0].strip(), "title": parts[1].strip(), "path": output_mp3}
        return {"artist": "Piano Relax", "title": name_no_ext.strip(), "path": output_mp3}

    # 파일이 없으면 고품질 앰비언트 연주곡 생성
    generate_ambient_piano_melody(temp_wav, duration=300)
    audio = AudioSegment.from_wav(temp_wav)
    audio.fade_in(2000).fade_out(3000).export(output_mp3, format="mp3", bitrate="320k")
    
    cfg = THEME_CONFIG.get(theme_key, THEME_CONFIG["piano"])
    return {"artist": "Keyin Relaxing Music", "title": cfg["title"].split('(')[0].strip(), "path": output_mp3}

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
        for _ in range(96): # 5분 x 96 = 8시간
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

    # 1. 고음질 오디오 트랙 준비 (assets/audio/ 우선 또는 고품질 엔진 생성)
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
        title = f"[8 Hours] {audio_info['title']}"

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
