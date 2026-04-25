import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 랜덤 소스 리스트 ---
MUSIC_SOURCES = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "https://cdn.pixabay.com/audio/2022/05/27/audio_180873748b.mp3", # Pixabay (User-Agent 필요)
    "https://cdn.pixabay.com/audio/2023/11/24/audio_349d447f53.mp3"
]

IMAGE_PROMPTS = [
    "cinematic lo-fi {time} {style}, aesthetic digital art, 4k, {weather}",
    "cyberpunk city in {weather}, {time}, anime style, neon lights",
    "peaceful forest with {weather}, {time}, studio ghibli style, watercolor",
    "cozy room with a view of {weather} {time}, pixel art style, lo-fi vibes",
    "surreal space landscape, nebulae and planets, {style}, detailed"
]

TIMES = ["sunset", "midnight", "early morning", "golden hour", "night"]
STYLES = ["oil painting", "digital art", "sketch", "retro synthwave", "minimalist"]
WEATHERS = ["rainy", "snowy", "clear sky", "foggy", "thunderstorm"]

def download_file(url, filename):
    print(f"Downloading {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download: {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"Error downloading: {e}")
        return False
    return True

def generate_ai_image(prompt, filename):
    print(f"Generating AI image for prompt: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    # seed를 랜덤하게 주어 매번 다른 그림 생성
    seed = random.randint(1, 100000)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    print("Combining image and audio into video...")
    audio = AudioFileClip(audio_path)
    # 영상 길이를 최대 1분(60초)으로 제한 (업로드 속도 및 리소스 고려)
    duration = min(audio.duration, 60)
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video created: {output_path}")

if __name__ == "__main__":
    # 랜덤하게 음악 선택
    default_music = random.choice(MUSIC_SOURCES)
    music_url = os.getenv("MUSIC_URL")
    if not music_url or music_url == "":
        music_url = default_music
    
    # 랜덤하게 프롬프트 조합
    base_prompt = random.choice(IMAGE_PROMPTS)
    full_prompt = base_prompt.format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    
    image_prompt = os.getenv("IMAGE_PROMPT")
    if not image_prompt or image_prompt == "":
        image_prompt = full_prompt
    
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    if download_file(music_url, audio_file):
        generate_ai_image(image_prompt, image_file)
        create_video(image_file, audio_file, video_file)
    else:
        print("Music download failed. Trying a backup...")
        download_file(random.choice(MUSIC_SOURCES), audio_file)
        generate_ai_image(image_prompt, image_file)
        create_video(image_file, audio_file, video_file)
