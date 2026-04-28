import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess

def generate_sleep_sound(duration_sec, output_path):
    # 솔페지오 주파수 정의 (특정 주파수일 경우 설명 제공)
    solfeggio_desc = {
        174: "Pain Relief", 432: "Deep Relaxation", 528: "DNA Repair", 639: "Connection"
    }
    
    # 1~1000Hz 사이의 가변 랜덤 주파수 생성
    base_freq = random.randint(1, 1000)
    description = solfeggio_desc.get(base_freq, "Deep Meditation & Healing")
    
    fs = 44100
    t = np.linspace(0, duration_sec, int(fs * duration_sec), False)
    
    # 1. 바이노럴 비트 & 솔페지오 톤
    beat_freq = random.uniform(1.0, 3.0)
    left_tone = np.sin(base_freq * 2 * np.pi * t) * 0.15
    right_tone = np.sin((base_freq + beat_freq) * 2 * np.pi * t) * 0.15
    
    # 2. ASMR 레이어: 빗소리 (Pinkish/Brownish Noise)
    # 핑크 노이즈 생성 후 로우패스 필터로 부드러운 빗소리 구현
    from scipy.signal import butter, lfilter
    def lowpass(data, cutoff, fs, order=2):
        nyq = 0.5 * fs
        b, a = butter(order, cutoff / nyq, btype='low')
        return lfilter(b, a, data)

    rain_raw = np.random.normal(0, 1, len(t))
    rain_sound = lowpass(rain_raw, 800, fs) * 0.08
    
    # 3. ASMR 레이어: 모닥불 장작 소리 (Crackling)
    # 짧은 고주파 펄스를 불규칙하게 배치
    crackling = np.zeros_like(t)
    num_cracks = int(duration_sec * 2) # 초당 약 2번의 탁탁 소리
    for _ in range(num_cracks):
        pos = random.randint(0, len(t) - 1)
        duration = random.randint(5, 20) # 아주 짧은 순간
        if pos + duration < len(t):
            crackling[pos:pos+duration] = np.random.normal(0, 1, duration) * 0.1
    
    # 4. 공간감 (Panning)
    # 소리가 좌우로 아주 천천히 이동하도록 설정
    pan_speed = 0.05
    pan = (np.sin(pan_speed * 2 * np.pi * t) + 1) / 2 # 0 ~ 1 사이 진동
    
    final_l = (left_tone + rain_sound + crackling) * (1 - pan * 0.3)
    final_r = (right_tone + rain_sound + crackling) * (pan * 0.3 + 0.7)

    # 5. 수면 유도를 위한 부드러운 맥동 (Breath-like pulsation)
    pulse = (np.sin((1.0/12.0) * 2 * np.pi * t) + 1.2) / 2.2
    final_l *= pulse
    final_r *= pulse

    # 정규화 및 저장
    final_l = (final_l / np.max(np.abs(final_l)) * 28000).astype(np.int16)
    final_r = (final_r / np.max(np.abs(final_r)) * 28000).astype(np.int16)
    stereo_wave = np.vstack((final_l, final_r)).T.flatten()

    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, stereo_wave.reshape(-1, 2))
    
    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")
    
    return base_freq, f"{description} with Soft Rain & Fire Crackling"


def create_8h_video(image_path, audio_path, output_path):
    print("Creating 8-hour video (High-speed concatenation mode)...")
    
    # 1. 5분짜리 단기 영상 생성 (용량 최적화를 위해 720p 사용)
    short_video = "temp/short.mp4"
    cmd_short = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", "300", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "128k", short_video
    ]
    subprocess.run(cmd_short, check=True)

    # 2. 5분 영상을 96번 반복 (96 * 5분 = 8시간)
    with open("temp/concat.txt", "w") as f:
        for _ in range(96):
            f.write(f"file 'short.mp4'\n")
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"Final 8-hour video created: {output_path}")

def generate_ai_image(prompt, filename):
    print(f"Generating background: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    with open(filename, 'wb') as f:
        f.write(response.content)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    image_file = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 5분 사운드 생성 (선택된 주파수 정보 획득)
    freq, desc = generate_sleep_sound(300, base_audio)
    
    # 2. 이미지 생성
    prompts = [
        "dark peaceful midnight landscape, dim moonlight, soft minimalist painting, very low brightness",
        "starry sky over a still dark lake, deep charcoal and blue tones, serene silence",
        "minimalist deep space nebula, extremely dark purple and black, ethereal and quiet"
    ]
    generate_ai_image(random.choice(prompts), image_file)
    
    # 3. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
    
    # 4. 정보 저장 (업로드 스크립트에서 읽을 수 있도록)
    with open("temp/video_info.txt", "w") as f:
        f.write(f"{freq}Hz | {desc}")
