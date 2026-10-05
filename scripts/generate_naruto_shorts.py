import os
import sys
import glob
import json
import math
import random
import asyncio
import subprocess
import requests
import unicodedata
import numpy as np
from pathlib import Path
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- 1. 나루토 대표 매치업 및 캐릭터 & 고유 스킬 데이터베이스 ---

CHARACTER_SKILLS = {
    "우치하 이타치": {
        "skill_name": "츠쿠요미 & 아마테라스",
        "skill_sub": "Tsukuyomi & Amaterasu (만화경 사륜안 오의)",
        "theme_color": (255, 40, 40),
        "aura_color": (160, 0, 30),
        "quote": "꺼지지 않는 흑염과 정신을 파괴하는 절대 환술!"
    },
    "페인 (텐도)": {
        "skill_name": "신라천정 & 지폭천성",
        "skill_sub": "Shinra Tensei & Chibaku Tensei (윤회안 신급 오의)",
        "theme_color": (180, 70, 255),
        "aura_color": (255, 120, 0),
        "quote": "세계에 고통을! 시공을 일그러뜨리는 척력과 만유인력!"
    },
    "나루토 (선인 모드)": {
        "skill_name": "선법 풍둔 나선수리검",
        "skill_sub": "Sage Art: Wind Style Rasenshuriken",
        "theme_color": (0, 230, 255),
        "aura_color": (255, 180, 0),
        "quote": "자연 차크라를 극한으로 융합한 세포 파괴 소용돌이!"
    },
    "나루토 (쿠라마 링크)": {
        "skill_name": "미수화 초대옥 나선연환",
        "skill_sub": "Kurama Chakra Tailed Beast Rasen-Barrage",
        "theme_color": (255, 190, 0),
        "aura_color": (255, 80, 0),
        "quote": "구미의 차크라와 황금빛 선술이 빚어내는 궁극의 탄막!"
    },
    "우치하 사스케 (윤회안)": {
        "skill_name": "스사노오 치도리 & 인드라의 화살",
        "skill_sub": "Susanoo Chidori & Indra's Arrow",
        "theme_color": (90, 150, 255),
        "aura_color": (180, 60, 255),
        "quote": "천동을 가르는 뇌둔과 미수의 차크라를 실은 벼락 화살!"
    },
    "우치하 마다라": {
        "skill_name": "완성체 스사노오 & 천애진성",
        "skill_sub": "Perfect Susanoo & Tengai Shinsei",
        "theme_color": (50, 120, 255),
        "aura_color": (220, 40, 90),
        "quote": "산맥을 가르는 거신참과 하늘에서 떨어지는 거대 운석!"
    },
    "센주 하시라마": {
        "skill_name": "선법 목둔 진수천수 정상화불",
        "skill_sub": "Sage Art Wood Style: True Several Thousand Hands",
        "theme_color": (50, 230, 120),
        "aura_color": (210, 220, 40),
        "quote": "수천 개의 주먹으로 전장을 초토화하는 닌자의 신의 위엄!"
    },
    "나미카제 미나토": {
        "skill_name": "비뢰신의 술 2의 단 & 나선환",
        "skill_sub": "Flying Raijin Level 2 & Massive Rasengan",
        "theme_color": (255, 230, 40),
        "aura_color": (0, 210, 255),
        "quote": "눈 깜짝할 사이에 배후를 찌르는 금빛 섬광의 일격!"
    },
    "마이트 가이 (8문 둔갑)": {
        "skill_name": "사문 개방 궁극오의 밤 가이",
        "skill_sub": "Night Guy (Eight Inner Gates Released)",
        "theme_color": (255, 30, 70),
        "aura_color": (255, 120, 0),
        "quote": "공간마저 일그러뜨리는 핏빛 붉은 용의 궁극의 킥!"
    },
    "하타케 카카시 (카무이)": {
        "skill_name": "카무이 뇌절 & 쌍신 카무이 수리검",
        "skill_sub": "Kamui Lightning Blade & Kamui Shuriken",
        "theme_color": (120, 210, 255),
        "aura_color": (170, 90, 255),
        "quote": "이공간으로 왜곡해 모든 방어를 무시하는 신속의 참격!"
    },
    "우치하 오비토 (육도)": {
        "skill_name": "구도옥 참격 & 천소모포의 검",
        "skill_sub": "Truth-Seeking Orbs & Sword of Nunoboko",
        "theme_color": (200, 200, 220),
        "aura_color": (130, 50, 200),
        "quote": "모든 인술을 무효화하는 창세의 영혼검 일격!"
    },
    "지라이야 (선인 모드)": {
        "skill_name": "선법 초대옥 나선환 & 두꺼비 유염탄",
        "skill_sub": "Sage Art: Ultra-Big Ball Rasengan & Toad Flame Bomb",
        "theme_color": (255, 130, 30),
        "aura_color": (180, 40, 20),
        "quote": "대지를 녹이는 두꺼비 화염과 거대 나선 차크라 폭풍!"
    },
    "사소리": {
        "skill_name": "적비진 백기의 연무 & 사철계법",
        "skill_sub": "Red Secret Technique: Performance of a Hundred Puppets",
        "theme_color": (200, 50, 80),
        "aura_color": (90, 40, 150),
        "quote": "전장을 가득 메우는 100기의 꼭두각시와 맹독 사철 가시!"
    },
    "데이다라": {
        "skill_name": "C4 카루라 & 궁극예술 C0 자폭",
        "skill_sub": "C4 Karura & Ultimate Art C0 Detonation",
        "theme_color": (255, 210, 40),
        "aura_color": (255, 60, 20),
        "quote": "예술은 폭발이다! 초미세 나노 폭탄과 10km 소멸 섬광!"
    },
    "센주 토비라마": {
        "skill_name": "수둔 수룡교자 & 비뢰신 참격",
        "skill_sub": "Water Style: Water Dragon & Flying Raijin Slash",
        "theme_color": (40, 160, 255),
        "aura_color": (255, 255, 255),
        "quote": "물 없는 전장에서 소환하는 거대 수룡과 즉사 시공간 베기!"
    },
    "오로치마루": {
        "skill_name": "초재생 팔기지술 & 초지검 난무",
        "skill_sub": "Eight Branches Technique & Kusanagi Blade",
        "theme_color": (160, 80, 220),
        "aura_color": (80, 200, 100),
        "quote": "신화의 8두 백사와 불사의 재생력을 지닌 궁극의 변신술!"
    }
}

NARUTO_CHARACTERS = list(CHARACTER_SKILLS.keys())

CURATED_MATCHUPS = [
    ("우치하 이타치", "페인 (텐도)"),
    ("지라이야 (선인 모드)", "나루토 (선인 모드)"),
    ("나미카제 미나토", "우치하 이타치"),
    ("사소리", "데이다라"),
    ("우치하 마다라", "센주 하시라마"),
    ("마이트 가이 (8문 둔갑)", "우치하 마다라"),
    ("하타케 카카시 (카무이)", "우치하 오비토 (육도)"),
    ("우치하 사스케 (윤회안)", "나루토 (쿠라마 링크)"),
    ("센주 토비라마", "나미카제 미나토"),
    ("오로치마루", "지라이야 (선인 모드)")
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
        "aura_color": (200, 40, 20),
        "quote": "전력을 다한 영혼의 궁극 비오의 격돌!"
    }

# --- 2. Gemini API를 통한 나루토 스탯 & 필살기 격돌 대본 생성 ---

def get_gemini_matchup_data(char_a, char_b, gemini_api_key=None):
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)

    prompt = f"""
당신은 나루토 공식 파워밸런스 전문 분석가입니다.
아래 두 나루토 캐릭터의 1:1 진검승부 및 '필살기 정면 격돌'을 분석하여 반드시 아래 JSON 형식으로만 응답하세요.

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
                print("[Gemini Pro API] 스탯 & 필살기 분석 데이터 수신 성공!")
                return data
        except Exception as e:
            print(f"[Gemini API Exception]: {e}")

    # Fallback 알고리즘
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

# --- 3. Edge-TTS & gTTS 음성 합성 트랙 생성 ---

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

    # 3. 필살기 격돌 (Skill Clash)
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

# --- 4. 그래픽 & 폰트 & 캐릭터 에셋 엔진 ---

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

ANIME_CHARACTER_IMAGES = {
    "우치하 이타치": ["https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=800&q=80"],
    "페인 (텐도)": ["https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=800&q=80"],
    "지라이야 (선인 모드)": ["https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80"],
    "나루토 (선인 모드)": ["https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80"],
    "나루토 (쿠라마 링크)": ["https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=800&q=80"],
    "나미카제 미나토": ["https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=800&q=80"],
    "우치하 마다라": ["https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=800&q=80"],
    "센주 하시라마": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80"],
    "우치하 사스케 (윤회안)": ["https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80"],
    "하타케 카카시 (카무이)": ["https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80"],
    "마이트 가이 (8문 둔갑)": ["https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=800&q=80"]
}

def fetch_character_anime_image(char_name, output_path):
    clean = char_name.split()[0].replace("(", "").replace(")", "")
    urls = ANIME_CHARACTER_IMAGES.get(char_name, ANIME_CHARACTER_IMAGES.get(clean, [
        "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=800&q=80"
    ]))
    url = random.choice(urls)
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False

def get_character_image(char_name, size=(500, 600), is_top=True):
    os.makedirs("assets/characters", exist_ok=True)
    clean_name = char_name.split()[0].replace("(", "").replace(")", "")
    possible_paths = [
        f"assets/characters/{char_name}.png",
        f"assets/characters/{clean_name}.png",
        f"assets/characters/{char_name}.jpg",
        f"assets/characters/{clean_name}.jpg"
    ]
    found_path = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            found_path = p
            break
    if not found_path:
        target_path = f"assets/characters/{clean_name}.jpg"
        if fetch_character_anime_image(char_name, target_path):
            found_path = target_path

    if found_path and os.path.exists(found_path):
        try:
            base_img = Image.open(found_path).convert("RGBA")
            base_img.thumbnail((size[0]*2, size[1]*2), Image.Resampling.LANCZOS)
            w, h = base_img.size
            left = (w - size[0]) // 2 if w > size[0] else 0
            top = (h - size[1]) // 2 if h > size[1] else 0
            cropped = base_img.crop((left, top, left + size[0], top + size[1])).resize(size, Image.Resampling.LANCZOS)

            card = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(card)
            border_color = (255, 60, 60, 240) if is_top else (60, 140, 255, 240)
            mask = Image.new("L", size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle([0, 0, size[0], size[1]], radius=28, fill=255)
            card.paste(cropped, (0, 0), mask)
            draw.rounded_rectangle([2, 2, size[0]-2, size[1]-2], radius=28, outline=border_color, width=6)
            return card
        except Exception:
            pass

    card = Image.new("RGBA", size, (25, 25, 35, 255))
    draw = ImageDraw.Draw(card)
    bg_color = (180, 40, 30) if is_top else (30, 70, 180)
    draw.rounded_rectangle([10, 10, size[0]-10, size[1]-10], radius=24, fill=bg_color, outline=(255, 215, 0), width=4)
    font_char = get_font(size=44, bold=True)
    draw.text((size[0]//2, size[1]//2), char_name, font=font_char, fill=(255, 255, 255), anchor="mm")
    return card

# --- 5. 씬 카드 렌더러 (스탯 씬 + 필살기 시전 씬 + 격돌 씬 + 피날레 씬) ---

def create_stat_scene_card(matchup_data, step_idx, output_png_path, width=1080, height=1920):
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    img = Image.new("RGBA", (width, height), (12, 14, 22, 255))
    draw = ImageDraw.Draw(img)

    # 상단 캐릭터 A
    avatar_a = get_character_image(char_a, size=(520, 580), is_top=True)
    img.paste(avatar_a, ((width - 520)//2, 130), avatar_a)
    font_title = get_font(52, bold=True)
    draw.text((width//2, 75), char_a, font=font_title, fill=(255, 225, 100), anchor="mm")

    # 하단 캐릭터 B
    avatar_b = get_character_image(char_b, size=(520, 580), is_top=False)
    img.paste(avatar_b, ((width - 520)//2, 1210), avatar_b)
    draw.text((width//2, 1845), char_b, font=font_title, fill=(100, 220, 255), anchor="mm")

    # 중앙 스탯 보드
    draw.rounded_rectangle([50, 760, width-50, 1160], radius=32, fill=(8, 10, 18, 245), outline=(255, 215, 0), width=5)
    curr_stat = matchup_data["stats"][step_idx]
    font_cat = get_font(48, bold=True)
    font_score = get_font(64, bold=True)
    font_reason = get_font(32, bold=False)

    draw.text((width//2, 825), curr_stat["category"], font=font_cat, fill=(255, 215, 0), anchor="mm")
    score_color = (255, 75, 75) if curr_stat["winner"] == "character_a" else (75, 175, 255)
    draw.text((width//2, 920), f"SCORE : {curr_stat['score']}", font=font_score, fill=score_color, anchor="mm")
    draw.text((width//2, 1030), curr_stat["reason"], font=font_reason, fill=(245, 245, 245), anchor="mm")

    img.save(output_png_path, "PNG")

def create_skill_charge_card(char_name, is_character_a, output_png_path, width=1080, height=1920):
    """
    캐릭터가 고유 필살기를 시전하며 차크라를 끌어올리는 역동적인 컷인 카드 생성
    """
    skill_info = get_character_skill_info(char_name)
    theme_col = skill_info["theme_color"]
    aura_col = skill_info["aura_color"]

    img = Image.new("RGBA", (width, height), (8, 8, 14, 255))
    draw = ImageDraw.Draw(img)

    # 차크라 방사형 광선 배경
    center_y = 750 if is_character_a else 1150
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        ex = int(width/2 + 1200 * math.cos(rad))
        ey = int(center_y + 1200 * math.sin(rad))
        draw.line([(width//2, center_y), (ex, ey)], fill=(*aura_col, 40), width=6)

    # 캐릭터 초대형 클로즈업 카드
    avatar = get_character_image(char_name, size=(700, 800), is_top=is_character_a)
    img.paste(avatar, ((width - 700)//2, center_y - 400), avatar)

    # 스킬 시전 헤더 배너
    banner_y = 180 if is_character_a else 1500
    draw.rectangle([0, banner_y, width, banner_y + 220], fill=(0, 0, 0, 230))
    draw.line([(0, banner_y), (width, banner_y)], fill=theme_col, width=6)
    draw.line([(0, banner_y + 220), (width, banner_y + 220)], fill=theme_col, width=6)

    font_lead = get_font(38, bold=True)
    font_skill = get_font(56, bold=True)
    font_sub = get_font(28, bold=False)

    draw.text((width//2, banner_y + 40), f"🔥 {char_name} 오의(奧義) 발동! 🔥", font=font_lead, fill=(255, 230, 100), anchor="mm")
    draw.text((width//2, banner_y + 115), skill_info["skill_name"], font=font_skill, fill=theme_col, anchor="mm")
    draw.text((width//2, banner_y + 175), skill_info["skill_sub"], font=font_sub, fill=(220, 220, 220), anchor="mm")

    img.save(output_png_path, "PNG")

def create_clash_impact_card(char_a, char_b, output_png_path, width=1080, height=1920):
    """
    두 고유 필살기가 중앙에서 맹렬하게 충돌하는 궁극의 오의 격돌 카드 생성 (에너지 파티클 & 충격파)
    """
    skill_a = get_character_skill_info(char_a)
    skill_b = get_character_skill_info(char_b)

    img = Image.new("RGBA", (width, height), (5, 5, 10, 255))
    draw = ImageDraw.Draw(img)

    # 상단 A 에너지 영역 (Red/Yellow/Purple)
    col_a = skill_a["theme_color"]
    for y in range(0, height//2, 8):
        alpha = int(180 * (1.0 - y / (height/2)))
        draw.line([(0, y), (width, y)], fill=(*col_a, alpha), width=8)

    # 하단 B 에너지 영역 (Blue/Cyan/Green)
    col_b = skill_b["theme_color"]
    for y in range(height//2, height, 8):
        alpha = int(180 * ((y - height/2) / (height/2)))
        draw.line([(0, y), (width, y)], fill=(*col_b, alpha), width=8)

    # 양 캐릭터 상하 배치 (격돌 돌진 모션)
    avatar_a = get_character_image(char_a, size=(460, 520), is_top=True)
    img.paste(avatar_a, ((width - 460)//2, 100), avatar_a)

    avatar_b = get_character_image(char_b, size=(460, 520), is_top=False)
    img.paste(avatar_b, ((width - 460)//2, 1300), avatar_b)

    # 중앙 충돌 충격파 (Shockwave Rings & Flash)
    center_x, center_y = width//2, height//2
    for r in [280, 220, 160, 100, 50]:
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=(255, 255, 255, 240), width=10)
    
    # 에너지 스파크 광선
    random.seed(42)
    for _ in range(40):
        rad = random.uniform(0, 2*math.pi)
        length = random.randint(150, 480)
        ex = int(center_x + length * math.cos(rad))
        ey = int(center_y + length * math.sin(rad))
        spark_col = random.choice([col_a, col_b, (255, 255, 255), (255, 220, 0)])
        draw.line([(center_x, center_y), (ex, ey)], fill=spark_col, width=random.randint(3, 8))

    # 중앙 CLASH 엠블럼
    draw.rectangle([60, center_y - 120, width - 60, center_y + 120], fill=(0, 0, 0, 245), outline=(255, 215, 0), width=6)
    font_clash = get_font(58, bold=True)
    font_vs = get_font(34, bold=True)

    draw.text((center_x, center_y - 45), "💥 ULTIMATE SKILL CLASH 💥", font=font_clash, fill=(255, 230, 50), anchor="mm")
    draw.text((center_x, center_y + 40), f"{skill_a['skill_name']}  VS  {skill_b['skill_name']}", font=font_vs, fill=(255, 255, 255), anchor="mm")

    img.save(output_png_path, "PNG")

def create_verdict_card(matchup_data, output_png_path, width=1080, height=1920):
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    verdict = matchup_data["final_verdict"]
    winner_name = char_a if verdict["winner"] == "character_a" else char_b

    img = Image.new("RGBA", (width, height), (10, 10, 18, 255))
    draw = ImageDraw.Draw(img)

    # 승자 캐릭터 특대형 헌정 카드
    avatar_win = get_character_image(winner_name, size=(650, 750), is_top=(verdict["winner"] == "character_a"))
    img.paste(avatar_win, ((width - 650)//2, 380), avatar_win)

    # 상단 승리 타이틀
    font_top = get_font(60, bold=True)
    font_subtop = get_font(42, bold=True)
    draw.text((width//2, 160), "🏆 FINAL WINNER 🏆", font=font_top, fill=(255, 215, 0), anchor="mm")
    draw.text((width//2, 260), verdict["final_score"], font=font_subtop, fill=(255, 80, 80), anchor="mm")

    # 하단 판정 설명 및 댓글창 유도 보드
    draw.rounded_rectangle([60, 1220, width-60, 1750], radius=32, fill=(0, 0, 0, 240), outline=(255, 215, 0), width=5)
    font_winner = get_font(52, bold=True)
    font_desc = get_font(32, bold=False)
    font_call = get_font(36, bold=True)

    draw.text((width//2, 1310), f"승자: {winner_name}", font=font_winner, fill=(255, 230, 80), anchor="mm")
    draw.text((width//2, 1420), verdict["narration"][:38], font=font_desc, fill=(240, 240, 240), anchor="mm")
    if len(verdict["narration"]) > 38:
        draw.text((width//2, 1475), verdict["narration"][38:76] + "...", font=font_desc, fill=(240, 240, 240), anchor="mm")
    
    draw.text((width//2, 1630), "💬 여러분의 생각은? 댓글로 토론해보세요!", font=font_call, fill=(80, 220, 255), anchor="mm")

    img.save(output_png_path, "PNG")

# --- 6. FFmpeg 역동적인 모션 애니메이션 숏츠 비디오 합성 엔진 ---

def render_naruto_shorts_video(matchup_data, voice_track, output_mp4="output_naruto_shorts.mp4"):
    os.makedirs("temp/scenes", exist_ok=True)
    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]
    num_stats = len(matchup_data["stats"])
    
    voice_audio = AudioSegment.from_file(voice_track)
    total_voice_sec = len(voice_audio) / 1000.0
    print(f"\n[Motion Animation Engine] 총 {total_voice_sec:.1f}초 분량의 고유 스킬 격돌 숏츠 애니메이션 생성 시작...")

    fps = 30
    scene_clips = []

    # 1. 스탯 5개 씬 (다이내믹 줌인 카메라 무빙)
    stat_duration = max(2.5, (total_voice_sec * 0.55) / float(num_stats))
    for i in range(num_stats):
        card_png = os.path.abspath(f"temp/scenes/stat_{i}.png")
        create_stat_scene_card(matchup_data, i, card_png)
        
        clip_mp4 = os.path.abspath(f"temp/scenes/clip_stat_{i}.mp4")
        frames_count = int(stat_duration * fps)
        zoom_filter = f"zoompan=z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_count}:s=1080x1920:fps={fps}"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", card_png,
            "-vf", zoom_filter,
            "-t", str(stat_duration),
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
            clip_mp4
        ]
        subprocess.run(cmd, check=True)
        scene_clips.append(clip_mp4)

    # 2. 스킬 시전 씬 A (캐릭터 A 고유 필살기 충전)
    charge_a_duration = 2.0
    charge_a_png = os.path.abspath("temp/scenes/charge_a.png")
    create_skill_charge_card(char_a, True, charge_a_png)
    clip_charge_a = os.path.abspath("temp/scenes/clip_charge_a.mp4")
    zoom_charge_a = f"zoompan=z='min(zoom+0.003,1.25)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':d={int(charge_a_duration*fps)}:s=1080x1920:fps={fps}"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", charge_a_png,
        "-vf", zoom_charge_a, "-t", str(charge_a_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_charge_a
    ], check=True)
    scene_clips.append(clip_charge_a)

    # 3. 스킬 시전 씬 B (캐릭터 B 고유 필살기 충전)
    charge_b_duration = 2.0
    charge_b_png = os.path.abspath("temp/scenes/charge_b.png")
    create_skill_charge_card(char_b, False, charge_b_png)
    clip_charge_b = os.path.abspath("temp/scenes/clip_charge_b.mp4")
    zoom_charge_b = f"zoompan=z='min(zoom+0.003,1.25)':x='iw/2-(iw/zoom/2)':y='2*ih/3-(2*ih/zoom/3)':d={int(charge_b_duration*fps)}:s=1080x1920:fps={fps}"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", charge_b_png,
        "-vf", zoom_charge_b, "-t", str(charge_b_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_charge_b
    ], check=True)
    scene_clips.append(clip_charge_b)

    # 4. 필살기 정면 격돌 씬 (THE ULTIMATE CLASH - 격렬한 화면 진동 & 줌인)
    clash_duration = 3.5
    clash_png = os.path.abspath("temp/scenes/clash.png")
    create_clash_impact_card(char_a, char_b, clash_png)
    clip_clash = os.path.abspath("temp/scenes/clip_clash.mp4")
    # 카메라 진동(Tremor / Shake)과 초고속 줌인 복합 필터
    shake_filter = f"zoompan=z='min(zoom+0.004,1.35)':x='iw/2-(iw/zoom/2)+15*sin(in*3)':y='ih/2-(ih/zoom/2)+15*cos(in*3)':d={int(clash_duration*fps)}:s=1080x1920:fps={fps}"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", clash_png,
        "-vf", shake_filter, "-t", str(clash_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_clash
    ], check=True)
    scene_clips.append(clip_clash)

    # 5. 최종 판정 및 승자 피날레 씬
    verdict_duration = 5.0
    verdict_png = os.path.abspath("temp/scenes/verdict.png")
    create_verdict_card(matchup_data, verdict_png)
    clip_verdict = os.path.abspath("temp/scenes/clip_verdict.mp4")
    zoom_verdict = f"zoompan=z='min(zoom+0.002,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(verdict_duration*fps)}:s=1080x1920:fps={fps}"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", verdict_png,
        "-vf", zoom_verdict, "-t", str(verdict_duration),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast",
        clip_verdict
    ], check=True)
    scene_clips.append(clip_verdict)

    # Concat
    concat_txt = "temp/scenes/concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")

    temp_video = "temp/scenes/video_combined.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", temp_video], check=True)

    # BGM + TTS 합성
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
    print(f" [Naruto Skill Clash Anime Shorts Rendered Successfully!]")
    print(f" [Output File] {output_mp4} (1080x1920 30fps with Dynamic Skill Clash & Camera Shake)")
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

    print(f"\n[Naruto Matchup Selected] '{char_a}' VS '{char_b}'")

    # 1. Gemini Pro 스탯 & 고유 필살기 분석
    matchup_data = get_gemini_matchup_data(char_a, char_b)

    # 2. 한국어 TTS 내레이션 음성 생성 (필살기 격돌 내레이션 포함)
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
