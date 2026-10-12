"""
매 실행마다 100% 새롭고 다채롭게 작사/작곡하는 감성 엔진.
선율(Melody) 유도 프롬프트와 문학적 서사 가사(Lyrics) 품질에 특화되어
기계적이거나 뻔한 AI 사운드를 벗어나 매번 사람의 숨결이 느껴지는 독창적인 곡을 창작합니다.
"""

import os
import json
import random
import requests
import time

# 발라드 및 인디밴드 감성을 극대화하기 위한 세부 장르 & 악기 & 선율 전개 프리셋
SUB_STYLES = [
    {
        "name": "어쿠스틱 서정 포크 발라드",
        "genre": "Korean Acoustic Indie Folk Ballad",
        "melody_style": "melancholic acoustic guitar fingerpicking lead, delicate piano counter-melody, heartfelt vocal phrasing, slow emotional buildup",
        "instruments": "warm nylon string acoustic guitar, warm upright bass, gentle brushed snare, emotional piano, expressive cello solo",
        "vocals": ["intimate breathy female vocal, close-mic singing", "warm tender male singer-songwriter vocal", "raw emotional male vocal with soft vibrato"],
        "bpm_range": (66, 75),
        "vibe": "새벽 골목 가로등 아래에서 나지막이 읊조리는 진솔한 위로와 여운"
    },
    {
        "name": "몽환적인 드림팝 / 슈게이징 인디록",
        "genre": "Korean Dream Pop, Shoegaze, Atmospheric Indie Rock",
        "melody_style": "shimmering chorus guitar melody hook, ambient stereo delay riffs, dreamy vocal line with deep reverb, nostalgic melodic progression",
        "instruments": "ambient vintage electric guitar, lush synth pads, driving rhythmic bassline, tight room indie drums, analog reverb",
        "vocals": ["ethereal airy female vocals, reverb-drenched melancholia", "nostalgic breathy male indie vocal, shoegaze phrasing"],
        "bpm_range": (82, 96),
        "vibe": "새벽 고속도로 창밖으로 번지는 네온사인과 안개처럼 몽환적인 낭만"
    },
    {
        "name": "청춘 질주 모던록 / 브릿팝 인디",
        "genre": "Korean Modern Rock, Nostalgic Britpop Indie Band",
        "melody_style": "catchy soaring guitar riffs, anthemic chorus melody, dynamic chord progression, explosive emotional chorus leap",
        "instruments": "jangly overdrive rhythm guitar, punchy melodic bass, energetic punchy drums, bright tambourine, soaring electric guitar solo",
        "vocals": ["passionate youthful male vocal with slight raspy edge", "expressive soaring female rocker vocal, powerful emotional chorus", "yearning male indie vocal with belting high notes"],
        "bpm_range": (108, 128),
        "vibe": "잔나비·넬·검정치마 감성, 가슴 터질 듯 벅차오르는 청춘의 계절과 질주"
    },
    {
        "name": "시네마틱 오케스트라 피아노 발라드",
        "genre": "Cinematic Emotional Korean Ballad, Dramatic Orchestral",
        "melody_style": "moving rubato grand piano intro, sorrowful soaring violin melody, tearful dramatic climax with vocal high note leap",
        "instruments": "rich acoustic grand piano, weeping cello and soaring violin section, subtle timpani rolls, gentle acoustic guitar backing",
        "vocals": ["deep emotional male tenor ballad vocal with soaring high notes", "crystal clear poignant female vocal, heartbreaking emotional crescendo"],
        "bpm_range": (64, 73),
        "vibe": "영화 마지막 장면의 묵직한 오열과 그리움, 웅장하고 깊은 스트링의 울림"
    },
    {
        "name": "비 내리는 밤의 로우파이 네오소울 / R&B 인디",
        "genre": "Lofi Indie Neo-Soul Ballad, Korean Cozy Bedroom Pop",
        "melody_style": "sweet soulful vocal ornamentation, mellow jazzy 7th chord progressions, lazy syncopated vocal groove, smooth earworm hook",
        "instruments": "vintage Rhodes MK1 electric piano, mellow jazz clean guitar, warm sub-bass, organic lofi drum chops, subtle vinyl hiss",
        "vocals": ["smooth soulful male vocal, groove-infused honey voice", "cozy breathy female vocal, laid-back melodic delivery"],
        "bpm_range": (72, 84),
        "vibe": "창가에 맺힌 빗방울과 식어가는 커피, 방 안의 노란 스탠드 불빛"
    },
    {
        "name": "감성 어반 어쿠스틱 팝 (싱어송라이터)",
        "genre": "Korean Acoustic Pop, Sentimental Singer-Songwriter",
        "melody_style": "bright yet nostalgic melody hook, playful rhythmic acoustic strumming, sweet conversational chorus melody",
        "instruments": "percussive acoustic guitar, rhodes piano, melodic electric bass, shakers and light cajon/percussion",
        "vocals": ["sweet conversational male singer-songwriter vocal", "clear lovely female acoustic vocal with bright tone"],
        "bpm_range": (86, 98),
        "vibe": "적재·폴킴·아이유 스타일, 일상적인 대화처럼 편안하게 귓가에 맴도는 선율"
    }
]

THEMES = [
    "마지막 버스가 떠난 텅 빈 정류장, 젖은 아스팔트에 비친 불빛을 보며",
    "서랍 속 오래된 수첩에 적힌, 이제는 닿을 수 없는 사람의 이름",
    "찬 바람 부는 계절의 틈새에서 문득 떠오르는 서툴렀던 우리의 첫 고백",
    "비 쏟아지는 밤, 켜지지 않는 휴대전화를 쥐고 멍하니 듣는 빗소리",
    "새벽 3시 40분, 불 꺼진 방 침대맡에 드리운 가로등 불빛과 혼잣말",
    "아무것도 몰라도 찬란했던 스무 살, 그때의 너와 내가 달렸던 바닷가",
    "소란스럽고 차가운 세상 속에서 홀로 지친 나에게 조용히 건네는 위로",
    "오래된 필름 카메라를 현상하다 발견한, 너의 가장 예뻤던 웃는 얼굴",
    "옥상 난간에 기대어 바라보는 서울의 푸른 새벽과 희미해지는 별빛",
    "너를 완전히 잊은 줄 알았는데, 익숙한 냄새 하나에 무너져 내리는 밤",
    "우리가 계절을 건너 서로 다른 길을 걷더라도, 그 시절의 빛은 영원하기를",
    "어깨를 짓누르던 어제를 털어내고, 내일의 햇살을 향해 내딛는 첫 발걸음"
]

def build_random_music_spec(song_type: str):
    """
    발라드 / 인디밴드 느낌 중심의 다채로운 음악 사양(서브 스타일, 선율 전개, 보컬, 악기)을 랜덤 조립
    """
    if song_type == "healing_ballad":
        sub = random.choice([SUB_STYLES[0], SUB_STYLES[3], SUB_STYLES[4]])
    elif song_type == "indie_band":
        sub = random.choice([SUB_STYLES[1], SUB_STYLES[2], SUB_STYLES[5]])
    elif song_type in ("random", "all"):
        sub = random.choice(SUB_STYLES)
    elif song_type == "ghost_duet":
        return {
            "name": "2010s 멜로딕 힙합 듀엣",
            "genre": "2010s Sentimental Melodic K-Rap & R&B Duet",
            "melody_style": "melancholic acoustic piano riff, sweet vocal chorus hook, emotional rap flow",
            "instruments": "warm grand piano, boom bap hiphop drums, warm cello, soft atmospheric pads",
            "vocals": ["emotional male rapper with sweet airy female singing chorus", "melodic rap duo"],
            "bpm_range": (88, 96),
            "vibe": "새벽 한강 다리 위에서 나누는 아련한 비밀 이야기"
        }
    elif song_type == "battle_epic":
        return {
            "name": "오리엔탈 에픽 록",
            "genre": "Epic Oriental Anime Rock",
            "melody_style": "high energy guitar riff hook, soaring pentatonic melody, driving breakdown",
            "instruments": "heavy distorted guitar riffs, taiko drum fills, soaring electric guitar solo",
            "vocals": ["powerful soaring male rock vocal"],
            "bpm_range": (150, 165),
            "vibe": "불꽃처럼 질주하는 투지와 결의의 록 사운드"
        }
    else:
        sub = random.choice(SUB_STYLES)

    bpm = random.randint(sub["bpm_range"][0], sub["bpm_range"][1])
    vocal = random.choice(sub["vocals"])
    return {
        "name": sub["name"],
        "genre": sub["genre"],
        "melody_style": sub["melody_style"],
        "instruments": sub["instruments"],
        "vocal": vocal,
        "bpm": bpm,
        "vibe": sub["vibe"]
    }


def generate_lyric_and_style(song_type: str = "random", custom_prompt: str = ""):
    """
    선율(Melody) 유도 프롬프트와 문학적 서사의 감성 가사를 100% 새롭게 창작합니다.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    spec = build_random_music_spec(song_type)
    selected_theme = custom_prompt if custom_prompt else random.choice(THEMES)

    # 1. Gemini AI를 통한 최고급 프로듀싱 수준의 신곡 작사/작곡
    if gemini_key:
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
        for model_name in models_to_try:
            try:
                print(f"[Lyric Engine] Gemini AI ({model_name})로 맞춤 선율/가사 창작 시작: [{spec['name']}] '{selected_theme}'")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"

                prompt_instruction = f"""
당신은 대한민국 음악계를 대표하는 최정상급 인디밴드 / 감성 발라드 싱어송라이터이자 프로듀서(잔나비, 넬, 검정치마, 적재, 아이유, 박효신, 혁오 스타일)입니다.

이번 곡의 프로듀싱 기획서:
- 장르: {spec['name']} ({spec['genre']})
- 핵심 선율 및 멜로디 테마: {spec.get('melody_style', 'heartfelt melody')}
- 핵심 악기 구성: {spec['instruments']}
- 보컬 구성 & 창법: {spec.get('vocal', '감성 보컬')}
- 목표 템포: {spec.get('bpm', 75)} BPM
- 분위기 및 정서: {spec['vibe']}
- 곡의 테마/서사: "{selected_theme}"

[★ 핵심 선율 프롬프트 (style_tags) 작성 규칙]
Suno AI V6 모델이 '선율(멜로디)'과 '감정 다이내믹스'를 정교하게 구현할 수 있도록 다음 요소들을 영문 콤마로 구체적으로 조합하세요:
1. 명확한 장르 & 악기 (예: {spec['genre']}, {spec['instruments']})
2. 선율 유도 태그: "melodic hook, memorable vocal melody line, emotional chord progression, dynamic buildup, soaring chorus melody"
3. 보컬 질감 및 창법 (예: {spec.get('vocal')})
4. 템포 및 마스터링 퀄리티: "{spec.get('bpm')} bpm, studio quality, warm organic master"
(절대 너무 길거나 난잡하지 않게 핵심 음악적 지시어 7~10개 내외로 정제)

[★ 감성 가사 (lyrics) 작사 규칙]
1. 단순 나열이나 유치한 사랑 타령을 지양하고, 한 편의 시 또는 영화의 한 장면 같은 문학적 서사를 담으세요.
2. 각인되는 킬링 파트(Catchy Chorus Hook)와 멜로디의 쉼표가 느껴지는 호흡을 고려하세요.
3. Suno V6가 선율과 악기 전개를 극대화할 수 있도록 섹션 태그에 선율/연주 큐를 함께 명시하세요:
   - [Intro: Soft Piano & Acoustic Lead]
   - [Verse 1: Whispering, Intimate Voice]
   - [Pre-Chorus: Building Tension, Strings Enter]
   - [Chorus: Soaring Emotional Climax, Full Band/Strings]
   - [Verse 2: Reflective, Rhythmic Bass Groove]
   - [Bridge: Dramatic Key Change, Explosive High Notes]
   - [Chorus: Final Grand Climax, Soaring Ad-libs]
   - [Outro: Fading Acoustic Melody, Gentle Whispering]
4. 기존 가요 제목이나 진부한 표현(예: '고스타그램', '꿈꾸던 어른' 등)을 절대 재사용하지 마세요. 독창적이고 여운이 남는 제목을 지으세요.

반드시 마크다운 코드블록(```json) 없이 순수 JSON만 출력하세요:
{{
  "title": "독창적이고 서정적인 한글 곡 제목 (부제 가능)",
  "style_tags": "Suno V6용 정교한 영문 선율 & 편곡 태그",
  "lyrics": "선율 연주 큐가 포함된 완성된 전체 신곡 가사"
}}
"""
                payload = {
                    "contents": [{"parts": [{"text": prompt_instruction}]}],
                    "generationConfig": {
                        "temperature": 1.0
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
                    print(f"[Lyric Engine Success] 새로운 오리지널 곡 창작 완료: '{parsed['title']}' ({spec['name']})")
                    return parsed["title"], parsed["style_tags"], parsed["lyrics"]
            except Exception as e:
                print(f"[Lyric Engine Warn] {model_name} 호출 중 오류 발생: {e}")
                continue

    # 2. Gemini 미연동 또는 실패 시 다채로운 룰베이스 폴백 생성기
    seed = int(time.time() * 1000) % 10000
    prefixes = ["우리가 머물던", "어느 늦은 밤의", "푸른 새벽의", "바람이 머무는", "달빛 스케치", "비 내리는 오후", "기억의 파도", "너에게 닿는", "계절의 끝자락", "작은 방 안의", "소란한 밤의", "서툰 마침표", "마지막 정거장의"]
    subjects = ["정거장", "노랫소리", "고백", "온기", "발자국", "그림자", "풍경", "기억", "바람", "빛", "계절", "여름밤", "일기장", "숨결"]
    title = f"{random.choice(prefixes)} {random.choice(subjects)} #{seed % 99 + 1}"

    vocal_str = spec.get('vocal', 'emotional vocals')
    melody_str = spec.get('melody_style', 'melancholic melody, memorable chorus hook')
    bpm_str = f"{spec.get('bpm', 75)} bpm"
    style_tags = f"{spec['genre']}, {melody_str}, {spec['instruments']}, {vocal_str}, soaring emotional chorus, {bpm_str}, studio quality"

    lyrics = f"""[Intro: {spec['name']} - Delicate Melody Lead]
(은은한 멜로디 라인이 흐르며 고요하게 감정을 여는 전주)

[Verse 1: Whispering, Intimate Tone]
어스름한 가로등 아래를 천천히 걸어가
마음속 깊이 접어두었던 서랍을 조용히 열어
{selected_theme}
우린 어디쯤 서서 이 긴 밤을 견디고 있었을까

[Pre-Chorus: Subtle Strings Buildup]
스쳐 지나가는 찬 바람결마다
남겨진 너의 온기가 피어오르고
아직 다 전하지 못한 서툰 이야기들이
가슴 깊은 곳에서 아련하게 차올라

[Chorus: Soaring Emotional Climax, Powerful Melody]
지나온 시간들이 눈부시게 흩어져도
너와 함께 숨 쉬었던 그 계절은 잊지 않아
어두운 밤하늘 길을 잃어 헤맬 때도
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어

[Verse 2: Reflective & Gentle Rhythm]
비워낸 마음 한구석에 피어나는
이름 모를 작은 들꽃처럼
혼자 걷는 골목길 끝에서
담담히 나의 이름을 다시 불러보네

[Bridge: Dramatic Buildup, Vocal Climax]
눈을 감으면 번져오는 너의 맑은 미소
모든 아픔은 지나가고
다시 불어올 바람 속에
우린 더 따뜻해질 테니까

[Chorus: Final Grand Climax, High Emotion]
지나온 시간들이 눈부시게 흩어져도
너와 함께 숨 쉬었던 그 계절은 잊지 않아
어두운 밤하늘 길을 잃어 헤맬 때도
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어

[Outro: Soft Fade Out, Echoing Piano]
새벽이 걷히고 햇살이 비출 때까지...
편안히 숨을 쉬어요.
안녕, 나의 어제여."""

    print(f"[Lyric Engine Fallback] 고품질 선율/가사 조합 곡 생성: '{title}' ({spec['name']})")
    return title, style_tags, lyrics
