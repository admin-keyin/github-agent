import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys
import random

# --- 대폭 확장된 잔잔한 음악 소스 리스트 (20곡 이상) ---
MUSIC_SOURCES = [
    # SoundHelix 시리즈 (잔잔한 곡 위주로 선별)
    f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{i}.mp3" for i in [1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14, 15, 16]
] + [
    # 추가적인 공개 라이선스 오디오 샘플들
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Ketsa/Raising_Frequencies/Ketsa_-_04_-_Day_Trip.mp3",
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Ketsa/Raising_Frequencies/Ketsa_-_09_-_Slowing_Down.mp3",
    "https://www.chosic.com/wp-content/uploads/2021/04/Rain-on-the-Window.mp3",
    "https://www.chosic.com/wp-content/uploads/2020/06/Warm-Memories-Emotional-Inspiring-Piano.mp3",
    "https://www.chosic.com/wp-content/uploads/2021/07/Midnight-Forest.mp3",
    "https://www.chosic.com/wp-content/uploads/2021/10/Lo-fi-Hip-Hop-Background-Music-For-Videos.mp3"
]

# --- 평온한 이미지 프롬프트 리스트 ---
IMAGE_PROMPTS = [
    "peaceful {time} with {weather}, starry night, soft moonlight, {style}, highly detailed, 4k, calm atmosphere",
    "aesthetic {time} view from window, {weather}, lo-fi aesthetic, {style}, cozy and warm, relax vibes",
    "surreal forest in {time}, {weather}, magical atmosphere, {style}, deep blue and purple colors",
    "cozy library at {time}, {weather} outside, warm candle light, {style}, pixel art, sleeping mood",
    "calm ocean waves under {time} {weather}, cinematic lighting, {style}, peaceful scenery",
    "snowy mountain cabin at {time}, {weather}, fireplace glow, {style}, winter chill vibes",
    "rainy city street at {time}, neon reflections, {weather}, lo-fi anime style, {style}",
    "underwater cave with glowing plants, {time}, {style}, ethereal and quiet"
]

TIMES = ["midnight", "late night", "dawn", "twilight", "sunset", "golden hour"]
STYLES = ["watercolor painting", "soft digital art", "ghibli anime style", "dreamy oil painting", "pastel colors", "8k render"]
WEATHERS = ["clear sky", "gentle rain", "soft snow", "misty fog", "calm breeze"]

def download_file(url, filename):
    print(f"Attempting to download: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded to: {filename}")
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
    seed = random.randint(1, 9999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    return download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    if not os.path.exists(audio_path):
        print(f"Error: Audio file missing at {audio_path}")
        sys.exit(1)
    
    print("Combining image and audio into video...")
    audio = AudioFileClip(audio_path)
    # 영상 길이를 1분~3분 사이로 랜덤하게 설정 (다양성 부여)
    max_duration = random.randint(60, 180)
    duration = min(audio.duration, max_duration)
    
    image_clip = ImageClip(image_path).set_duration(duration)
    video = image_clip.set_audio(audio.subclip(0, duration))
    
    # 페이드 인/아웃 효과 추가 (더 부드러운 느낌)
    video = video.fadein(2).fadeout(2)
    
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video created successfully: {output_path}")

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    # 1. 음악 선택 및 다운로드
    success = False
    tried_urls = []
    
    # 환경 변수 확인
    env_music = os.getenv("MUSIC_URL")
    if env_music and env_music.strip() != "":
        if download_file(env_music, audio_file):
            success = True
            print(f"Using user provided music: {env_music}")
    
    if not success:
        random.shuffle(MUSIC_SOURCES) # 리스트 섞기
        for music_url in MUSIC_SOURCES:
            if download_file(music_url, audio_file):
                success = True
                print(f"Randomly selected music: {music_url}")
                break
            print("Trying next available music source...")

    if not success:
        print("Critical Error: No music sources are accessible.")
        sys.exit(1)

    # 2. 이미지 프롬프트 생성
    base_prompt = random.choice(IMAGE_PROMPTS)
    full_prompt = base_prompt.format(
        time=random.choice(TIMES),
        style=random.choice(STYLES),
        weather=random.choice(WEATHERS)
    )
    image_prompt = os.getenv("IMAGE_PROMPT")
    if not image_prompt or image_prompt.strip() == "":
        image_prompt = full_prompt
    
    # 3. 이미지 생성 및 영상 합성
    if generate_ai_image(image_prompt, image_file):
        create_video(image_file, audio_file, video_file)
    else:
        print("Critical Error: Failed to generate background image.")
        sys.exit(1)
