import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess
from bs4 import BeautifulSoup
import re

def midi_to_freq(m):
    if m == 0 or m is None:
        return 0.0
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))

# --- 실시간 멜론 발라드 TOP 100 크롤러 ---

def fetch_melon_top_ballad():
    """멜론 발라드 차트 TOP 100을 크롤링하여 무작위 또는 상위 인기곡 1곡 선정"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    url = 'https://www.melon.com/chart/genre/index.htm?classCd=GN0100'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            titles = soup.select('div.ellipsis.rank01 a')
            artists = soup.select('div.ellipsis.rank02 a:first-child')
            
            song_list = []
            for rank, (t, a) in enumerate(zip(titles, artists), 1):
                clean_title = t.text.strip().replace('\xa0', ' ')
                clean_artist = a.text.strip().replace('\xa0', ' ')
                song_list.append({
                    "rank": rank,
                    "title": clean_title,
                    "artist": clean_artist
                })
            
            if song_list:
                # 상위 50위 내에서 가중치 있게 선정 (인기곡 우선)
                target_pool = song_list[:50]
                selected = random.choice(target_pool)
                print(f"[Melon Chart] 실시간 발라드 {selected['rank']}위 선정: {selected['artist']} - {selected['title']}")
                return selected
    except Exception as e:
        print(f"[Melon Chart] 크롤링 오류 발생 (기본 발라드 사용): {e}")

    # 크롤링 실패 시 기본 폴백 K-발라드 명곡
    fallback_songs = [
        {"rank": 1, "title": "밤편지", "artist": "아이유"},
        {"rank": 2, "title": "모든 날, 모든 순간", "artist": "폴킴"},
        {"rank": 3, "title": "너의 모든 순간", "artist": "성시경"},
        {"rank": 4, "title": "그라데이션", "artist": "최유리"},
        {"rank": 5, "title": "첫사랑", "artist": "10CM"},
        {"rank": 6, "title": "우주를 줄게", "artist": "백아"},
        {"rank": 7, "title": "스토커", "artist": "10CM"},
        {"rank": 8, "title": "생각을 멈추다 보면", "artist": "최유리"},
    ]
    return random.choice(fallback_songs)

# --- 사운드 신디사이저 엔진 ---

def synth_acoustic_grand(freq, duration, velocity=0.7, fs=44100):
    """서정적이고 맑은 어쿠스틱 그랜드 피아노 사운드"""
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq <= 0:
        return np.zeros_like(t)
    
    # 그랜드 피아노 고유의 배음 감쇠 커브 (Harmonic overtones)
    w1 = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.1)
    w2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.45 * np.exp(-t * 2.1)
    w3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.25 * np.exp(-t * 3.4)
    w4 = np.sin(2 * np.pi * (freq * 4) * t) * 0.12 * np.exp(-t * 4.6)
    w5 = np.sin(2 * np.pi * (freq * 5) * t) * 0.05 * np.exp(-t * 5.8)
    
    # 해머 타격감 (어택 초기 노이즈감)
    hammer = np.sin(2 * np.pi * (freq * 1.5) * t) * 0.08 * np.exp(-t * 25.0)
    
    wave = (w1 + w2 + w3 + w4 + w5 + hammer) * velocity
    
    # 클릭 방지 어택 램프
    attack = int(fs * 0.004)
    if len(wave) > attack:
        wave[:attack] *= np.linspace(0, 1, attack)
    return wave

def apply_spatial_reverb(buffer_l, buffer_r, fs=44100):
    """콘서트홀/스튜디오 감성의 스테레오 공간감 리버브"""
    total_len = len(buffer_l)
    out_l = np.copy(buffer_l)
    out_r = np.copy(buffer_r)
    
    taps = [
        (int(fs * 0.095), 0.28, 0.70),
        (int(fs * 0.180), 0.22, 0.60),
        (int(fs * 0.290), 0.18, 0.50),
        (int(fs * 0.430), 0.12, 0.40),
    ]
    
    for delay_samples, wet_l, wet_r in taps:
        if delay_samples < total_len:
            out_l[delay_samples:] += buffer_r[:-delay_samples] * wet_l
            out_r[delay_samples:] += buffer_l[:-delay_samples] * wet_r
            
    return out_l, out_r

# --- K-발라드 감성 화성 진행 & 멜로디 테마 ---

BALLAD_PROGRESSIONS = [
    # 1. K-발라드 대표 왕도 진행 (IVmaj7 - V - iii7 - vi - ii7 - V7 - I)
    [
        ([53, 57, 60, 64], 41, [64, 65, 67, 72, 76]), # Fmaj7
        ([55, 59, 62, 67], 43, [67, 71, 74, 76, 79]), # G
        ([52, 55, 59, 64], 40, [64, 67, 71, 74, 76]), # Em7
        ([57, 60, 64, 67], 45, [67, 69, 72, 76, 79]), # Am7
        ([50, 53, 57, 62], 38, [62, 65, 69, 72, 74]), # Dm7
        ([53, 55, 59, 65], 43, [65, 67, 71, 74, 77]), # G7sus4
        ([48, 52, 55, 60], 36, [60, 64, 67, 72, 76]), # C
        ([48, 52, 55, 59], 36, [59, 62, 64, 67, 71]), # Cmaj7
    ],
    # 2. 감성 하강 베이스 발라드 (C - G/B - Am7 - C/G - Fadd9 - C/E - Dm7 - Gsus4)
    [
        ([48, 52, 55, 60], 36, [60, 64, 67, 72, 76]), # C
        ([47, 50, 55, 59], 35, [59, 62, 67, 71, 74]), # G/B
        ([45, 48, 52, 57], 33, [57, 60, 64, 69, 72]), # Am7
        ([43, 48, 52, 55], 31, [55, 60, 64, 67, 72]), # C/G
        ([41, 48, 53, 57], 29, [57, 60, 65, 69, 72]), # Fadd9
        ([40, 48, 52, 55], 28, [55, 60, 64, 67, 72]), # C/E
        ([38, 45, 50, 53], 26, [53, 57, 62, 65, 69]), # Dm7
        ([43, 48, 50, 55], 31, [55, 60, 62, 67, 71]), # Gsus4
    ],
    # 3. 애절한 마이너 모달 발라드 (Am - F - C - G)
    [
        ([45, 52, 57, 60], 33, [60, 64, 67, 69, 72]), # Am
        ([41, 48, 53, 57], 29, [57, 60, 65, 69, 72]), # Fadd9
        ([48, 52, 55, 60], 36, [60, 64, 67, 72, 76]), # C
        ([43, 47, 50, 55], 31, [55, 59, 62, 67, 71]), # G
        ([45, 52, 57, 60], 33, [60, 64, 67, 69, 72]), # Am
        ([50, 53, 57, 62], 38, [62, 65, 69, 72, 74]), # Dm7
        ([53, 55, 59, 65], 43, [65, 67, 71, 74, 77]), # G7
        ([48, 52, 55, 60], 36, [60, 64, 67, 72, 76]), # C
    ]
]

def generate_ballad_track(song_info, duration_sec, output_path):
    fs = 44100
    total_samples = int(fs * duration_sec)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    # 템포 설정 (K-발라드 표준 66~72 BPM)
    bpm = random.randint(66, 72)
    beat_sec = 60.0 / bpm
    beat_samples = int(fs * beat_sec)
    measure_samples = beat_samples * 4
    
    progression = random.choice(BALLAD_PROGRESSIONS)
    
    def play_note(midi_pitch, start_sample, length_sec, vel, pan):
        if midi_pitch <= 0:
            return
        freq = midi_to_freq(midi_pitch)
        wave = synth_acoustic_grand(freq, length_sec, velocity=vel, fs=fs)
        if start_sample >= total_samples:
            return
        start_sample = max(0, start_sample)
        end_s = min(total_samples, start_sample + len(wave))
        wave_slice = wave[:end_s - start_sample]
        if len(wave_slice) == 0:
            return
        
        buffer_l[start_sample:end_s] += wave_slice * (1.0 - pan)
        buffer_r[start_sample:end_s] += wave_slice * pan

    current_time_samples = 0
    chord_idx = 0
    prog_len = len(progression)
    
    while current_time_samples < total_samples:
        chord_midi, bass_midi, melody_scale = progression[chord_idx % prog_len]
        chord_idx += 1
        
        # 곡 진행 구조 (Intro -> Verse -> Chorus -> Outro)
        progress_ratio = current_time_samples / total_samples
        if progress_ratio < 0.12 or progress_ratio > 0.88:
            section_type = "soft"      # 인트로 / 아웃트로
            bass_vel = 0.45
            chord_vel = 0.28
            lead_prob = 0.45
        elif 0.35 <= progress_ratio <= 0.75:
            section_type = "chorus"    # 클라이맥스 후렴
            bass_vel = 0.68
            chord_vel = 0.42
            lead_prob = 0.90
        else:
            section_type = "verse"     # 일반 절
            bass_vel = 0.55
            chord_vel = 0.32
            lead_prob = 0.70

        # (1) 왼손 루트 베이스
        timing_jitter = random.randint(-int(fs * 0.005), int(fs * 0.005))
        s_bass = max(0, current_time_samples + timing_jitter)
        play_note(bass_midi, s_bass, beat_sec * 3.8, bass_vel, 0.48)
        
        # (2) 왼손 감성 아르페지오 (1 - 5 - 8 - 10 패턴)
        if section_type in ["verse", "chorus"]:
            fifth_midi = bass_midi + 7
            oct_midi = bass_midi + 12
            tenth_midi = chord_midi[1]
            
            arp_pattern = [
                (beat_samples * 1, fifth_midi, 0.34),
                (beat_samples * 2, oct_midi, 0.32),
                (beat_samples * 3, tenth_midi, 0.30),
            ]
            for offset_s, pitch, a_vel in arp_pattern:
                j = random.randint(-int(fs * 0.005), int(fs * 0.005))
                play_note(pitch, s_bass + offset_s + j, beat_sec * 2.2, a_vel * (1.15 if section_type == "chorus" else 0.95), random.uniform(0.38, 0.52))

        # (3) 오른손 하모니 코드 보이싱
        if section_type == "soft":
            for m in chord_midi:
                play_note(m, s_bass + random.randint(0, int(fs * 0.012)), beat_sec * 3.6, chord_vel, random.uniform(0.35, 0.65))
        else:
            for m in chord_midi:
                play_note(m, s_bass, beat_sec * 2.2, chord_vel, random.uniform(0.35, 0.65))
            if random.random() < 0.70:
                s_chord2 = s_bass + beat_samples * 2
                for m in chord_midi:
                    play_note(m, s_chord2, beat_sec * 1.8, chord_vel * 0.85, random.uniform(0.35, 0.65))

        # (4) 감성 주선율(테마 멜로디) 연주
        steps = 8
        step_samples = measure_samples // steps
        
        for step in range(steps):
            if random.random() < lead_prob:
                m_pitch = random.choice(melody_scale)
                if section_type == "chorus" and random.random() < 0.50:
                    m_pitch += 12
                    
                note_dur = random.choice([beat_sec * 0.8, beat_sec * 1.2, beat_sec * 1.6])
                note_pos = s_bass + step * step_samples + random.randint(-int(fs * 0.006), int(fs * 0.006))
                
                m_vel = random.uniform(0.42, 0.70) if section_type == "chorus" else random.uniform(0.30, 0.52)
                m_pan = random.uniform(0.25, 0.75)
                play_note(m_pitch, note_pos, note_dur, m_vel, m_pan)

        current_time_samples += measure_samples

    print("Applying high-end stereo reverb & spatial effects...")
    buffer_l, buffer_r = apply_spatial_reverb(buffer_l, buffer_r, fs)

    # 피크 마스터링 & 노멀라이즈
    max_val = max(np.max(np.abs(buffer_l)), np.max(np.abs(buffer_r)))
    if max_val > 0:
        buffer_l = (buffer_l / max_val) * 0.88
        buffer_r = (buffer_r / max_val) * 0.88

    buffer_l = (buffer_l * 32767).astype(np.int16)
    buffer_r = (buffer_r * 32767).astype(np.int16)
    stereo_wave = np.vstack((buffer_l, buffer_r)).T.flatten()

    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, stereo_wave.reshape(-1, 2))

    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")

def create_8h_video(image_path, audio_path, output_path):
    print("Creating 8-hour video (High-speed concatenation mode)...")
    short_video = "temp/short.mp4"
    cmd_short = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", "300", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "128k", short_video
    ]
    subprocess.run(cmd_short, check=True)

    with open("temp/concat.txt", "w") as f:
        for _ in range(96):
            f.write("file 'short.mp4'\n")
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"Final 8-hour video created: {output_path}")

def generate_ai_image(prompt, filename):
    print(f"Generating background image: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        with open(filename, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"Image generation fallback due to: {e}")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    image_file = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 최신 멜론 TOP 발라드 차트 크롤링 및 대상 곡 선정
    song = fetch_melon_top_ballad()
    
    # 2. 5분 고품질 발라드 피아노 트랙 생성
    generate_ballad_track(song, 300, base_audio)
    
    # 3. K-발라드 감성 AI 이미지 프롬프트 생성
    image_prompts = [
        f"poetic rainy seoul street at quiet dawn, glowing amber streetlights reflection on wet asphalt, emotional Korean ballad mood inspired by {song['artist']}, 35mm film aesthetic",
        f"solitary grand piano by a floor-to-ceiling glass window overlooking a rainy night city, soft warm mood lighting, emotional romantic Korean ballad aesthetic",
        f"serene misty autumn han river park at sunset, gentle warm cinematic lighting, romantic melancholy, moody film tone for {song['title']}",
        f"vintage cozy acoustic cafe corner with upright piano, soft dusk sunlight streaming through linen curtains, warm nostalgic Korean drama vibe",
        f"quiet moonlit ocean horizon at blue hour twilight, distant lights twinkling, lonely emotional melody atmosphere, cinematic lighting"
    ]
    img_prompt = random.choice(image_prompts)
    generate_ai_image(img_prompt, image_file)
    
    # 4. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
    
    # 5. 유튜브 업로드용 정보 기록
    title = f"{song['artist']} - {song['title']} 연주"
    desc = f"멜론 실시간 발라드 TOP 100 인기곡 [{song['artist']} - {song['title']}]을 감미로운 피아노 선율로 연주한 힐링 트랙입니다. 수면, 공부, 집중과 편안한 휴식을 위해 8시간 연속 재생됩니다."
    
    with open("temp/video_info.txt", "w", encoding="utf-8") as f:
        f.write(f"{title} | {desc} | {song['artist']} | {song['title']}")
