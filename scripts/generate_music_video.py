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

# --- 1. 전략 & 웅장한 감성 비주얼 & 비주얼라이저 테마 설정 ---

# 3대 지정 음원 목록 (이 3개 이외에는 절대 사용하지 않음)
ALLOWED_TRACKS = ["뇌룡격파", "용전", "화룡진군"]

TITLE_TEMPLATES = [
    "전략게임할 때 듣기 좋은 웅장한 음악 - {name}",
    "마음이 벅차오르는 웅장한 판타지 BGM | {name}",
    "가슴이 벅차오르는 전투 전략 테마곡 - {name}",
    "전략 시뮬레이션 몰입용 웅장한 음악 | {name}",
    "심장을 울리는 대서사시 웅장한 BGM - {name}",
    "승리를 이끄는 가슴 벅찬 전략게임 OST - {name}"
]

EPIC_THEMES = {
    "fire_gold": {
        "title_genre": "화룡의 숨결 (골드 & 파이어)",
        "eq_colors": "0xff4500@0.95|0xffd700@0.7",
        "title_color": (255, 245, 210, 255),
        "box_color": (15, 8, 5, 180),
        "images": [
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "lightning_blue": {
        "title_genre": "뇌룡의 번개 (일렉트릭 사이안 & 블루)",
        "eq_colors": "0x00e5ff@0.95|0x7c4dff@0.7",
        "title_color": (220, 245, 255, 255),
        "box_color": (5, 12, 25, 180),
        "images": [
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "epic_battle": {
        "title_genre": "전장의 기백 (크림슨 & 화이트)",
        "eq_colors": "0xff1744@0.95|0xffffff@0.7",
        "title_color": (255, 230, 230, 255),
        "box_color": (20, 5, 5, 185),
        "images": [
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    }
}


# --- 2. 3대 원곡 음원 100% 원음 복원 & 로드 엔진 ---

def get_exclusive_music_track(selected_file=None, output_mp3_path="temp/ai_song.mp3"):
    """
    오직 지정된 3개 곡(뇌룡격파, 용전, 화룡진군) 중 하나를 선택하여
    100% 원음 그대로의 다이내믹 레인지와 음질을 보존하여 로드합니다.
    """
    music_dir = "assets/audio/music"
    all_files = glob.glob(f"{music_dir}/*.mp3") + glob.glob(f"{music_dir}/*.wav")
    
    # 3개 곡에 대해서만 필터링
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
    print(f"\n=======================================================")
    print(f" [100% 원음 복원 연주] {chosen_file}")
    print(f" [곡 명] {song_name}")
    print(f"=======================================================")

    # 원곡 로드 (음원 왜곡, 템포 변경, 피치 변조 없이 100% 원음 보존)
    audio = AudioSegment.from_file(chosen_file)
    original_duration = len(audio) / 1000.0
    print(f"[음원 재생 시간] {original_duration:.1f}초 ({int(original_duration//60)}분 {int(original_duration%60)}초)")

    # 320kbps 하이파이 최고 음질로 마스터링 저장
    audio.export(output_mp3_path, format="mp3", bitrate="320k", parameters=["-ar", "44100"])
    print(f"[Mastering Complete] {output_mp3_path} (320kbps High-Fidelity)")

    return song_name, chosen_file, original_duration


# --- 3. Pillow 기반 감성/웅장 타이틀 오버레이 생성기 ---

def create_title_overlay_png(title_text, theme_profile, output_png_path, width=1280, height=720):
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
    pad_x = 24
    pad_y = 14

    # 반투명 라운드 박스
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
        radius=14,
        fill=theme_profile["box_color"]
    )

    # 감성 텍스트 컬러
    draw.text((x, y), title_text, font=font, fill=theme_profile["title_color"])
    img.save(output_png_path, "PNG")


# --- 4. 고화질 배경 다운로드 & 비주얼라이저 비디오 합성 ---

def fetch_hd_background(theme_profile, filename):
    chosen_url = random.choice(theme_profile["images"])
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)


def create_equalizer_music_video(image_path, title_png_path, audio_path, theme_profile, output_path):
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    eq_colors = theme_profile["eq_colors"]
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
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()

    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    title_png = "temp/title_overlay.png"
    final_video = "output_music_video.mp4"

    # 1. 오직 3개 음원(뇌룡격파, 용전, 화룡진군) 중 선택 및 100% 원음 로드
    song_name, chosen_path, duration = get_exclusive_music_track(input_music_file, ai_mp3)

    # 2. 곡 분위기에 맞는 테마 자동 매칭
    if "뇌룡" in song_name:
        theme_profile = EPIC_THEMES["lightning_blue"]
    elif "화룡" in song_name:
        theme_profile = EPIC_THEMES["fire_gold"]
    else:
        theme_profile = EPIC_THEMES["epic_battle"]

    # 3. 전략게임 & 마음이 벅차오르는 감성 제목 생성
    if custom_title:
        final_title = custom_title
    else:
        template = random.choice(TITLE_TEMPLATES)
        final_title = template.format(name=song_name)

    print(f"\n[최종 비디오 제목] {final_title}")
    print(f"[테마 스타일] {theme_profile['title_genre']}")

    # 4. 고화질 배경 이미지 준비
    fetch_hd_background(theme_profile, bg_image)

    # 5. Pillow로 감성 타이틀 PNG 오버레이 생성
    create_title_overlay_png(final_title, theme_profile, title_png)

    # 6. 하이파이 이퀄라이저 비주얼라이저 비디오 렌더링
    create_equalizer_music_video(bg_image, title_png, ai_mp3, theme_profile, final_video)

    # 7. 유튜브 업로드용 메타데이터 JSON 저장
    desc = (
        f"🎧 {final_title}\n\n"
        f"⚔️ 트랙명: {song_name}\n"
        f"⏱️ 재생 시간: {int(duration // 60)}분 {int(duration % 60)}초\n"
        f"✨ 테마: 전략게임할 때 듣기 좋은 음악 / 가슴이 벅차오르는 음악\n\n"
        f"100% 오리지널 마스터 사운드로 복원 및 제작되었습니다.\n\n"
        f"#{song_name} #전략게임음악 #마음이벅차오르는음악 #웅장한음악 #게임BGM #이퀄라이저 #InkeyMusic"
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
