"""
'Inkey Studio' - 고품격 감성 AI 뮤직 비디오 및 숏츠 생성 파이프라인.
Suno AI API (Kie.ai, SunoApi.org, Apiframe, Cookie) 연동 음원 생성
-> AI 맞춤 일러스트 배경 생성
-> 프로페셔널 썸네일 자동 그래픽 합성
-> 가사 타임라인 파싱 & 키네틱 가사 애니메이션 (풀버전 리릭 비디오 & 숏츠 팝업 바운스)
-> 시네마틱 비디오 렌더링 & 고품격 스토리텔링 메타데이터 생성까지 자동 수행합니다.
"""

import os
import sys
import json
import time
import math
import random
import shutil
import requests
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scripts.suno_api_client import SunoMusicGenerator
    from scripts.kie_video_client import KieVideoGenerator
    from scripts.lyric_engine import generate_lyric_and_style, generate_scene_prompts_for_duration
    from scripts.visual_generator import (
        generate_artwork,
        generate_multi_scene_artworks,
        build_multi_scene_concat,
        build_multi_scene_video_concat,
        calculate_scene_durations,
        create_professional_thumbnail,
        extract_video_frame,
        select_most_eyecatching_frame,
        parse_lyrics_timeline,
        render_lyric_animation_assets,
        render_full_cinematic_mv,
        extract_shorts_from_full_video,
        get_korean_font
    )
except ImportError:
    from suno_api_client import SunoMusicGenerator
    from kie_video_client import KieVideoGenerator
    from lyric_engine import generate_lyric_and_style, generate_scene_prompts_for_duration
    from visual_generator import (
        generate_artwork,
        generate_multi_scene_artworks,
        build_multi_scene_concat,
        build_multi_scene_video_concat,
        calculate_scene_durations,
        create_professional_thumbnail,
        extract_video_frame,
        select_most_eyecatching_frame,
        parse_lyrics_timeline,
        render_lyric_animation_assets,
        render_full_cinematic_mv,
        extract_shorts_from_full_video,
        get_korean_font
    )



def create_minimal_title_card(title: str, subtitle: str, output_path: str, width=1280, height=720):
    """
    풀버전 영상 상단 중앙에 배치되는 미니멀하고 세련된 글래스모피즘 타이틀 카드
    """
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_title = get_korean_font(26, bold=True)
    font_sub = get_korean_font(15, bold=False)

    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    w_t = bbox_t[2] - bbox_t[0]
    h_t = bbox_t[3] - bbox_t[1]

    bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
    w_s = bbox_s[2] - bbox_s[0]

    max_w = max(w_t, w_s)
    x = (width - max_w) // 2
    y = 42

    # 슬림 반투명 글래스 박스
    draw.rounded_rectangle(
        [x - 24, y - 10, x + max_w + 24, y + h_t + 28],
        radius=12,
        fill=(10, 14, 24, 170),
        outline=(255, 255, 255, 38),
        width=1
    )

    draw.text(((width - w_t) // 2, y), title, font=font_title, fill=(255, 255, 255, 255))
    draw.text(((width - w_s) // 2, y + h_t + 6), subtitle, font=font_sub, fill=(205, 225, 250, 215))
    img.save(output_path, "PNG")


def create_shorts_top_badge(title: str, output_path: str, width=1080, height=1920):
    """
    숏츠 상단에 배치되는 미니 배지 카드
    """
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_badge = get_korean_font(28, bold=True)
    font_sub = get_korean_font(20, bold=False)

    badge_line = f"🎧 {title}"
    sub_line = "INKEY STUDIO ORIGINAL • HIGHLIGHT"

    bbox_b = draw.textbbox((0, 0), badge_line, font=font_badge)
    wb = bbox_b[2] - bbox_b[0]
    hb = bbox_b[3] - bbox_b[1]

    bbox_s = draw.textbbox((0, 0), sub_line, font=font_sub)
    ws = bbox_s[2] - bbox_s[0]

    max_w = max(wb, ws)
    x = (width - max_w) // 2
    y = 160

    draw.rounded_rectangle(
        [x - 28, y - 12, x + max_w + 28, y + hb + 36],
        radius=14,
        fill=(10, 14, 24, 185),
        outline=(255, 255, 255, 45),
        width=1
    )
    draw.text(((width - wb) // 2, y), badge_line, font=font_badge, fill=(255, 255, 255, 255))
    draw.text(((width - ws) // 2, y + hb + 8), sub_line, font=font_sub, fill=(210, 230, 255, 220))
    img.save(output_path, "PNG")


def generate_all_video_scenes(
    kie_video_client,
    scene_prompts: list,
    output_dir: str = "temp/videos_full",
    max_workers: int = 3
) -> list:
    """
    10초 단위 비디오 씬 N개를 병렬(최대 max_workers 스레드)로 요청/대기하여,
    원래 씬 순서(0 ~ N-1)대로 정렬된 비디오 파일 경로 리스트를 반환합니다.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    os.makedirs(output_dir, exist_ok=True)
    num_scenes = len(scene_prompts)
    results = [None] * num_scenes

    def _worker(idx, prompt_text):
        v_clip_path = os.path.join(output_dir, f"scene_{idx}.mp4")
        # 동시 폭주 요청을 방지하기 위해 각 워커 시작 시 약간의 시차 부여
        time.sleep(idx * 0.8)
        print(f" - [Scene {idx+1}/{num_scenes}] SeaDance V1 Pro 10초 렌더링 요청: {prompt_text[:65]}...")
        res_v = kie_video_client.generate_video_clip(
            prompt=prompt_text,
            duration=10,
            resolution="480p",
            aspect_ratio="16:9",
            output_path=v_clip_path
        )
        return idx, res_v

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_worker, i, p): i for i, p in enumerate(scene_prompts)}
        for future in as_completed(future_map):
            i = future_map[future]
            try:
                idx, v_path = future.result()
                if v_path and os.path.exists(v_path):
                    results[idx] = v_path
                    print(f" [Scene {idx+1}/{num_scenes} 성공] 저장 완료: {v_path}")
                else:
                    print(f" [Scene {idx+1}/{num_scenes} 실패] 비디오가 생성되지 않음")
            except Exception as e:
                print(f" [Scene {i+1}/{num_scenes} 에러 발생] {e}")

    valid_clips = [p for p in results if p and os.path.exists(p)]
    print(f"\n[Video Summary] 총 {num_scenes}개 중 {len(valid_clips)}개의 10초 비디오 씬 생성 완료!")
    return valid_clips


def main():
    os.makedirs("temp", exist_ok=True)

    song_type = os.getenv("INPUT_SONG_TYPE", "random").strip().lower()
    if not song_type or song_type == "":
        song_type = "random"
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    instrumental = os.getenv("INPUT_INSTRUMENTAL", "false").lower() == "true"

    print("\n" + "="*65)
    print(" [Inkey Studio - Premium AI Story Song & Lyric Video Engine]")
    print(f" [Song Theme] {song_type}")
    print(f" [Custom Prompt] {custom_prompt or 'None (Using Preset/Gemini)'}")
    print("="*65 + "\n")

    # 1. 감성 가사, 스타일 태그, 아트 프롬프트 및 스토리 메타데이터 생성
    lyric_res = generate_lyric_and_style(song_type, custom_prompt)
    if len(lyric_res) == 4:
        title, style_tags, lyrics, extra_meta = lyric_res
    else:
        title, style_tags, lyrics = lyric_res[:3]
        extra_meta = {
            "image_prompt": "masterpiece, anime aesthetic, Makoto Shinkai wallpaper style, cinematic lighting",
            "story_description": f"Inkey Studio가 전하는 감성 오리지널 트랙 '{title}'.",
            "shorts_concept": f"가슴을 울리는 킬링파트 🎧 '{title}'",
            "genre_name": "감성 인디 & 록",
            "category": "indie_band"
        }

    # 곡명 클렌징
    import re
    title = re.sub(r'\s*#\d+', '', title).strip()

    print(f"[곡 제목] {title}")
    print(f"[장르] {extra_meta.get('genre_name', 'Original')}")
    print(f"[음악 스타일 태그]\n{style_tags}\n")
    print(f"[아트 프롬프트]\n{extra_meta.get('image_prompt')}\n")

    # 가사 클렌징
    clean_lyrics_lines = []
    for line in lyrics.splitlines():
        if re.match(r'^\s*\([가-힣\s\.,!\?]+\)\s*$', line):
            continue
        cleaned_line = re.sub(r'\s*\([^\)]*(?:잔나비|넬|검정치마|day6|qwer|style|가수)[^\)]*\)', '', line, flags=re.IGNORECASE)
        clean_lyrics_lines.append(cleaned_line)
    display_lyrics = "\n".join(clean_lyrics_lines).strip()

    audio_path = "temp/ai_song.mp3"
    bg_16_9 = "temp/bg_full.jpg"
    bg_9_16 = "temp/bg_shorts.jpg"
    title_png = "temp/title_overlay.png"
    shorts_badge_png = "temp/shorts_badge.png"
    output_video = "output_music_video.mp4"
    output_shorts = "output_shorts_video.mp4"

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

    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    print(f"[Audio Info] 음원 준비 완료: 길이 {duration_sec:.1f}초 ({int(duration_sec // 60)}분 {int(duration_sec % 60)}초)")

    # 3. 노래 길이에 맞춘 10초 단위 N개 애니메이션 비디오 씬 기획 및 생성 (Kie.ai SeaDance V1 Pro, 480p 10초)
    cat_type = extra_meta.get("category", "indie_band")
    clip_duration = 10.0
    num_scenes = max(1, math.ceil(duration_sec / clip_duration))
    print(f"\n[Video Strategy] 총 음원 길이 {duration_sec:.1f}초에 맞춰 10초 단위 씬 {num_scenes}개를 생성합니다 (총 {num_scenes * 10}초 분량).")

    # 전체 음원 시간과 가사에 맞춰 정확히 num_scenes개의 씬 프롬프트 생성 (동물/자연/우주 중심, 인물 얼굴 배제)
    scene_prompts = generate_scene_prompts_for_duration(
        lyrics=display_lyrics,
        duration_sec=duration_sec,
        clip_duration=clip_duration,
        base_prompts=extra_meta.get("scene_prompts", [])
    )
    shorts_scene_prompts = extra_meta.get("shorts_scene_prompts", scene_prompts[:3])

    kie_video_client = KieVideoGenerator()
    video_clips_full = []
    video_clips_shorts = []

    # 각 씬의 지속시간 계산 (노래 길이에 맞춰 분배)
    full_durations = calculate_scene_durations(duration_sec, len(scene_prompts), is_shorts=False)

    shorts_duration = 45.0
    if duration_sec > shorts_duration + 20:
        start_sec = 40.0
    elif duration_sec > shorts_duration:
        start_sec = max(0.0, (duration_sec - shorts_duration) / 2.0)
    else:
        start_sec = 0.0
        shorts_duration = duration_sec

    shorts_durations = calculate_scene_durations(shorts_duration, len(shorts_scene_prompts), is_shorts=True, shorts_duration=shorts_duration)

    # Kie.ai API 키가 있는 경우 ByteDance SeaDance V1 Pro (초당 2.8 크레딧 가성비) 10초 씬 N개 병렬 생성
    if kie_video_client.has_api_key():
        print(f"\n[Step 3] Kie.ai ByteDance SeaDance V1 Pro 엔진으로 10초 애니메이션 씬 {num_scenes}개 병렬 렌더링 시작 (480P 가성비 모드)...")
        os.makedirs("temp/videos_full", exist_ok=True)
        video_clips_full = generate_all_video_scenes(
            kie_video_client=kie_video_client,
            scene_prompts=scene_prompts,
            output_dir="temp/videos_full",
            max_workers=3
        )

    # 비디오가 정상 생성된 경우 하나의 결합 배경 비디오로 빌드
    use_video_bg_full = False
    bg_full_input = ""

    if video_clips_full and len(video_clips_full) > 0:
        print(f"[Video Pipeline] {len(video_clips_full)}개의 SeaDance V1 애니메이션 비디오 클립을 연결합니다.")
        bg_full_video_path = "temp/bg_full_video.mp4"
        bg_full_input = build_multi_scene_video_concat(
            video_paths=video_clips_full,
            target_duration=duration_sec,
            output_video_path=bg_full_video_path,
            width=1280,
            height=720
        )
        use_video_bg_full = True

    # 3-B. 비디오 생성이 없거나 실패한 경우 정지 이미지 멀티씬 디졸브로 안전한 폴백
    scenes_full_dir = "temp/scenes_full"
    scene_full_paths = []

    if not use_video_bg_full:
        print("\n[Step 3-Fallback] 비디오 미생성으로 정지 이미지 멀티 씬 일러스트 생성 중 (폴백용)...")
        scene_full_paths = generate_multi_scene_artworks(
            scene_prompts=scene_prompts,
            output_dir=scenes_full_dir,
            width=1280,
            height=720,
            song_type=cat_type,
            is_shorts=False
        )

        bg_full_input = build_multi_scene_concat(
            scene_image_paths=scene_full_paths,
            scene_durations=full_durations,
            output_dir="temp",
            width=1280,
            height=720,
            transition_dur=0.8,
            is_shorts=False
        )
        best_full_scene = scene_full_paths[min(2, len(scene_full_paths)-1)] if scene_full_paths else "temp/bg.jpg"
        best_shorts_scene = best_full_scene
    else:
        # 완성된 비디오 배경 영상에서 여러 후보 컷을 분석하여 가장 눈길을 사로잡는 최적의 하이라이트 프레임 자동 선별
        print("\n[Step 4] 완성된 16:9 비디오 영상에서 가장 눈길을 사로잡는 최상의 썸네일 컷 선별 중...")
        best_full_scene = "temp/video_frame_full.jpg"
        select_most_eyecatching_frame(
            video_path=bg_full_video_path,
            duration_sec=duration_sec,
            output_image_path=best_full_scene,
            width=1280,
            height=720,
            is_shorts=False
        )
        best_shorts_scene = "temp/video_frame_shorts.jpg"
        select_most_eyecatching_frame(
            video_path=bg_full_video_path,
            duration_sec=duration_sec,
            output_image_path=best_shorts_scene,
            width=1080,
            height=1920,
            is_shorts=True
        )

    # 4. 프로페셔널 유튜브 썸네일 그래픽 합성 (영상에서 추출한 실 프레임 기반)
    thumb_full = "temp/thumbnail.jpg"
    thumb_shorts = "temp/thumbnail_shorts.jpg"
    genre_display = extra_meta.get("genre_name", "Original Track")
    sub_text = extra_meta.get("story_description", "").split("\n")[0][:36] or "Inkey Studio Original"

    create_professional_thumbnail(
        bg_image_path=best_full_scene,
        title=title,
        subtitle=sub_text,
        genre_name=genre_display,
        output_path=thumb_full,
        width=1280,
        height=720,
        is_shorts=False
    )
    create_professional_thumbnail(
        bg_image_path=best_shorts_scene,
        title=title,
        subtitle=extra_meta.get("shorts_concept", f"{title} 킬링파트"),
        genre_name=genre_display,
        output_path=thumb_shorts,
        width=1080,
        height=1920,
        is_shorts=True
    )

    # 5. 가사 타임라인 파싱 및 키네틱 가사 애니메이션 렌더링 (Whisper 보컬 발화 시간 감지 & 원본 가사 매핑)
    print("\n[Step 5] 오디오 보컬 타이밍 분석 및 원본 가사 타임라인 정밀 동기화 중...")
    timeline_full = parse_lyrics_timeline(display_lyrics, duration_sec, audio_path=audio_path, is_shorts=False)
    concat_txt_full = render_lyric_animation_assets(timeline_full, 1280, 720, "temp", is_shorts=False)

    # 6. 상단 미니 오버레이 카드 생성
    create_minimal_title_card(title, f"Inkey Studio • {genre_display}", title_png, 1280, 720)
    create_shorts_top_badge(title, shorts_badge_png, 1080, 1920)

    # 7. 풀버전 16:9 감성 애니메이션 뮤직 비디오 렌더링
    print("\n[Step 7] 16:9 풀버전 감성 애니메이션 리릭 MV 합성 렌더링 (이퀄라이저 제거)...")
    render_full_cinematic_mv(
        bg_input=bg_full_input,
        title_png_path=title_png,
        lyric_concat_txt=concat_txt_full,
        audio_path=audio_path,
        output_video_path=output_video,
        duration=duration_sec,
        is_video_bg=use_video_bg_full
    )

    # 8. 원본 풀버전 영상에서 하이라이트 구간을 세로(9:16)로 직접 크롭하여 숏츠 생성
    print("\n[Step 8] 원본 풀버전 영상에서 하이라이트 구간을 9:16 세로로 크롭하여 숏츠 자동 제작...")
    extract_shorts_from_full_video(
        full_video_path=output_video,
        output_shorts_path=output_shorts,
        top_badge_png=shorts_badge_png,
        start_sec=start_sec,
        duration=shorts_duration
    )

    if os.path.exists(output_shorts):
        print("\n[Step 8-B] 제작된 9:16 세로 쇼츠 영상에서 가장 눈길을 사로잡는 프레임 선별 및 썸네일 합성...")
        final_shorts_frame = "temp/final_shorts_frame.jpg"
        select_most_eyecatching_frame(
            video_path=output_shorts,
            duration_sec=shorts_duration,
            output_image_path=final_shorts_frame,
            width=1080,
            height=1920,
            is_shorts=True
        )
        create_professional_thumbnail(
            bg_image_path=final_shorts_frame,
            title=title,
            subtitle=extra_meta.get("shorts_concept", f"{title} 킬링파트"),
            genre_name=genre_display,
            output_path=thumb_shorts,
            width=1080,
            height=1920,
            is_shorts=True
        )


    # 9. 유튜브 고품격 스토리텔링 메타데이터 저장 (풀버전용)
    youtube_title = f"{title} - Inkey Studio [Official Lyric Video]"
    story_essay = extra_meta.get("story_description", "").strip()

    desc = (
        f"🎧 {youtube_title}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 [Track Story & Liner Notes]\n"
        f"{story_essay}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎼 트랙 정보 (Information)\n"
        f"• 곡명: {title}\n"
        f"• 장르: {genre_display}\n"
        f"• 프로듀싱: Inkey Studio\n"
        f"• 재생 시간: {int(duration_sec // 60)}분 {int(duration_sec % 60)}초\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 가사 (Lyrics)\n"
        f"{display_lyrics}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"☕ 이런 순간에 함께 들어보세요\n"
        f"• 혼자 걷는 늦은 밤, 조용히 마음을 정리하고 싶을 때\n"
        f"• 하루 끝 지친 마음을 따뜻하게 안아줄 위로가 필요할 때\n"
        f"• 몰입이 필요한 작업 시간, 새벽 드라이브를 나설 때\n\n"
        f"✨ Collaboration:\n"
        f"본 음원은 음악 협업도구 KIE와 함께 제작되었습니다.\n"
        f"🔗 KIE 바로가기: https://kie.ai?ref=a75838b6fecc53ef2774b5279d142d11\n\n"
        f"#InkeyStudio #InkeyMusic #신곡 #감성인디 #리릭비디오 #OfficialMV #노래추천 #KIE"
    )

    meta_info = {
        "title": youtube_title[:100],
        "description": desc,
        "artist": "Inkey Studio",
        "song_title": title,
        "thumbnail": thumb_full
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)

    # 10. 유튜브 쇼츠용 메타데이터 저장
    shorts_concept_text = extra_meta.get("shorts_concept", f"{title} 킬링파트")
    shorts_title = f"{title} 🎧 킬링파트 #Shorts"
    shorts_desc = (
        f"🎧 {title} - Inkey Studio Highlight\n\n"
        f"✨ {shorts_concept_text}\n\n"
        f"풀버전 가사 뮤직비디오는 채널에서 감상하실 수 있습니다.\n\n"
        f"🔗 음악 협업도구 KIE: https://kie.ai?ref=a75838b6fecc53ef2774b5279d142d11\n\n"
        f"#Shorts #InkeyStudio #리릭비디오 #신곡 #킬링파트 #노래추천 #KIE"
    )
    shorts_meta_info = {
        "title": shorts_title[:100],
        "description": shorts_desc,
        "artist": "Inkey Studio",
        "song_title": title,
        "thumbnail": thumb_shorts
    }
    with open("temp/video_info_shorts.json", "w", encoding="utf-8") as f:
        json.dump(shorts_meta_info, f, ensure_ascii=False, indent=2)

    print("\n" + "="*65)
    print(" [Complete] 풀버전 리릭 비디오 & 9:16 쇼츠 키네틱 애니메이션 제작 완료!")
    print(f" - 풀버전 영상: {output_video}")
    print(f" - 쇼츠 영상: {output_shorts}")
    print(f" - 풀버전 썸네일: {thumb_full}")
    print(f" - 쇼츠 썸네일: {thumb_shorts}")
    print("="*65 + "\n")


if __name__ == "__main__":
    main()
