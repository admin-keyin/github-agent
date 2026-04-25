import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from moviepy.editor import ImageClip, AudioFileClip
import random
import sys

def generate_sleep_sound(duration_sec, output_path):
    print(f"Generating procedural sleep music ({duration_sec}s)...")
    fs = 44100  # Sample rate
    t = np.linspace(0, duration_sec, int(fs * duration_sec), False)

    # 1. 딥 드론 (Deep Drone) - 솔페지오 주파수 기반
    # 174Hz (고통 완화), 432Hz (우주 주파수), 528Hz (치유) 중 랜덤 선택
    base_freq = random.choice([174, 432, 528])
    drone = np.sin(base_freq * 2 * np.pi * t) * 0.3
    drone += np.sin((base_freq / 2) * 2 * np.pi * t) * 0.2 # 서브 베이스
    
    # 2. 화이트/핑크 노이즈 (빗소리/바람 효과)
    noise = np.random.normal(0, 1, len(t))
    # 저주파 필터 효과 (잔잔한 느낌)
    from scipy.signal import butter, lfilter
    def lowpass(data, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)
    
    noise_filtered = lowpass(noise, random.randint(500, 1500), fs) * 0.1
    
    # 3. 맥동 효과 (Pulsing) - 호흡 유도
    pulse = (np.sin(0.2 * 2 * np.pi * t) + 1) / 2 # 5초 주기 호흡
    final_wave = (drone + noise_filtered) * pulse

    # Normalize to 16-bit PCM
    final_wave = (final_wave / np.max(np.abs(final_wave)) * 32767).astype(np.int16)
    
    temp_wav = "temp/generated.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, final_wave)
    
    # WAV to MP3 conversion using pydub
    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")
    print(f"Procedural music generated: {output_path}")

def generate_ai_image(prompt, filename):
    print(f"Generating image: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 9999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    with open(filename, 'wb') as f:
        f.write(response.content)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    final_audio = "temp/final.mp3"
    image_file = "temp/bg.jpg"
    video_file = "output_music_video.mp4"

    # 1. 수학적으로 새로운 수면 음악 생성 (3분)
    generate_sleep_sound(180, final_audio)

    # 2. 이미지 생성
    prompts = [
        "extremely dark night, minimalistic charcoal painting, very low brightness, starry sky, sleep mood",
        "deep blue midnight sky with soft nebula, dark landscape, peaceful silence, dark aesthetic",
        "dark bedroom with a soft ember glow, window with rain drops, night atmosphere, lo-fi dark"
    ]
    generate_ai_image(random.choice(prompts), image_file)

    # 3. 영상 합성
    audio = AudioFileClip(final_audio)
    clip = ImageClip(image_file).set_duration(audio.duration)
    video = clip.set_audio(audio).fadein(7).fadeout(7)
    video.write_videofile(video_file, fps=24, codec="libx264", audio_codec="aac")
