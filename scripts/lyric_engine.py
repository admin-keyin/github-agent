"""
고스타그램(GHOSTagram), 꿈꾸던 어른이 되었나요 스타일의
스토리텔링 가사 & 음악 프롬프트 생성기 (Gemini 연동 및 프리셋 지원)
"""

import os
import json
import random
import requests

PRESET_TRACKS = {
    "ghostagram": {
        "title": "고스타그램 (GHOSTagram - Remake Vibe)",
        "theme": "성불하기 싫은 MZ 귀신의 이야기와 이를 잡으러 온 저승사자",
        "style_tags": "2010s k-pop hiphop, melodic rap, catchy duet, bright boom bap, nostalgic melody, piano intro, playful synth, male rapper and sweet female vocals, 96 bpm",
        "vocal_gender": "m/f",
        "keywords": ["성불", "저승사자", "MBTI", "인생네컷", "인스타그램", "야식", "새벽"],
        "lyrics": """[Intro: Female Vocal & Soft Piano]
거울 속에 비친 내 모습은 흐릿하지만
아직 세상엔 하고 싶은 게 너무 많은걸
(Wait, hold on, 누구세요?)

[Verse 1: Male Rap - Grim Reaper]
Yo, Time's UP, 모래시계는 다 됐어
이승에서의 너의 미련 이제 그만 내려놓고
서천 꽃밭행 특급열차 출발할 시간
영수증 챙겨, 이제 갈 준비 해

[Verse 2: Female Vocal & Rap - MZ Ghost]
잠깐만요 사자님, 저 아직 MBTI도 모른단 말예요
인생네컷 프레임도 다 못 찍어봤는데
내 피드에 올릴 성불 챌린지 하나만 하고 가면 안 돼요?
새벽 한강 라면 맛도 아직 잊지 못했단 말야

[Pre-Chorus: Female Vocal]
밤하늘 별빛 아래 반짝이는 이 거리
나만 두고 떠나긴 너무 눈부시잖아
조금만 더 머물고 싶어

[Chorus: Duet - Ghost & Reaper]
Don't send me away, 오늘 밤만은 나를 놓아줘
고스타그램 피드 속 우리들의 기억처럼
새벽달빛이 저물 때까지만
우리 조금만 더 이 밤을 춤추자
(성불은 내일 아침에 할게요, 진짜로!)

[Bridge: Playful Acoustic & Beat Drop]
"야, 너 저번 주에도 그 말 했잖아!"
"에이, 사자님도 탕후루 한 입 드셔보실래요?"

[Outro: Duet & Fade Out]
희미해지는 불빛 사이로
내일도 여기서 만나요, 안녕."""
    },
    "grown_up": {
        "title": "꿈꾸던 어른이 되었나요? (Acoustic Ballad Ver.)",
        "theme": "어린 시절의 나와 마주하며 건네는 담담하고 벅찬 위로",
        "style_tags": "emotional k-ballad, soft acoustic guitar, warm grand piano, melancholy cello, sentimental female vocal, cinematic orchestral build-up, 72 bpm, 2020s indie pop",
        "vocal_gender": "f",
        "keywords": ["어른", "위로", "어릴적", "눈물", "거울", "새벽", "꿈"],
        "lyrics": """[Intro: Grand Piano & Warm Cello]
거울에 비춘 나는 잘 지내는 척해요
말은 점점 줄고 한숨만 길어져요
소란한 하룰 지나 집으로 돌아올 때면
참았던 마음들이 문 앞에 서 있어요

[Verse 1]
어린 나는 더 멀리 갈 줄 알았죠
울지 않는 얼굴로 커갈 줄 알았죠
그런데 아직도 난 작은 말에 흔들려요
그래도 무너지진 않으려 깊은 숨을 쉬어요

[Chorus: Emotional & Orchestral Surge]
꿈꾸던 어른이 되었나요?
어릴 적 몰랐던 고민들이 하나 둘씩
어깨에 조용히 내려앉아 나를 짓누르네요
꿈꾸던 어른이 된 걸까요?
가끔은 무너지는 새벽 밤에도
겨우 겨우 버티는 작은 나를
어른이라 부를 수 있을까요?

[Bridge: Strings Swell]
넘어지고 헤매어도
그 시절 내가 꿈꿨던 다정함만은
잃지 않기를

[Outro: Soft Piano & Whisper]
오늘 밤도 수고했어요
어린 날의 내가 나를 안아주네요."""
    },
    "cyber_warrior": {
        "title": "전장의 그림자 (Ninja Battle Epic)",
        "theme": "닌자 대전과 나루토 풍의 비장한 전투와 신념",
        "style_tags": "oriental cinematic rock, heavy shamisen, taiko drum roll, electric guitar distortion, epic male vocal, aggressive breakdown, anime opening style, 155 bpm",
        "vocal_gender": "m",
        "keywords": ["닌자", "전장", "오의", "불꽃", "차크라", "운명"],
        "lyrics": """[Intro: Shamisen Solo & Taiko Drums]
어둠을 가르는 푸른 뇌광의 섬광
피할 수 없는 전장의 붉은 운명

[Verse 1]
바람을 가르며 달리는 그림자
눈동자에 맺힌 차가운 결의
물러설 곳 없는 벼랑 끝에서도
나의 신념은 결코 꺾이지 않아

[Chorus: Explosive Rock Drop]
불타오르는 영혼의 나선환
운명을 넘어선 전설의 격돌
끝나지 않는 싸움의 끝에서
내 이름을 세상에 새겨라!

[Outro]
바람이 잠들고 남은 승자의 침묵."""
    }
}

def generate_lyric_and_style(preset_key: str = "ghostagram", custom_prompt: str = ""):
    """
    선택된 프리셋 또는 사용자 지정 프롬프트에 맞춰 가사와 스타일 태그를 반환합니다.
    Gemini API 키가 있으면 Gemini를 통해 완전히 새로운 가사와 스타일을 생성합니다.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if custom_prompt and gemini_key:
        try:
            print(f"[Lyric Engine] Gemini AI로 맞춤 가사 & 음악 스타일 작사/작곡 프롬프트 생성 중...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            sys_instruction = (
                "당신은 '고스타그램'이나 '꿈꾸던 어른이 되었나요' 같은 감성적이고 트렌디한 히트곡을 만드는 천재 AI 작사가 및 음악 프로듀서입니다.\n"
                "사용자의 주제를 바탕으로 Suno AI에 최적화된 형식으로 다음 JSON을 출력하세요:\n"
                "{\n"
                '  "title": "곡 제목",\n'
                '  "style_tags": "Suno 스타일 프롬프트 (영문 태그 조합: 장르, 악기, 분위기, BPM, 보컬 특징)",\n'
                '  "lyrics": "[Intro]...[Verse 1]...[Chorus]...[Bridge]...[Outro] 형태의 서사적이고 감동적인 한글 가사"\n'
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
            print(f"[Lyric Engine Warn] Gemini 생성 실패 ({e}), 프리셋으로 전환합니다.")

    # 프리셋 반환
    if preset_key not in PRESET_TRACKS:
        preset_key = random.choice(list(PRESET_TRACKS.keys()))

    preset = PRESET_TRACKS[preset_key]
    return preset["title"], preset["style_tags"], preset["lyrics"]
