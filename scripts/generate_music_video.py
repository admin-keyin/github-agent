import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 더 안정적인 잔잔한 음악 소스 리스트 (차단이 적은 곳 위주) ---
MUSIC_SOURCES = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3"
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
            return True
        else:
            print(f"Failed to download: {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"Error downloading: {e}")
        return False

def generate_ai_image(prompt, filename):
    print(f"Generating AI image for prompt: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 1000000)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    return download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        sys.exit(1)
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        sys.exit(1)

    print("Combining image and audio into video...")
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 180) # 최대 3분
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video created: {output_path}")

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    # 1. 음악 다운로드 시도 (성공할 때까지 최대 3번 다른 곡 시도)
    success = False
    tried_urls = []
    for _ in range(3):
        music_url = os.getenv("MUSIC_URL")
        if not music_url or music_url in tried_urls:
            music_url = random.choice([u for u in MUSIC_SOURCES if u not in tried_urls])
        
        tried_urls.append(music_url)
        if download_file(music_url, audio_file):
            success = True
            break
        print("Retrying with another music source...")

    if not success:
        print("Critical Error: All music downloads failed.")
        sys.exit(1)

    # 2. 이미지 생성
    base_prompt = random.choice(IMAGE_PROMPTS)
    full_prompt = base_prompt.format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    image_prompt = os.getenv("IMAGE_PROMPT") or full_prompt
    
    if generate_ai_image(image_prompt, image_file):
        # 3. 영상 합성
        create_video(image_file, audio_file, video_file)
    else:
        print("Critical Error: Image generation failed.")
        sys.exit(1)
