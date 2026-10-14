"""
매 실행마다 100% 새롭고 다채롭게 작사/작곡하는 감성 & 밴드 사운드 엔진.
- 발라드 (Acoustic, Cinematic, Lofi, Urban)
- 인디밴드 / 모던록 (Britpop, Dream pop, Shoegaze)
- 창팝 / 질주형 애니메이션 팝록 / J-Rock 스타일 (신창섭, DAY6, QWER, 애니 OP 스타일)
- 세부 파라미터(장르, 악기 콤보, 멜로디 훅, 보컬 톤, 믹싱 질감, BPM, 감정선)를 매번 동적으로 조합하여
  반복적이지 않고 완전히 개성 있는 신곡을 창작합니다.
"""

import os
import json
import random
import requests
import time
import re

# -------------------------------------------------------------
# 1. 서브 장르 & 사운드 팔레트 (동적 조합 풀)
# -------------------------------------------------------------

# 장르 모듈
GENRE_POOLS = {
    "changpop": [
        "Korean J-Pop Style Anime Opening Rock",
        "Fast-paced Korean Modern Pop Rock, High Energy Anime OP",
        "Korean Funk Pop Rock with Driving Bassline, Catchy Dance-Rock",
        "Catchy 2020s K-Pop Band Anime Rock",
        "Piano Rock with Fast Driving Drum Beats and Slap Bass"
    ],
    "indie_band": [
        "Korean Britpop-influenced Melancholic Indie Rock",
        "Korean Dream Pop, Atmospheric Shoegaze Indie Band",
        "Uplifting Korean Youth Indie Pop Rock",
        "Jangly Acoustic-Electric Indie Rock",
        "Melodic Indie Modern Rock with Soaring Guitar Hooks"
    ],
    "healing_ballad": [
        "Heartfelt Korean Acoustic Indie Folk Ballad",
        "Cinematic Emotional Korean Ballad, Dramatic Orchestral Strings",
        "Lofi Indie Neo-Soul Bedroom Ballad, Rainy Mood",
        "Warm Grand Piano & Cello Sentimental Ballad",
        "Sentimental Korean Singer-Songwriter Acoustic Pop"
    ],
    "ghost_duet": [
        "2010s Sentimental Melodic K-Rap & R&B Duet",
        "Late Night Acoustic Boom Bap Melodic Rap Duo",
        "Nostalgic K-Hip Hop Duet with Sweet Vocal Chorus Hook"
    ],
    "battle_epic": [
        "Epic Oriental Anime Rock with Taiko Drum Fills",
        "High Octane Anime Battle Metal Rock, Blazing Guitar Solo"
    ]
}

# 멜로디 전개 스타일 풀 (동적 선택)
MELODY_HOOK_POOLS = {
    "changpop": [
        "insanely catchy soaring chorus melody, infectious vocal hook, explosive high note leap",
        "rapid rhythmic vocal phrasing in verses followed by euphoric melodic chorus drop",
        "energetic pentatonic guitar hook, dramatic pre-chorus build-up, anthemic shout-along chorus",
        "playful slap bass groove leading into soaring emotional vocal hook with bright harmonies"
    ],
    "indie_band": [
        "melancholic guitar riff hook, yearning vocal melody line, emotional chord progression",
        "shimmering chorus guitar leads, nostalgic vocal harmonies, slow-burning dynamic crescendo",
        "catchy conversational melody in verses, bursting into an uplifting anthemic chorus",
        "dreamy atmospheric synth textures intertwined with jangly lead guitar counter-melodies"
    ],
    "healing_ballad": [
        "delicate rubato grand piano intro, sorrowful soaring violin melody, tearful emotional climax",
        "whispering intimate acoustic fingerpicking lead, heartfelt vocal phrasing with tender pauses",
        "deep cinematic strings swell, weeping cello melody, breathtaking vocal high note",
        "mellow Rhodes electric piano chords, soulful vocal runs, gentle comforting melody"
    ]
}

# 악기 콤비네이션 풀 (동적 랜덤 조합)
INSTRUMENT_POOLS = {
    "changpop": [
        "fast driving live drums, crunchy overdrive electric guitar riffs, punchy slap bassline, bright grand piano comping",
        "energetic 140bpm four-on-the-floor beat, melodic lead guitar solo, vibrant synth brass, driving pick bass",
        "bright rhythmic acoustic guitar strumming layered with distorted rock guitars, prominent walking bass, dynamic crash cymbals"
    ],
    "indie_band": [
        "jangly rhythm guitar, melodic bassline, acoustic piano accompaniment, melancholic lead guitar hooks, spacious drum fills",
        "ambient vintage electric guitar, lush synth pads, driving rhythmic bassline, tight room indie drums, analog reverb",
        "overdrive power chords, energetic punchy drums, bright tambourine, soaring electric guitar solo"
    ],
    "healing_ballad": [
        "warm nylon string acoustic guitar, warm upright bass, gentle brushed snare, emotional grand piano, expressive cello solo",
        "rich grand piano arpeggios, sweeping orchestral strings, subtle timpani rolls, gentle acoustic guitar backing",
        "vintage Rhodes MK1 electric piano, mellow jazz clean guitar, warm sub-bass, organic lofi drum chops, subtle vinyl hiss"
    ]
}

# 보컬 톤 풀 (동적 랜덤 선택)
VOCAL_POOLS = {
    "changpop": [
        "passionate soaring male rock vocal with emotional belting and clear high notes",
        "energetic expressive youthful male vocal with playful rhythmic phrasing",
        "powerful and bright vocal delivery, charismatic soaring anime rock vocal",
        "dynamic male vocal with sharp diction and explosive chorus energy"
    ],
    "indie_band": [
        "passionate youthful male vocal with slight raspy edge and emotional crack",
        "ethereal airy female vocals, reverb-drenched melancholia and wistful tone",
        "nostalgic breathy male indie vocal, yearning delivery and raw emotion",
        "expressive female rocker vocal, powerful emotional chorus with bright timbre"
    ],
    "healing_ballad": [
        "intimate breathy female vocal, close-mic singing with gentle vibrato",
        "warm tender male singer-songwriter vocal, deep emotional baritone-to-tenor",
        "crystal clear sorrowful female vocal with rich emotional dynamic range",
        "raw emotional male vocal with soft vibrato and heartfelt sighs"
    ]
}

# 믹싱/사운드 질감 풀 (동적 선택)
TEXTURE_POOLS = [
    "studio quality master, crisp transient attack, wide stereo imaging",
    "warm organic vintage tape saturation, punchy dynamics, high fidelity",
    "spacious room reverb, polished commercial mixing, dynamic analog warmth",
    "tight modern rock production, explosive chorus impact, crystal clear separation"
]

# 가사 테마 풀
THEMES = [
    # 서정 / 청춘 / 성장
    "마지막 버스가 떠난 텅 빈 정류장, 젖은 아스팔트에 비친 불빛을 보며",
    "서랍 속 오래된 수첩에 적힌, 이제는 닿을 수 없는 사람의 이름",
    "찬 바람 부는 계절의 틈새에서 문득 떠오르는 서툴렀던 우리의 첫 고백",
    "새벽 3시 40분, 불 꺼진 방 침대맡에 드리운 가로등 불빛과 혼잣말",
    "아무것도 몰라도 찬란했던 스무 살, 그때의 너와 내가 달렸던 바닷가",
    "소란스럽고 차가운 세상 속에서 홀로 지친 나에게 조용히 건네는 위로",
    "오래된 필름 카메라를 현상하다 발견한, 너의 가장 예뻤던 웃는 얼굴",
    "옥상 난간에 기대어 바라보는 서울의 푸른 새벽과 희미해지는 별빛",
    "어깨를 짓누르던 어제를 털어내고, 내일의 햇살을 향해 내딛는 첫 발걸음",
    # 질주 팝록 / 애니메이션 밴드 / 에너지 / 해방감 테마
    "답답했던 일상에서 벗어나 시원하게 터져 나오는 통쾌한 질주와 해방감",
    "끝없는 야근과 반복되는 일상을 박차고 나와 밤의 고속도로를 시속 150km로 달리는 순간",
    "남들의 시선 따위 상관없이 내 방식대로 리듬을 타고 웃어넘기는 유쾌한 반란",
    "절망의 늪에서 피어오른 오기와 자신감, 절대 무너지지 않고 끝까지 밀어붙이는 불꽃의 결의",
    "빛바랜 꿈을 다시 꺼내 들고 무대 위에서 온몸으로 포효하는 청춘의 뜨거운 에너지",
    "숨 막히는 도시의 소음을 뚫고 울려 퍼지는 시원한 사이다 기타 리프와 자유"
]


def resolve_category(song_type: str) -> str:
    """song_type을 changpop / indie_band / healing_ballad 중 하나로 매핑 (random시 가중치 선택)"""
    st = song_type.lower().strip()
    if st in ("changpop", "chang_pop", "anime_rock", "anime_pop_rock", "normal_pop"):
        return "changpop"
    if st in ("healing_ballad", "ballad"):
        return "healing_ballad"
    if st in ("indie_band", "indie", "modern_rock"):
        return "indie_band"
    if st == "ghost_duet":
        return "ghost_duet"
    if st == "battle_epic":
        return "battle_epic"
    
    # 'random' 기본 모드: 창팝(질주 팝록), 인디밴드, 감성 발라드를 골고루 다채롭게 분배
    # 40% 창팝/질주팝록, 35% 인디밴드/모던록, 25% 감성 발라드
    return random.choices(
        ["changpop", "indie_band", "healing_ballad"],
        weights=[40, 35, 25],
        k=1
    )[0]


def generate_short_title(category: str) -> str:
    """
    한계, 돌파, 플레이리스트 등 진부한 단어와 장황한 문장형 제목을 철저히 배제하고,
    짧고 감각적인 1~2단어(2~5음절)의 순수 단어, 혼합어(합성어), 감성 신조어를 생성합니다.
    """
    if category in ("changpop", "battle_epic"):
        # 질주 팝록 / 애니메이션 밴드 / 파워풀 팝
        standalones = [
            "야간비행", "스파크런", "달빛서퍼", "네온스텝", "비행운",
            "은하질주", "새벽워프", "루미너스", "블루스텝", "플래시백",
            "스카이워크", "불꽃놀이", "찰나", "잔향", "소닉붐", "유성우",
            "일탈", "점프컷", "선샤인", "파도타기", "빛의궤적", "스타더스트"
        ]
        part_a = ["달빛", "별빛", "네온", "새벽", "은하", "바람", "불꽃", "구름", "푸른", "물빛", "광속", "태양"]
        part_b = ["유영", "비행", "스텝", "서퍼", "러너", "스파크", "웨이브", "소풍", "워프", "궤도", "점프", "샤워"]
    else:
        # 서정 발라드 / 인디 밴드 / 어쿠스틱
        standalones = [
            "윤슬", "잔향", "여명", "새벽녘", "물그림자", "달그림자",
            "낮달", "소나기", "바람결", "밤안개", "별조각", "온도",
            "잔상", "귀로", "계절감", "여운", "초록", "숲결", "봄샘",
            "노을빛", "달빛창가", "이슬길"
        ]
        part_a = ["달빛", "별빛", "새벽", "바람", "물빛", "꽃잎", "구름", "노을", "숲속", "기억", "안개", "풀잎"]
        part_b = ["유영", "항해", "산책", "소풍", "조각", "스케치", "그림자", "물결", "속삭임", "발자국", "온기", "선율"]

    # 50% 확률로 엄선된 단독 단어/신조어, 50% 확률로 감각적인 합성어(혼합어)
    if random.random() < 0.5:
        return random.choice(standalones)
    else:
        return f"{random.choice(part_a)}{random.choice(part_b)}"


def build_dynamic_music_spec(song_type: str):
    """
    고정된 프리셋이 아니라 장르, 멜로디 훅, 악기, 보컬, BPM, 텍스처를 매번 완전히 다르게 조립(Combinatorial Dynamic Engine)
    """
    category = resolve_category(song_type)

    if category == "ghost_duet":
        return {
            "category": "ghost_duet",
            "name": "2010s 멜로딕 힙합 듀엣",
            "genre": random.choice(GENRE_POOLS["ghost_duet"]),
            "melody_style": "melancholic acoustic piano riff, sweet vocal chorus hook, emotional rap flow",
            "instruments": "warm grand piano, boom bap hiphop drums, warm cello, soft atmospheric pads",
            "vocal": "emotional male rapper with sweet airy female singing chorus",
            "bpm": random.randint(88, 96),
            "texture": random.choice(TEXTURE_POOLS),
            "vibe": "새벽 한강 다리 위에서 나누는 아련하고 은밀한 대화"
        }
    if category == "battle_epic":
        return {
            "category": "battle_epic",
            "name": "오리엔탈 에픽 록",
            "genre": random.choice(GENRE_POOLS["battle_epic"]),
            "melody_style": "high energy guitar riff hook, soaring pentatonic melody, driving breakdown",
            "instruments": "heavy distorted guitar riffs, taiko drum fills, soaring electric guitar solo",
            "vocal": "powerful soaring male rock vocal",
            "bpm": random.randint(150, 165),
            "texture": random.choice(TEXTURE_POOLS),
            "vibe": "불꽃처럼 질주하는 투지와 결의의 록 사운드"
        }

    genre = random.choice(GENRE_POOLS[category])
    melody_style = random.choice(MELODY_HOOK_POOLS[category])
    instruments = random.choice(INSTRUMENT_POOLS[category])
    vocal = random.choice(VOCAL_POOLS[category])
    texture = random.choice(TEXTURE_POOLS)

    if category == "changpop":
        name = "질주형 팝록"
        bpm = random.randint(132, 146)
        vibe = "강렬한 비트와 펑키한 슬랩 베이스, 가슴 뻥 뚫리는 사이다 후렴구와 시원한 질주감"
    elif category == "indie_band":
        name = "감성 모던록 & 인디밴드"
        bpm = random.randint(86, 124)
        vibe = "청춘의 낭만과 서정성이 깃든 독창적인 밴드 사운드, 여운 넘치는 기타 리프"
    else: # healing_ballad
        name = "어쿠스틱 & 시네마틱 발라드"
        bpm = random.randint(64, 82)
        vibe = "새벽 공기처럼 담담하게 스며드는 눈물과 따뜻한 위로, 서서히 벅차오르는 스트링"

    return {
        "category": category,
        "name": name,
        "genre": genre,
        "melody_style": melody_style,
        "instruments": instruments,
        "vocal": vocal,
        "bpm": bpm,
        "texture": texture,
        "vibe": vibe
    }


def generate_lyric_and_style(song_type: str = "random", custom_prompt: str = ""):
    """
    매번 호출될 때마다 100% 새로운 제목, 세부 장르 스타일 태그, 가사를 동적으로 생성합니다.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    spec = build_dynamic_music_spec(song_type)
    selected_theme = custom_prompt if custom_prompt else random.choice(THEMES)

    # 1. Gemini AI를 통한 100% 실시간 맞춤 신곡 작사/작곡
    if gemini_key:
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
        for model_name in models_to_try:
            try:
                print(f"[Lyric Engine] Gemini AI ({model_name})로 신곡 창작: [{spec['name']}] '{selected_theme}'")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"

                prompt_instruction = f"""
당신은 대한민국 대중음악계를 뒤흔드는 천재 히트곡 프로듀서이자 싱어송라이터입니다.
이번에 프로듀싱할 음악은 전형적인 뻔한 스타일을 벗어나, 특유의 강렬하고 중독적인 선율과 살아있는 가사 호흡이 핵심입니다.

[프로듀싱 기본 사양]
- 세부 장르: {spec['genre']} ({spec['name']})
- 멜로디 및 훅 스타일: {spec['melody_style']}
- 악기 구성: {spec['instruments']}
- 보컬 구성 & 음색: {spec['vocal']}
- 템포: {spec['bpm']} BPM
- 사운드 질감: {spec['texture']}
- 곡의 무드: {spec['vibe']}
- 핵심 주제/서사: "{selected_theme}"

[★ 1. Suno AI V6 최적화 영문 스타일 태그 (style_tags) 작성 규칙]
Suno AI가 뻔한 곡을 만들지 않고 의도한 다이내믹 선율을 확실히 연출하도록 정교한 영문 태그 8~12개를 콤마로 연결하세요:
1. 구체적인 장르 (예: {spec['genre']})
2. 핵심 악기 콤보 (예: {spec['instruments']})
3. 선율 및 보컬 특성 (예: {spec['melody_style']}, {spec['vocal']})
4. 템포 및 마스터링 (예: "{spec['bpm']} bpm", "{spec['texture']}")
(주의: 추상적인 미사여구 대신 Suno 엔진이 바로 오디오 신디사이징으로 해석할 수 있는 구체적 음악 용어 위주로 작성)

[★ 2. 곡 제목 (title) 및 중독적인 가사 (lyrics) 작사 규칙]
1. 【곡 제목(title) 필수 절대 원칙 - 짧은 단어 / 혼합어 / 신조어】:
   - 길이 및 형식: 공백 포함 2~6자 내외의 짧고 감각적인 '단어', '혼합어(합성어)', 또는 '감성 신조어'로만 지으세요.
   - 절대 문장형이나 장황한 수식어구(예: '모두가 잠든 밤의 노래', '너를 향해 달리는 순간', '마지막 정거장에서' 등)로 짓지 마세요.
   - 썸네일과 영상에 크게 박힐 때 뇌리에 단번에 꽂히는 1~2단어(2~5음절) 형태여야 합니다.
   - 【절대 금지 단어】: '한계', '돌파', '플레이리스트', '하이라이트', '오버드라이브', '카운트다운' 등 진부하고 상투적인 단어는 제목과 가사 모두에서 절대 사용 금지.
   - 절대 '#1', '#91' 같은 해시태그나 임의의 트랙 번호를 붙이지 마세요.
   - 【추천 스타일 예시】:
     • 질주/애니록/팝: '야간비행', '스파크런', '달빛서퍼', '네온스텝', '비행운', '은하질주', '새벽워프', '찰나', '불꽃놀이', '루미너스', '블루스텝', '플래시백'
     • 서정/인디/발라드: '윤슬', '잔향', '새벽녘', '달빛유영', '물그림자', '별조각', '여명', '바람소풍', '낮달', '소나기', '구름산책', '밤안개'
2. 가사 본문이나 제목에 '정상화', '카운터', '신창섭' 등 특정 인터넷 밈 단어를 절대 사용하지 마세요. 대신 청춘, 일탈, 자유, 사랑, 질주, 열정 등 신선하고 몰입감 넘치는 대중가요 어휘를 사용하세요.
3. 가사 본문이나 대괄호 섹션 태그에 특정 가수명이나 밴드명(예: 잔나비, 넬, DAY6 등)을 절대 언급하거나 포함하지 마세요. 순수 음악적 연주 지시어만 영문으로 작성하세요.
4. 벌스(Verse)는 이야기하듯 호흡을 쪼개며 긴장감을 만들고, 프리코러스(Pre-Chorus)에서 감정을 고조시킨 뒤, 후렴(Chorus)에서 뇌리에 박히는 폭발적인 멜로디 훅(Catchy Hook)이 터져 나오게 쓰세요.
5. 장르가 창팝/질주록인 경우, 시원시원한 라임과 통쾌한 딕션, 따라 부르기 쉬운 킬링 파트를 만드세요.
6. 장르가 발라드/인디인 경우, 문학적이고 시적인 서사와 먹먹한 여운을 담으세요.
4. 섹션별로 Suno가 연주 다이내믹스를 극대화할 수 있도록 연주 지시 큐를 반드시 대괄호에 표기하세요:
   예시:
   - [Intro: Fast Slap Bass & Driving Guitar Hook] 또는 [Intro: Gentle Piano & Acoustic Lead]
   - [Verse 1: Fast Rhythmic Phrasing]
   - [Pre-Chorus: Building Drum Roll & Bass]
   - [Chorus: Euphoric Melodic Climax, Powerful Belting Vocals]
   - [Verse 2: Playful Rhythm Breakdown]
   - [Bridge: Dramatic Key Change, Soaring High Notes]
   - [Chorus: Final Grand Explosion, High Ad-libs]
   - [Outro: Energetic Guitar Riff Fade Out] 또는 [Outro: Soft Fade Out]

[★ 3. 작사된 가사 파트와 1:1로 일치하는 사이버펑크 글래머러스 여캐(최애의 아이 스타일) 2D 씬 프롬프트 (scene_prompts)]
※ 절대 원칙 (최애의 아이 Oshi no Ko 스타일 스타 아이즈, 매혹적이고 약간 글래머러스한 사이버펑크 애니메이션 여주인공 고정, 네온 시티 & 서사 탐험, 가사와 1:1 직결):
1. 일본 최정상급 2D 애니메이션 화풍 (Oshi no Ko aesthetic, Doga Kobo production quality, Makoto Shinkai level cinematic lighting):
   - 생동감 넘치는 고채도 네온 색감과 정교한 셀 셰이딩(vibrant high-contrast neon palette, clean cel shading, crisp dynamic 2D outlines).
   - 실사 사진(photorealistic), 3D CGI, 기괴한 얼굴 왜곡 철저 배제(not 3D, not photorealistic, no live-action, no real human photo).
2. '최애의 아이' 스타일의 눈부신 별빛 눈동자(Star Pupils)를 지닌 매혹적이고 약간 글래머러스한 사이버펑크 애니 여주인공을 모든 씬의 '고정 주인공'으로 전면 등장:
   - 외형 고정: 동공 속에 박힌 상징적인 별 모양 하이라이트(iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes), 매혹적이고 세련된 표정, 우아하고 글래머러스한 체형 실루엣(gorgeous glamorous figure, stylish cyberpunk techwear outfit with luminous glowing neon accents and holographic details), 바람에 흩날리는 섬세한 헤어.
   - 캐릭터 외형과 분위기는 씬 전체에서 흔들림 없이 고정되며, 가사의 무드와 감정선에 맞춰 사이버 시티 속을 걸어가거나, 노래하거나, 난간에 기대어 응시하거나, 질주합니다.
3. 가사 텍스트와 사이버펑크 여캐 서사의 1:1 직결 연출:
   - 방금 작사한 [lyrics]의 실제 단어, 소재, 감정선, 공간적 배경과 여주인공의 감정/행동을 1:1로 매핑하세요:
     • [비/우산/물/눈물]: 네온 불빛이 젖은 아스팔트에 일렁이는 미래 도시 거리에서 투명 홀로그램 우산을 쓴 채 뒤돌아보며 반짝이는 별 눈빛으로 카메라를 응시하는 여캐
     • [밤/별/우주/새벽]: 마천루 옥상 난간에 기대어 거대한 홀로그램 별들과 은하수가 수놓인 네온 스카이라인을 바라보며 바람에 머리카락을 흩날리는 여캐
     • [질주/탈출/바람/길]: 네온 라인이 빛나는 사이버 바이크에 올라타거나 고속 모노레일 창가에 서서 질주하는 바람을 맞으며 결의에 찬 눈빛을 빛내는 여캐
     • [무대/열정/불꽃/소리쳐]: 홀로그램 조명과 사이버 레이저가 쏟아지는 미래형 라이브 무대 위에서 마이크를 쥐고 열정적으로 포효하듯 노래하는 여캐
     • [꽃/봄/온기/사랑]: 네온 온실이나 사이버 정원에서 빛나는 바이오루미네센스 꽃잎을 손끝에 얹고 부드럽고 매혹적인 미소를 짓는 여캐
     • [기억/시간/시계/어제]: 디지털 홀로그램 기억 조각들이 부유하는 아늑한 사이버룸 창가에서 헤드폰을 끼고 아련한 눈빛으로 회상하는 여캐
4. 씬의 전개:
   - Scene 1 (도입부): 푸른 네온 골목이나 고층 룸에서 여주인공이 시크하게 등장하며 시작하는 오프닝
   - Scene 2 (1절/프리코러스): 가사의 소재와 감정을 마주하며 네온 시티를 이동하거나 몰입하는 여주인공의 씬
   - Scene 3 (후렴): 후렴 훅의 벅찬 감정과 함께 가장 화려한 네온 클라이맥스(마천루 옥상 레이저, 화려한 라이브 무대 등) 속 매혹적인 여주인공 씬
   - Scene 4 (2절/브릿지): 깊은 감정선과 아련한 별빛 눈동자의 감성 클로즈업/미디엄 씬
   - Scene 5 (아웃트로): 사이버 시티 너머로 떠오르는 여명이나 찬란한 네온 야경을 바라보며 깊은 여운을 남기는 피날레 씬
(형식: "masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, stylish futuristic cyberpunk techwear outfit with glowing luminous neon accents, elegant glamorous proportions, flowing detailed hair, [가사 파트에 기반한 여주인공의 행동/표정 및 사이버 시티 배경 연출], vibrant cyberpunk cityscape background, glowing holographic signs, rainy neo-city reflections, breathtaking cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action")

[★ 5. 유튜브 시청자를 울리는 감성 곡 설명 에세이 (story_description) 작성 규칙]
단순한 템플릿이 아닌, 이 곡을 듣는 사람의 마음에 깊은 울림을 주는 3~5단락의 아름다운 한국어 곡 소개 에세이/시놉시스를 작성하세요:
- 감성을 자극하는 시적인 한 줄 헤드카피 (예: "불 꺼진 방, 귓가에 조용히 스며드는 우리들의 지나간 계절")
- 곡이 탄생하게 된 서사와 화자의 감정선, 음악적 메시지
- 이 곡을 들으면 좋은 순간들 (새벽 드라이브, 지친 하루의 퇴근길, 눈물 흘리고 싶은 밤 등)

[★ 6. 숏츠용 킬링파트 문구 (shorts_concept)]
숏츠 영상에서 시선을 강탈할 1줄의 임팩트 있는 문구 및 하이라이트 가사 안내

반드시 마크다운 코드블록(```json) 없이 순수 JSON만 출력하세요:
{{
  "title": "2~6글자의 짧고 감각적인 단어/혼합어/신조어 제목 (한계, 돌파, 플레이리스트 등 상투어 절대 금지. 예: 야간비행, 윤슬, 스파크런, 달빛유영)",
  "style_tags": "Suno V6용 정교한 영문 스타일 & 선율 태그 문자열",
  "lyrics": "섹션별 연주 지시 큐가 포함된 완성된 전체 신곡 가사",
  "story_description": "유튜브 감성 곡 소개 에세이 및 시놉시스",
  "shorts_concept": "숏츠용 킬링파트 문구",
  "scene_prompts": [
    "Scene 1 영문 프롬프트",
    "Scene 2 영문 프롬프트",
    "Scene 3 영문 프롬프트",
    "Scene 4 영문 프롬프트",
    "Scene 5 영문 프롬프트"
  ],
  "shorts_scene_prompts": [
    "Shorts Scene 1 영문 프롬프트",
    "Shorts Scene 2 영문 프롬프트",
    "Shorts Scene 3 영문 프롬프트"
  ]
}}
"""
                payload = {
                    "contents": [{"parts": [{"text": prompt_instruction}]}],
                    "generationConfig": {
                        "temperature": 1.0  # 매번 완전히 다른 창의적인 결과 생성
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
                    raw_title = parsed.get("title", "").strip()
                    clean_title = re.sub(r'[\'\"#\[\]\(\)]', '', raw_title).strip()
                    for sep in [":", "-", "–", "—", "/"]:
                        if sep in clean_title:
                            clean_title = clean_title.split(sep)[0].strip()
                    forbidden_words = ["한계", "돌파", "플레이리스트", "하이라이트", "오버드라이브", "카운트다운"]
                    if not clean_title or any(fw in clean_title for fw in forbidden_words) or len(clean_title) > 8:
                        clean_title = generate_short_title(spec["category"])
                    parsed["title"] = clean_title
                    print(f"[Lyric Engine Success] 새로운 오리지널 곡 창작 완료: '{parsed['title']}' ({spec['name']})")
                    scenes = parsed.get("scene_prompts", [])
                    if not isinstance(scenes, list) or len(scenes) < 3:
                        scenes = [
                            f"masterpiece, anime aesthetic, lonely night city street, rainy reflections, {spec['vibe']}, cinematic lighting",
                            f"masterpiece, anime aesthetic, youth character looking at starry sky, emotional atmosphere, Makoto Shinkai style",
                            f"masterpiece, anime aesthetic, explosive glowing fireworks, breathtaking cosmic night sky, vibrant illumination",
                            f"masterpiece, anime aesthetic, rooftop sunset skyline, nostalgic golden hour, beautiful clouds",
                            f"masterpiece, anime aesthetic, peaceful sunrise over ocean horizon, warm morning glow, hopeful feeling"
                        ]
                    shorts_scenes = parsed.get("shorts_scene_prompts", [])
                    if not isinstance(shorts_scenes, list) or len(shorts_scenes) < 2:
                        shorts_scenes = [
                            f"masterpiece, anime aesthetic, emotional character face close up, dramatic lighting, high quality anime",
                            f"masterpiece, anime aesthetic, explosive concert stage or night sky with blazing vibrant fireworks, dynamic pose",
                            f"masterpiece, anime aesthetic, smiling under warm glowing stars, peaceful cinematic anime"
                        ]

                    extra_meta = {
                        "image_prompt": scenes[0],
                        "scene_prompts": scenes,
                        "shorts_scene_prompts": shorts_scenes,
                        "story_description": parsed.get("story_description", f"Inkey Studio가 전하는 오리지널 사운드트랙 '{parsed['title']}'."),
                        "shorts_concept": parsed.get("shorts_concept", f"{parsed['title']} 킬링파트"),
                        "genre_name": spec["name"],
                        "category": spec["category"]
                    }
                    return parsed["title"], parsed["style_tags"], parsed["lyrics"], extra_meta
            except Exception as e:
                print(f"[Lyric Engine Warn] {model_name} 호출 중 오류 발생: {e}")
                continue

    # 2. Gemini 미연동 또는 실패 시 다채로운 룰베이스 동적 폴백 생성기
    seed = int(time.time() * 1000) % 10000
    title = generate_short_title(spec["category"])

    if spec["category"] == "changpop":
        style_tags = f"{spec['genre']}, {spec['melody_style']}, {spec['instruments']}, {spec['vocal']}, {spec['bpm']} bpm, {spec['texture']}"
        lyrics = f"""[Intro: Driving Drums & Bass Riff]
[Verse 1: Fast Rhythmic Delivery]
어둠 속에 멈춰있던 시계태엽을 감아
답답했던 한숨 따윈 전부 뒤로 던져
{selected_theme}
눈치 보며 망설이던 시간은 이제 끝났어

[Pre-Chorus: Building Tension, Drum Rolls]
심장박동이 점점 빨라져 오고
터질 듯한 열기가 차오를 때
더는 숨길 수 없는 우리의 진짜 목소리
지금 이 순간, 소리쳐!

[Chorus: Explosive Melodic Climax, Soaring High Notes]
달려가 거침없이 온 세상을 흔들어
답답했던 어제를 전부 날려버려!
타오르는 불빛 속에 마주한 우리
절대 멈추지 않아, 끝까지 날아올라!

[Verse 2: Funky Bass Groove Breakdown]
아무도 가지 않은 길이라 해도
우리가 밟는 순간 새로운 길이 돼
겁먹지 마, 두려움 따윈 한순간의 연기일 뿐

[Bridge: Dramatic Key Change, Blazing Guitar Solo]
(화려한 기타 솔로와 함께 감정의 절정으로 치닫는 브릿지)
하늘 끝까지 닿아라, 우리의 멜로디!

[Chorus: Final Grand Climax, High Energy Ad-libs]
달려가 거침없이 온 세상을 흔들어
답답했던 어제를 전부 날려버려!
타오르는 불빛 속에 마주한 우리
절대 멈추지 않아, 끝까지 날아올라!

[Outro: Driving Guitar Riff & Punchy Drum Hit]
완벽한 순간!
지금부터가 진짜 시작이야."""
    else:
        style_tags = f"{spec['genre']}, {spec['melody_style']}, {spec['instruments']}, {spec['vocal']}, {spec['bpm']} bpm, {spec['texture']}"
        lyrics = f"""[Intro: Acoustic & Piano Melody Lead]
[Verse 1: Whispering Intimate Voice]
어스름한 가로등 아래를 천천히 걸어가
마음속 깊이 접어두었던 서랍을 조용히 열어
{selected_theme}
우린 어디쯤 서서 이 긴 밤을 견디고 있었을까

[Pre-Chorus: Gentle Strings Buildup]
스쳐 지나가는 찬 바람결마다
남겨진 너의 온기가 피어오르고
아직 다 전하지 못한 서툰 이야기들이
가슴 깊은 곳에서 아련하게 차올라

[Chorus: Soaring Emotional Climax, Full Sound]
지나온 시간들이 눈부시게 흩어져도
너와 함께 숨 쉬었던 그 계절은 잊지 않아
어두운 밤하늘 길을 잃어 헤맬 때도
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어

[Verse 2: Gentle Rhythm]
비워낸 마음 한구석에 피어나는
이름 모를 작은 들꽃처럼
혼자 걷는 골목길 끝에서
담담히 나의 이름을 다시 불러보네

[Bridge: Emotional Key Change & Vocal Climax]
눈을 감으면 번져오는 너의 맑은 미소
모든 아픔은 지나가고
다시 불어올 바람 속에
우린 더 따뜻해질 테니까

[Chorus: Final Grand Climax]
지나온 시간들이 눈부시게 흩어져도
너와 함께 숨 쉬었던 그 계절은 잊지 않아
어두운 밤하늘 길을 잃어 헤맬 때도
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어

[Outro: Soft Fade Out]
새벽이 걷히고 햇살이 비출 때까지...
편안히 숨을 쉬어요.
안녕, 나의 어제여."""

    fallback_scenes = [
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, stylish futuristic cyberpunk techwear outfit with glowing luminous neon accents, standing on high skyscraper rooftop terrace looking out at vast futuristic neon metropolis under starry galaxy night sky, flowing detailed hair caught in wind, vibrant cyberpunk cityscape background, glowing holographic signs, rainy neo-city reflections, breathtaking cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, holding a transparent holographic umbrella on rainy neon Tokyo street, glowing pink and cyan puddle reflections, stylish futuristic cyberpunk techwear, vibrant cyberpunk cityscape background, cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, singing passionately with microphone on glowing neon cyber live concert stage, laser beams and holographic digital stars bursting around her, glamorous figure and charismatic aura, cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, riding a sleek glowing cyber-bike along an elevated highway, city lights streaking past in neon motion blur, cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, leaning against panoramic glass window of penthouse as pink pastel sunrise illuminates the cyberpunk city skyline, gentle hopeful smile, cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action"
    ]
    fallback_shorts_scenes = [
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, stylish futuristic techwear with luminous neon details, singing into microphone on high-tech stage, dynamic angle, dazzling digital laser sparkles, cinematic lighting, clean 2D cel shading, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, rooftop night view with neon city skyline, gentle breeze blowing hair, warm neon reflections, cinematic lighting, clean 2D cel shading, not photorealistic, not 3D CGI, no live-action",
        f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, gazing through rain-streaked neon window, emotional expression, cinematic lighting, clean 2D cel shading, not photorealistic, not 3D CGI, no live-action"
    ]
    extra_meta = {
        "image_prompt": fallback_scenes[0],
        "scene_prompts": fallback_scenes,
        "shorts_scene_prompts": fallback_shorts_scenes,
        "story_description": (
            f"어스름한 새벽, 마음에 조용히 스며드는 이야기. Inkey Studio의 오리지널 트랙 '{title}'입니다.\n\n"
            f"지나온 시간들의 아련한 온기와 아직 못다 한 이야기들을 {spec['name']}의 섬세한 선율 위에 담아냈습니다.\n"
            f"지친 일상 속에서 잠시 멈추어 서서 위로가 필요할 때, 당신의 마음을 따뜻하게 감싸 안아줄 음악입니다."
        ),
        "shorts_concept": f"가슴을 울리는 {spec['name']} 킬링파트 🎧 '{title}'",
        "genre_name": spec["name"],
        "category": spec["category"]
    }
    return title, style_tags, lyrics, extra_meta


def generate_scene_prompts_for_duration(
    lyrics: str,
    duration_sec: float,
    clip_duration: float = 10.0,
    base_prompts: list = None
) -> list:
    """
    곡의 총 재생 시간(duration_sec)을 clip_duration(10초)으로 나눈 N개의 씬에 대해,
    최애의 아이 스타일 별빛 눈동자(Star Pupils)를 지닌 글래머러스 사이버펑크 여캐 애니메이션 프롬프트 N개를 생성합니다.
    """
    import math
    num_scenes = max(1, math.ceil(duration_sec / clip_duration))
    print(f"\n[Scene Engine] 음원 길이({duration_sec:.1f}초)에 맞춰 {clip_duration:.0f}초 단위 씬 {num_scenes}개 프롬프트 기획 시작...")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        for m in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
                prompt_instruction = f"""
당신은 <최애의 아이 (Oshi no Ko)> 작화와 감각적인 사이버펑크 2D 애니메이션의 최고 비주얼 총괄 디렉터입니다.
이 곡의 총 길이는 {duration_sec:.1f}초이며, 10초마다 순차적으로 재생될 총 {num_scenes}개의 시네마틱 애니메이션 프롬프트가 필요합니다.

[가사 전문]:
{lyrics}

[★ 사이버펑크 감성 + 최애의 아이 스타일 스타 아이즈(별 눈빛) 글래머러스 여캐 고정 주인공 규칙]:
1. 최정상급 2D 일본 애니메이션 화풍 (Oshi no Ko aesthetic, Doga Kobo production quality, Makoto Shinkai cinematic lighting):
   - 고채도 네온 컬러 팔레트, 정교한 셀 셰이딩, 역동적인 2D 애니메이션 선화.
   - 실사 사진(photorealistic), 3D CGI, 기괴한 얼굴 왜곡 절대 금지(not 3D, no photorealism, no live-action).
2. '최애의 아이' 스타일 눈부신 별빛 눈동자(Star Pupils)와 우아하고 약간 글래머러스한 체형의 사이버펑크 여주인공 고정:
   - 외형 고정: 눈동자 속 상징적인 별 모양 스파클 하이라이트(iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes), 매혹적이고 세련된 표정, 우아하고 글래머러스한 체형 실루엣(gorgeous glamorous figure, stylish cyberpunk techwear outfit with luminous glowing neon accents and holographic details), 바람에 흩날리는 섬세한 헤어.
   - 캐릭터 외형과 매력은 모든 씬에서 일관되게 유지됩니다.
3. 가사 텍스트와 사이버펑크 여캐 서사의 1:1 직결 연출:
   - 가사의 실제 단어, 감정, 분위기에 맞춰 여주인공의 표정, 행동, 공간을 정밀하게 연출:
     • [비/우산/물/눈물]: 네온 불빛이 젖은 아스팔트에 일렁이는 미래 도시 거리에서 투명 홀로그램 우산을 쓴 채 뒤돌아보며 반짝이는 별 눈빛으로 카메라를 응시하는 여캐
     • [밤/별/우주/새벽]: 마천루 옥상 난간에 기대어 거대한 홀로그램 별들과 은하수가 수놓인 네온 스카이라인을 바라보며 바람에 머리카락을 흩날리는 여캐
     • [질주/탈출/바람/길]: 네온 라인이 빛나는 사이버 바이크에 올라타거나 고속 모노레일 창가에 서서 질주하는 바람을 맞으며 결의에 찬 눈빛을 빛내는 여캐
     • [무대/열정/불꽃/소리쳐]: 홀로그램 조명과 사이버 레이저가 쏟아지는 미래형 라이브 무대 위에서 마이크를 쥐고 열정적으로 포효하듯 노래하는 여캐
     • [꽃/봄/온기/사랑]: 네온 온실이나 사이버 정원에서 빛나는 바이오루미네센스 꽃잎을 손끝에 얹고 부드럽고 매혹적인 미소를 짓는 여캐
     • [기억/시간/시계/어제]: 디지털 홀로그램 기억 조각들이 부유하는 아늑한 사이버룸 창가에서 헤드폰을 끼고 아련한 눈빛으로 회상하는 여캐
4. 씬 전개: 각 10초 구간(0~10s, 10~20s, ..., 마지막 씬)마다 그 타임라인에 실제로 노래되는 가사 파트의 상황과 감정선에 맞춰 유기적으로 이어지도록 씬을 기획하세요.
5. 프롬프트 형식: 각 씬마다 영문으로 작성:
   "masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, stylish futuristic cyberpunk techwear outfit with glowing luminous neon accents, elegant glamorous proportions, flowing detailed hair, [가사 해당 파트에 기반한 여주인공의 행동/표정 및 사이버 시티 배경 연출], vibrant cyberpunk cityscape background, glowing holographic signs, rainy neo-city reflections, breathtaking cinematic anime lighting, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, not photorealistic, not 3D CGI, no live-action"

반드시 마크다운 코드블록 없이 순수 JSON 배열만 반환하세요:
[
  "Scene 1 영문 프롬프트 (0~10s)",
  "Scene 2 영문 프롬프트 (10~20s)",
  ... (정확히 {num_scenes}개의 문자열 리스트)
]
"""
                payload = {
                    "contents": [{"parts": [{"text": prompt_instruction}]}],
                    "generationConfig": {"temperature": 0.7}
                }
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    elif raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]

                    parsed = json.loads(raw_text.strip())
                    if isinstance(parsed, list) and len(parsed) >= num_scenes:
                        print(f"[Scene Engine] Gemini가 사이버펑크 스타아이즈 여캐 씬 {len(parsed)}개 프롬프트를 완벽하게 기획했습니다!")
                        return parsed[:num_scenes]
                    elif isinstance(parsed, list) and len(parsed) > 0:
                        print(f"[Scene Engine] Gemini 생성 {len(parsed)}개 수령, 목표치 {num_scenes}개로 확장합니다.")
                        prompts = list(parsed)
                        while len(prompts) < num_scenes:
                            prompts.append(prompts[len(prompts) % len(parsed)])
                        return prompts[:num_scenes]
            except Exception as e:
                print(f"[Scene Engine Warn] Gemini 씬 프롬프트 생성 시도 중 예외: {e}")

    # 폴백: 가사 실제 텍스트 구절 분석 기반 지능형 씬 시퀀스 빌드 (사이버펑크 글래머러스 여캐 최애의 아이 스타일)
    print(f"[Scene Engine] 가사 실제 구절을 분석하여 {num_scenes}개 씬 시퀀스를 빌드합니다.")
    clean_lines = [l.strip() for l in lyrics.splitlines() if l.strip() and not l.strip().startswith("[") and not l.strip().startswith("(")]
    if not clean_lines:
        clean_lines = ["빛나는 계절", "어두운 밤하늘", "불어오는 바람", "지나온 시간들", "새벽의 온기"]

    cam_variations = [
        "cinematic slow camera tracking shot, floating holographic dust particles, soft glowing neon ambient lighting",
        "wide atmospheric shot capturing the glamorous anime girl on high skyscraper ledge overlooking sprawling neon metropolis",
        "medium close-up showing radiant star-shaped pupils glowing in mesmerizing eyes, flowing hair, breathtaking anime expression",
        "dynamic low angle shot, glowing laser beams and digital sparks fluttering in wind, energetic anime mood",
        "epic cyberpunk sunset golden hour backlighting, vibrant neon skyline, deeply emotional and nostalgic anime atmosphere"
    ]

    result_prompts = []
    for i in range(num_scenes):
        line_idx = int((i / num_scenes) * len(clean_lines))
        line_idx = min(line_idx, len(clean_lines) - 1)
        target_line = clean_lines[line_idx]

        # 가사 단어 기반 사이버펑크 글래머러스 여캐(최애의 아이 스타일) 행동 및 배경 정밀 매핑
        if any(w in target_line for w in ["용", "드래곤", "하쿠", "비늘"]):
            visual_theme = "standing on high rooftop as a colossal glowing holographic neon dragon glides majestically through the futuristic night sky behind her"
        elif any(w in target_line for w in ["검", "칼", "용사", "기사", "전쟁", "싸움", "승리"]):
            visual_theme = "wielding a glowing magenta cyber energy blade with fierce determined star eyes, wind whipping her stylish techwear outfit on skyscraper ledge"
        elif any(w in target_line for w in ["시간", "시공", "과거", "시계", "태엽", "기억", "차원"]):
            visual_theme = "surrounded by floating golden holographic clockwork cogs and shimmering digital memory fragments in a high-tech observatory, wistful gaze"
        elif any(w in target_line for w in ["우주", "은하", "성운", "행성", "궤도"]):
            visual_theme = "gazing up from high glass observation platform at a breathtaking celestial galaxy nebula and neon shooting stars across the cosmic night sky"
        elif any(w in target_line for w in ["성", "유적", "고대", "탑", "라퓨타", "신전"]):
            visual_theme = "exploring towering overgrown cybernetic ruins where glowing bioluminescent vines entangle futuristic steel monoliths, curious gaze"
        elif any(w in target_line for w in ["산", "절벽", "바위", "협곡", "봉우리"]):
            visual_theme = "standing at the edge of an ultra-high cyber tower skydeck, wind blowing her hair as misty clouds swirl below the neon megacity at dawn"
        elif any(w in target_line for w in ["심해", "해저", "산호", "해파리"]):
            visual_theme = "visiting a massive futuristic underwater bio-dome, watching glowing turquoise jellyfish and coral lights reflect across her radiant star eyes"
        elif any(w in target_line for w in ["바다", "파도", "수평선", "모래", "해변"]):
            visual_theme = "standing on a coastal cyber walkway at purple twilight, gentle ocean breeze blowing her hair as bioluminescent waves roll in"
        elif any(w in target_line for w in ["기차", "철길", "역", "정거장", "플랫폼"]):
            visual_theme = "leaning against the glass window of a sleek high-speed neon cyber-train streaking across elevated tracks over glowing city lights"
        elif any(w in target_line for w in ["눈", "겨울", "얼음", "시리", "추위"]):
            visual_theme = "catching glowing cyber snowflakes on her fingertips on a snowy neon street illuminated by soft holographic aurora lanterns"
        elif any(w in target_line for w in ["비", "빗", "물", "적시"]):
            visual_theme = "holding a transparent holographic umbrella on a rain-soaked neon street, pink and cyan streetlight puddles shimmering under her feet"
        elif any(w in target_line for w in ["밤", "별", "하늘", "어둠"]):
            visual_theme = "sitting on high rooftop railing overlooking endless glowing city lights, looking up at vast starry indigo sky with sparkling star pupils"
        elif any(w in target_line for w in ["바람", "흔들", "풀", "나무", "숲"]):
            visual_theme = "walking through an illuminated rooftop greenhouse garden, gentle breeze fluttering her glamorous techwear and vibrant hair"
        elif any(w in target_line for w in ["꽃", "봄", "피어", "향기"]):
            visual_theme = "gently cupping glowing holographic cherry blossom petals dancing in neon night air, soft enchanting smile with dazzling star eyes"
        elif any(w in target_line for w in ["빛", "햇살", "새벽", "아침", "태양"]):
            visual_theme = "basking on penthouse balcony as warm pink morning sunlight illuminates her glamorous silhouette against the futuristic city horizon"
        elif any(w in target_line for w in ["불", "타오", "열정", "폭발", "화염"]):
            visual_theme = "singing passionately with microphone on a dazzling cyber live stage, surrounded by burst of pyrotechnic sparks and laser beams"
        elif base_prompts and len(base_prompts) > i:
            visual_theme = f"charismatically standing in {base_prompts[i]}"
        else:
            visual_theme = f"reflecting the emotional scene of '{target_line}' in stunning cyberpunk setting, star eyes gleaming"

        cam_mod = cam_variations[i % len(cam_variations)]
        full_p = (
            f"masterpiece 2D Japanese anime visual, Oshi no Ko inspired animation style, "
            f"gorgeous glamorous cyberpunk anime girl protagonist, iconic dazzling star-shaped sparkle highlights in pupils, mesmerizing radiant star eyes, "
            f"stylish futuristic cyberpunk techwear outfit with glowing luminous neon accents, elegant glamorous proportions, flowing detailed hair, "
            f"{visual_theme}, "
            f"vibrant cyberpunk cityscape background, glowing holographic signs, rainy neo-city reflections, "
            f"{cam_mod}, clean 2D cel shading, crisp dynamic anime outlines, Doga Kobo production quality, "
            f"not photorealistic, not 3D CGI, no live-action"
        )
        result_prompts.append(full_p)

    return result_prompts



