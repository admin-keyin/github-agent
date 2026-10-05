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

# --- 1. Giphy 공식 애니메이션 비디오 에셋 풀 및 매핑 DB ---

GIPHY_API_KEY = "sXpGFDGZs0Dv1mmNFvYaGUvYwKX0PWIh"

CHARACTER_SKILLS = {
    "우치하 이타치": {
        "giphy_char": "itachi uchiha anime fight",
        "giphy_skill": "itachi amaterasu",
        "skill_name": "츠쿠요미 & 아마테라스",
        "skill_sub": "Tsukuyomi & Amaterasu (만화경 사륜안 오의)",
        "theme_color": (255, 40, 40),
        "quote": "꺼지지 않는 흑염과 정신을 파괴하는 절대 환술!"
    },
    "페인 (텐도)": {
        "giphy_char": "pain tendo naruto",
        "giphy_skill": "pain shinra tensei",
        "skill_name": "신라천정 & 지폭천성",
        "skill_sub": "Shinra Tensei & Chibaku Tensei (윤회안 신급 오의)",
        "theme_color": (180, 70, 255),
        "quote": "세계에 고통을! 시공을 일그러뜨리는 척력과 만유인력!"
    },
    "나루토 (선인 모드)": {
        "giphy_char": "naruto sage mode",
        "giphy_skill": "naruto rasenshuriken",
        "skill_name": "선법 풍둔 나선수리검",
        "skill_sub": "Sage Art: Wind Style Rasenshuriken",
        "theme_color": (0, 230, 255),
        "quote": "자연 차크라를 극한으로 융합한 세포 파괴 소용돌이!"
    },
    "나루토 (쿠라마 링크)": {
        "giphy_char": "naruto kurama mode",
        "giphy_skill": "naruto bijuu dama",
        "skill_name": "미수화 초대옥 나선연환",
        "skill_sub": "Kurama Chakra Tailed Beast Rasen-Barrage",
        "theme_color": (255, 190, 0),
        "quote": "구미의 차크라와 황금빛 선술이 빚어내는 궁극의 탄막!"
    },
    "우치하 사스케 (윤회안)": {
        "giphy_char": "sasuke uchiha rinnegan",
        "giphy_skill": "sasuke chidori susanoo",
        "skill_name": "스사노오 치도리 & 인드라의 화살",
        "skill_sub": "Susanoo Chidori & Indra's Arrow",
        "theme_color": (90, 150, 255),
        "quote": "천동을 가르는 뇌둔과 미수의 차크라를 실은 벼락 화살!"
    },
    "우치하 마다라": {
        "giphy_char": "madara uchiha fight",
        "giphy_skill": "madara meteor",
        "skill_name": "완성체 스사노오 & 천애진성",
        "skill_sub": "Perfect Susanoo & Tengai Shinsei",
        "theme_color": (50, 120, 255),
        "quote": "산맥을 가르는 거신참과 하늘에서 떨어지는 거대 운석!"
    },
    "센주 하시라마": {
        "giphy_char": "hashirama senju",
        "giphy_skill": "hashirama thousand hands",
        "skill_name": "선법 목둔 진수천수 정상화불",
        "skill_sub": "Sage Art Wood Style: True Several Thousand Hands",
        "theme_color": (50, 230, 120),
        "quote": "수천 개의 주먹으로 전장을 초토화하는 닌자의 신의 위엄!"
    },
    "나미카제 미나토": {
        "giphy_char": "minato namikaze fight",
        "giphy_skill": "minato rasengan",
        "skill_name": "비뢰신의 술 2의 단 & 나선환",
        "skill_sub": "Flying Raijin Level 2 & Massive Rasengan",
        "theme_color": (255, 230, 40),
        "quote": "눈 깜짝할 사이에 배후를 찌르는 금빛 섬광의 일격!"
    },
    "마이트 가이 (8문 둔갑)": {
        "giphy_char": "might guy 8 gates",
        "giphy_skill": "might guy night guy",
        "skill_name": "사문 개방 궁극오의 밤 가이",
        "skill_sub": "Night Guy (Eight Inner Gates Released)",
        "theme_color": (255, 30, 70),
        "quote": "공간마저 일그러뜨리는 핏빛 붉은 용의 궁극의 킥!"
    },
    "하타케 카카시 (카무이)": {
        "giphy_char": "kakashi hatake fight",
        "giphy_skill": "kakashi kamui raikiri",
        "skill_name": "카무이 뇌절 & 쌍신 카무이 수리검",
        "skill_sub": "Kamui Lightning Blade & Kamui Shuriken",
        "theme_color": (120, 210, 255),
        "quote": "이공간으로 왜곡해 모든 방어를 무시하는 신속의 참격!"
    },
    "지라이야 (선인 모드)": {
        "giphy_char": "jiraiya sage mode",
        "giphy_skill": "jiraiya rasengan",
        "skill_name": "선법 초대옥 나선환",
        "skill_sub": "Sage Art: Ultra-Big Ball Rasengan",
        "theme_color": (255, 130, 30),
        "quote": "대지를 녹이는 두꺼비 화염과 거대 나선 차크라 폭풍!"
    },
    "데이다라": {
        "giphy_char": "deidara akatsuki",
        "giphy_skill": "deidara explosion",
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
    ("우치하 사스케 (윤회안)", "나루토 (쿠라마 링크)")
]

def get_character_skill_info(char_name):
    clean = char_name.split()[0].replace("(", "").replace(")", "")
    for k, v in CHARACTER_SKILLS.items():
        if char_name in k or clean in k or k in char_name:
            return v
    return {
        "giphy_char": f"naruto {clean}",
        "giphy_skill": f"naruto {clean} jutsu",
        "skill_name": "비전 오의 필살일격",
        "skill_sub": "Ultimate Ninja Secret Technique",
        "theme_color": (255, 100, 50),
        "quote": "전력을 다한 영혼의 궁극 비오의 격돌!"
    }

# --- 2. Giphy 공식 나루토 애니메이션 비디오(MP4) 다운로더 & 캐시 엔진 ---

def fetch_giphy_anime_video(search_term, output_mp4):
    """
    Giphy API를 호출하여 실제 나루토 만화영화 공식 애니메이션 클립(MP4)을 다운로드합니다.
    """
    os.makedirs(os.path.dirname(output_mp4) or ".", exist_ok=True)
    if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 10000:
        return True

    print(f"[Giphy Anime Video Fetch] 검색어: '{search_term}' -> 다운로드 중...")
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q=naruto+{requests.utils.quote(search_term)}&limit=5&rating=pg-13"
    try:
        r = requests.get(url, timeout=10).json()
        items = r.get("data", [])
        for item in items:
            mp4_url = item.get("images", {}).get("original", {}).get("mp4") or item.get("images", {}).get("hd", {}).get("mp4")
            if mp4_url:
                v_resp = requests.get(mp4_url, timeout=20)
                if v_resp.status_code == 200 and len(v_resp.content) > 10000:
                    with open(output_mp4, "wb") as f:
                        f.write(v_resp.content)
                    print(f"[Giphy Video Success] {output_mp4} ({len(v_resp.content)/1024:.1f} KB)")
                    return True
    except Exception as e:
        print(f"[Giphy Fetch Exception]: {e}")
    return False

def get_character_anime_video(char_name):
    os.makedirs("assets/anime_clips", exist_ok=True)
    clean = char_name.split()[0].replace("(", "").replace(")", "")
    cached = f"assets/anime_clips/{clean}_char.mp4"
    skill_info = get_character_skill_info(char_name)
    if not os.path.exists(cached) or os.path.getsize(cached) < 10000:
        fetch_giphy_anime_video(skill_info["giphy_char"], cached)
    return cached

def get_skill_anime_video(char_name):
    os.makedirs("assets/anime_clips", exist_ok=True)
    clean = char_name.split()[0].replace("(", "").replace(")", "")
    cached = f"assets/anime_clips/{clean}_skill.mp4"
    skill_info = get_character_skill_info(char_name)
    if not os.path.exists(cached) or os.path.getsize(cached) < 10000:
        fetch_giphy_anime_video(skill_info["giphy_skill"], cached)
    return cached

def get_clash_anime_video():
    os.makedirs("assets/anime_clips", exist_ok=True)
    cached = "assets/anime_clips/ultimate_clash.mp4"
    if not os.path.exists(cached) or os.path.getsize(cached) < 10000:
        fetch_giphy_anime_video("anime clash explosion", cached)
    return cached

# --- 3. Gemini API를 통한 나루토 스탯 & 필살기 대본 생성 ---

def get_gemini_matchup_data(char_a, char_b, gemini_api_key=None):
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)

    prompt = f"""
당신은 나루토 공식 파워밸런스 전문 분석가입니다.
아래 두 나루토 캐릭터의 1:1 진검승부 및 '고유 필살기 정면 격돌'을 분석하여 반드시 아래 JSON 형식으로만 응답하세요.

캐릭터 A: {char_a} (필살기: {skill_a['skill_name']})
캐릭터 B: {char_b} (필살기: {skill_b['skill_name']})

비교 항목(5개):
1. 체술 (Taijutsu)
2. 인술 및 파괴력 (Ninjutsu & Power)
3. 환술 (Genjutsu)
4. 차크라량 및 스태미나 (Chakra Pool)
5. 전투 지능 및 속도 (Battle IQ & Speed)

JSON 응답 스키마:
{{
  "matchup": {{
    "character_a": "{char_a}",
    "character_b": "{char_b}",
    "title": "{char_a} VS {char_b}, 궁극의 필살기 격돌!"
  }},
  "stats": [
    {{
      "category": "스탯 카테고리 이름",
      "winner": "character_a 또는 character_b",
      "score": "현재 누적 스코어 (예: 1 - 0)",
      "reason": "해당 스탯 승리 이유 1줄 요약",
      "duration": 2.5
    }}
  ],
  "clash": {{
    "skill_a": "{skill_a['skill_name']}",
    "skill_b": "{skill_b['skill_name']}",
    "narration": "두 궁극기 격돌 묘사 1~2문장 (예: {char_a}의 {skill_a['skill_name']}과 {char_b}의 {skill_b['skill_name']}이 정면으로 충돌합니다!)",
    "clash_winner": "character_a 또는 character_b"
  }},
  "final_verdict": {{
    "winner": "character_a 또는 character_b",
    "final_score": "최종 승자 영문 (예: {char_a} WINS 또는 {char_b} WINS)",
    "narration": "최종 승부 결론 및 댓글 유도 멘트 1~2문장",
    "duration": 4.5
  }}
}}
"""

    if api_key:
        print(f"[Gemini Pro API] '{char_a} VS {char_b}' 스탯 및 필살기 격돌 분석 요청 중...")
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
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                res_json = resp.json()
                text_content = res_json['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(text_content)
                if "clash" not in data:
                    data["clash"] = {
                        "skill_a": skill_a["skill_name"],
                        "skill_b": skill_b["skill_name"],
                        "narration": f"{char_a}의 {skill_a['skill_name']}과 {char_b}의 {skill_b['skill_name']}이 정면으로 격돌합니다!",
                        "clash_winner": "character_a"
                    }
                print("[Gemini Pro API] 분석 성공!")
                return data
        except Exception:
            pass

    # Fallback
    categories = [
        ("체술 (Taijutsu)", "체술 숙련도와 근접전 센스 격돌!"),
        ("인술 (Ninjutsu)", "비전 인술과 광역 파괴력 대결!"),
        ("환술 (Genjutsu)", "동술 및 정신계 환술 제어력!"),
        ("차크라량 (Chakra Pool)", "혈통과 차크라 유지력의 차이!"),
        ("전투 지능 (Battle IQ)", "전황을 뒤집는 전술적 두뇌 플레이!")
    ]

    stats = []
    score_a = 0
    score_b = 0
    for cat_name, desc in categories:
        winner = random.choice(["character_a", "character_b"])
        if winner == "character_a":
            score_a += 1
            win_name = char_a
        else:
            score_b += 1
            win_name = char_b
        stats.append({
            "category": cat_name,
            "winner": winner,
            "score": f"{score_a} - {score_b}",
            "reason": f"{win_name}의 압도적인 {cat_name} 우세! {desc}",
            "duration": 2.5
        })

    final_winner = "character_a" if score_a >= score_b else "character_b"
    final_win_name = char_a if final_winner == "character_a" else char_b
    return {
        "matchup": {
            "character_a": char_a,
            "character_b": char_b,
            "title": f"{char_a} VS {char_b}, 궁극의 필살기 격돌!"
        },
        "stats": stats,
        "clash": {
            "skill_a": skill_a["skill_name"],
            "skill_b": skill_b["skill_name"],
            "narration": f"마침내 터져나오는 궁극의 오의! {char_a}의 {skill_a['skill_name']} 대 {char_b}의 {skill_b['skill_name']}! 거대한 차크라가 폭발하며 정면으로 격돌합니다!",
            "clash_winner": final_winner
        },
        "final_verdict": {
            "winner": final_winner,
            "final_score": f"{final_win_name} WINS!",
            "narration": f"치열한 필살기 격돌 끝에 승리를 거머쥔 {final_win_name}! 과연 여러분의 생각은 어떠신가요?",
            "duration": 4.5
        }
    }

# --- 4. Edge-TTS & gTTS 음성 합성 트랙 생성 ---

def generate_single_tts(text, output_file, voice="ko-KR-InJoonNeural"):
    try:
        import edge_tts
        async def _edge():
            communicate = edge_tts.Communicate(text, voice, rate="+15%")
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

def generate_voice_track(matchup_data, output_audio_path="temp/naruto_narration.mp3"):
    os.makedirs("temp/tts", exist_ok=True)
    combined_audio = AudioSegment.silent(duration=400)

    # 1. 인트로
    char_a = matchup_data['matchup']['character_a']
    char_b = matchup_data['matchup']['character_b']
    intro_text = f"{char_a} 대 {char_b}! 세기의 닌자 대결, 과연 승자는?"
    intro_path = "temp/tts/intro.mp3"
    generate_single_tts(intro_text, intro_path)
    combined_audio += AudioSegment.from_file(intro_path) + AudioSegment.silent(duration=300)

    # 2. 스탯 5개
    for idx, stat in enumerate(matchup_data["stats"]):
        stat_text = f"{stat['category']}! {stat['reason']}"
        stat_path = f"temp/tts/stat_{idx}.mp3"
        generate_single_tts(stat_text, stat_path)
        combined_audio += AudioSegment.from_file(stat_path) + AudioSegment.silent(duration=250)

    # 3. 필살기 격돌
    clash_text = matchup_data["clash"]["narration"]
    clash_path = "temp/tts/clash.mp3"
    generate_single_tts(clash_text, clash_path)
    combined_audio += AudioSegment.from_file(clash_path) + AudioSegment.silent(duration=400)

    # 4. 최종 판정
    final_text = f"최종 승부 결과! {matchup_data['final_verdict']['narration']}"
    final_path = "temp/tts/final.mp3"
    generate_single_tts(final_text, final_path)
    combined_audio += AudioSegment.from_file(final_path) + AudioSegment.silent(duration=500)

    combined_audio.export(output_audio_path, format="mp3", bitrate="192k")
    print(f"[TTS Complete] {output_audio_path} (총 길이: {len(combined_audio)/1000:.1f}초)")
    return len(combined_audio) / 1000.0

# --- 5. 폰트 로더 ---

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

# --- 6. 스탯 씬 및 오버레이 그래픽 생성기 ---

def create_stat_overlay_png(matchup_data, step_idx, output_png_path, width=1080, height=1920):
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    curr_stat = matchup_data["stats"][step_idx]

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 상단 캐릭터 A 이름 헤더
    draw.rectangle([0, 0, width, 120], fill=(0, 0, 0, 200))
    font_char = get_font(52, bold=True)
    draw.text((width//2, 60), char_a, font=font_char, fill=(255, 230, 80), anchor="mm")

    # 하단 캐릭터 B 이름 헤더
    draw.rectangle([0, height-120, width, height], fill=(0, 0, 0, 200))
    draw.text((width//2, height-60), char_b, font=font_char, fill=(100, 220, 255), anchor="mm")

    # 중앙 스탯 보드 (Y: 760 ~ 1160)
    draw.rounded_rectangle([40, 760, width-40, 1160], radius=32, fill=(0, 0, 0, 235), outline=(255, 215, 0), width=6)
    font_cat = get_font(48, bold=True)
    font_score = get_font(64, bold=True)
    font_reason = get_font(32, bold=False)

    draw.text((width//2, 825), curr_stat["category"], font=font_cat, fill=(255, 215, 0), anchor="mm")
    score_color = (255, 75, 75) if curr_stat["winner"] == "character_a" else (75, 175, 255)
    draw.text((width//2, 920), f"SCORE : {curr_stat['score']}", font=font_score, fill=score_color, anchor="mm")
    draw.text((width//2, 1030), curr_stat["reason"], font=font_reason, fill=(245, 245, 245), anchor="mm")

    img.save(output_png_path, "PNG")

def create_skill_charge_overlay_png(char_name, is_character_a, output_png_path, width=1080, height=1920):
    skill_info = get_character_skill_info(char_name)
    theme_col = skill_info["theme_color"]

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    banner_y = 120 if is_character_a else height - 360
    draw.rectangle([0, banner_y, width, banner_y + 240], fill=(0, 0, 0, 235))
    draw.line([(0, banner_y), (width, banner_y)], fill=theme_col, width=8)
    draw.line([(0, banner_y + 240), (width, banner_y + 240)], fill=theme_col, width=8)

    font_lead = get_font(42, bold=True)
    font_skill = get_font(58, bold=True)
    font_sub = get_font(30, bold=False)

    draw.text((width//2, banner_y + 45), f"🔥 {char_name} 오의(奧義) 발동! 🔥", font=font_lead, fill=(255, 230, 100), anchor="mm")
    draw.text((width//2, banner_y + 125), skill_info["skill_name"], font=font_skill, fill=theme_col, anchor="mm")
    draw.text((width//2, banner_y + 190), skill_info["skill_sub"], font=font_sub, fill=(220, 220, 220), anchor="mm")

    img.save(output_png_path, "PNG")

def create_clash_overlay_png(char_a, char_b, output_png_path, width=1080, height=1920):
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center_y = height // 2

    draw.rectangle([40, center_y - 130, width - 40, center_y + 130], fill=(0, 0, 0, 245), outline=(255, 215, 0), width=7)
    font_clash = get_font(60, bold=True)
    font_vs = get_font(34, bold=True)

    draw.text((width//2, center_y - 45), "💥 ULTIMATE SKILL CLASH 💥", font=font_clash, fill=(255, 230, 50), anchor="mm")
    draw.text((width//2, center_y + 40), f"{skill_a['skill_name']}  VS  {skill_b['skill_name']}", font=font_vs, fill=(255, 255, 255), anchor="mm")

    img.save(output_png_path, "PNG")

def create_verdict_overlay_png(matchup_data, output_png_path, width=1080, height=1920):
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    verdict = matchup_data["final_verdict"]
    winner_name = char_a if verdict["winner"] == "character_a" else char_b

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 상단 승리 타이틀
    draw.rectangle([0, 0, width, 300], fill=(0, 0, 0, 230))
    font_top = get_font(60, bold=True)
    font_subtop = get_font(42, bold=True)
    draw.text((width//2, 100), "🏆 FINAL WINNER 🏆", font=font_top, fill=(255, 215, 0), anchor="mm")
    draw.text((width//2, 200), verdict["final_score"], font=font_subtop, fill=(255, 80, 80), anchor="mm")

    # 하단 판정 설명 및 댓글창 유도 보드
    draw.rounded_rectangle([60, height - 420, width-60, height - 60], radius=32, fill=(0, 0, 0, 240), outline=(255, 215, 0), width=5)
    font_winner = get_font(52, bold=True)
    font_desc = get_font(32, bold=False)
    font_call = get_font(36, bold=True)

    draw.text((width//2, height - 350), f"승자: {winner_name}", font=font_winner, fill=(255, 230, 80), anchor="mm")
    draw.text((width//2, height - 250), verdict["narration"][:38], font=font_desc, fill=(240, 240, 240), anchor="mm")
    draw.text((width//2, height - 120), "💬 여러분의 생각은? 댓글로 토론해보세요!", font=font_call, fill=(80, 220, 255), anchor="mm")

    img.save(output_png_path, "PNG")

# --- 7. 실제 만화영화 비디오 숏츠 렌더러 (FFmpeg Multi-Video Live Compositor) ---

def render_naruto_shorts_video(matchup_data, voice_track, output_mp4="output_naruto_shorts.mp4"):
    os.makedirs("temp/scenes", exist_ok=True)
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    num_stats = len(matchup_data["stats"])

    voice_audio = AudioSegment.from_file(voice_track)
    total_voice_sec = len(voice_audio) / 1000.0
    print(f"\n[Full Anime Motion Engine] 총 {total_voice_sec:.1f}초 분량의 실제 만화영화(Anime Movie) 숏츠 비디오 합성 시작...")

    # 1. 캐릭터별 실제 공식 애니메이션 비디오 MP4 다운로드
    video_char_a = get_character_anime_video(char_a)
    video_char_b = get_character_anime_video(char_b)
    video_skill_a = get_skill_anime_video(char_a)
    video_skill_b = get_skill_anime_video(char_b)
    video_clash = get_clash_anime_video()

    fps = 30
    scene_clips = []

    # 2. 스탯 5개 씬 (상단: 캐릭터 A 애니메이션 비디오 루프 / 하단: 캐릭터 B 애니메이션 비디오 루프)
    stat_duration = max(2.5, (total_voice_sec * 0.55) / float(num_stats))
    for i in range(num_stats):
        overlay_png = os.path.abspath(f"temp/scenes/stat_overlay_{i}.png")
        create_stat_overlay_png(matchup_data, i, overlay_png)
        clip_stat = os.path.abspath(f"temp/scenes/clip_stat_{i}.mp4")

        # FFmpeg: 상단에 A 비디오(1080x960), 하단에 B 비디오(1080x960) vstack 후 중앙 오버레이 합성!
        filter_stat = (
            f"[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            f"[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bot];"
            f"[top][bot]vstack[bg];"
            f"[bg][2:v]overlay=0:0[vout]"
        )
        cmd_stat = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", video_char_a,
            "-stream_loop", "-1", "-i", video_char_b,
            "-i", overlay_png,
            "-filter_complex", filter_stat,
            "-map", "[vout]",
            "-t", str(stat_duration),
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
            clip_stat
        ]
        subprocess.run(cmd_stat, check=True)
        scene_clips.append(clip_stat)

    # 3. 스킬 A 시전 씬: 캐릭터 A의 실제 공식 오의 애니메이션 비디오 풀스크린 재생
    skill_a_duration = 2.5
    overlay_skill_a = os.path.abspath("temp/scenes/overlay_skill_a.png")
    create_skill_charge_overlay_png(char_a, True, overlay_skill_a)
    clip_skill_a = os.path.abspath("temp/scenes/clip_skill_a.mp4")

    filter_skill_a = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[bg][1:v]overlay=0:0[vout]"
    )
    cmd_skill_a = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_skill_a,
        "-i", overlay_skill_a,
        "-filter_complex", filter_skill_a,
        "-map", "[vout]",
        "-t", str(skill_a_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_skill_a
    ]
    subprocess.run(cmd_skill_a, check=True)
    scene_clips.append(clip_skill_a)

    # 4. 스킬 B 시전 씬: 캐릭터 B의 실제 공식 오의 애니메이션 비디오 풀스크린 재생
    skill_b_duration = 2.5
    overlay_skill_b = os.path.abspath("temp/scenes/overlay_skill_b.png")
    create_skill_charge_overlay_png(char_b, False, overlay_skill_b)
    clip_skill_b = os.path.abspath("temp/scenes/clip_skill_b.mp4")

    filter_skill_b = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[bg][1:v]overlay=0:0[vout]"
    )
    cmd_skill_b = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_skill_b,
        "-i", overlay_skill_b,
        "-filter_complex", filter_skill_b,
        "-map", "[vout]",
        "-t", str(skill_b_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_skill_b
    ]
    subprocess.run(cmd_skill_b, check=True)
    scene_clips.append(clip_skill_b)

    # 5. 정면 격돌 씬 (💥 ULTIMATE CLASH 💥): 실제 오의 대격돌 & 대폭발 애니메이션 비디오 재생
    clash_duration = 3.5
    overlay_clash = os.path.abspath("temp/scenes/overlay_clash.png")
    create_clash_overlay_png(char_a, char_b, overlay_clash)
    clip_clash = os.path.abspath("temp/scenes/clip_clash.mp4")

    filter_clash = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[bg][1:v]overlay=0:0[vout]"
    )
    cmd_clash = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_clash,
        "-i", overlay_clash,
        "-filter_complex", filter_clash,
        "-map", "[vout]",
        "-t", str(clash_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_clash
    ]
    subprocess.run(cmd_clash, check=True)
    scene_clips.append(clip_clash)

    # 6. 최종 승자 판정 씬 (Final Verdict): 승리한 캐릭터의 실제 애니메이션 비디오 재생
    verdict_duration = 5.0
    overlay_verdict = os.path.abspath("temp/scenes/overlay_verdict.png")
    create_verdict_overlay_png(matchup_data, overlay_verdict)
    clip_verdict = os.path.abspath("temp/scenes/clip_verdict.mp4")
    winner_video = video_char_a if matchup_data["final_verdict"]["winner"] == "character_a" else video_char_b

    filter_verdict = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[bg][1:v]overlay=0:0[vout]"
    )
    cmd_verdict = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", winner_video,
        "-i", overlay_verdict,
        "-filter_complex", filter_verdict,
        "-map", "[vout]",
        "-t", str(verdict_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_verdict
    ]
    subprocess.run(cmd_verdict, check=True)
    scene_clips.append(clip_verdict)

    # Concat
    concat_txt = "temp/scenes/concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")

    temp_video = "temp/scenes/video_combined.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", temp_video], check=True)

    # BGM + TTS 음성 믹싱
    bgm_files = glob.glob("assets/audio/music/*.mp3") + glob.glob("assets/audio/*/*.mp3")
    bgm_path = random.choice(bgm_files) if bgm_files else None

    if bgm_path and os.path.exists(bgm_path):
        filter_audio = "[1:a]volume=1.0[v_voice];[2:a]volume=0.22,aloop=loop=-1:size=2e+09[v_bgm];[v_voice][v_bgm]amix=inputs=2:duration=first[aout]"
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
    print(f" [Naruto Full-Motion Anime Movie Shorts Rendered!]")
    print(f" [Output File] {output_mp4} (100% Real Anime Video Footage)")
    print(f"=======================================================\n")

# --- 8. 메인 실행 진입점 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)

    input_char_a = os.getenv("INPUT_CHAR_A", "").strip()
    input_char_b = os.getenv("INPUT_CHAR_B", "").strip()

    if input_char_a and input_char_b:
        char_a = input_char_a
        char_b = input_char_b
    else:
        char_a, char_b = random.choice(CURATED_MATCHUPS)

    print(f"\n[Naruto Matchup Selected] '{char_a}' VS '{char_b}'")

    # 1. Gemini Pro 스탯 & 고유 필살기 분석
    matchup_data = get_gemini_matchup_data(char_a, char_b)

    # 2. 한국어 TTS 내레이션 음성 생성
    voice_track = "temp/naruto_narration.mp3"
    voice_duration = generate_voice_track(matchup_data, voice_track)

    # 3. 1080x1920 숏츠 비디오 합성
    output_video = "output_naruto_shorts.mp4"
    render_naruto_shorts_video(matchup_data, voice_track, output_video)

    # 4. 메타데이터 생성
    skill_a_name = matchup_data["clash"]["skill_a"]
    skill_b_name = matchup_data["clash"]["skill_b"]
    final_title = f"{char_a} [{skill_a_name}] VS {char_b} [{skill_b_name}] 세기의 오의 격돌! #Shorts"
    desc = (
        f"🔥 {char_a} ({skill_a_name}) VS {char_b} ({skill_b_name})!\n\n"
        f"나루토 세계관 최강의 고유 필살기 정면 승부!\n"
        f"과연 격돌의 승자는 누구일까요? 여러분의 의견을 댓글로 남겨주세요!\n\n"
        f"#{char_a.replace(' ', '')} #{char_b.replace(' ', '')} #나루토 #오의격돌 #나루토쇼츠 #가상대결 #Shorts #Naruto"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Naruto VS Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"[Metadata Saved] {final_title}")
