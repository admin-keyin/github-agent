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

# --- 1. 장르별 전용 사운드 & 비주얼 프로파일 마스터 설정 ---

GENRE_PROFILES = {
    "piano": {
        "title_genre": "감성 피아노",
        "eq_colors": "white@0.95|white@0.4",
        "title_color": (255, 255, 255, 245),
        "box_color": (0, 0, 0, 150),
        # 맑은 고음 배음 + 깊은 콘서트홀 리버브
        "audio_filter": "treble=g=2.5:f=3800,aecho=0.8:0.88:45:0.28",
        "images": [
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "lofi": {
        "title_genre": "새벽 로파이",
        "eq_colors": "0xffd27f@0.95|0xff9933@0.45", # 따뜻한 앰버/오렌지 빛
        "title_color": (255, 235, 200, 245),
        "box_color": (20, 15, 10, 160),
        # 빈티지 바이닐 테이프 웜톤 (따뜻한 로우패스 4800Hz + 포근한 808 서브 베이스)
        "audio_filter": "lowpass=f=4800,bass=g=3:f=110,aecho=0.8:0.8:25:0.15",
        "images": [
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "jazz": {
        "title_genre": "카페 재즈",
        "eq_colors": "0xffdf80@0.95|0xd4af37@0.4", # 고급스러운 샴페인 골드
        "title_color": (255, 240, 190, 245),
        "box_color": (15, 10, 5, 160),
        # 묵직한 콘트라베이스 + 감미로운 미드레인지(색소폰/피아노 강조)
        "audio_filter": "bass=g=3.5:f=120,equalizer=f=1200:t=q:w=1.5:g=2.5,aecho=0.8:0.85:30:0.2",
        "images": [
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "citypop": {
        "title_genre": "시티팝",
        "eq_colors": "0x00ffff@0.95|0xff00ff@0.6", # 네온 사이안 & 마젠타 핑크
        "title_color": (210, 250, 255, 250),
        "box_color": (10, 5, 20, 160),
        # 80s 펑키 슬랩 베이스(100Hz) + 영롱한 신스 브라스 고음(5kHz)
        "audio_filter": "bass=g=3.5:f=95,treble=g=3.0:f=4500,aecho=0.8:0.8:20:0.12",
        "images": [
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "ambient": {
        "title_genre": "수면 앰비언트",
        "eq_colors": "0x80c0ff@0.9|0xa070ff@0.35", # 신비로운 오로라 블루/퍼플
        "title_color": (220, 235, 255, 240),
        "box_color": (5, 10, 25, 150),
        # 초저주파 힐링 드론(432Hz) + 광활한 우주 무한 잔향
        "audio_filter": "lowpass=f=3500,bass=g=2:f=80,aecho=0.85:0.92:60:0.4",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "edm": {
        "title_genre": "EDM 페스티벌",
        "eq_colors": "0x00ff88@0.95|0x00ccff@0.5", # 네온 일렉트릭 라임 & 사이안
        "title_color": (200, 255, 230, 255),
        "box_color": (0, 15, 10, 170),
        # 묵직한 4-on-the-floor 펀치 킥(60Hz Boost) + 촵! 스네어 타격감 (리버브 최소화로 펀치감 극대화)
        "audio_filter": "bass=g=4.5:f=65,treble=g=3.0:f=4000,aecho=0.8:0.75:10:0.06",
        "images": [
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    },
    "jpop": {
        "title_genre": "J-POP 애니메이션",
        "eq_colors": "0x66ccff@0.95|white@0.55", # 청량한 스카이 블루 & 화이트
        "title_color": (220, 245, 255, 250),
        "box_color": (5, 15, 30, 160),
        # 질주하는 140BPM 밴드 비트 + 쨍한 일렉기타 리프(3kHz) & 청량한 고음역대
        "audio_filter": "bass=g=2.5:f=100,equalizer=f=2800:t=q:w=1.2:g=3.0,treble=g=2.5:f=5000,aecho=0.8:0.8:18:0.1",
        "images": [
            "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1280&h=720&q=90",
            "https://images.unsplash.com/photo-1542051841857-5f90071e7989?auto=format&fit=crop&w=1280&h=720&q=90"
        ]
    }
}

INSTRUMENTS = {
    "piano": ["acoustic grand piano solo", "warm upright piano with felt dampers", "cinematic piano with subtle strings"],
    "lofi": ["warm Rhodes electric piano and boom bap drums", "mellow nylon guitar and vinyl chill beat"],
    "citypop": ["80s Tokyo nighttime groove with slap bass and synth brass", "retro seaside city pop with funky guitar"],
    "jazz": ["bossa nova acoustic guitar with shaker rhythm", "late-night jazz club trio with upright bass and sax"],
    "ambient": ["serene cosmic synth pads with 432Hz deep drone", "ethereal ocean ambient with crystal harp"],
    "edm": ["festival progressive house drop with punchy kicks and saw leads", "future bass with emotional vocal chops"],
    "jpop": ["upbeat anime opening rock with electric guitar riffs", "Shibuya night pop with driving bass and strings"]
}

MOODS = [
    "deeply emotional and nostalgic", "warm and cozy for deep relaxation",
    "peaceful and calming for sleep", "focus and inspiring for study and coding",
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
        ("새벽 {h}시 {m}분", ["불 꺼진 방에서 너를 떠올리며", "나지막이 흐르는 피아노", "잊혀지지 않는 계절의 기억"]),
        ("그때 너에게", ["하지 못했던 마지막 한마디", "전하지 못한 편지 한 장", "남겨둔 작은 온기"]),
        ("비 내리는 {w}", ["창가에 맺힌 너의 얼굴", "작은 우산 아래의 우리", "흘러나오는 선율"])
    ],
    "lofi": [
        ("퇴근길 지하철 막차", ["이어폰 너머로 번지는 위로", "창밖으로 스쳐가는 도심의 불빛", "나를 다독이는 따뜻한 비트"]),
        ("새벽 2시", ["편의점 앞 흐린 가로등 아래", "어질러진 책상 위 식어버린 커피", "조용히 흘러가는 나만의 시간"])
    ],
    "citypop": [
        ("자정이 넘은", ["한강 다리 위를 달리며", "네온사인 불빛 아래 너와 나만의 춤", "도심의 밤바람을 가르는 드라이브"]),
        ("80년대 서울의 밤", ["반짝이는 빌딩 숲과 너의 실루엣", "레트로 카세트테이프에서 흘러나오는 노래"])
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

def build_dynamic_prompt_and_title(genre):
    inst = random.choice(INSTRUMENTS.get(genre, INSTRUMENTS["piano"]))
    mood = random.choice(MOODS)
    key = random.choice(KEYS)
    bpm = random.choice(TEMPOS.get(genre, [70]))
    
    prompt = f"{inst}, in {key} key, {mood}, beautiful emotional melody, rich harmonic climax drop, studio quality mastering, {bpm} bpm"
    
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

# --- 2. 장르별 특색 마스터링 & 3~4분 완성형 편곡 엔진 ---

def extract_best_melody_section(audio_segment, min_duration_sec=35, max_duration_sec=65):
    total_len_ms = len(audio_segment)
    if total_len_ms > 70000:
        start_ms = 35000
        end_ms = min(total_len_ms - 2000, start_ms + (max_duration_sec * 1000))
        section = audio_segment[start_ms:end_ms]
    elif total_len_ms > 35000:
        start_ms = 15000
        section = audio_segment[start_ms:]
    else:
        section = audio_segment
    return section

def get_unique_audio_track(genre, prompt_text, output_mp3_path, target_duration_sec=210):
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["piano"])
    random_seed = random.randint(100000, 999999999)
    print(f"\n[Genre Master Engine] '{genre.upper()}' 장르 전용 특색 마스터링 편곡 (Seed: {random_seed})")

    genre_dir = f"assets/audio/{genre}"
    genre_files = glob.glob(f"{genre_dir}/*.mp3")
    if not genre_files:
        genre_files = glob.glob("assets/audio/*/*.mp3")
        
    base_audio = None
    random.shuffle(genre_files)
    for fpath in genre_files:
        try:
            temp_a = AudioSegment.from_file(fpath)
            if len(temp_a) > 5000:
                base_audio = temp_a
                chosen_file = fpath
                break
        except Exception as e:
            print(f"File load warning: {e}")

    if base_audio is None:
        fallback_files = glob.glob("assets/audio/*/*.mp3")
        for fpath in fallback_files:
            try:
                base_audio = AudioSegment.from_file(fpath)
                chosen_file = fpath
                break
            except Exception:
                pass

    print(f"[Master Highlight Track] {chosen_file}")
    
    # 1. 클라이맥스 멜로디 구간 추출
    highlight_section = extract_best_melody_section(base_audio, min_duration_sec=35, max_duration_sec=65)
    
    # 2. 조성 변화 (-2 ~ +2 반음) 및 템포 가변
    semitone = random.choice([-2, -1, 1, 2])
    pitch_factor = 2 ** (semitone / 12.0)
    speed_factor = random.uniform(0.96, 1.04)
    sample_rate = int(44100 * pitch_factor)
    atempo = speed_factor / pitch_factor

    # 3. 3~4분(210초) 확장
    full_song = highlight_section.fade_in(1500)
    target_ms = target_duration_sec * 1000
    while len(full_song) < target_ms:
        full_song = full_song.append(highlight_section, crossfade=2000)
    full_song = full_song[:target_ms]
    
    full_song = full_song.normalize(headroom=0.5).fade_out(4000)
    temp_arranged = "temp/arranged.wav"
    full_song.export(temp_arranged, format="wav")
    
    # 4. 장르별 맞춤 DSP 사운드 마스터링 필터 적용
    genre_dsp = profile["audio_filter"]
    af = f"asetrate={sample_rate},aresample=44100,atempo={atempo:.4f},{genre_dsp}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_arranged,
        "-af", af,
        "-c:a", "libmp3lame", "-b:a", "320k",
        output_mp3_path
    ]
    subprocess.run(cmd, check=True)
    
    final_audio = AudioSegment.from_file(output_mp3_path)
    print(f"[Genre Tuned Track Complete] {output_mp3_path} (길이: {len(final_audio)/1000:.1f}초, 필터: {genre_dsp})")
    return True

# --- 3. Pillow 기반 장르별 감성 컬러 타이틀 오버레이 생성기 ---

def create_title_overlay_png(title_text, genre, output_png_path, width=1280, height=720):
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["piano"])
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

    # 장르별 반투명 라운드 박스
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
        radius=12,
        fill=profile["box_color"]
    )

    # 장르별 감성 텍스트 컬러
    draw.text((x, y), title_text, font=font, fill=profile["title_color"])
    img.save(output_png_path, "PNG")

# --- 4. 고화질 배경 다운로드 & 장르별 맞춤 비주얼라이저 비디오 합성 ---

def fetch_hd_background(genre, filename):
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["piano"])
    chosen_url = random.choice(profile["images"])
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a2130:s=1280x720:d=1", "-vframes", "1", filename], check=True)

def create_equalizer_music_video(image_path, title_png_path, audio_path, genre, output_path):
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["piano"])
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    eq_colors = profile["eq_colors"]
    filter_complex = (
        f"[0:v]scale=1280:720[bg];"
        f"[bg][1:v]overlay=0:0[bg_titled];"
        f"[2:a]showfreqs=s=860x130:mode=bar:fscale=log:colors={eq_colors}:win_size=1024[eq];"
        f"[bg_titled][eq]overlay=x=(W-w)/2:y=H-180[v]"
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

    # 2. 장르별 맞춤 DSP 특색 마스터링 3~4분 음원 생성
    get_unique_audio_track(genre, final_prompt, ai_mp3, target_duration_sec=210)

    # 3. 장르별 감성 고화질 배경 이미지 다운로드
    fetch_hd_background(genre, bg_image)

    # 4. Pillow로 장르별 감성 컬러 타이틀 PNG 생성
    create_title_overlay_png(final_title, genre, title_png)

    # 5. 장르별 맞춤 컬러 이퀄라이저 비디오 렌더링 (3~4분)
    create_equalizer_music_video(bg_image, title_png, ai_mp3, genre, final_video)

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
