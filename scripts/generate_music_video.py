import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 검증된 안정적인 수면/앰비언트 음악 소스 (SoundHelix 중 잔잔한 곡 & 오픈 소스) ---
MUSIC_SOURCES = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-16.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/b/b9/Relaxing_Ambient_Music.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/5/52/Ambient_Piano_Music.mp3"
]

# --- 숙면을 위한 어둡고 평온한 이미지 프롬프트 ---
IMAGE_PROMPTS = [
    "extremely dark and peaceful {time}, {weather}, very low brightness, dim moonlight, {style}, minimalistic, sleep atmosphere, 4k",
    "calm bedroom with a view of starry {time}, {weather}, soft candle light, no blue light, {style}, deep relaxation",
    "still lake in the {time}, reflection of stars, {weather}, dark blue and charcoal tones, {style}, peaceful silence",
    "minimalist {style} of a sleeping cat in a dark room, {time}, soft {weather} outside, cozy and dim, 4k",
    "abstract {style} of deep space and soft nebulae, very dark, {time}, soothing purple and blue tones, peaceful",
    "a single lantern in a dark {time} forest, {weather}, soft glow, {style}, cinematic low light, calm"
]

TIMES = ["deep night", "midnight", "pre-dawn", "pitch black night"]
STYLES = ["dark oil painting", "low-light digital art", "soft charcoal sketch", "minimalist dark aesthetic", "noir style anime"]
WEATHERS = ["complete silence", "gentle drizzle", "light mist", "calm wind"]

def download_file(url, filename):
    print(f"Downloading: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded: {filename}")
            return True
        else:
            print(f"Failed (Status {response.status_code}): {url}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def generate_ai_image(prompt, filename):
    print(f"Generating sleep-themed image: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 10000000)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    return download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    print("Creating calming video...")
    audio = AudioFileClip(audio_path)
    # 수면 영상은 호흡이 길어야 하므로 최대 3분으로 설정
    max_duration = 180 
    duration = min(audio.duration, max_duration)
    
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    
    # 페이드를 아주 길게(5초) 주어 잠들기 편하게 만듦
    video = video.fadein(5).fadeout(5)
    
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    success = False
    random.shuffle(MUSIC_SOURCES)
    for music_url in MUSIC_SOURCES:
        if download_file(music_url, audio_file):
            success = True
            break
    
    if not success:
        print("All music sources failed. Trying fallback URL...")
        # 최후의 보루: 가장 안정적인 SoundHelix 1번 곡 사용
        if not download_file("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", audio_file):
            sys.exit(1)

    base_prompt = random.choice(IMAGE_PROMPTS)
    full_prompt = base_prompt.format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    
    if generate_ai_image(full_prompt, image_file):
        create_video(image_file, audio_file, video_file)
    else:
        sys.exit(1)
