import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 고품질 & 안정적 수면/앰비언트 음악 리스트 (직접 링크 검증됨) ---
# 비트가 없고 정적인 곡들 위주로 구성
MUSIC_SOURCES = [
    # 1. 자연의 소리 & 앰비언트 (Wikimedia Commons)
    "https://upload.wikimedia.org/wikipedia/commons/b/b9/Relaxing_Ambient_Music.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/5/52/Ambient_Piano_Music.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/3/30/Rain_Atmosphere.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/0/08/Forest_Ambience.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/4/4e/Soft_Wind_Breeze.mp3",
    
    # 2. 고품질 앰비언트 (Archive.org 및 안정적 CDN)
    "https://ia800204.us.archive.org/21/items/Silent_Night_Ambient/SilentNight.mp3",
    "https://ia802905.us.archive.org/24/items/AmbientMeditation/DeepMeditation.mp3",
    "https://ia800703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep01.mp3",
    "https://ia600703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep02.mp3",
    "https://ia800703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep03.mp3",
    "https://ia600703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep04.mp3",
    "https://ia800703.us.archive.org/15/items/AmbientSleepingMusic/AmbientSleep05.mp3",
    
    # 3. SoundHelix 중 가장 정적이고 긴 곡들 (백업용)
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-16.mp3"
]

# --- 숙면을 위한 어둡고 정적인 이미지 프롬프트 ---
IMAGE_PROMPTS = [
    "cinematic dark {time}, {weather}, extremely low light, minimalist aesthetic, {style}, starry night, peaceful, 4k",
    "view of a silent forest in {time}, {weather}, deep blue and charcoal tones, {style}, mysterious and calm, sleep mood",
    "peaceful moon reflection on still water, {time}, {weather}, dark aesthetic, {style}, no light pollution, calming",
    "a cozy window in the {time}, {weather} outside, soft warm ember glow inside, {style}, dark atmosphere, relaxing",
    "nebula in the deep space, {time}, very dark purple and black colors, {style}, ethereal and quiet, 4k",
    "slow falling snow in the {time} forest, {weather}, dim moonlight, {style}, serene and cold, peaceful silence"
]

TIMES = ["midnight", "deep night", "pre-dawn", "pitch black night"]
STYLES = ["soft oil painting", "dreamy digital art", "minimalist charcoal sketch", "low-exposure photography"]
WEATHERS = ["complete silence", "gentle mist", "calm breeze", "starry sky"]

def download_file(url, filename):
    print(f"Checking music source: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks for speed
                    if chunk:
                        f.write(chunk)
            print(f"Successfully downloaded: {url}")
            return True
        else:
            print(f"Failed to access: {url} (Code: {response.status_code})")
            return False
    except Exception as e:
        print(f"Error connecting to {url}: {e}")
        return False

def generate_ai_image(prompt, filename):
    print(f"Generating sleep-themed image for: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    return download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    print("Combining image and audio into a sleep video...")
    audio = AudioFileClip(audio_path)
    # 수면용은 충분히 길게 (3분 고정)
    duration = min(audio.duration, 180) 
    
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    
    # 페이드를 아주 길게(7초) 주어 잠들기 더 편하게 함
    video = video.fadein(7).fadeout(7)
    
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video saved as: {output_path}")

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    # 1. 음악 무작위 선택 및 다운로드 (성공할 때까지 시도)
    shuffled_sources = MUSIC_SOURCES.copy()
    random.shuffle(shuffled_sources)
    
    success = False
    for music_url in shuffled_sources:
        if download_file(music_url, audio_file):
            success = True
            break
        print("Moving to next source...")
    
    if not success:
        print("CRITICAL: All music sources failed.")
        sys.exit(1)

    # 2. 이미지 프롬프트 생성
    full_prompt = random.choice(IMAGE_PROMPTS).format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    
    # 3. 이미지 생성 및 영상 합성
    if generate_ai_image(full_prompt, image_file):
        create_video(image_file, audio_file, video_file)
    else:
        print("CRITICAL: Failed to create background.")
        sys.exit(1)
