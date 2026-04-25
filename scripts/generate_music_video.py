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
    base_freq = random.choice([174, 432, 528])
    drone = np.sin(base_freq * 2 * np.pi * t) * 0.3
    drone += np.sin((base_freq / 2) * 2 * np.pi * t) * 0.2 # 서브 베이스
    
    # 2. 다중 노이즈 레이어 생성 (2~5개 랜덤 레이어)
    from scipy.signal import butter, lfilter
    def lowpass(data, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)

    num_layers = random.randint(2, 5)
    noise_combined = np.zeros_like(t)
    print(f"Adding {num_layers} layers of noise for rich texture...")
    
    for i in range(num_layers):
        layer_noise = np.random.normal(0, 1, len(t))
        # 각 레이어마다 다른 컷오프 주파수와 볼륨 적용
        cutoff = random.randint(200, 2000)
        volume = random.uniform(0.02, 0.08)
        noise_combined += lowpass(layer_noise, cutoff, fs) * volume
    
    # 3. 맥동 효과 (Pulsing) - 1~30초 랜덤 주기
    pulse_period = random.uniform(1, 30)
    pulse_freq = 1.0 / pulse_period
    print(f"Applying pulse effect with period of {pulse_period:.2f} seconds.")
    
    pulse = (np.sin(pulse_freq * 2 * np.pi * t) + 1) / 2
    final_wave = (drone + noise_combined) * pulse

    # Normalize to 16-bit PCM
    max_val = np.max(np.abs(final_wave))
    if max_val > 0:
        final_wave = (final_wave / max_val * 32767).astype(np.int16)
    else:
        final_wave = final_wave.astype(np.int16)
    
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
    seed = random.randint(1, 99999999)
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
