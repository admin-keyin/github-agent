import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess

def generate_sleep_sound(duration_sec, output_path):
    print(f"Generating base sound ({duration_sec}s)...")
    fs = 44100
    t = np.linspace(0, duration_sec, int(fs * duration_sec), False)

    base_freq = random.choice([174, 432, 528])
    drone = np.sin(base_freq * 2 * np.pi * t) * 0.3
    drone += np.sin((base_freq / 2) * 2 * np.pi * t) * 0.2
    
    from scipy.signal import butter, lfilter
    def lowpass(data, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)

    num_layers = random.randint(3, 6)
    noise_combined = np.zeros_like(t)
    for _ in range(num_layers):
        layer_noise = np.random.normal(0, 1, len(t))
        cutoff = random.randint(200, 1200)
        noise_combined += lowpass(layer_noise, cutoff, fs) * random.uniform(0.02, 0.06)
    
    pulse_period = random.uniform(5, 20)
    pulse = (np.sin((1.0/pulse_period) * 2 * np.pi * t) + 1) / 2
    final_wave = (drone + noise_combined) * pulse

    final_wave = (final_wave / np.max(np.abs(final_wave)) * 32767).astype(np.int16)
    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, final_wave)
    
    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")

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
            # ffmpeg concat 필터는 상대 경로를 사용해야 안전함
            f.write(f"file 'short.mp4'\n")
    
    # temp 폴더 안에서 실행하여 경로 문제 방지
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

    # 1. 5분 사운드 생성
    generate_sleep_sound(300, base_audio)
    
    # 2. 이미지 생성 (수면용 어두운 테마)
    prompts = [
        "dark peaceful midnight landscape, dim moonlight, soft minimalist painting, very low brightness",
        "starry sky over a still dark lake, deep charcoal and blue tones, serene silence",
        "minimalist deep space nebula, extremely dark purple and black, ethereal and quiet"
    ]
    generate_ai_image(random.choice(prompts), image_file)
    
    # 3. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
