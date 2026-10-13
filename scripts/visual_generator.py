"""
Inkey Studio - 고품격 멀티 씬 애니메이션 비주얼 & 키네틱 가사 렌더링 엔진.
- 가사 전개(Intro -> Verse -> Chorus -> Bridge -> Outro) 맞춤형 멀티 씬 AI 애니메이션 생성
- 씬 간 부드러운 디졸브(Crossfade Dissolve) 트랜지션 합성
- 프로급 유튜브 썸네일 (16:9 가로 & 9:16 세로) 자동 그래픽 합성
- 가사 타임라인 파싱 및 팝업/페이드 키네틱 타이포그래피 애니메이션
- 시네마틱 비네팅/색감 보정 & 네온 오디오 비주얼라이저 결합
"""

import os
import re
import json
import math
import time
import random
import urllib.parse
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydub import AudioSegment

# ----------------------------------------------------------------------
# 폰트 로더 유틸리티
# ----------------------------------------------------------------------
def get_korean_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/NanumGothic.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ----------------------------------------------------------------------
# 1. 고품질 AI 일러스트 배경 생성기 (단일 및 멀티 씬)
# ----------------------------------------------------------------------

HIGH_QUALITY_BACKUP_IMAGES = {
    "changpop": [
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1920&h=1080&q=90"
    ],
    "indie_band": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90"
    ],
    "healing_ballad": [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90"
    ],
    "general": [
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90"
    ]
}

def generate_artwork(image_prompt: str, output_path: str, width: int = 1280, height: int = 720, song_type: str = "indie_band", seed: int = None) -> bool:
    """
    곡 프롬프트에 최적화된 고화질 감성 애니메이션 일러스트 이미지를 다운로드하거나 폴백 이미지를 확보합니다.
    """
    enhanced_prompt = (
        f"{image_prompt}, masterpiece, anime aesthetic, high quality, cinematic lighting, "
        f"Makoto Shinkai wallpaper style, 4k resolution, beautiful composition, rich details, no watermark, no text"
    )
    if seed is None:
        seed = random.randint(1000, 999999)
    encoded = urllib.parse.quote(enhanced_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        if r.status_code == 200 and len(r.content) > 15000:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"[Visual Engine Warn] AI 생성 일시적 실패/타임아웃 ({output_path}): {e}")

    # 폴백: 장르별 고화질 감성 사진 풀에서 가져오기
    cat_key = song_type if song_type in HIGH_QUALITY_BACKUP_IMAGES else "general"
    backup_urls = HIGH_QUALITY_BACKUP_IMAGES[cat_key]
    backup_url = random.choice(backup_urls)
    try:
        r = requests.get(backup_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"[Visual Engine Warn] 폴백 이미지 다운로드 실패: {e}")

    # 최후의 수단: ffmpeg 컬러 배경
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x0f1424:s={width}x{height}:d=1",
        "-vframes", "1", output_path
    ], check=True)
    return True


def generate_multi_scene_artworks(scene_prompts: list, output_dir: str, width: int = 1280, height: int = 720, song_type: str = "indie_band", is_shorts: bool = False) -> list:
    """
    가사 기승전결 서사에 맞춘 4~5개의 멀티 씬 애니메이션 이미지를 생성하여 파일 경로 리스트를 반환합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    scene_paths = []
    prefix = "shorts_scene" if is_shorts else "scene"

    print(f"\n[Multi-Scene Engine] 가사 흐름 맞춤형 멀티 씬 애니메이션 {len(scene_prompts)}컷 생성 중 ({'Shorts 9:16' if is_shorts else 'Full 16:9'})...")

    for idx, prompt in enumerate(scene_prompts):
        scene_file = os.path.join(output_dir, f"{prefix}_{idx}.jpg")
        print(f" - Scene {idx+1}/{len(scene_prompts)}: {prompt[:65]}...")
        generate_artwork(
            image_prompt=prompt,
            output_path=scene_file,
            width=width,
            height=height,
            song_type=song_type,
            seed=random.randint(10000, 999999) + idx * 777
        )
        scene_paths.append(scene_file)

    print(f"[Multi-Scene Success] 총 {len(scene_paths)}개 멀티 씬 아트웍 생성 완료!\n")
    return scene_paths


# ----------------------------------------------------------------------
# 2. 멀티 씬 디졸브(Crossfade Dissolve) 트랜지션 비디오 스트림 빌더
# ----------------------------------------------------------------------
def build_multi_scene_concat(
    scene_image_paths: list,
    scene_durations: list,
    output_dir: str,
    width: int = 1280,
    height: int = 720,
    transition_dur: float = 0.8,
    is_shorts: bool = False
) -> str:
    """
    여러 개의 씬 이미지를 받아, 씬 간에 부드러운 디졸브(Crossfade) 트랜지션 프레임을 생성하고
    FFmpeg concat demuxer 파일(bg_scenes_concat.txt) 경로를 반환합니다.
    """
    trans_dir = os.path.join(output_dir, "trans_frames_shorts" if is_shorts else "trans_frames_full")
    os.makedirs(trans_dir, exist_ok=True)
    concat_file_path = os.path.join(output_dir, "shorts_bg_concat.txt" if is_shorts else "full_bg_concat.txt")

    concat_lines = ["ffconcat version 1.0\n"]
    num_scenes = len(scene_image_paths)

    # 1. 모든 씬 이미지를 목표 해상도(width x height)에 맞게 비율 유지 중앙 크롭 및 정규화
    norm_scene_paths = []
    for i, p in enumerate(scene_image_paths):
        norm_p = os.path.join(trans_dir, f"norm_scene_{i}.jpg")
        try:
            with Image.open(p) as img_raw:
                img_conv = img_raw.convert("RGB")
                w_raw, h_raw = img_conv.size
                target_ratio = width / height
                raw_ratio = w_raw / h_raw
                if raw_ratio > target_ratio:
                    new_w = int(h_raw * target_ratio)
                    left = (w_raw - new_w) // 2
                    img_cropped = img_conv.crop((left, 0, left + new_w, h_raw))
                else:
                    new_h = int(w_raw / target_ratio)
                    top = (h_raw - new_h) // 2
                    img_cropped = img_conv.crop((0, top, w_raw, top + new_h))
                img_resized = img_cropped.resize((width, height), Image.Resampling.LANCZOS)
                img_resized.save(norm_p, "JPEG", quality=92)
                norm_scene_paths.append(norm_p)
        except Exception as e:
            print(f"[Multi-Scene Warn] 정규화 실패 ({p}): {e}")
            norm_scene_paths.append(p)

    for i in range(num_scenes):
        current_img_path = norm_scene_paths[i]
        dur = scene_durations[i] if i < len(scene_durations) else 30.0

        if i < num_scenes - 1:
            # 다음 씬으로 전환되는 경우: 디졸브 트랜지션 생성
            main_dur = max(1.0, dur - transition_dur)
            concat_lines.append(f"file {os.path.abspath(current_img_path)}\nduration {main_dur:.2f}\n")

            # Image.blend로 부드러운 4단계 디졸브 블렌딩 프레임 생성
            try:
                img_curr = Image.open(current_img_path)
                img_next = Image.open(norm_scene_paths[i+1])

                step_dur = transition_dur / 4.0
                for step_idx, alpha in enumerate([0.25, 0.50, 0.75, 0.90]):
                    blended = Image.blend(img_curr, img_next, alpha)
                    trans_file = os.path.join(trans_dir, f"trans_{i}_to_{i+1}_step_{step_idx}.jpg")
                    blended.save(trans_file, "JPEG", quality=90)
                    concat_lines.append(f"file {os.path.abspath(trans_file)}\nduration {step_dur:.2f}\n")
            except Exception as e:
                print(f"[Multi-Scene Warn] 블렌딩 중 예외: {e}")
                concat_lines.append(f"file {os.path.abspath(current_img_path)}\nduration {transition_dur:.2f}\n")
        else:
            # 마지막 씬
            concat_lines.append(f"file {os.path.abspath(current_img_path)}\nduration {dur:.2f}\n")

    # concat demuxer 마지막 더미 프레임
    concat_lines.append(f"file {os.path.abspath(norm_scene_paths[-1])}\n")

    with open(concat_file_path, "w", encoding="utf-8") as f:
        f.writelines(concat_lines)

    print(f"[Multi-Scene Success] 부드러운 디졸브 멀티 씬 타임라인 생성 완료: {concat_file_path}")
    return concat_file_path


def calculate_scene_durations(total_duration: float, num_scenes: int, is_shorts: bool = False, shorts_duration: float = 45.0) -> list:
    """
    가사 서사의 흐름에 맞추어 각 씬의 최적 지속 시간(초)을 배분합니다.
    """
    if is_shorts:
        # 숏츠: 45초 동안 3개 씬 (빌드업 12초 -> 클라이맥스 21초 -> 피날레 12초)
        if num_scenes == 3:
            return [12.0, 21.0, 12.0]
        elif num_scenes == 2:
            return [18.0, 27.0]
        else:
            step = shorts_duration / num_scenes
            return [round(step, 1)] * num_scenes

    # 풀버전 (16:9): 기승전결 5단 서사 배분
    # Intro(약 10%), Verse 1(약 22%), Chorus(약 28%), Verse 2/Bridge(약 22%), Outro(약 18%)
    if num_scenes == 5:
        dur_intro = round(total_duration * 0.10, 1)
        dur_verse1 = round(total_duration * 0.22, 1)
        dur_chorus = round(total_duration * 0.28, 1)
        dur_bridge = round(total_duration * 0.22, 1)
        dur_outro = round(total_duration - (dur_intro + dur_verse1 + dur_chorus + dur_bridge), 1)
        return [dur_intro, dur_verse1, dur_chorus, dur_bridge, max(5.0, dur_outro)]
    else:
        step = total_duration / num_scenes
        durs = [round(step, 1)] * (num_scenes - 1)
        rem = round(total_duration - sum(durs), 1)
        durs.append(max(5.0, rem))
        return durs


# ----------------------------------------------------------------------
# 3. 프로페셔널 유튜브 썸네일 생성기 (16:9 및 9:16)
# ----------------------------------------------------------------------
def create_professional_thumbnail(
    bg_image_path: str,
    title: str,
    subtitle: str,
    genre_name: str,
    output_path: str,
    width: int = 1280,
    height: int = 720,
    is_shorts: bool = False
):
    """
    유튜브 시청자의 시선을 사로잡는 최상급 퀄리티의 썸네일을 렌더링합니다.
    - 배경 블러 & 다크 시네마틱 비네팅
    - 대형 볼드 타이포그래피 + 엠보싱/네온 글로우 + 드롭 섀도우
    - 감성 카피라이트 문구 & 트랙 배지
    - 오디오 플레이어 UI 모티브
    """
    if os.path.exists(bg_image_path):
        base_img = Image.open(bg_image_path).convert("RGBA")
        base_img = base_img.resize((width, height), Image.Resampling.LANCZOS)
    else:
        base_img = Image.new("RGBA", (width, height), (15, 20, 35, 255))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_overlay = ImageDraw.Draw(overlay)

    if not is_shorts:
        # 16:9 가로 썸네일
        for y in range(height):
            ratio = max(0.0, (y - height * 0.45) / (height * 0.55))
            alpha = int(220 * (ratio ** 1.3))
            d_overlay.line([(0, y), (width, y)], fill=(5, 8, 18, alpha))
        
        d_overlay.rectangle([0, 0, width, height], fill=(0, 0, 0, 40))
        img = Image.alpha_composite(base_img, overlay)
        draw = ImageDraw.Draw(img)

        font_title = get_korean_font(58, bold=True)
        font_sub = get_korean_font(24, bold=False)
        font_badge = get_korean_font(18, bold=True)

        # 상단 좌측: 배지
        badge_text = f"★ ORIGINAL MV • {genre_name.upper()}"
        bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
        bw = bbox_b[2] - bbox_b[0]
        bh = bbox_b[3] - bbox_b[1]
        bx, by = 60, 50
        draw.rounded_rectangle(
            [bx - 14, by - 8, bx + bw + 14, by + bh + 8],
            radius=8,
            fill=(255, 45, 85, 230),
            outline=(255, 255, 255, 120),
            width=1
        )
        draw.text((bx, by), badge_text, font=font_badge, fill=(255, 255, 255, 255))

        # 메인 타이틀
        tx = 60
        ty = height - 230

        glow_color = (0, 230, 255, 140)
        for offset_x, offset_y in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
            draw.text((tx + offset_x, ty + offset_y), title, font=font_title, fill=glow_color)
        
        for shadow_dist in range(4, 9, 2):
            draw.text((tx + shadow_dist, ty + shadow_dist), title, font=font_title, fill=(0, 0, 0, 240))
        
        draw.text((tx, ty), title, font=font_title, fill=(255, 255, 255, 255))

        # 서브타이틀
        sy = ty + 75
        sub_display = f"🎧 Inkey Studio | {subtitle}"
        draw.text((tx + 2, sy + 2), sub_display, font=font_sub, fill=(0, 0, 0, 200))
        draw.text((tx, sy), sub_display, font=font_sub, fill=(210, 235, 255, 240))

        # 하단 미니 오디오 플레이어 UI
        py = height - 55
        draw.rounded_rectangle([tx, py, tx + 400, py + 4], radius=2, fill=(255, 255, 255, 50))
        draw.rounded_rectangle([tx, py, tx + 180, py + 4], radius=2, fill=(0, 240, 255, 220))
        draw.ellipse([tx + 176, py - 4, tx + 188, py + 8], fill=(255, 255, 255, 255))
        draw.text((tx + 420, py - 8), "01:24 / 03:40", font=font_badge, fill=(180, 200, 230, 180))

    else:
        # 9:16 세로 숏츠 썸네일
        for y in range(height):
            dist_center = abs(y - height * 0.45) / (height * 0.5)
            alpha = int(140 + (1.0 - min(1.0, dist_center)) * 70)
            d_overlay.line([(0, y), (width, y)], fill=(10, 12, 20, alpha))
        
        img = Image.alpha_composite(base_img, overlay)
        draw = ImageDraw.Draw(img)

        font_shorts_badge = get_korean_font(32, bold=True)
        font_shorts_title = get_korean_font(74, bold=True)
        font_shorts_sub = get_korean_font(36, bold=False)

        # 상단 뱃지
        badge_text = "INKEY STUDIO ORIGINAL #SHORTS"
        bbox_sb = draw.textbbox((0, 0), badge_text, font=font_shorts_badge)
        sbw = bbox_sb[2] - bbox_sb[0]
        sbx = (width - sbw) // 2
        sby = 240
        draw.rounded_rectangle(
            [sbx - 20, sby - 10, sbx + sbw + 20, sby + 48],
            radius=12,
            fill=(255, 0, 80, 240),
            outline=(255, 255, 255, 150),
            width=2
        )
        draw.text((sbx, sby), badge_text, font=font_shorts_badge, fill=(255, 255, 255, 255))

        # 중앙 대형 타이틀
        bbox_st = draw.textbbox((0, 0), title, font=font_shorts_title)
        stw = bbox_st[2] - bbox_st[0]
        sth = bbox_st[3] - bbox_st[1]
        stx = (width - stw) // 2
        sty = (height - sth) // 2 - 80

        for ox in range(-4, 5, 2):
            for oy in range(-4, 5, 2):
                draw.text((stx + ox, sty + oy), title, font=font_shorts_title, fill=(0, 0, 0, 240))
        for ox in [-2, 2]:
            for oy in [-2, 2]:
                draw.text((stx + ox, sty + oy), title, font=font_shorts_title, fill=(0, 240, 255, 220))
        draw.text((stx, sty), title, font=font_shorts_title, fill=(255, 255, 255, 255))

        # 하단 서브
        sub_t = f"🎧 {subtitle}"
        bbox_sub = draw.textbbox((0, 0), sub_t, font=font_shorts_sub)
        subw = bbox_sub[2] - bbox_sub[0]
        subx = (width - subw) // 2
        suby = sty + sth + 50
        draw.text((subx + 2, suby + 2), sub_t, font=font_shorts_sub, fill=(0, 0, 0, 220))
        draw.text((subx, suby), sub_t, font=font_shorts_sub, fill=(255, 235, 120, 255))

    img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"[Thumbnail Success] 썸네일 생성 완료: {output_path} ({'Shorts 9:16' if is_shorts else 'Full 16:9'})")
    return True


# ----------------------------------------------------------------------
# 4. 가사 타임라인 파서 및 지능적 시간 동기화
# ----------------------------------------------------------------------
def parse_lyrics_timeline(lyrics_text: str, total_duration: float, is_shorts: bool = False, shorts_start: float = 40.0, shorts_duration: float = 45.0):
    """
    가사 텍스트를 분석하여 각 가사 라인의 (start_sec, end_sec, text, section) 타임라인을 계산합니다.
    """
    lines = lyrics_text.splitlines()
    sections = []
    current_section = "Intro"
    current_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        sec_match = re.match(r"^\[([A-Za-z0-9\s_\-:]+)\]", line)
        if sec_match:
            if current_lines:
                sections.append((current_section, current_lines))
                current_lines = []
            current_section = sec_match.group(1).split(":")[0].strip()
            continue
        if re.match(r"^\(.*\)$", line):
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines))

    if not sections:
        all_lines = [l.strip() for l in lines if l.strip() and not l.startswith("[")]
        sections = [("Song", all_lines)]

    timeline = []

    if is_shorts:
        chorus_lines = []
        for s_name, s_lines in sections:
            if "chorus" in s_name.lower() or "climax" in s_name.lower():
                chorus_lines.extend(s_lines)

        if not chorus_lines:
            all_l = []
            for _, sl in sections:
                all_l.extend(sl)
            mid = len(all_l) // 2
            chorus_lines = all_l[max(0, mid - 3):min(len(all_l), mid + 4)]

        n = max(1, len(chorus_lines))
        line_dur = shorts_duration / n
        t = 0.5
        for idx, line in enumerate(chorus_lines):
            st = t
            et = min(shorts_duration, t + line_dur)
            timeline.append({
                "start": round(st, 2),
                "end": round(et, 2),
                "duration": round(et - st, 2),
                "text": line,
                "section": "Chorus"
            })
            t = et
        return timeline

    # 풀버전 (16:9)
    intro_time = min(12.0, total_duration * 0.08)
    outro_time = min(10.0, total_duration * 0.06)
    effective_duration = max(30.0, total_duration - intro_time - outro_time)

    flattened = []
    for s_name, s_lines in sections:
        for l in s_lines:
            flattened.append((s_name, l))

    total_lines_count = len(flattened)
    if total_lines_count == 0:
        return []

    char_counts = [max(6, len(item[1])) for item in flattened]
    sum_chars = sum(char_counts)

    cur_time = intro_time
    for idx, (s_name, text) in enumerate(flattened):
        dur = (char_counts[idx] / sum_chars) * effective_duration
        dur = max(2.5, min(8.0, dur))
        st = cur_time
        et = cur_time + dur
        timeline.append({
            "start": round(st, 2),
            "end": round(et, 2),
            "duration": round(dur, 2),
            "text": text,
            "section": s_name
        })
        cur_time = et

    return timeline


# ----------------------------------------------------------------------
# 5. 키네틱 가사 애니메이션 프레임 & concat 디먹서 생성기
# ----------------------------------------------------------------------
def render_lyric_animation_assets(
    timeline: list,
    width: int,
    height: int,
    temp_dir: str,
    is_shorts: bool = False
) -> str:
    lyric_assets_dir = os.path.join(temp_dir, "lyric_assets_shorts" if is_shorts else "lyric_assets_full")
    os.makedirs(lyric_assets_dir, exist_ok=True)
    concat_txt_path = os.path.join(lyric_assets_dir, "concat.txt")

    concat_lines = ["ffconcat version 1.0\n"]

    empty_frame_path = os.path.join(lyric_assets_dir, "empty.png")
    empty_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    empty_img.save(empty_frame_path)

    first_start = timeline[0]["start"] if timeline else 0.0
    if first_start > 0.1:
        concat_lines.append(f"file empty.png\nduration {first_start:.2f}\n")

    last_time = first_start
    font_main = get_korean_font(64 if is_shorts else 38, bold=True)

    for i, item in enumerate(timeline):
        text = item["text"]
        start_t = item["start"]
        end_t = item["end"]
        dur = max(1.0, end_t - start_t)

        if start_t > last_time + 0.1:
            gap = start_t - last_time
            concat_lines.append(f"file empty.png\nduration {gap:.2f}\n")

        if is_shorts:
            # 숏츠: 팝업 바운스 키네틱 애니메이션
            t_in = min(0.12, dur * 0.15)
            t_out = min(0.12, dur * 0.15)
            t_main = dur - t_in - t_out

            frame_in = os.path.join(lyric_assets_dir, f"frame_{i}_in.png")
            frame_main = os.path.join(lyric_assets_dir, f"frame_{i}_main.png")
            frame_out = os.path.join(lyric_assets_dir, f"frame_{i}_out.png")

            img_main = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            d_main = ImageDraw.Draw(img_main)

            bbox = d_main.textbbox((0, 0), text, font=font_main)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            cx, cy = width // 2, height // 2 - 40

            card_pad_x, card_pad_y = 36, 22
            d_main.rounded_rectangle(
                [cx - tw // 2 - card_pad_x, cy - th // 2 - card_pad_y,
                 cx + tw // 2 + card_pad_x, cy + th // 2 + card_pad_y],
                radius=18,
                fill=(10, 15, 25, 210),
                outline=(0, 240, 255, 90),
                width=2
            )

            for ox in [-3, 0, 3]:
                for oy in [-3, 0, 3]:
                    d_main.text((cx, cy), text, font=font_main, fill=(0, 0, 0, 255), anchor="mm")
            highlight_color = (255, 240, 80, 255) if i % 2 == 1 else (255, 255, 255, 255)
            d_main.text((cx, cy), text, font=font_main, fill=highlight_color, anchor="mm")
            img_main.save(frame_main)

            # 바운스 인 (0.94 스케일)
            img_in = img_main.resize((int(width * 0.94), int(height * 0.94)), Image.Resampling.BILINEAR)
            canvas_in = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            canvas_in.paste(img_in, ((width - img_in.width) // 2, (height - img_in.height) // 2), img_in)
            canvas_in.save(frame_in)

            # 아웃 프레임
            canvas_out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            canvas_out.paste(img_main, (0, -12), img_main)
            canvas_out.putalpha(160)
            canvas_out.save(frame_out)

            concat_lines.append(f"file frame_{i}_in.png\nduration {t_in:.2f}\n")
            concat_lines.append(f"file frame_{i}_main.png\nduration {t_main:.2f}\n")
            concat_lines.append(f"file frame_{i}_out.png\nduration {t_out:.2f}\n")

        else:
            # 풀버전: 감성 글래스모피즘 페이드 인/아웃 리릭
            t_fade = min(0.3, dur * 0.15)
            t_hold = dur - (t_fade * 2)

            frame_fade_in = os.path.join(lyric_assets_dir, f"frame_{i}_fin.png")
            frame_hold = os.path.join(lyric_assets_dir, f"frame_{i}_hold.png")
            frame_fade_out = os.path.join(lyric_assets_dir, f"frame_{i}_fout.png")

            img_hold = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            d_hold = ImageDraw.Draw(img_hold)

            bbox = d_hold.textbbox((0, 0), text, font=font_main)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            cx, cy = width // 2, height - 120

            pad_x, pad_y = 34, 16
            d_hold.rounded_rectangle(
                [cx - tw // 2 - pad_x, cy - th // 2 - pad_y,
                 cx + tw // 2 + pad_x, cy + th // 2 + pad_y],
                radius=14,
                fill=(10, 15, 28, 205),
                outline=(255, 255, 255, 45),
                width=1
            )
            d_hold.text((cx + 1, cy + 2), text, font=font_main, fill=(0, 0, 0, 220), anchor="mm")
            d_hold.text((cx, cy), text, font=font_main, fill=(255, 255, 255, 255), anchor="mm")
            img_hold.save(frame_hold)

            # 페이드 인 (알파 45%)
            img_fin = img_hold.copy()
            r, g, b, a = img_fin.split()
            a = a.point(lambda p: int(p * 0.45))
            img_fin.putalpha(a)
            img_fin.save(frame_fade_in)

            # 페이드 아웃 (알파 35%)
            img_fout = img_hold.copy()
            r, g, b, a = img_fout.split()
            a = a.point(lambda p: int(p * 0.35))
            img_fout.putalpha(a)
            img_fout.save(frame_fade_out)

            concat_lines.append(f"file frame_{i}_fin.png\nduration {t_fade:.2f}\n")
            concat_lines.append(f"file frame_{i}_hold.png\nduration {t_hold:.2f}\n")
            concat_lines.append(f"file frame_{i}_fout.png\nduration {t_fade:.2f}\n")

        last_time = end_t

    concat_lines.append("file empty.png\n")

    with open(concat_txt_path, "w", encoding="utf-8") as f:
        f.writelines(concat_lines)

    return concat_txt_path


def build_multi_scene_video_concat(
    video_paths: list,
    target_duration: float,
    output_video_path: str,
    width: int = 1280,
    height: int = 720
) -> str:
    """
    Kie.ai Wan 3.0으로 생성된 여러 비디오 클립들을 받아
    해상도를 정규화하고 부드러운 전환과 함께 하나의 통 배경 비디오로 결합합니다.
    """
    if not video_paths:
        return ""
    
    # 단일 비디오인 경우 길이 맞춤 루프/확장
    if len(video_paths) == 1:
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", video_paths[0],
            "-t", str(target_duration),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", output_video_path
        ]
        subprocess.run(cmd, check=True)
        return output_video_path

    # 여러 비디오 클립 Concat
    list_txt = output_video_path + ".list.txt"
    with open(list_txt, "w", encoding="utf-8") as f:
        for vp in video_paths:
            f.write(f"file '{os.path.abspath(vp)}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt,
        "-stream_loop", "-1", "-t", str(target_duration),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", output_video_path
    ]
    subprocess.run(cmd, check=True)
    return output_video_path


# ----------------------------------------------------------------------
# 6. 풀버전 시네마틱 멀티 씬 뮤직 비디오 렌더링 (16:9, 이퀄라이저 제거)
# ----------------------------------------------------------------------
def render_full_cinematic_mv(
    bg_input: str,
    title_png_path: str,
    lyric_concat_txt: str,
    audio_path: str,
    output_video_path: str,
    duration: float,
    is_video_bg: bool = False
):
    """
    16:9 가로 풀버전 멀티 씬 지브리 애니메이션 영상 렌더링:
    - 완벽한 지브리 애니메이션 배경 영상 (이퀄라이저 제거로 화면 가림 없음)
    - 시네마틱 감성 색감 보정
    - 동적 가사 타이포그래피 애니메이션 오버레이
    - 상단 미니 타이틀 카드
    """
    if is_video_bg:
        bg_input_args = ["-i", bg_input]
    else:
        bg_input_args = ["-f", "concat", "-safe", "0", "-i", bg_input]

    filter_complex = (
        f"[0:v]scale=1280:720,vignette=PI/4,eq=contrast=1.04:saturation=1.08[bg];"
        f"[bg][1:v]overlay=0:0[bg_lyric];"
        f"[bg_lyric][2:v]overlay=0:0[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        *bg_input_args,
        "-f", "concat", "-safe", "0", "-i", lyric_concat_txt,
        "-loop", "1", "-i", title_png_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "3:a",
        "-c:v", "libx264", "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_video_path
    ]

    print(f"[Render Engine] 16:9 지브리 애니메이션 뮤직비디오 렌더링 시작 ({duration:.1f}초, 이퀄라이저 제거됨)...")
    subprocess.run(cmd, check=True)
    print(f"[Render Success] 풀버전 지브리 MV 완료: {output_video_path}")


# ----------------------------------------------------------------------
# 7. 키네틱 9:16 쇼츠 멀티 씬 뮤직 비디오 렌더링 (Shorts, 이퀄라이저 제거)
# ----------------------------------------------------------------------
def render_kinetic_shorts_mv(
    bg_input: str,
    top_badge_png: str,
    lyric_concat_txt: str,
    audio_path: str,
    output_video_path: str,
    shorts_duration: float = 45.0,
    is_video_bg: bool = False
):
    """
    9:16 세로형 쇼츠 지브리 애니메이션 영상 렌더링:
    - 지브리 세로형 애니메이션 씬 (이퀄라이저 제거로 화면 집중도 극대화)
    - 1080x1920 세로 시네마틱 비네팅
    - 중앙 키네틱 팝업 바운스 가사 애니메이션 오버레이
    - 상단 미니 뱃지 오버레이
    """
    if is_video_bg:
        bg_input_args = ["-i", bg_input]
    else:
        bg_input_args = ["-f", "concat", "-safe", "0", "-i", bg_input]

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,vignette=PI/3,eq=contrast=1.06:saturation=1.12[bg];"
        f"[bg][1:v]overlay=0:0[bg_lyric];"
        f"[bg_lyric][2:v]overlay=0:0[v]"
    )

def extract_shorts_from_full_video(
    full_video_path: str,
    output_shorts_path: str,
    top_badge_png: str,
    start_sec: float = 40.0,
    duration: float = 45.0
):
    """
    Kie.ai 비디오를 중복 생성하지 않고, 완성된 16:9 풀버전 뮤직비디오의
    하이라이트 구간(start_sec ~ start_sec+duration)을 9:16 세로 화면으로 자동 중앙 크롭 및 뱃지 오버레이합니다.
    """
    print(f"[Shorts Generator] 원본 풀버전 영상에서 하이라이트 구간({start_sec:.1f}초~{start_sec+duration:.1f}초) 9:16 세로 쇼츠 추출 중...")
    
    # 1. 16:9 -> 9:16 중앙 크롭 & 오디오 페이드 인/아웃 & 상단 뱃지 오버레이
    # 세로 1080x1920 해상도에 맞춤 (가로 중앙을 스마트 크롭 후 블러 배경 패딩 또는 직접 크롭)
    filter_complex = (
        f"[0:v]trim=start={start_sec}:duration={duration},setpts=PTS-STARTPTS,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[cropped];"
        f"[cropped][1:v]overlay=0:0[v];"
        f"[0:a]atrim=start={start_sec}:duration={duration},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=1,afade=t=out:st={duration-1.5}:d=1.5[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", full_video_path,
        "-loop", "1", "-i", top_badge_png,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "21",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_shorts_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[Shorts Success] 원본 영상 기반 9:16 쇼츠 추출 완료: {output_shorts_path}")
