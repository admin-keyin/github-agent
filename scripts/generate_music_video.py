import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess

def midi_to_freq(m):
    if m == 0 or m is None:
        return 0.0
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))

# --- 사운드 신디사이저 엔진 ---

def synth_rhodes(freq, duration, velocity=0.7, fs=44100):
    """감성 Lo-Fi용 Rhodes / Electric Piano 음색 (벨 톤 + 부드러운 하모닉스 + 약한 트레몰로)"""
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq <= 0:
        return np.zeros_like(t)
    
    # 기본 사운드 + 벨 톤 + 오버톤
    w1 = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.6)
    w2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.35 * np.exp(-t * 2.8)
    w3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.15 * np.exp(-t * 4.2)
    w_bell = np.sin(2 * np.pi * (freq * 4.02) * t) * 0.12 * np.exp(-t * 7.0) # 금속 벨 잔향
    
    # 은은한 4.5Hz 코러스/트레몰로 느낌
    tremolo = 1.0 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    
    wave = (w1 + w2 + w3 + w_bell) * tremolo * velocity
    
    # 어택 페이드 (클릭 방지)
    attack = int(fs * 0.008)
    if len(wave) > attack:
        wave[:attack] *= np.linspace(0, 1, attack)
    return wave

def synth_grand_piano(freq, duration, velocity=0.7, fs=44100):
    """서정적인 K-발라드 / 뉴에이지용 어쿠스틱 그랜드 피아노 음색"""
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq <= 0:
        return np.zeros_like(t)
    
    # 자연스러운 배음 감쇠 커브
    w1 = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.2)
    w2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.45 * np.exp(-t * 2.2)
    w3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.25 * np.exp(-t * 3.5)
    w4 = np.sin(2 * np.pi * (freq * 4) * t) * 0.12 * np.exp(-t * 4.8)
    w5 = np.sin(2 * np.pi * (freq * 5) * t) * 0.06 * np.exp(-t * 6.0)
    
    # 타건 어택감 시뮬레이션 (초기 타격 노이즈 느낌)
    hammer = np.sin(2 * np.pi * (freq * 1.5) * t) * 0.1 * np.exp(-t * 25.0)
    
    wave = (w1 + w2 + w3 + w4 + w5 + hammer) * velocity
    
    attack = int(fs * 0.004)
    if len(wave) > attack:
        wave[:attack] *= np.linspace(0, 1, attack)
    return wave

def apply_spatial_reverb(buffer_l, buffer_r, fs=44100):
    """풍성하고 몽환적인 공간감을 위한 딜레이 & 리버브 잔향"""
    total_len = len(buffer_l)
    out_l = np.copy(buffer_l)
    out_r = np.copy(buffer_r)
    
    # 다양한 딜레이 탭으로 깊은 잔향 생성
    taps = [
        (int(fs * 0.095), 0.25, 0.7),
        (int(fs * 0.175), 0.20, 0.6),
        (int(fs * 0.285), 0.18, 0.5),
        (int(fs * 0.420), 0.12, 0.4),
    ]
    
    for delay_samples, wet_l, wet_r in taps:
        if delay_samples < total_len:
            out_l[delay_samples:] += buffer_r[:-delay_samples] * wet_l
            out_r[delay_samples:] += buffer_l[:-delay_samples] * wet_r
            
    return out_l, out_r

# --- 장르별 코드 진행 및 프리셋 정의 ---

GENRES = [
    {
        "id": "lofi_chill",
        "title": "새벽 감성 Lo-Fi 피아노 (Chill Lo-Fi Rhodes Piano)",
        "desc": "포근하고 몽환적인 Lo-Fi 칠합 감성의 Rhodes 일렉트릭 피아노 연주곡입니다. 따뜻한 7th·9th 코드 진행과 나른한 멜로디로 편안한 휴식과 집중을 선사합니다.",
        "synth": "rhodes",
        "bpm": 76,
        "image_prompts": [
            "cozy aesthetic anime bedroom at midnight, heavy rain on large window, warm amber desk lamp, steaming cup of coffee, cat sleeping on desk, lo-fi hip hop chill vibe, highly detailed digital painting",
            "chill night cafe in seoul, rain reflections on glass window, warm glowing neon interior lights, lofi anime aesthetic, serene and calm, 4k masterpiece",
            "aesthetic night rooftop garden with starry sky, city skyline bokeh distant glow, cozy fairy lights, lo-fi chill mood, pastel color palette",
            "vintage room with vinyl record player spinning, warm ambient bedside light, plants hanging by window, cozy rainy night, aesthetic lofi artwork",
            "retro train window seat at dusk, purple twilight sky, distant city lights, earphones on table, nostalgic lofi anime scenery"
        ],
        "progressions": [
            # 1. NewJeans/R&B 하강 감성: Fmaj7 - Em7 - Dm7 - Cmaj7
            [
                ([53, 57, 60, 64], 41, [64, 65, 67, 69]), # Fmaj7
                ([52, 55, 59, 62], 40, [62, 64, 67, 71]), # Em7
                ([50, 53, 57, 60], 38, [60, 62, 65, 69]), # Dm7
                ([48, 52, 55, 59], 36, [59, 60, 64, 67]), # Cmaj7
            ],
            # 2. Neo-Soul 2-5-1-6 재즈 팝: Dm9 - G13 - Cmaj9 - A7(b13)
            [
                ([50, 57, 60, 64], 38, [64, 65, 67, 72]), # Dm9
                ([53, 57, 59, 64], 43, [62, 64, 67, 71]), # G13
                ([48, 55, 59, 62], 36, [59, 62, 64, 67]), # Cmaj9
                ([49, 55, 58, 61], 45, [61, 64, 67, 69]), # A7(b13)
            ],
            # 3. 몽환적인 Lo-fi 팝: Bbmaj7 - Am7 - Gm7 - Fmaj7
            [
                ([58, 62, 65, 69], 46, [69, 70, 72, 74]), # Bbmaj7
                ([57, 60, 64, 67], 45, [67, 69, 72, 76]), # Am7
                ([55, 58, 62, 65], 43, [65, 67, 70, 74]), # Gm7
                ([53, 57, 60, 64], 41, [64, 65, 69, 72]), # Fmaj7
            ]
        ]
    },
    {
        "id": "k_ballad",
        "title": "새벽 감성 K-발라드 피아노 (Emotional K-Ballad Piano)",
        "desc": "아이유·성시경 감성의 벅차오르고 애절한 한국형 발라드 피아노 연주곡입니다. 유려한 아르페지오와 감성적인 멜로디 라인이 마음을 따뜻하게 위로해 줍니다.",
        "synth": "grand",
        "bpm": 68,
        "image_prompts": [
            "poetic rainy seoul street at quiet dawn, glowing amber streetlights reflection on wet asphalt, cinematic Korean drama emotional vibe, 35mm film photography aesthetic",
            "solitary grand piano by a floor-to-ceiling glass window overlooking a rainy city night, soft mood lighting, melancholy aesthetic, photorealistic",
            "serene misty autumn park at sunset, fallen golden maple leaves, gentle warm cinematic lighting, romantic melancholy, moody film tone",
            "quiet han river bridge overlook at blue hour twilight, distant city lights twinkling on water surface, lonely emotional mood, cinematic lighting",
            "vintage acoustic cafe corner with upright piano, soft dusk sunlight streaming through linen curtains, warm nostalgic aesthetic"
        ],
        "progressions": [
            # 1. K-POP 감성 왕도 진행 (IVmaj7 - V - iii7 - vi - ii7 - V7 - I): Fmaj7 - G - Em7 - Am7 - Dm7 - G7 - C
            [
                ([53, 57, 60, 64], 41, [64, 65, 67, 72]), # Fmaj7
                ([55, 59, 62, 67], 43, [67, 71, 74, 76]), # G
                ([52, 55, 59, 64], 40, [64, 67, 71, 74]), # Em7
                ([57, 60, 64, 67], 45, [67, 69, 72, 76]), # Am7
                ([50, 53, 57, 62], 38, [62, 65, 69, 72]), # Dm7
                ([53, 55, 59, 65], 43, [65, 67, 71, 74]), # G7sus4-G7
                ([48, 52, 55, 60], 36, [60, 64, 67, 72]), # C
                ([48, 52, 55, 59], 36, [59, 62, 64, 67]), # Cmaj7
            ],
            # 2. 감성 발라드 하강 베이스: C - G/B - Am7 - C/G - Fadd9 - C/E - Dm7 - Gsus4
            [
                ([48, 52, 55, 60], 36, [60, 64, 67, 72]), # C
                ([47, 50, 55, 59], 35, [59, 62, 67, 71]), # G/B
                ([45, 48, 52, 57], 33, [57, 60, 64, 69]), # Am7
                ([43, 48, 52, 55], 31, [55, 60, 64, 67]), # C/G
                ([41, 48, 53, 57], 29, [57, 60, 65, 69]), # Fadd9
                ([40, 48, 52, 55], 28, [55, 60, 64, 67]), # C/E
                ([38, 45, 50, 53], 26, [53, 57, 62, 65]), # Dm7
                ([43, 48, 50, 55], 31, [55, 60, 62, 67]), # Gsus4
            ]
        ]
    },
    {
        "id": "new_age",
        "title": "감성 힐링 뉴에이지 피아노 (Peaceful New Age Piano)",
        "desc": "이루마, 히사이시 조 감성의 맑고 몽환적인 뉴에이지 피아노 연주곡입니다. 귓가를 맴도는 맑은 물방울 같은 아르페지오와 평온한 선율로 깊은 힐링과 수면을 돕습니다.",
        "synth": "grand",
        "bpm": 84,
        "image_prompts": [
            "dreamy fantasy night landscape, tranquil crystal blue lake under glowing stars and gentle aurora, ethereal fairytale aesthetic, Studio Ghibli style",
            "mystical glowing ancient forest with tiny floating bioluminescent orbs, soft silver moonlight filtering through lush trees, masterpiece wallpaper",
            "peaceful cloud garden at golden hour sunset, soft floating islands, dreamy surreal atmosphere, ultra calming pastel colors",
            "calm ocean waves gently touching sandy beach under a giant full moon and starry milky way sky, mystical fantasy serenity",
            "blooming cherry blossom tree on a peaceful hilltop at night under vibrant galaxy sky, magical anime art style"
        ],
        "progressions": [
            # 1. 뉴에이지 캐논 변형 진행: C - G - Am - Em - F - C - F - G
            [
                ([48, 52, 55, 60], 36, [60, 64, 67, 72]), # C
                ([47, 50, 55, 59], 35, [59, 62, 67, 71]), # G
                ([45, 48, 52, 57], 33, [57, 60, 64, 69]), # Am
                ([40, 43, 47, 52], 28, [52, 55, 59, 64]), # Em
                ([41, 45, 48, 53], 29, [53, 57, 60, 65]), # F
                ([48, 52, 55, 60], 36, [60, 64, 67, 72]), # C
                ([41, 45, 48, 53], 29, [53, 57, 60, 65]), # Fadd9
                ([43, 47, 50, 55], 31, [55, 59, 62, 67]), # G
            ],
            # 2. 히사이시 조 감성 서정적 진행: Am7 - Fadd9 - Cmaj7 - G6
            [
                ([45, 52, 57, 60], 33, [60, 64, 67, 69]), # Am7
                ([41, 48, 53, 57], 29, [57, 60, 65, 69]), # Fadd9
                ([48, 52, 55, 59], 36, [59, 64, 67, 71]), # Cmaj7
                ([43, 47, 50, 55], 31, [55, 59, 62, 67]), # G6
            ]
        ]
    }
]

def generate_music_track(duration_sec, output_path):
    fs = 44100
    total_samples = int(fs * duration_sec)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    # 1. 장르 및 코드 진행 선택
    genre = random.choice(GENRES)
    progression = random.choice(genre["progressions"])
    synth_type = genre["synth"]
    bpm = genre["bpm"]
    beat_sec = 60.0 / bpm
    beat_samples = int(fs * beat_sec)
    measure_samples = beat_samples * 4
    
    synth_func = synth_rhodes if synth_type == "rhodes" else synth_grand_piano
    
    def play_note(midi_pitch, start_sample, length_sec, vel, pan):
        if midi_pitch <= 0:
            return
        freq = midi_to_freq(midi_pitch)
        wave = synth_func(freq, length_sec, velocity=vel, fs=fs)
        if start_sample >= total_samples:
            return
        start_sample = max(0, start_sample)
        end_s = min(total_samples, start_sample + len(wave))
        wave_slice = wave[:end_s - start_sample]
        if len(wave_slice) == 0:
            return
        
        buffer_l[start_sample:end_s] += wave_slice * (1.0 - pan)
        buffer_r[start_sample:end_s] += wave_slice * pan

    # 2. 곡 구조 (다이내믹스) 생성
    current_time_samples = 0
    chord_idx = 0
    prog_len = len(progression)
    
    while current_time_samples < total_samples:
        chord_midi, bass_midi, melody_scale = progression[chord_idx % prog_len]
        chord_idx += 1
        
        # 현재 곡의 구간에 따른 다이내믹스 (Intro/Verse/Chorus)
        progress_ratio = current_time_samples / total_samples
        if progress_ratio < 0.15 or progress_ratio > 0.88:
            section_type = "soft"      # 인트로 / 아웃트로
            bass_vel = 0.45
            chord_vel = 0.28
            lead_prob = 0.40
        elif 0.35 <= progress_ratio <= 0.75:
            section_type = "chorus"    # 클라이맥스 후렴
            bass_vel = 0.65
            chord_vel = 0.40
            lead_prob = 0.85
        else:
            section_type = "verse"     # 일반 절
            bass_vel = 0.55
            chord_vel = 0.32
            lead_prob = 0.65

        # (1) 왼손 베이스 (묵직하고 둥근 톤)
        # 휴머나이즈 미세 타이밍 오차
        timing_jitter = random.randint(-int(fs * 0.005), int(fs * 0.005))
        s_bass = max(0, current_time_samples + timing_jitter)
        play_note(bass_midi, s_bass, beat_sec * 3.8, bass_vel, 0.48)
        
        # (2) 왼손 아르페지오 (1 - 5 - 8 - 10 롤링 패턴)
        if section_type in ["verse", "chorus"]:
            fifth_midi = bass_midi + 7
            oct_midi = bass_midi + 12
            tenth_midi = chord_midi[1]
            
            arp_pattern = [
                (beat_samples * 1, fifth_midi, 0.32),
                (beat_samples * 2, oct_midi, 0.30),
                (beat_samples * 3, tenth_midi, 0.28),
            ]
            for offset_s, pitch, a_vel in arp_pattern:
                j = random.randint(-int(fs * 0.005), int(fs * 0.005))
                play_note(pitch, s_bass + offset_s + j, beat_sec * 2.0, a_vel * (1.1 if section_type == "chorus" else 0.9), random.uniform(0.35, 0.55))

        # (3) 오른손 하모니 코드 (감성 보이싱)
        if section_type == "soft":
            # 잔잔하게 1박에 서스테인 코드
            for m in chord_midi:
                play_note(m, s_bass + random.randint(0, int(fs * 0.015)), beat_sec * 3.5, chord_vel, random.uniform(0.3, 0.7))
        else:
            # 1박과 3박에 나뉘어 리듬감 부여
            for m in chord_midi:
                play_note(m, s_bass, beat_sec * 2.0, chord_vel, random.uniform(0.3, 0.7))
            if random.random() < 0.65:
                s_chord2 = s_bass + beat_samples * 2
                for m in chord_midi:
                    play_note(m, s_chord2, beat_sec * 1.8, chord_vel * 0.85, random.uniform(0.3, 0.7))

        # (4) 감성 테마 멜로디 연주 (8분음표/16분음표 멜로디 라인)
        steps = 8 # 1마디를 8분음표 단위로 분할
        step_samples = measure_samples // steps
        
        for step in range(steps):
            if random.random() < lead_prob:
                m_pitch = random.choice(melody_scale)
                # 코러스에서는 한 옥타브 위로 도약하여 벅찬 느낌
                if section_type == "chorus" and random.random() < 0.45:
                    m_pitch += 12
                    
                note_dur = random.choice([beat_sec * 0.8, beat_sec * 1.2, beat_sec * 1.8])
                note_pos = s_bass + step * step_samples + random.randint(-int(fs * 0.008), int(fs * 0.008))
                
                m_vel = random.uniform(0.40, 0.68) if section_type == "chorus" else random.uniform(0.28, 0.50)
                m_pan = random.uniform(0.2, 0.8)
                play_note(m_pitch, note_pos, note_dur, m_vel, m_pan)

        current_time_samples += measure_samples

    # 3. 공간감 리버브 & 딜레이 잔향 적용
    print("Applying high-end stereo reverb & spatial effects...")
    buffer_l, buffer_r = apply_spatial_reverb(buffer_l, buffer_r, fs)

    # 4. 피크 마스터링 & 노멀라이즈
    max_val = max(np.max(np.abs(buffer_l)), np.max(np.abs(buffer_r)))
    if max_val > 0:
        buffer_l = (buffer_l / max_val) * 0.88
        buffer_r = (buffer_r / max_val) * 0.88

    # 16-bit PCM 저장
    buffer_l = (buffer_l * 32767).astype(np.int16)
    buffer_r = (buffer_r * 32767).astype(np.int16)
    stereo_wave = np.vstack((buffer_l, buffer_r)).T.flatten()

    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, stereo_wave.reshape(-1, 2))

    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")

    return genre

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
        # 실패 시 단색 이미지 또는 기본 파일 생성 방어
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    image_file = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 5분 음악 트랙 생성 (장르 및 메타데이터 획득)
    custom_prompt = os.getenv("IMAGE_PROMPT", "").strip()
    selected_genre = generate_music_track(300, base_audio)
    
    print(f"Selected Genre: {selected_genre['title']}")
    
    # 2. 이미지 프롬프트 결정 및 생성
    if custom_prompt:
        img_prompt = custom_prompt
    else:
        img_prompt = random.choice(selected_genre["image_prompts"])
        
    generate_ai_image(img_prompt, image_file)
    
    # 3. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
    
    # 4. 정보 저장 (업로드 스크립트에서 읽을 수 있도록)
    with open("temp/video_info.txt", "w") as f:
        f.write(f"{selected_genre['title']} | {selected_genre['desc']}")
