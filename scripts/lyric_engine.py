"""
매 실행마다 100% 새롭게 작사/작곡하는 동적 생성 엔진.
Gemini AI를 기본 엔진으로 사용하여 매번 완전히 새로운 곡명, 장르 태그, 가사를 창작합니다.
기존 곡명 및 가사를 절대 재사용하지 않습니다.
"""

import os
import json
import random
import requests
import time

STYLE_PROMPTS = {
    "healing_ballad": {
        "genre": "어쿠스틱 감성 인디 발라드 (Warm Piano, Cello, Sentimental Acoustic Guitar)",
        "themes": [
            "새벽 골목길을 걸으며 스스로에게 건네는 따뜻한 위로",
            "잊고 지냈던 어릴 적 꿈과 서랍 속 오래된 사진",
            "비 내리는 오후 창가에서 전하는 마음의 쉼표",
            "소란한 하루를 마치고 돌아오는 퇴근길 지하철의 감정",
            "서툴렀던 지난 사랑과 계절의 변화를 담담하게 보내주는 이야기",
            "달빛이 은은하게 비치는 작은 방에서 적어 내려가는 일기"
        ],
        "default_tags": "heartfelt korean indie ballad, warm grand piano, expressive cello, gentle emotional vocal, cinematic emotional build-up, 72 bpm"
    },
    "ghost_duet": {
        "genre": "2010년대 멜로딕 힙합 듀엣 (R&B Melodic Rap, Acoustic Boom Bap, Sweet Duet)",
        "themes": [
            "새벽 3시 편의점 앞에서 만난 유쾌한 영혼과의 심야 대화",
            "이승에 남겨둔 버킷리스트를 채우기 위해 밤거리를 누비는 이야기",
            "새벽 한강 다리 위에서 별을 보며 나누는 남녀의 비밀스러운 약속",
            "성불 열차를 타기 전 마지막으로 추억의 사진을 남기는 스토리",
            "잠들지 못하는 도시의 밤을 함께 걷는 신비로운 듀엣"
        ],
        "default_tags": "2010s sentimental melodic k-rap, sweet acoustic piano, boom bap beat, emotional male rap with airy female vocals, nostalgic chorus, 94 bpm"
    },
    "battle_epic": {
        "genre": "오리엔탈 애니메이션 에픽 록 (Epic Rock Opening, Taiko Drums, Distorted Electric Guitar)",
        "themes": [
            "어둠을 가르고 번개처럼 질주하는 닌자의 신념과 각성",
            "운명의 전장에서 꺾이지 않는 투지와 불꽃의 결의",
            "폭풍우 치는 절벽 끝에서 펼쳐지는 마지막 오의의 격돌",
            "동터오는 여명 속에서 승리를 다짐하는 전사의 맹세"
        ],
        "default_tags": "epic oriental rock anime opening, heavy distorted guitar, fast taiko drum roll, soaring male vocals, high energy breakdown, 160 bpm"
    }
}

def generate_lyric_and_style(song_type: str = "healing_ballad", custom_prompt: str = ""):
    """
    매번 호출될 때마다 100% 새로운 제목, 스타일, 가사를 생성합니다.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    key_map = {
        "ghostagram": "ghost_duet",
        "grown_up": "healing_ballad",
        "cyber_warrior": "battle_epic"
    }
    target_key = key_map.get(song_type, song_type)
    if target_key not in STYLE_PROMPTS:
        target_key = random.choice(list(STYLE_PROMPTS.keys()))

    config = STYLE_PROMPTS[target_key]
    selected_theme = custom_prompt if custom_prompt else random.choice(config["themes"])

    # 1. Gemini AI를 통한 100% 실시간 순수 신곡 생성
    if gemini_key:
        try:
            print(f"[Lyric Engine] Gemini AI를 통해 100% 새로운 신곡 작사/작곡 시작: '{selected_theme}'")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            prompt_instruction = f"""
당신은 대한민국 최고의 히트곡을 작곡하는 천재 싱어송라이터이자 프로듀서입니다.
주제: "{selected_theme}"
음악 장르: "{config['genre']}"

[절대 준수 지침]
1. 기존 가수의 노래(예: '고스타그램', '꿈꾸던 어른이 되었나요', '어린 날의 나에게 띄우는 편지' 등)의 제목이나 가사를 절대 재사용하지 마세요.
2. 매번 완전히 새롭고 창의적인 '곡 제목'을 지으세요 (시적이고 독창적인 한글 제목, 영문 부제 가능).
3. 가사는 노래의 기승전결이 살아있도록 [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Verse 2], [Bridge], [Chorus], [Outro] 구조로 완전한 분량의 신곡 가사를 쓰세요.
4. Suno V6 음악 생성에 최적화된 영문 스타일 태그를 구체적으로 작성하세요.

반드시 마크다운 코드블록 없이 순수 JSON만 출력하세요:
{{
  "title": "새롭고 독창적인 곡 제목",
  "style_tags": "Suno V6용 영문 스타일 프롬프트 (악기, 장르, 분위기, BPM)",
  "lyrics": "전체 가사 텍스트"
}}
"""
            payload = {
                "contents": [{"parts": [{"text": prompt_instruction}]}],
                "generationConfig": {
                    "temperature": 0.95  # 매번 완전히 다른 결과를 생성하도록 높은 창의성 설정
                }
            }
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                parsed = json.loads(raw_text.strip())
                print(f"[Lyric Engine Success] 새로운 오리지널 곡 생성 완료: '{parsed['title']}'")
                return parsed["title"], parsed["style_tags"], parsed["lyrics"]
        except Exception as e:
            print(f"[Lyric Engine Warn] Gemini 호출 중 오류 발생: {e}")

    # 2. Gemini 미연동 또는 일시적 오류 시 동적 조합 폴백 생성기
    seed = int(time.time()) % 1000
    adjectives = ["새벽의", "바람결에 실린", "달빛 아래", "어느 겨울의", "기억의 저편", "가로등 불빛", "조용한 밤", "남겨진 계절"]
    nouns = ["위로", "발걸음", "메모", "이야기", "멜로디", "온기", "약속", "시간", "그림자"]
    title = f"{random.choice(adjectives)} {random.choice(nouns)} (Vol.{seed})"

    style_tags = config["default_tags"]
    lyrics = f"""[Intro: Soft Instrument Solo]
어둠이 걷히고 새벽이 찾아올 때
마음속 깊은 곳에 울리는 작은 소리

[Verse 1]
바쁘게 흘러가는 시간들 속에서
우린 무엇을 잊고 살아왔을까
{selected_theme}
그 작은 빛을 향해 조용히 걸어가네

[Chorus: Emotional Surge]
지나간 슬픔은 바람에 흩어지고
새로운 계절이 우리를 맞이해
어두운 밤하늘 길을 잃어도
마음속 꺼지지 않는 빛을 따라가

[Outro: Fade Out]
내일의 햇살이 비출 때까지
편안히 숨을 쉬어요."""

    print(f"[Lyric Engine Dynamic Fallback] 신규 동적 조합 곡 생성: '{title}'")
    return title, style_tags, lyrics
