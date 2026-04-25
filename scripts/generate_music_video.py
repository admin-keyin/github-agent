import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
from pydub import AudioSegment
import sys
import random

# --- 레이어별 소리 소스 ---
# 1. 배경음 (자연의 소리)
BACKGROUND_SOURCES = [
    "https://upload.wikimedia.org/wikipedia/commons/3/30/Rain_Atmosphere.mp3", # 빗소리
    "https://upload.wikimedia.org/wikipedia/commons/0/08/Forest_Ambience.mp3", # 숲 소리
    "https://upload.wikimedia.org/wikipedia/commons/4/4e/Soft_Wind_Breeze.mp3", # 바람 소리
    "https://upload.wikimedia.org/wikipedia/commons/f/f0/Small_Ocean_Waves.mp3"   # 파도 소리
]

# 2. 멜로디 (정적인 악기/앰비언트)
MELODY_SOURCES = [
    "https://upload.wikimedia.org/wikipedia/commons/5/52/Ambient_Piano_Music.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/b/b9/Relaxing_Ambient_Music.mp3",
    "https://ia800703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep03.mp3",
    "https://ia600703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep05.mp3"
]

def download_file(url, filename):
    print(f"Downloading: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def mix_audio(bg_path, melody_path, output_path):
    print(f"Mixing {bg_path} and {melody_path}...")
    bg = AudioSegment.from_file(bg_path)
    melody = AudioSegment.from_file(melody_path)

    # 3분(180초)으로 길이 맞추기
    duration_ms = 180 * 1000
    bg = (bg * (duration_ms // len(bg) + 1))[:duration_ms]
    melody = (melody * (duration_ms // len(melody) + 1))[:duration_ms]

    # 배경음은 조금 작게 (-15dB), 멜로디는 적당히 (-5dB)
    mixed = bg.overlay(melody - 5) - 10
    mixed.export(output_path, format="mp3")
    print(f"New generated music saved to: {output_path}")

def generate_ai_image(prompt, filename):
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    download_file(url, filename)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    bg_file = "temp/bg.mp3"
    melody_file = "temp/melody.mp3"
    final_audio = "temp/final_generated.mp3"
    image_file = "temp/bg.jpg"
    video_file = "output_music_video.mp4"

    # 1. 배경음과 멜로디 랜덤 선택 및 다운로드
    if not download_file(random.choice(BACKGROUND_SOURCES), bg_file):
        download_file(BACKGROUND_SOURCES[0], bg_file)
    if not download_file(random.choice(MELODY_SOURCES), melody_file):
        download_file(MELODY_SOURCES[0], melody_file)

    # 2. 두 소리를 합성하여 '새로운 곡' 생성
    mix_audio(bg_file, melody_file, final_audio)

    # 3. 이미지 생성 (수면용 어두운 테마)
    prompts = [
        "extremely dark and peaceful night, dim moonlight, soft minimalist oil painting, sleep atmosphere",
        "starry sky over a still dark lake, deep charcoal and blue tones, serene silence",
        "a cozy room in pitch black night, soft warm candle glow, lo-fi aesthetic, very low brightness"
    ]
    generate_ai_image(random.choice(prompts), image_file)

    # 4. 최종 영상 제작
    audio = AudioFileClip(final_audio)
    clip = ImageClip(image_file).set_duration(audio.duration)
    video = clip.set_audio(audio).fadein(5).fadeout(5)
    video.write_videofile(video_file, fps=24, codec="libx264", audio_codec="aac")
