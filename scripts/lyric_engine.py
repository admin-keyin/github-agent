"""
100% 독창적(Original) 창작 스토리텔링 가사 & 음악 프롬프트 생성기.
기존 아티스트(심통봇, 머무르 등)의 곡명 및 고유 가사를 절대 복제하지 않고,
감성 힙합 듀엣 / 힐링 어쿠스틱 발라드 / 에픽 애니 락 장르의 순수 창작곡을 제작합니다.
"""

import os
import json
import random
import requests

# 100% 고유한 창작 스토리텔링 테마 및 독창적 가사
ORIGINAL_THEMES = {
    "ghost_duet": {
        "title_pool": [
            "새벽 세 시의 유령 친구 (Ghost in the Feed)",
            "성불 보류 중 (Pending Spirit)",
            "이승에 남긴 메모 (Midnight Note)",
            "밤하늘 네컷 사진 (Polaroid with You)"
        ],
        "style_tags": "2010s sentimental melodic k-rap, sweet acoustic piano, boom bap beat, emotional male rap with airy female vocals, nostalgic chorus, 94 bpm",
        "lyrics": """[Intro: Soft Piano & Vinyl Crackle]
희미한 가로등 아래 그림자 하나
아직 세상은 잠들지 못했나 봐
(저기... 누구세요?)

[Verse 1: Male Rap]
시간은 벌써 새벽 세 시 반
달빛이 내려앉은 편의점 앞
떠나야 할 시간이 찾아왔지만
이 거리를 걷는 발걸음이 무거워
다들 바쁘게 앞만 보며 살아갈 때
우린 남겨진 온기를 이야기해

[Verse 2: Female Vocal]
아직 읽지 않은 메시지들이 마음에 맴돌아요
밤하늘 별빛은 왜 이리 따뜻한 건가요
조금만 더 이 바람을 느끼고 싶어
하루만 더 머물면 안 될까요

[Chorus: Duet]
흐려지는 시간의 경계 속에서
우리 함께 나눈 작은 웃음들
달빛이 구름 뒤로 숨기 전까지
마지막 춤을 추듯 걸어가요
이 밤이 끝나지 않기를 기도하며

[Outro: Soft Piano Solo]
조용히 울리는 새벽 종소리
내일도 기억해 줄래요."""
    },
    "healing_ballad": {
        "title_pool": [
            "어린 날의 나에게 띄우는 편지 (To My Younger Self)",
            "새벽을 걷는 너에게 (Walking Through Dawn)",
            "그 시절 우리가 꿈꾼 계절 (The Season We Dreamed)",
            "다정했던 소년의 눈빛 (Warm Memories)"
        ],
        "style_tags": "heartfelt korean indie ballad, warm grand piano, expressive cello, gentle female acoustic vocal, cinematic emotional build-up, 70 bpm",
        "lyrics": """[Intro: Warm Grand Piano]
오랜만에 꺼내본 낡은 서랍 속
작은 일기장엔 서툰 글씨들
세상이 전부 다 찬란할 줄 알았던
그 시절 내가 묻고 있네요

[Verse 1]
넘어질 때마다 아파서 울던 아이는
어느덧 남몰래 눈물을 훔치는 법을 배웠죠
모든 게 뜻대로 되지 않는 오늘이어도
버텨낸 하루가 헛되지 않음을

[Chorus: Emotional Strings Surge]
어린 날의 나에게 전하고 싶어
넌 충분히 잘 해내고 있다고
차가운 밤하늘 길을 잃어도
네 안의 따뜻한 빛을 잃지 마
내가 널 안아줄 테니

[Outro: Gentle Piano & Whisper]
수고 많았어, 오늘 밤도
편히 잠들기를."""
    },
    "battle_epic": {
        "title_pool": [
            "푸른 번개의 맹세 (Oath of Blue Lightning)",
            "바람의 궤적 (Trajectory of the Wind)",
            "전설의 갈림길 (Path of Destiny)"
        ],
        "style_tags": "epic oriental rock anime opening, heavy distorted guitar, fast taiko drum roll, soaring male vocals, high energy breakdown, 160 bpm",
        "lyrics": """[Intro: Shamisen Solo & Heavy Drums]
칠흑 같은 어둠을 가르는 불꽃
결코 물러서지 않을 나의 길

[Verse 1]
휘몰아치는 비바람 속에서도
눈동자에 맺힌 차가운 신념
운명이 나를 시험한다 해도
꺾이지 않는 칼날처럼 나아가리

[Chorus: Explosive Rock Drop]
하늘을 뒤흔드는 푸른 섬광
끝없는 전장 위를 질주해
모든 시련을 넘어선 순간
새로운 새벽이 밝아오리라!

[Outro]
바람만이 기억할 우리들의 승리."""
    }
}

def generate_lyric_and_style(song_type: str = "ghost_duet", custom_prompt: str = ""):
    """
    100% 독창적인 가사와 제목을 생성합니다.
    기존 상용곡 제목/가사를 모방하지 않고 순수 창작물로 출력합니다.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if custom_prompt and gemini_key:
        try:
            print(f"[Lyric Engine] Gemini AI로 100% 독창적인 순수 창작 가사 및 스타일 생성 중...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            sys_instruction = (
                "당신은 감성적이고 트렌디한 K-POP/인디 발라드를 작사/작곡하는 전문 AI 프로듀서입니다.\n"
                "주의사항: 기존 가수(심통봇, 머무르 등)의 노래 제목('고스타그램', '꿈꾸던 어른이 되었나요' 등)이나 고유 가사를 절대 사용하거나 복제하지 마세요.\n"
                "완전히 새롭고 시적인 100% 독창적인 오리지널 제목과 가사를 작성하세요.\n"
                "다음 JSON 형식으로만 출력하세요:\n"
                "{\n"
                '  "title": "완전히 독창적이고 매력적인 순수 창작 곡 제목 (영문 부제 포함 가능)",\n'
                '  "style_tags": "Suno V6용 영문 스타일 태그 (장르, 악기, 분위기, 템포, 보컬 특징)",\n'
                '  "lyrics": "[Intro]...[Verse 1]...[Chorus]...[Outro] 구조의 100% 순수 창작 감성 가사"\n'
                "}\n"
                "반드시 마크다운 없이 순수 JSON만 반환하세요."
            )
            payload = {
                "contents": [{
                    "parts": [{"text": f"주제: {custom_prompt}\n지침: {sys_instruction}"}]
                }]
            }
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())
                return parsed["title"], parsed["style_tags"], parsed["lyrics"]
        except Exception as e:
            print(f"[Lyric Engine Warn] Gemini 자동 작사 오류 ({e}), 독창적 프리셋으로 전환합니다.")

    # 매핑 호환성 처리 (이전 키 지원)
    key_map = {
        "ghostagram": "ghost_duet",
        "grown_up": "healing_ballad",
        "cyber_warrior": "battle_epic"
    }
    target_key = key_map.get(song_type, song_type)
    if target_key not in ORIGINAL_THEMES:
        target_key = random.choice(list(ORIGINAL_THEMES.keys()))

    preset = ORIGINAL_THEMES[target_key]
    title = random.choice(preset["title_pool"])
    return title, preset["style_tags"], preset["lyrics"]
