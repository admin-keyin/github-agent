"""
'고스타그램', '꿈꾸던 어른이 되었나요' 스타일의 감성 AI 뮤직 비디오 생성 파이프라인.
Suno AI API (Kie.ai, SunoApi.org, Apiframe, Cookie) 연동을 우선으로 하며,
음원 생성 -> 감성 비주얼 배경 및 가사 타이포그래피 생성 -> 비주얼라이저 합성 -> 유튜브 메타데이터 생성까지 자동 수행합니다.
"""

import os
import sys
import json
import random
import requests
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scripts.suno_api_client import SunoMusicGenerator
    from scripts.lyric_engine import generate_lyric_and_style
    from scripts.audio_mixer_engine import create_standalone_studio_track
except ImportError:
    from suno_api_client import SunoMusicGenerator
    from lyric_engine import generate_lyric_and_style
    from audio_mixer_engine import create_standalone_studio_track

BACKGROUND_IMAGES = [
    # 감성 새벽 밤하늘 / 도시 야경 / 방 안의 감성
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1920&h=1080&q=90",
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
    "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90",
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
    "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1920&h=1080&q=90"
]

def fetch_background_image(output_path: str):
    url = random.choice(BACKGROUND_IMAGES)
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return
    except Exception as e:
        print(f"Background fetch fallback: {e}")
    # 폴백 이미지 생성
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x0d1117:s=1280x720:d=1", "-vframes", "1", output_path], check=True)


def create_lyric_title_overlay(title: str, subtitle: str, output_path: str, width=1280, height=720):
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
    font_title = None
    font_sub = None
    for p in font_paths:
        if os.path.exists(p):
            try:
                font_title = ImageFont.truetype(p, 32)
                font_sub = ImageFont.truetype(p, 18)
                break
            except Exception:
                pass

    if not font_title:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    w_t = bbox_t[2] - bbox_t[0]
    h_t = bbox_t[3] - bbox_t[1]

    bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
    w_s = bbox_s[2] - bbox_s[0]

    max_w = max(w_t, w_s)
    x = (width - max_w) // 2
    y = 60

    # 반투명 배경 카드 박스
    draw.rounded_rectangle(
        [x - 30, y - 16, x + max_w + 30, y + h_t + 40],
        radius=16,
        fill=(10, 15, 25, 200),
        outline=(255, 255, 255, 40),
        width=1
    )

    # 텍스트 그리기
    draw.text(((width - w_t) // 2, y), title, font=font_title, fill=(255, 255, 255, 255))
    draw.text(((width - w_s) // 2, y + h_t + 10), subtitle, font=font_sub, fill=(180, 210, 255, 230))

    img.save(output_path, "PNG")


def render_music_video(image_path: str, overlay_png: str, audio_path: str, output_path: str):
    audio = AudioSegment.from_file(audio_path)
    duration = len(audio) / 1000.0

    # 파스텔 시안 & 핑크 감성 이퀄라이저 비주얼라이저 (16:9 가로형 풀버전)
    filter_complex = (
        f"[0:v]scale=1280:720[bg];"
        f"[bg][1:v]overlay=0:0[bg_titled];"
        f"[2:a]showfreqs=s=920x150:mode=bar:fscale=log:colors=0x00ffee@0.95|0xff66cc@0.7:win_size=1024[eq];"
        f"[bg_titled][eq]overlay=x=(W-w)/2:y=H-180[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", overlay_png,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[Render Success] 풀버전 영상 완료: {output_path} (길이: {duration:.1f}초)")


def render_shorts_video(image_path: str, title: str, audio_path: str, output_path: str, shorts_duration=45.0):
    """
    곡의 가장 에너지 넘치는 하이라이트(싸비/클라이맥스) 45초를 자동 추출하여
    9:16 (1080x1920) 세로형 유튜브 쇼츠(Shorts) 영상을 렌더링합니다.
    """
    audio = AudioSegment.from_file(audio_path)
    total_sec = len(audio) / 1000.0

    # 하이라이트 구간 시작점 계산 (보통 1분 지점부터 하이라이트)
    if total_sec > shorts_duration + 20:
        start_sec = 40.0 # 40초~85초 하이라이트
    elif total_sec > shorts_duration:
        start_sec = max(0.0, (total_sec - shorts_duration) / 2.0)
    else:
        start_sec = 0.0
        shorts_duration = total_sec

    # 하이라이트 오디오 슬라이스 및 페이드 인/아웃
    highlight_audio = audio[int(start_sec * 1000):int((start_sec + shorts_duration) * 1000)]
    highlight_audio = highlight_audio.fade_in(1000).fade_out(1500)
    temp_shorts_audio = "temp/shorts_highlight.mp3"
    highlight_audio.export(temp_shorts_audio, format="mp3", bitrate="320k")

    # 9:16 쇼츠용 세로 타이틀 카드 생성 (1080x1920)
    shorts_overlay_png = "temp/shorts_overlay.png"
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc"
    ]
    font_main = None
    font_sub = None
    for p in font_paths:
        if os.path.exists(p):
            try:
                font_main = ImageFont.truetype(p, 48)
                font_sub = ImageFont.truetype(p, 28)
                break
            except Exception:
                pass

    if not font_main:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    sub_text = "Inkey Studio Highlight #Shorts"
    bbox_m = draw.textbbox((0, 0), title, font=font_main)
    w_m = bbox_m[2] - bbox_m[0]
    h_m = bbox_m[3] - bbox_m[1]

    bbox_s = draw.textbbox((0, 0), sub_text, font=font_sub)
    w_s = bbox_s[2] - bbox_s[0]

    max_w = max(w_m, w_s)
    x = (1080 - max_w) // 2
    y = 380

    # 세로형 반투명 카드
    draw.rounded_rectangle(
        [x - 40, y - 20, x + max_w + 40, y + h_m + 60],
        radius=20,
        fill=(10, 15, 25, 210),
        outline=(255, 255, 255, 60),
        width=2
    )
    draw.text(((1080 - w_m) // 2, y), title, font=font_main, fill=(255, 255, 255, 255))
    draw.text(((1080 - w_s) // 2, y + h_m + 16), sub_text, font=font_sub, fill=(180, 220, 255, 240))
    img.save(shorts_overlay_png, "PNG")

    # 9:16 세로 렌더링 + 중앙 센터 비주얼라이저
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[bg][1:v]overlay=0:0[bg_titled];"
        f"[2:a]showfreqs=s=880x200:mode=bar:fscale=log:colors=0x00ffee@0.95|0xff66cc@0.75:win_size=1024[eq];"
        f"[bg_titled][eq]overlay=x=(W-w)/2:y=H-450[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", shorts_overlay_png,
        "-i", temp_shorts_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-t", str(shorts_duration),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[Shorts Render Success] 9:16 쇼츠 하이라이트 영상 완료: {output_path} ({shorts_duration:.1f}초)")


def main():
    os.makedirs("temp", exist_ok=True)

    song_type = os.getenv("INPUT_SONG_TYPE", "random").strip().lower()
    if not song_type or song_type == "":
        song_type = "random"
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    instrumental = os.getenv("INPUT_INSTRUMENTAL", "false").lower() == "true"

    print("\n" + "="*65)
    print(" [Inkey Studio - Suno AI Storytelling Song Generator]")
    print(f" [Song Theme] {song_type}")
    print(f" [Custom Prompt] {custom_prompt or 'None (Using Preset)'}")
    print("="*65 + "\n")

    # 1. 감성 가사 및 스타일 태그 생성
    title, style_tags, lyrics = generate_lyric_and_style(song_type, custom_prompt)
    print(f"[곡 제목] {title}")
    print(f"[음악 스타일 태그]\n{style_tags}\n")
    print(f"[작사된 가사]\n{lyrics[:300]}...\n")

    audio_path = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    title_png = "temp/title_overlay.png"
    output_video = "output_music_video.mp4"

    # 2. 음원 생성 (Kie.ai Suno V6 클라우드 AI 엔진 호출)
    suno_client = SunoMusicGenerator()

    if not suno_client.has_any_api_key():
        raise RuntimeError("KIE_API_KEY 또는 SUNO_API_KEY 가 설정되지 않았습니다. Suno AI 음원을 생성할 수 없습니다.")

    print("[INFO] 등록된 Suno API 토큰으로 100% 순수 AI 신곡 음원 생성을 시작합니다...")
    result = suno_client.generate_music(
        title=title,
        style=style_tags,
        lyrics=lyrics,
        output_audio_path=audio_path,
        instrumental=instrumental
    )
    print(f"[Suno Complete] {result['provider']} 로부터 고음질 AI 오리지널 트랙 생성 완료!")

    # 3. 비주얼 배경 및 타이포그래피 생성
    fetch_background_image(bg_image)
    subtitle = f"Inkey Story Track | Style: {style_tags[:45]}..."
    create_lyric_title_overlay(title, subtitle, title_png)

    # 4. 풀버전 16:9 비디오 렌더링
    render_music_video(bg_image, title_png, audio_path, output_video)

    # 4-2. 9:16 세로형 쇼츠 하이라이트 영상 렌더링 (45초)
    output_shorts = "output_shorts_video.mp4"
    render_shorts_video(bg_image, title, audio_path, output_shorts, shorts_duration=45.0)

    # 5. 유튜브 업로드용 메타데이터 저장 (풀버전용)
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    youtube_title = f"{title} - Inkey Studio"
    desc = (
        f"🎧 {youtube_title}\n\n"
        f"🎼 트랙 정보\n"
        f"• 곡명: {title}\n"
        f"• 스타일: {style_tags}\n"
        f"• 프로듀싱: Inkey Studio\n"
        f"• 재생 시간: {int(duration_sec // 60)}분 {int(duration_sec % 60)}초\n\n"
        f"📝 가사 (Lyrics)\n"
        f"----------------------------------------\n"
        f"{lyrics}\n"
        f"----------------------------------------\n\n"
        f"✨ Collaboration:\n"
        f"본 음원은 음악 협업도구 KIE와 함께 제작되었습니다.\n"
        f"🔗 KIE 바로가기: https://kie.ai?ref=a75838b6fecc53ef2774b5279d142d11\n\n"
        f"일상 속 따뜻한 위로와 감성을 전하는 Inkey Studio의 오리지널 음악입니다.\n\n"
        f"#InkeyMusic #InkeyStudio #인디발라드 #새벽감성 #KPOP #오리지널트랙 #힐링음악 #KIE"
    )

    meta_info = {
        "title": youtube_title[:100],
        "description": desc,
        "artist": "Inkey Studio",
        "song_title": title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)

    # 5-2. 유튜브 쇼츠용 메타데이터 저장
    shorts_title = f"{title} (Highlight) #Shorts"
    shorts_desc = (
        f"🎧 {title} - Inkey Studio Highlight\n\n"
        f"풀버전 음원은 채널에서 감상하실 수 있습니다.\n\n"
        f"✨ 음악 협업도구 KIE: https://kie.ai?ref=a75838b6fecc53ef2774b5279d142d11\n\n"
        f"#Shorts #InkeyStudio #InkeyMusic #하이라이트 #신곡 #노래추천 #킬링파트 #KIE"
    )
    shorts_meta_info = {
        "title": shorts_title[:100],
        "description": shorts_desc,
        "artist": "Inkey Studio",
        "song_title": title
    }
    with open("temp/video_info_shorts.json", "w", encoding="utf-8") as f:
        json.dump(shorts_meta_info, f, ensure_ascii=False, indent=2)

    print("\n[Complete] 풀버전 영상 및 9:16 쇼츠 하이라이트 영상 제작이 모두 완료되었습니다!")


if __name__ == "__main__":
    main()
