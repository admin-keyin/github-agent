import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 잔잔한 음악 소스 리스트 ---
MUSIC_SOURCES = [
    "https://cdn.pixabay.com/audio/2022/03/10/audio_c330c67990.mp3", # Chill ambient
    "https://cdn.pixabay.com/audio/2022/01/21/audio_31743c589f.mp3", # Lofi study
    "https://cdn.pixabay.com/audio/2023/10/16/audio_f52363013d.mp3", # Emotional piano
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3", # Relatively calm
    "https://cdn.pixabay.com/audio/2022/05/27/audio_180873748b.mp3"  # Relaxing lofi
]

# --- 평온한 이미지 프롬프트 리스트 ---
IMAGE_PROMPTS = [
    "peaceful {time} with {weather}, starry night, soft moonlight, {style}, highly detailed, 4k, calm atmosphere",
    "aesthetic {time} view from window, {weather}, lo-fi aesthetic, {style}, cozy and warm, relax vibes",
    "surreal forest in {time}, {weather}, magical atmosphere, {style}, deep blue and purple colors",
    "cozy library at {time}, {weather} outside, warm candle light, {style}, pixel art, sleeping mood",
    "calm ocean waves under {time} {weather}, cinematic lighting, {style}, peaceful scenery"
]

TIMES = ["midnight", "late night", "dawn", "twilight"]
STYLES = ["watercolor painting", "soft digital art", "ghibli anime style", "dreamy oil painting"]
WEATHERS = ["clear sky", "gentle rain", "soft snow", "misty fog"]

def download_file(url, filename):
    print(f"Downloading {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=45)
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
    seed = random.randint(1, 1000000)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    print("Combining image and audio into video...")
    audio = AudioFileClip(audio_path)
    # 잘 때 듣기 좋게 길이를 조금 더 늘림 (최대 3분)
    duration = min(audio.duration, 180)
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video created: {output_path}")

if __name__ == "__main__":
    # 랜덤 음악 및 프롬프트 선택 (잔잔한 분위기 고정)
    music_url = os.getenv("MUSIC_URL") or random.choice(MUSIC_SOURCES)
    
    base_prompt = random.choice(IMAGE_PROMPTS)
    full_prompt = base_prompt.format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    image_prompt = os.getenv("IMAGE_PROMPT") or full_prompt
    
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
