import os
import sys
import glob
import json
import time
import math
import random
import asyncio
import subprocess
import requests
import unicodedata
import numpy as np
from pathlib import Path
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. 나루토 대표 캐릭터 & 고유 술법(오의) 데이터베이스 ---

CHARACTER_SKILLS = {
    "우치하 이타치": {
        "skill_name": "츠쿠요미 & 아마테라스",
        "skill_sub": "Tsukuyomi & Amaterasu (만화경 사륜안 오의)",
        "theme_color": (255, 40, 40),
        "quote": "꺼지지 않는 흑염과 정신을 파괴하는 절대 환술!"
    },
    "페인 (텐도)": {
        "skill_name": "신라천정 & 지폭천성",
        "skill_sub": "Shinra Tensei & Chibaku Tensei (윤회안 신급 오의)",
        "theme_color": (180, 70, 255),
        "quote": "세계에 고통을! 시공을 일그러뜨리는 척력과 만유인력!"
    },
    "나루토 (선인 모드)": {
        "skill_name": "선법 풍둔 나선수리검",
        "skill_sub": "Sage Art: Wind Style Rasenshuriken",
        "theme_color": (0, 230, 255),
        "quote": "자연 차크라를 극한으로 융합한 세포 파괴 소용돌이!"
    },
    "나루토 (쿠라마 링크)": {
        "skill_name": "미수화 초대옥 나선연환",
        "skill_sub": "Kurama Chakra Tailed Beast Rasen-Barrage",
        "theme_color": (255, 190, 0),
        "quote": "구미의 차크라와 황금빛 선술이 빚어내는 궁극의 탄막!"
    },
    "우치하 사스케 (윤회안)": {
        "skill_name": "스사노오 치도리 & 인드라의 화살",
        "skill_sub": "Susanoo Chidori & Indra's Arrow",
        "theme_color": (90, 150, 255),
        "quote": "천동을 가르는 뇌둔과 미수의 차크라를 실은 벼락 화살!"
    },
    "우치하 마다라": {
        "skill_name": "완성체 스사노오 & 천애진성",
        "skill_sub": "Perfect Susanoo & Tengai Shinsei",
        "theme_color": (50, 120, 255),
        "quote": "산맥을 가르는 거신참과 하늘에서 떨어지는 거대 운석!"
    },
    "센주 하시라마": {
        "skill_name": "선법 목둔 진수천수 정상화불",
        "skill_sub": "Sage Art Wood Style: True Several Thousand Hands",
        "theme_color": (50, 230, 120),
        "quote": "수천 개의 주먹으로 전장을 초토화하는 닌자의 신의 위엄!"
    },
    "나미카제 미나토": {
        "skill_name": "비뢰신의 술 2의 단 & 나선환",
        "skill_sub": "Flying Raijin Level 2 & Massive Rasengan",
        "theme_color": (255, 230, 40),
        "quote": "눈 깜짝할 사이에 배후를 찌르는 금빛 섬광의 일격!"
    },
    "마이트 가이 (8문 둔갑)": {
        "skill_name": "사문 개방 궁극오의 밤 가이",
        "skill_sub": "Night Guy (Eight Inner Gates Released)",
        "theme_color": (255, 30, 70),
        "quote": "공간마저 일그러뜨리는 핏빛 붉은 용의 궁극의 킥!"
    },
    "하타케 카카시 (카무이)": {
        "skill_name": "카무이 뇌절 & 쌍신 카무이 수리검",
        "skill_sub": "Kamui Lightning Blade & Kamui Shuriken",
        "theme_color": (120, 210, 255),
        "quote": "이공간으로 왜곡해 모든 방어를 무시하는 신속의 참격!"
    },
    "지라이야 (선인 모드)": {
        "skill_name": "선법 초대옥 나선환",
        "skill_sub": "Sage Art: Ultra-Big Ball Rasengan",
        "theme_color": (255, 130, 30),
        "quote": "대지를 녹이는 두꺼비 화염과 거대 나선 차크라 폭풍!"
    },
    "데이다라": {
        "skill_name": "C4 카루라 & 궁극예술 C0 자폭",
        "skill_sub": "C4 Karura & Ultimate Art C0 Detonation",
        "theme_color": (255, 210, 40),
        "quote": "예술은 폭발이다! 초미세 나노 폭탄과 10km 소멸 섬광!"
    }
}

NARUTO_CHARACTERS = list(CHARACTER_SKILLS.keys())

CURATED_MATCHUPS = [
    ("우치하 이타치", "페인 (텐도)"),
    ("나미카제 미나토", "우치하 이타치"),
    ("우치하 마다라", "센주 하시라마"),
    ("마이트 가이 (8문 둔갑)", "우치하 마다라"),
    ("하타케 카카시 (카무이)", "우치하 사스케 (윤회안)"),
    ("우치하 사스케 (윤회안)", "나루토 (쿠라마 링크)"),
    ("지라이야 (선인 모드)", "페인 (텐도)")
]

def get_character_skill_info(char_name):
    clean = char_name.split()[0].replace("(", "").replace(")", "")
    for k, v in CHARACTER_SKILLS.items():
        if char_name in k or clean in k or k in char_name:
            return v
    return {
        "skill_name": "비전 오의 필살일격",
        "skill_sub": "Ultimate Ninja Secret Technique",
        "theme_color": (255, 100, 50),
        "quote": "전력을 다한 영혼의 궁극 비오의 격돌!"
    }

# --- 2. Gemini Pro 대본 생성 (만화 전투씬 내레이션) ---

def get_gemini_battle_script(char_a, char_b, gemini_api_key=None):
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)

    prompt = f"""
당신은 나루토 공식 애니메이션 액션 연출가입니다.
아래 두 나루토 캐릭터의 '풀 모션 만화 전투씬 숏츠'의 내레이션 대본과 최종 승자를 JSON으로 작성하세요.

캐릭터 A: {char_a} (오의: {skill_a['skill_name']})
캐릭터 B: {char_b} (오의: {skill_b['skill_name']})

JSON 응답 형식:
{{
  "title": "{char_a} VS {char_b}, 숨막히는 혈투!",
  "phases": {{
    "phase1_intro": "{char_a} 대 {char_b}! 피할 수 없는 정상결전이 시작됩니다!",
    "phase2_taijutsu": "폭발적인 스피드로 맞붙는 초반 체술 공방전!",
    "phase3_ninjutsu": "치명적인 비전 인술이 연이어 폭발하며 전장을 뒤흔듭니다!",
    "phase4_awakening": "마침내 발동하는 궁극의 오의! {char_a}의 {skill_a['skill_name']} 대 {char_b}의 {skill_b['skill_name']}!",
    "phase5_clash": "두 거대한 차크라가 정면 충돌하며 대폭발을 일으킵니다!",
    "phase6_verdict": "치열한 격돌 끝에 전장을 지배한 승자는 {char_a}입니다! 여러분의 생각은 어떠신가요?"
  }},
  "winner": "character_a 또는 character_b",
  "winner_name": "{char_a}",
  "score": "HIGH-DIFF VICTORY"
}}
"""

    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                return data
        except Exception:
            pass

    # Fallback 대본
    winner_key = random.choice(["character_a", "character_b"])
    winner_name = char_a if winner_key == "character_a" else char_b
    return {
        "title": f"{char_a} VS {char_b}, 세기의 오의 대격돌!",
        "phases": {
            "phase1_intro": f"{char_a} 대 {char_b}! 물러설 수 없는 정상결전이 시작됩니다!",
            "phase2_taijutsu": "초고속으로 전개되는 치열한 체술과 수리검 공방!",
            "phase3_ninjutsu": "대지를 가르는 강력한 인술 폭격이 연이어 터져나옵니다!",
            "phase4_awakening": f"마침내 폭발하는 궁극의 오의! {char_a}의 {skill_a['skill_name']} 대 {char_b}의 {skill_b['skill_name']}!",
            "phase5_clash": "두 차크라가 정면으로 충돌하며 거대한 섬광과 폭풍을 일으킵니다!",
            "phase6_verdict": f"치열한 혈투 끝에 승리를 거머쥔 {winner_name}! 여러분의 생각은 어떠신가요?"
        },
        "winner": winner_key,
        "winner_name": winner_name,
        "score": f"{winner_name} WINS (HIGH-DIFF)"
    }

# --- 3. Edge-TTS & gTTS 음성 합성 트랙 생성 ---

def generate_single_tts(text, output_file, voice="ko-KR-InJoonNeural"):
    try:
        import edge_tts
        async def _edge():
            communicate = edge_tts.Communicate(text, voice, rate="+20%")
            await communicate.save(output_file)
        asyncio.run(_edge())
        if os.path.exists(output_file) and os.path.getsize(output_file) > 500:
            return
    except Exception:
        pass

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='ko')
        tts.save(output_file)
    except Exception:
        silent = AudioSegment.silent(duration=2500)
        silent.export(output_file, format="mp3")

def generate_battle_voice_track(battle_data, output_audio_path="temp/naruto_battle_voice.mp3"):
    os.makedirs("temp/tts", exist_ok=True)
    combined = AudioSegment.silent(duration=300)
    phases = battle_data["phases"]

    phase_keys = ["phase1_intro", "phase2_taijutsu", "phase3_ninjutsu", "phase4_awakening", "phase5_clash", "phase6_verdict"]
    durations = {}

    for k in phase_keys:
        txt = phases[k]
        p_path = f"temp/tts/{k}.mp3"
        generate_single_tts(txt, p_path)
        seg = AudioSegment.from_file(p_path)
        durations[k] = len(seg) / 1000.0
        combined += seg + AudioSegment.silent(duration=250)

    combined.export(output_audio_path, format="mp3", bitrate="192k")
    total_sec = len(combined) / 1000.0
    print(f"[Battle Voice Track Ready] 총 {total_sec:.1f}초")
    return durations, total_sec

# --- 4. 폰트 로더 ---

def get_font(size=40, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

# --- 5. 시네마틱 애니메이션 HUD 오버레이 생성기 ---

def create_anime_hud_overlay(phase_name, title_text, sub_text, char_a, char_b, output_png, width=1080, height=1920):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. 상단 체력바 및 대결 헤더 (VS Header)
    draw.rectangle([0, 0, width, 180], fill=(0, 0, 0, 220))
    font_head = get_font(38, bold=True)
    font_vs = get_font(44, bold=True)
    
    # 캐릭터 A 체력바 (Left Blue)
    draw.text((60, 45), char_a, font=font_head, fill=(255, 225, 80), anchor="lt")
    draw.rounded_rectangle([60, 100, 480, 135], radius=10, fill=(30, 30, 40), outline=(255, 215, 0), width=3)
    draw.rounded_rectangle([63, 103, 440, 132], radius=8, fill=(255, 60, 60))

    # VS 마크 (Center)
    draw.text((width//2, 90), "VS", font=font_vs, fill=(255, 255, 255), anchor="mm")

    # 캐릭터 B 체력바 (Right Red)
    draw.text((width-60, 45), char_b, font=font_head, fill=(100, 220, 255), anchor="rt")
    draw.rounded_rectangle([width-480, 100, width-60, 135], radius=10, fill=(30, 30, 40), outline=(255, 215, 0), width=3)
    draw.rounded_rectangle([width-440, 103, width-63, 132], radius=8, fill=(60, 140, 255))

    # 2. 하단 시네마틱 자막 배너 (Bottom Action Subtitle)
    draw.rectangle([0, height-260, width, height], fill=(0, 0, 0, 230))
    draw.line([(0, height-260), (width, height-260)], fill=(255, 215, 0), width=6)

    font_phase = get_font(36, bold=True)
    font_title = get_font(52, bold=True)
    font_sub = get_font(32, bold=False)

    draw.text((width//2, height-210), f"⚔️ {phase_name} ⚔️", font=font_phase, fill=(255, 230, 80), anchor="mm")
    draw.text((width//2, height-140), title_text, font=font_title, fill=(255, 255, 255), anchor="mm")
    if sub_text:
        draw.text((width//2, height-75), sub_text, font=font_sub, fill=(200, 200, 200), anchor="mm")

    img.save(output_png, "PNG")

# --- 6. 실제 만화 애니메이션 전투씬 숏츠 렌더러 (From skill_list.mp4) ---

def render_anime_battle_movie(char_a, char_b, battle_data, durations, output_mp4="output_naruto_shorts.mp4"):
    """
    assets/anime_clips/skill_list.mp4 원본 비디오에서 역동적인 전투 액션 컷들을 정밀 추출하고
    시네마틱 9:16 모바일 풀스크린 만화영화 배틀 숏츠로 렌더링합니다.
    """
    src_video = "assets/anime_clips/skill_list.mp4"
    if not os.path.exists(src_video):
        print(f"[Error] {src_video} 파일이 존재하지 않습니다.")
        return False

    os.makedirs("temp/battle_scenes", exist_ok=True)
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)
    phases = battle_data["phases"]

    print("\n[Anime Movie Battle Engine] 만화 전투씬 비디오 시퀀스 추출 및 시네마틱 렌더링 시작...")

    # 전투 씬별 타임스탬프 앵커 (skill_list.mp4에서 액션 밀도가 높은 구간들)
    # 총 658초 영상에서 전투 페이즈에 맞는 다이내믹 컷 추출
    scene_defs = [
        {
            "id": "phase1",
            "phase_name": "PROLOGUE : CLASH OF DESTINY",
            "title": f"{char_a}  VS  {char_b}",
            "sub": "피할 수 없는 세기의 정상결전!",
            "start_ss": random.randint(10, 40),
            "dur": max(3.5, durations.get("phase1_intro", 3.5))
        },
        {
            "id": "phase2",
            "phase_name": "PHASE 1 : TAIJUTSU & SPEED",
            "title": "초고속 체술 & 수리검 공방전!",
            "sub": "눈으로 쫓을 수 없는 극한의 스피드 공방",
            "start_ss": random.randint(70, 130),
            "dur": max(4.5, durations.get("phase2_taijutsu", 4.5))
        },
        {
            "id": "phase3",
            "phase_name": "PHASE 2 : NINJUTSU BARRAGE",
            "title": "대지를 가르는 비전 인술 폭격!",
            "sub": "파괴적인 차크라와 인술의 연속 작렬",
            "start_ss": random.randint(180, 260),
            "dur": max(5.0, durations.get("phase3_ninjutsu", 5.0))
        },
        {
            "id": "phase4",
            "phase_name": "PHASE 3 : ULTIMATE JUTSU AWAKENING",
            "title": f"오의(奧義) 각성 : {skill_a['skill_name']}",
            "sub": f"{char_a} VS {char_b} 전력 개방!",
            "start_ss": random.randint(320, 420),
            "dur": max(5.5, durations.get("phase4_awakening", 5.5))
        },
        {
            "id": "phase5",
            "phase_name": "FINAL PHASE : THE ULTIMATE CLASH",
            "title": "💥 전장을 집어삼키는 대폭발! 💥",
            "sub": "두 궁극기의 정면 충돌과 초토화",
            "start_ss": random.randint(480, 560),
            "dur": max(6.0, durations.get("phase5_clash", 6.0))
        },
        {
            "id": "phase6",
            "phase_name": "EPILOGUE : VICTORY & VERDICT",
            "title": f"🏆 {battle_data['winner_name']} WINS! 🏆",
            "sub": "💬 여러분의 의견은? 댓글로 남겨주세요!",
            "start_ss": random.randint(580, 640),
            "dur": max(5.0, durations.get("phase6_verdict", 5.0))
        }
    ]

    scene_clips = []
    fps = 30

    for idx, sc in enumerate(scene_defs):
        sc_id = sc["id"]
        overlay_png = os.path.abspath(f"temp/battle_scenes/hud_{sc_id}.png")
        create_anime_hud_overlay(sc["phase_name"], sc["title"], sc["sub"], char_a, char_b, overlay_png)

        clip_mp4 = os.path.abspath(f"temp/battle_scenes/clip_{sc_id}.mp4")

        # 9:16 세로형 시네마틱 애니메이션 필터:
        # 배경: 화면 전체 블러 처리된 1080x1920 차크라 배경
        # 전면: 1080p 중앙 액션 프레이밍 + 애니메이션 HUD 오버레이
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            f"[0:v]scale=1080:720[fg];"
            f"[bg][fg]overlay=0:(H-h)/2[base];"
            f"[base][1:v]overlay=0:0[vout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(sc["start_ss"]),
            "-i", src_video,
            "-i", overlay_png,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-t", str(sc["dur"]),
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
            clip_mp4
        ]
        subprocess.run(cmd, check=True)
        scene_clips.append(clip_mp4)

    # Concat 비디오 결합
    concat_txt = "temp/battle_scenes/concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in scene_clips:
            f.write(f"file '{c}'\n")

    temp_video = "temp/battle_scenes/battle_video_only.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", temp_video], check=True)

    # TTS 보이스 + OST BGM 믹싱
    voice_track = "temp/naruto_battle_voice.mp3"
    bgm_files = glob.glob("assets/audio/music/*.mp3") + glob.glob("assets/audio/*/*.mp3")
    bgm_path = random.choice(bgm_files) if bgm_files else None

    if bgm_path and os.path.exists(bgm_path):
        filter_audio = "[1:a]volume=1.1[v_voice];[2:a]volume=0.25,aloop=loop=-1:size=2e+09[v_bgm];[v_voice][v_bgm]amix=inputs=2:duration=first[aout]"
        cmd_final = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", voice_track,
            "-i", bgm_path,
            "-filter_complex", filter_audio,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_mp4
        ]
    else:
        cmd_final = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", voice_track,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_mp4
        ]

    subprocess.run(cmd_final, check=True)
    print(f"\n=======================================================")
    print(f" [Naruto Real Anime Battle Movie Shorts Rendered!]")
    print(f" [Output File] {output_mp4} (100% Real Anime Movie Battle Scenes)")
    print(f"=======================================================\n")

# --- 7. 메인 실행 진입점 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)

    input_char_a = os.getenv("INPUT_CHAR_A", "").strip()
    input_char_b = os.getenv("INPUT_CHAR_B", "").strip()

    if input_char_a and input_char_b:
        char_a = input_char_a
        char_b = input_char_b
    else:
        char_a, char_b = random.choice(CURATED_MATCHUPS)

    print(f"\n[Naruto Real Anime Battle Selected] '{char_a}' VS '{char_b}'")

    # 1. Gemini Pro 만화 전투 대본 생성
    battle_data = get_gemini_battle_script(char_a, char_b)

    # 2. 한국어 TTS 내레이션 음성 생성
    durations, total_sec = generate_battle_voice_track(battle_data, "temp/naruto_battle_voice.mp3")

    # 3. skill_list.mp4 기반 1080x1920 만화영화 전투씬 숏츠 렌더링
    output_video = "output_naruto_shorts.mp4"
    render_anime_battle_movie(char_a, char_b, battle_data, durations, output_video)

    # 4. 유튜브 메타데이터 생성
    final_title = f"{battle_data['title']} #Shorts"
    desc = (
        f"🔥 {char_a} VS {char_b} 나루토 세기의 진검승부!\n\n"
        f"체술부터 궁극의 오의 격돌까지, 전장을 뒤흔든 승자는 누구일까요?\n"
        f"여러분의 생각을 댓글로 남겨주세요!\n\n"
        f"#{char_a.replace(' ', '')} #{char_b.replace(' ', '')} #나루토 #만화전투씬 #나루토쇼츠 #가상대결 #Shorts #Naruto"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Naruto Battle Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"[Metadata Saved] {final_title}")
