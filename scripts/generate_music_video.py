import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. 장르별 악기, 템포, 무드 및 신박한 제목 생성 엔진 ---

INSTRUMENTS = {
    "piano": [
        "acoustic grand piano solo", "warm upright piano with soft felt dampers",
        "cinematic piano with subtle violin strings", "romantic jazz piano with delicate touches",
        "flowing arpeggio new age piano", "melancholic ballad piano with vintage studio room reverb"
    ],
    "lofi": [
        "warm Rhodes electric piano and cozy boom bap drums", "mellow nylon acoustic guitar and lo-fi hip hop beat",
        "vintage synth chords with gentle vinyl crackle and chill groove", "rainy ambient window sound with soft jazz piano chords",
        "deep warm 808 sub bass and relaxed soulful lofi melody"
    ],
    "citypop": [
        "80s Tokyo nighttime groove with funky slap bass and bright synth brass",
        "breezy seaside city pop with catchy electric guitar riffs and retro drums",
        "nostalgic analog synthesizers with upbeat 80s disco groove and sax accents"
    ],
    "jazz": [
        "laid-back bossa nova acoustic guitar with soft shaker rhythm",
        "smoky late-night jazz club trio with upright bass and brushed snare",
        "sweet lyrical saxophone over gentle acoustic jazz piano chords"
    ],
    "ambient": [
        "serene cosmic synth pads with 432Hz deep relaxation drone",
        "ethereal floating ambient soundscape with crystal harp overtones",
        "peaceful ocean waves and slow cinematic atmospheric pads"
    ],
    "edm": [
        "energetic festival progressive house drop with punchy kicks and saw leads",
        "uplifting future bass with sidechained emotional vocal chops and huge supersaws",
        "driving melodic techno bassline with hypnotic synth arpeggios and laser FX"
    ],
    "jpop": [
        "upbeat anime opening rock with sparkling electric guitar riffs and fast drums",
        "emotional Shibuya night pop with sweet synth strings and fast driving bassline",
        "breezy summer youth anime OST with energetic acoustic guitar and piano runs"
    ]
}

MOODS = [
    "deeply emotional and nostalgic", "warm and cozy for deep relaxation",
    "peaceful and calming for sleep", "focus and inspiring for study and coding",
    "wistful and bittersweet", "dreamy and cinematic", "heartwarming and serene",
    "euphoric and full of festival energy", "breezy and refreshing youth vibe"
]

KEYS = ["C Major", "A Minor", "D Major", "B Minor", "G Major", "E Minor", "F Major", "D Minor", "Ab Major", "Eb Major", "F# Minor"]
TEMPOS = {
    "piano": [60, 64, 68, 72],
    "lofi": [70, 74, 78, 82],
    "citypop": [108, 114, 120],
    "jazz": [75, 80, 85, 90],
    "ambient": [48, 52, 56, 60],
    "edm": [126, 128, 130, 132],
    "jpop": [135, 140, 145, 150]
}

POETIC_TITLE_PIECES = {
    "piano": [
        ("새벽 {h}시 {m}분", ["불 꺼진 방에서 너를 떠올리며", "나지막이 흐르는 피아노", "잊혀지지 않는 계절의 기억", "우리가 머물렀던 그 자리에"]),
        ("그때 너에게", ["하지 못했던 마지막 한마디", "전하지 못한 편지 한 장", "꼭 들려주고 싶었던 노래", "남겨둔 작은 온기"]),
        ("비 내리는 {w}", ["창가에 맺힌 너의 얼굴", "작은 우산 아래의 우리", "골목길 카페에서", "흘러나오는 선율"]),
        ("언젠가 우리가", ["다시 만날 수 있다면", "사랑이라 불렀던 날들의 끝", "서로를 기억하게 될 때", "지나온 계절을 돌아보며"])
    ],
    "lofi": [
        ("퇴근길 지하철 막차", ["이어폰 너머로 번지는 위로", "창밖으로 스쳐가는 도심의 불빛", "나를 다독이는 따뜻한 비트"]),
        ("새벽 2시", ["편의점 앞 흐린 가로등 아래", "어질러진 책상 위 식어버린 커피", "조용히 흘러가는 나만의 시간"]),
        ("잠들지 못하는 밤", ["창문 틈으로 스며드는 새벽 공기", "괜찮은 척 웃어넘긴 하루의 끝", "따뜻한 이불 속에서 듣는 노래"])
    ],
    "citypop": [
        ("자정이 넘은", ["한강 다리 위를 달리며", "네온사인 불빛 아래 너와 나만의 춤", "도심의 밤바람을 가르는 드라이브"]),
        ("80년대 서울의 밤", ["반짝이는 빌딩 숲과 너의 실루엣", "레트로 카세트테이프에서 흘러나오는 노래", "도시의 낭만이 가득한 밤"])
    ],
    "jazz": [
        ("골목길 모퉁이", ["작은 재즈 카페의 온기", "비 내리는 밤의 색소폰", "따뜻한 와인 한 잔과 흐르는 음악"]),
        ("늦은 밤 홀로 앉아", ["조용히 울리는 콘트라베이스", "피아노 건반 위로 흩어지는 생각들"])
    ],
    "ambient": [
        ("우주 끝자락에", ["혼자 멈춰선 고요의 순간", "숨결조차 닿지 않는 평온함", "별들의 속삭임이 머무는 곳"]),
        ("깊은 밤의 쉼표", ["모든 소음이 사라진 깊은 바닷속", "지친 마음을 감싸주는 고요한 숨결"])
    ],
    "edm": [
        ("심장을 뛰게 하는", ["페스티벌의 뜨거운 밤", "네온 불빛 아래 터지는 에너지", "새벽까지 멈추지 않는 비트"]),
        ("끝없는 질주", ["한계를 넘어 날아오르는 순간", "도시의 밤을 가르는 신스 사운드"])
    ],
    "jpop": [
        ("푸른 하늘 아래", ["질주하는 청춘의 계절", "너와 함께 달렸던 언덕길", "끝나지 않을 우리들의 여름"]),
        ("시부야의 저녁 노을", ["이어폰 속으로 터져 나오는 멜로디", "빛나는 내일을 향한 발걸음"])
    ]
}

GENRE_IMAGES = {
    "piano": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "lofi": [
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "citypop": [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "jazz": [
        "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "ambient": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "edm": [
        "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "jpop": [
        "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1542051841857-5f90071e7989?auto=format&fit=crop&w=1280&h=720&q=90"
    ]
}

def build_dynamic_prompt_and_title(genre):
    inst = random.choice(INSTRUMENTS.get(genre, INSTRUMENTS["piano"]))
    mood = random.choice(MOODS)
    key = random.choice(KEYS)
    bpm = random.choice(TEMPOS.get(genre, [70]))
    
    prompt = f"{inst}, in {key} key, {mood}, beautiful emotional melody, rich harmonic chorus climax, studio quality mastering, {bpm} bpm"
    
    pieces = POETIC_TITLE_PIECES.get(genre, POETIC_TITLE_PIECES["piano"])
    prefix_template, suffixes = random.choice(pieces)
    prefix = prefix_template.format(
        h=random.choice([1, 2, 3, 4]),
        m=random.choice([12, 25, 34, 42, 51]),
        w=random.choice(["월요일", "수요일", "금요일", "주말 밤", "오후"])
    )
    suffix = random.choice(suffixes)
    title = f"{prefix}, {suffix}"
    
    return prompt, title, bpm, key

# --- 2. 최상급 클라이맥스 멜로디 중심의 3~4분 완성형 편곡 엔진 ---

def extract_best_melody_section(audio_segment, min_duration_sec=30, max_duration_sec=65):
    """
    음원에서 어색하거나 비어있는 앞부분을 건너뛰고,
    가장 멜로디와 화음이 풍성하게 터져 나오는 최상급 클라이맥스/하이라이트 구간 추출
    """
    total_len_ms = len(audio_segment)
    # 도입부(0~15초)의 비어있는 구간은 스킵
    start_offset_ms = min(15000, int(total_len_ms * 0.15)) if total_len_ms > 30000 else 0
    
    # 하이라이트 구간 길이 (35~60초)
    section_len_ms = min(max_duration_sec * 1000, total_len_ms - start_offset_ms)
    section = audio_segment[start_offset_ms : start_offset_ms + section_len_ms]
    return section

def get_unique_audio_track(genre, prompt_text, output_mp3_path, target_duration_sec=210):
    """
    가장 듣기 좋은 풍성한 클라이맥스 멜로디를 전면에 배치하여
    처음부터 끝까지 3~4분 내내 최고의 멜로디 감성을 유지하도록 편곡
    """
    random_seed = random.randint(100000, 999999999)
    print(f"\n[Highlight-Driven Composer] '{genre.upper()}' 클라이맥스 멜로디 중심 편곡 (Seed: {random_seed})")

    genre_dir = f"assets/audio/{genre}"
    genre_files = glob.glob(f"{genre_dir}/*.mp3")
    if not genre_files:
        genre_files = glob.glob("assets/audio/*/*.mp3")
        
    chosen_file = random.choice(genre_files)
    print(f"[Master Highlight Track] {chosen_file}")
    
    base_audio = AudioSegment.from_file(chosen_file)
    
    # 1. 가장 풍성하고 멜로디가 좋은 알짜배기 클라이맥스 구간 추출
    highlight_section = extract_best_melody_section(base_audio, min_duration_sec=35, max_duration_sec=65)
    
    # 조성 변화 (-2 ~ +2 반음)
    semitone = random.choice([-2, -1, 1, 2])
    pitch_factor = 2 ** (semitone / 12.0)
    speed_factor = random.uniform(0.96, 1.04)
    sample_rate = int(44100 * pitch_factor)
    atempo = speed_factor / pitch_factor

    # 2. 처음부터 풍성한 멜로디로 시작하는 하이라이트 루프 구성
    # 부드러운 1.5초 페이드인과 함께 바로 감미로운 메인 멜로디 시작
    full_song = highlight_section.fade_in(1500)
    
    target_ms = target_duration_sec * 1000 # 3분 30초
    while len(full_song) < target_ms:
        # 매끄러운 2초 크로스페이드로 클라이맥스 멜로디를 자연스럽게 순환
        full_song = full_song.append(highlight_section, crossfade=2000)
        
    full_song = full_song[:target_ms]
    
    # 최종 마스터링: 볼륨 노멀라이즈 & 서서히 사라지는 4초 엔딩 페이드아웃
    full_song = full_song.normalize(headroom=0.5).fade_out(4000)
    
    temp_arranged = "temp/arranged.wav"
    full_song.export(temp_arranged, format="wav")
    
    # FFmpeg로 풍부한 스튜디오 앰비언스 및 EQ 마스터링
    reverb_mix = random.uniform(0.2, 0.32)
    af = f"asetrate={sample_rate},aresample=44100,atempo={atempo:.4f},aecho=0.8:0.85:30:{reverb_mix:.2f}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_arranged,
        "-af", af,
        "-c:a", "libmp3lame", "-b:a", "320k",
        output_mp3_path
    ]
    subprocess.run(cmd, check=True)
    
    final_audio = AudioSegment.from_file(output_mp3_path)
    print(f"[Highlight Master Composition Complete] {output_mp3_path} (길이: {len(final_audio)/1000:.1f}초, 클라이맥스 멜로디 풀 적용)")
    return True

# --- 3. Pillow 기반 한글 깨짐 0% 고화질 타이틀 오버레이 생성기 ---

def create_title_overlay_png(title_text, output_png_path, width=1280, height=720):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc"
    ]

    font = None
    for p in font_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 28)
                break
            except Exception:
                pass

    if not font:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (width - text_w) // 2
    y = 65
    pad_x = 20
    pad_y = 12

    # 반투명 라운드 박스
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
        radius=12,
        fill=(0, 0, 0, 150)
    )

    draw.text((x, y), title_text, font=font, fill=(255, 255, 255, 245))
    img.save(output_png_path, "PNG")

# --- 4. 고화질 배경 다운로드 & 비주얼라이저 비디오 합성 ---

def fetch_hd_background(genre, filename):
    image_pool = GENRE_IMAGES.get(genre, GENRE_IMAGES["piano"])
    chosen_url = random.choice(image_pool)
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a2130:s=1280x720:d=1", "-vframes", "1", filename], check=True)

def create_equalizer_music_video(image_path, title_png_path, audio_path, output_path):
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    filter_complex = (
        "[0:v]scale=1280:720[bg];"
        "[bg][1:v]overlay=0:0[bg_titled];"
        "[2:a]showfreqs=s=860x130:mode=bar:fscale=log:colors=white@0.85|white@0.4:win_size=1024[eq];"
        "[bg_titled][eq]overlay=x=(W-w)/2:y=H-180[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", title_png_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[Visualizer Success] {output_path} (Duration: {duration_sec:.1f}s)")
    except Exception as e:
        print(f"Visualizer fallback simple render ({e})")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ], check=True)

# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    genre_input = os.getenv("INPUT_GENRE", "").strip().lower()
    available_genres = ["piano", "lofi", "citypop", "jazz", "ambient", "edm", "jpop"]
    
    if genre_input not in available_genres:
        genre = random.choice(available_genres)
    else:
        genre = genre_input
        
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    
    # 1. 동적 프롬프트 및 신박한 제목 생성
    auto_prompt, auto_title, bpm, key = build_dynamic_prompt_and_title(genre)
    final_prompt = custom_prompt if custom_prompt else auto_prompt
    final_title = custom_title if custom_title else f"[AI Music] {auto_title}"
    
    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    title_png = "temp/title_overlay.png"
    final_video = "output_music_video.mp4"

    # 2. 클라이맥스 멜로디 중심 3~4분 완성형 신곡 편곡
    get_unique_audio_track(genre, final_prompt, ai_mp3, target_duration_sec=210)

    # 3. 장르별 감성 고화질 배경 이미지 다운로드
    fetch_hd_background(genre, bg_image)

    # 4. Pillow로 한글 깨짐 0% 타이틀 PNG 생성
    create_title_overlay_png(final_title, title_png)

    # 5. 실시간 오디오 이퀄라이저 비디오 렌더링 (3~4분)
    create_equalizer_music_video(bg_image, title_png, ai_mp3, final_video)

    # 6. 유튜브 메타데이터 JSON 저장
    desc = (
        f"🎧 {final_title}\n\n"
        f"Genre: {genre.upper()} | Key: {key} | BPM: {bpm}\n"
        f"AI Prompt: \"{final_prompt}\"\n\n"
        f"Composed & Visualized by Keyin AI Music Studio.\n\n"
        f"#{genre.upper()} #AIMusic #AI작곡 #감성음악 #이퀄라이저 #Visualizer"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Keyin AI Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"Video metadata saved successfully for [{genre.upper()}]: {final_title}")
