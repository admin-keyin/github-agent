import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess

def generate_piano_note(freq, duration, fs=44100):
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq == 0:
        return np.zeros_like(t)
    
    # 피아노 음색 합성 (기본음 + 배음)
    wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.0)
    wave += np.sin(2 * np.pi * 2 * freq * t) * 0.4 * np.exp(-t * 3.5)
    wave += np.sin(2 * np.pi * 3 * freq * t) * 0.2 * np.exp(-t * 5.0)
    wave += np.sin(2 * np.pi * 4 * freq * t) * 0.1 * np.exp(-t * 6.5)
    
    # 어택 (틱음 방지)
    attack_samples = int(fs * 0.005)
    if len(wave) > attack_samples:
        wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
        
    return wave


def generate_piano_music(duration_sec, output_path):
    fs = 44100
    total_samples = int(fs * duration_sec)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    # C major pentatonic (C3 ~ C6)
    melody_midi = [48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84]
    melody_freqs = [440.0 * (2.0 ** ((m - 69.0) / 12.0)) for m in melody_midi]
    
    # 베이스 용 저음역대 (C2 ~ C4)
    bass_midi = [36, 38, 40, 43, 45, 48, 50, 52]
    bass_freqs = [440.0 * (2.0 ** ((m - 69.0) / 12.0)) for m in bass_midi]
    
    # 템포 설정 (BPM 120)
    bpm = 120
    beat_sec = 60.0 / bpm
    beat_samples = int(fs * beat_sec)
    
    current_sample = 0
    while current_sample < total_samples:
        current_beat = current_sample // beat_samples
        
        # 1. 베이스 연주 (4박자마다 80% 확률로)
        if current_beat % 4 == 0 and random.random() < 0.8:
            freq = random.choice(bass_freqs)
            note_duration = random.uniform(3.0, 5.0)
            note_wave = generate_piano_note(freq, note_duration, fs)
            
            pan = random.uniform(0.4, 0.6)
            volume = random.uniform(0.3, 0.5)
            
            end_sample = current_sample + len(note_wave)
            if end_sample > total_samples:
                note_wave = note_wave[:total_samples - current_sample]
                end_sample = total_samples
                
            buffer_l[current_sample:end_sample] += note_wave * (1.0 - pan) * volume
            buffer_r[current_sample:end_sample] += note_wave * pan * volume
            
        # 2. 멜로디 연주 (65% 확률)
        if random.random() < 0.65:
            play_double = random.random() < 0.25  # 25% 확률로 2화음
            
            notes_to_play = [random.choice(melody_freqs)]
            if play_double:
                notes_to_play.append(random.choice(melody_freqs))
                
            for freq in notes_to_play:
                note_duration = random.choice([1.0, 1.5, 2.0, 3.0])
                note_wave = generate_piano_note(freq, note_duration, fs)
                
                pan = random.uniform(0.1, 0.9)
                volume = random.uniform(0.15, 0.35)
                
                end_sample = current_sample + len(note_wave)
                if end_sample > total_samples:
                    note_wave = note_wave[:total_samples - current_sample]
                    end_sample = total_samples
                    
                buffer_l[current_sample:end_sample] += note_wave * (1.0 - pan) * volume
                buffer_r[current_sample:end_sample] += note_wave * pan * volume
        
        # 박자 간격 이동
        if random.random() < 0.4:
            current_sample += beat_samples // 2
        else:
            current_sample += beat_samples
            
    # 정규화
    max_val = max(np.max(np.abs(buffer_l)), np.max(np.abs(buffer_r)))
    if max_val > 0:
        buffer_l = buffer_l / max_val * 0.85
        buffer_r = buffer_r / max_val * 0.85
        
    # 16-bit PCM
    buffer_l = (buffer_l * 32767).astype(np.int16)
    buffer_r = (buffer_r * 32767).astype(np.int16)
    stereo_wave = np.vstack((buffer_l, buffer_r)).T.flatten()
    
    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, stereo_wave.reshape(-1, 2))
    
    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")
    
    return "Random Piano", "Beautiful Random Piano Music using Pentatonic Scale"


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

    # 2. 5분 영상을 48번 반복 (48 * 5분 = 4시간)
    with open("temp/concat.txt", "w") as f:
        for _ in range(48):
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
    freq, desc = generate_piano_music(300, base_audio)
    
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
        if isinstance(freq, (int, float)):
            f.write(f"{freq}Hz | {desc}")
        else:
            f.write(f"{freq} | {desc}")
