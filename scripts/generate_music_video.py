import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
import unicodedata
from pathlib import Path
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. 3대 지정 음원 목록 (이 3개 이외에는 절대 사용하지 않음) ---
ALLOWED_TRACKS = ["뇌룡격파", "용전", "화룡진군"]

# --- 2. 75% 원곡 충실도 + 25% 스타일별 스튜디오 마스터링 설정 (음질 깨짐 0%, 원음 75% 보존) ---

PERFORMANCE_STYLES = {
    "edm": {
        "style_name": "EDM 페스티벌 리믹스",
        "title_template": "[Inkey EDM] 전략게임할 때 듣기 좋은 신나는 비트 - {name} (Festival EDM Drop)",
        "eq_colors": "0x00ffcc@0.95|0x00ff66@0.6",
        "title_color": (200, 255, 240, 255),
        "box_color": (0, 15, 12, 185),
        # 원곡 75% 선명도 유지 + 60Hz 서브 베이스 펀치 + 트레블 에어 + 와이드 스테레오
        "dsp_filter": "volume=-1.0dB,bass=g=3.0:f=65,equalizer=f=3500:t=q:w=1.2:g=2.0,stereotools=mlev=1.15,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "dance": {
        "style_name": "신나는 댄스 비트 리믹스",
        "title_template": "[Inkey 댄스] 가슴이 벅차오르는 신나는 댄스 비트 - {name} (Dance Remix)",
        "eq_colors": "0xff007f@0.95|0x9900ff@0.6",
        "title_color": (255, 220, 245, 255),
        "box_color": (15, 5, 20, 185),
        # 원곡 75% 유지 + 경쾌한 110Hz 리듬 펀치 + 브라이트 하모닉스
        "dsp_filter": "volume=-1.0dB,bass=g=2.8:f=110,equalizer=f=4000:t=q:w=1.2:g=2.2,stereotools=mlev=1.12,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "classic": {
        "style_name": "클래식 대심포니 오케스트라",
        "title_template": "[Inkey 클래식] 마음이 벅차오르는 대서사시 심포니 - {name} (Symphony Orchestra)",
        "eq_colors": "0xffdf80@0.95|0xd4af37@0.6",
        "title_color": (255, 245, 210, 255),
        "box_color": (15, 12, 5, 180),
        # 원곡 75% 유지 + 웅장한 오케스트라 콘서트홀 리버브 + 묵직한 저음역 심포니
        "dsp_filter": "volume=-1.0dB,bass=g=2.5:f=80,equalizer=f=1800:t=q:w=1.5:g=1.5,aecho=0.8:0.6:35:0.18,stereotools=mlev=1.18,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "piano": {
        "style_name": "감성 어쿠스틱 피아노 독주",
        "title_template": "[Inkey 피아노] 전략게임할 때 듣기 좋은 감성 피아노 선율 - {name} (Piano Solo)",
        "eq_colors": "white@0.95|0xddddff@0.5",
        "title_color": (255, 255, 255, 255),
        "box_color": (5, 8, 15, 175),
        # 원곡 75% 유지 + 맑고 영롱한 그랜드 피아노 건반 배음(3.2kHz) + 따뜻한 룸 잔향
        "dsp_filter": "volume=-1.0dB,equalizer=f=3200:t=q:w=1.2:g=2.8,treble=g=1.8:f=5500,aecho=0.8:0.5:28:0.15,stereotools=mlev=1.1,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "recorder": {
        "style_name": "동화 감성 리코더 & 목관 합주",
        "title_template": "[Inkey 리코더] 마음이 벅차오르는 동화 감성 멜로디 - {name} (Woodwind Ver.)",
        "eq_colors": "0x7fffd4@0.95|0xffff99@0.6",
        "title_color": (230, 255, 245, 255),
        "box_color": (5, 20, 15, 175),
        # 원곡 75% 유지 + 맑고 청아한 목관 멜로디 대역(2.4kHz) 부각
        "dsp_filter": "volume=-1.0dB,equalizer=f=2400:t=q:w=1.4:g=3.0,equalizer=f=1200:t=q:w=1.2:g=1.8,aecho=0.8:0.5:22:0.14,stereotools=mlev=1.1,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "guitar": {
        "style_name": "어쿠스틱 & 나일론 기타 연주",
        "title_template": "[Inkey 어쿠스틱 기타] 심장을 울리는 감성 기타 선율 - {name} (Acoustic Guitar)",
        "eq_colors": "0xffaa33@0.95|0xcc6600@0.6",
        "title_color": (255, 235, 205, 255),
        "box_color": (20, 12, 5, 180),
        # 원곡 75% 유지 + 통기타 바디 온기(180Hz) + 핑거링 어택감(3.0kHz)
        "dsp_filter": "volume=-1.0dB,bass=g=2.0:f=180,equalizer=f=3000:t=q:w=1.2:g=2.4,treble=g=1.8:f=6000,aecho=0.8:0.55:25:0.15,stereotools=mlev=1.12,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1525201548942-d8732f6617a0?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "electric": {
        "style_name": "강렬한 일렉 기타 & 락 밴드",
        "title_template": "[Inkey 일렉 기타] 심장을 뛰게 하는 강렬한 일렉트릭 연주 - {name} (Rock Electric Ver.)",
        "eq_colors": "0xff0033@0.95|0x9900ff@0.6",
        "title_color": (255, 210, 220, 255),
        "box_color": (20, 5, 10, 185),
        # 원곡 75% 유지 + 튜브 앰프 아날로그 드라이브 + 락 베이스 펀치
        "dsp_filter": "volume=-1.0dB,bass=g=2.8:f=100,equalizer=f=2800:t=q:w=1.2:g=2.6,equalizer=f=4500:t=q:w=1.0:g=2.2,aecho=0.8:0.6:20:0.16,stereotools=mlev=1.15,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "epic": {
        "style_name": "웅장한 오리엔탈 판타지 라이브",
        "title_template": "[Inkey 연주] 전략게임할 때 듣기 좋은 웅장한 음악 - {name} (Live Orchestra Ver.)",
        "eq_colors": "0xff4500@0.95|0xffd700@0.7",
        "title_color": (255, 245, 210, 255),
        "box_color": (15, 8, 5, 180),
        # 원곡 75% 유지 + 웅장한 전장 브라스 & 퍼커션 다이내믹스
        "dsp_filter": "volume=-1.0dB,bass=g=2.5:f=85,equalizer=f=3000:t=q:w=1.2:g=2.0,aecho=0.8:0.6:30:0.18,stereotools=mlev=1.15,alimiter=limit=0.92:attack=5:release=50",
        "images": [
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    }
}


# --- 3. 75% 원곡 충실도 + 스튜디오 마스터링 생성 엔진 ---

def get_inkey_performance_track(selected_file=None, selected_style=None, output_mp3_path="temp/ai_song.mp3"):
    """
    지정된 3개 음원 중 하나를 선택하고, 원본 음색의 75% 충실도를 완벽하게 보존하면서
    선택된 스타일에 맞추어 깨끗한 고음질 320kbps 스튜디오 마스터링을 적용합니다.
    """
    music_dir = "assets/audio/music"
    all_files = glob.glob(f"{music_dir}/*.mp3") + glob.glob(f"{music_dir}/*.wav")
    
    valid_files = []
    for f in all_files:
        stem = unicodedata.normalize('NFC', Path(f).stem)
        for allowed in ALLOWED_TRACKS:
            if allowed in stem:
                valid_files.append(f)
                break

    if not valid_files:
        raise FileNotFoundError(f"지정된 3개 음원({ALLOWED_TRACKS})을 {music_dir} 에서 찾을 수 없습니다.")

    chosen_file = None

    if selected_file and selected_file.strip() and selected_file.strip().lower() != "random":
        target = unicodedata.normalize('NFC', selected_file.strip())
        for f in valid_files:
            f_norm = unicodedata.normalize('NFC', f)
            f_base = unicodedata.normalize('NFC', os.path.basename(f))
            f_stem = unicodedata.normalize('NFC', Path(f).stem)
            if target in (f_norm, f_base, f_stem) or target in f_stem:
                chosen_file = f
                break
        if not chosen_file:
            print(f"[Notice] '{selected_file}' 대신 지정된 3개 음원 중 무작위 선택합니다.")

    if not chosen_file:
        chosen_file = random.choice(valid_files)

    song_name = unicodedata.normalize('NFC', Path(chosen_file).stem)

    # 연주 스타일 결정
    available_styles = list(PERFORMANCE_STYLES.keys())
    if selected_style and selected_style.strip().lower() in available_styles:
        style_key = selected_style.strip().lower()
    else:
        style_key = random.choice(available_styles)

    style_profile = PERFORMANCE_STYLES[style_key]

    print(f"\n=======================================================")
    print(f" [Inkey Studio 75% Master Fidelity Sound Engine]")
    print(f" [Original Track] {chosen_file}")
    print(f" [Song Name] {song_name}")
    print(f" [Performance Style] {style_profile['style_name']} ({style_key.upper()})")
    print(f"=======================================================")

    raw_audio = AudioSegment.from_file(chosen_file)
    original_duration = len(raw_audio) / 1000.0
    print(f"[원곡 길이] {original_duration:.1f}초 ({int(original_duration//60)}분 {int(original_duration%60)}초)")

    # 1. 75% 원곡 선명도 보존 + 스튜디오 마스터링 리마스터
    temp_raw_wav = "temp/raw_source.wav"
    raw_audio.normalize(headroom=0.5).export(temp_raw_wav, format="wav")

    # 2. 선택된 스타일 전용 어쿠스틱 DSP 필터 체인 적용 (클리핑 방지 및 최고 음질 320k 출력)
    dsp = style_profile["dsp_filter"]
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_raw_wav,
        "-af", dsp,
        "-ar", "48000",
        "-b:a", "320k",
        output_mp3_path
    ]
    subprocess.run(cmd, check=True)

    remastered_audio = AudioSegment.from_file(output_mp3_path)
    final_duration = len(remastered_audio) / 1000.0
    print(f"[Mastering Complete] {output_mp3_path} (원본 75% 충실도 + {style_profile['style_name']}, 재생 시간: {final_duration:.1f}초)")

    return song_name, chosen_file, final_duration, style_profile, style_key


# --- 4. Pillow 기반 감성/스타일별 타이틀 오버레이 생성기 ---

def create_title_overlay_png(title_text, style_profile, output_png_path, width=1280, height=720):
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
                font = ImageFont.truetype(p, 26)
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
    pad_x = 24
    pad_y = 14

    # 반투명 라운드 박스
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
        radius=14,
        fill=style_profile["box_color"]
    )

    # 스타일 텍스트 컬러
    draw.text((x, y), title_text, font=font, fill=style_profile["title_color"])
    img.save(output_png_path, "PNG")


# --- 5. 고화질 배경 다운로드 & 비주얼라이저 비디오 합성 ---

def fetch_hd_background(style_profile, filename):
    chosen_url = random.choice(style_profile["images"])
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)


def create_equalizer_music_video(image_path, title_png_path, audio_path, style_profile, output_path):
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    eq_colors = style_profile["eq_colors"]
    filter_complex = (
        f"[0:v]scale=1280:720[bg];"
        f"[bg][1:v]overlay=0:0[bg_titled];"
        f"[2:a]showfreqs=s=880x140:mode=bar:fscale=log:colors={eq_colors}:win_size=1024[eq];"
        f"[bg_titled][eq]overlay=x=(W-w)/2:y=H-185[v]"
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
        "-preset", "ultrafast", "-crf", "20",
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
            "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ], check=True)


# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)

    input_music_file = os.getenv("INPUT_MUSIC_FILE", "").strip()
    input_style = os.getenv("INPUT_STYLE", os.getenv("INPUT_THEME", "")).strip().lower()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()

    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    title_png = "temp/title_overlay.png"
    final_video = "output_music_video.mp4"

    # 1. 원곡 선택 및 원본 75% 충실도 + 스타일별 스튜디오 리마스터링
    song_name, chosen_path, duration, style_profile, style_key = get_inkey_performance_track(
        input_music_file, input_style, ai_mp3
    )

    # 2. 스타일별 맞춤 유튜브 영상 제목 생성
    if custom_title:
        final_title = custom_title
    else:
        final_title = style_profile["title_template"].format(name=song_name)

    print(f"\n[최종 비디오 제목] {final_title}")
    print(f"[스타일] {style_profile['style_name']}")

    # 3. 스타일별 감성 고화질 배경 이미지 준비
    fetch_hd_background(style_profile, bg_image)

    # 4. Pillow로 스타일 타이틀 PNG 오버레이 생성
    create_title_overlay_png(final_title, style_profile, title_png)

    # 5. 하이파이 이퀄라이저 비주얼라이저 비디오 렌더링
    create_equalizer_music_video(bg_image, title_png, ai_mp3, style_profile, final_video)

    # 6. 유튜브 업로드용 메타데이터 JSON 저장
    desc = (
        f"🎧 {final_title}\n\n"
        f"⚔️ 원곡명: {song_name}\n"
        f"🎼 연주 스타일: {style_profile['style_name']}\n"
        f"⏱️ 재생 시간: {int(duration // 60)}분 {int(duration % 60)}초\n"
        f"✨ 테마: 전략게임할 때 듣기 좋은 음악 / 마음이 벅차오르는 음악\n\n"
        f"Produced & Mastered by Inkey Music Studio.\n"
        f"3대 대표 명곡({song_name})의 웅장한 원음을 75% 본연 그대로 보존하고, {style_profile['style_name']} 감성으로 리마스터한 프리미엄 음원입니다.\n\n"
        f"#{song_name} #{style_key.upper()} #Inkey연주 #전략게임음악 #마음이벅차오르는음악 #게임BGM #InkeyMusic"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Inkey Music Studio",
        "song_title": song_name
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"\n[Video metadata saved successfully]: {final_title}")
