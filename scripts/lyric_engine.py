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

try:
    from scripts.character_profile import generate_random_character_profile, build_character_prompt
except ImportError:
    from character_profile import generate_random_character_profile, build_character_prompt

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
    짧고 감각적인 1~2단어(2~5음절)의 한국어, 영어, 또는 한영 혼합 감성 신조어 제목을 생성합니다.
    """
    if category in ("changpop", "battle_epic"):
        # 질주 팝록 / 애니메이션 밴드 / 파워풀 팝
        standalones = [
            "야간비행", "스파크런", "달빛서퍼", "네온스텝", "비행운",
            "은하질주", "새벽워프", "루미너스", "블루스텝", "플래시백",
            "스카이워크", "불꽃놀이", "찰나", "잔향", "소닉붐", "유성우",
            "일탈", "점프컷", "선샤인", "파도타기", "빛의궤적", "스타더스트",
            # 세련된 영문 타이틀
            "IGNITE", "SPARK", "FLASHBACK", "NIGHTWALK", "NEON STEP",
            "SONIC", "BLAZE", "BLUE PULSE", "CRUSH", "OVERPASS",
            "STARFALL", "DIVE", "RUNNER", "BREAKOUT", "AFTERSHOCK"
        ]
        part_a = ["달빛", "별빛", "네온", "새벽", "은하", "바람", "불꽃", "구름", "푸른", "물빛", "광속", "태양", "Blue", "Neon", "Cyber", "Dark"]
        part_b = ["유영", "비행", "스텝", "서퍼", "러너", "스파크", "웨이브", "소풍", "워프", "궤도", "점프", "샤워", "Pulse", "Rush", "Dive", "Flash"]
    else:
        # 서정 발라드 / 인디 밴드 / 어쿠스틱
        standalones = [
            "윤슬", "잔향", "여명", "새벽녘", "물그림자", "달그림자",
            "낮달", "소나기", "바람결", "밤안개", "별조각", "온도",
            "잔상", "귀로", "계절감", "여운", "초록", "숲결", "봄샘",
            "노을빛", "달빛창가", "이슬길",
            # 세련된 영문 타이틀
            "BLUE", "BLOOM", "REWIND", "LAST NIGHT", "MEMORIES",
            "STARDUST", "GLOW", "WHISPER", "DREAM", "AFTERGLOW",
            "ECHO", "SILENCE", "SUNSET", "TRACE", "DRIFT"
        ]
        part_a = ["달빛", "별빛", "새벽", "바람", "물빛", "꽃잎", "구름", "노을", "숲속", "기억", "안개", "풀잎", "Pure", "Soft", "Silent", "Deep"]
        part_b = ["유영", "항해", "산책", "소풍", "조각", "스케치", "그림자", "물결", "속삭임", "발자국", "온기", "선율", "Wave", "Glow", "Echo", "Breeze"]

    # 55% 확률로 엄선된 단독 단어/신조어/영문, 45% 확률로 감각적인 합성어(혼합어)
    if random.random() < 0.55:
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

    # 캐릭터(인물) 생성 배제 - 순수 감성 시네마틱 애니메이션 배경 및 풍경 모드
    char_profile = None
    char_prompt_base = "no people, no human, no characters, pure Japanese anime background scenery"
    print(f"\n[Visual Engine] 캐릭터(인물)를 제외한 감성 시네마틱 애니메이션 배경 & 풍경 모드로 생성합니다.")

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
1. 【곡 제목(title) 필수 절대 원칙 - 짧은 단어 / 영문 / 혼합어 / 신조어】:
   - 길이 및 형식: 공백 포함 2~8자 내외의 짧고 감각적인 한국어 단어, 세련된 영문 단어(예: SPARK, IGNITE, ECHO, BLUE, DIVE, NIGHTWALK), 또는 감성 합성어로 지으세요.
   - 절대 문장형이나 장황한 수식어구(예: '모두가 잠든 밤의 노래', '너를 향해 달리는 순간', '마지막 정거장에서' 등)로 짓지 마세요.
   - 썸네일과 영상에 크게 박힐 때 뇌리에 단번에 꽂히는 1~2단어 형태여야 합니다.
   - 【절대 금지 단어】: '한계', '돌파', '플레이리스트', '하이라이트', '오버드라이브', '카운트다운' 등 진부하고 상투적인 단어는 제목과 가사 모두에서 절대 사용 금지.
   - 절대 '#1', '#91' 같은 해시태그나 임의의 트랙 번호를 붙이지 마세요.
2. 【★ 가사 언어 스타일: 꼭 100% 한글이 아니어도 되며, 영어가사를 자연스럽게 섞어서(한영 혼용 / 바이링구얼 Bilingual lyrics) 작성하세요!】:
   - K-Pop, K-Rock, J-Pop 스타일처럼 중독성 있는 영어 훅(Catchy English Hooks), 킬링 파트, 코러스의 세련된 영문 라인(English Chorus Lines)을 적극적으로 섞어서 작성하세요.
   - 코러스(Chorus)나 프리코러스(Pre-Chorus), 인트로/아웃트로 등에 강렬하고 기억하기 쉬운 영문 펀치라인을 한글 가사와 리드미컬하게 믹스하세요.
   - 예시 (질주/록/배틀):
     `Don't look back, we're burning in the dark! / 멈추지 마, 심장이 터질 때까지 / Break the silence, shout it out loud! / 끝없는 밤을 뚫고 날아올라`
   - 예시 (감성/인디/발라드):
     `'Cause in my memories you still shine, / 스쳐 지나간 너의 계절 속에 / I will never let you fade away, / 이 밤이 지나도 너를 기억해`
3. 가사 본문이나 제목에 '정상화', '카운터', '신창섭' 등 특정 인터넷 밈 단어를 절대 사용하지 마세요. 대신 청춘, 일탈, 자유, 사랑, 질주, 열정 등 신선하고 몰입감 넘치는 대중가요 어휘를 사용하세요.
4. 가사 본문이나 대괄호 섹션 태그에 특정 가수명이나 밴드명(예: 잔나비, 넬, DAY6 등)을 절대 언급하거나 포함하지 마세요. 순수 음악적 연주 지시어만 영문으로 작성하세요.
5. 벌스(Verse)는 이야기하듯 호흡을 쪼개며 긴장감을 만들고, 프리코러스(Pre-Chorus)에서 감정을 고조시킨 뒤, 후렴(Chorus)에서 뇌리에 박히는 폭발적인 멜로디 훅(Catchy Hook)이 터져 나오게 쓰세요.
6. 장르가 창팝/질주록인 경우, 시원시원한 라임과 통쾌한 딕션, 따라 부르기 쉬운 킬링 파트를 만드세요.
7. 장르가 발라드/인디인 경우, 문학적이고 시적인 서사와 먹먹한 여운을 담으세요.
8. 섹션별로 Suno가 연주 다이내믹스를 극대화할 수 있도록 연주 지시 큐를 반드시 대괄호에 표기하세요:
   예시:
   - [Intro: Fast Slap Bass & Driving Guitar Hook] 또는 [Intro: Gentle Piano & Acoustic Lead]
   - [Verse 1: Fast Rhythmic Phrasing]
   - [Pre-Chorus: Building Drum Roll & Bass]
   - [Chorus: Euphoric Melodic Climax, Powerful Belting Vocals]
   - [Verse 2: Playful Rhythm Breakdown]
   - [Bridge: Dramatic Key Change, Soaring High Notes]
   - [Chorus: Final Grand Explosion, High Ad-libs]
   - [Outro: Energetic Guitar Riff Fade Out] 또는 [Outro: Soft Fade Out]

[★ 3. 작사된 가사 파트와 1:1로 일치하는 순수 일본 2D 애니 배경/풍경 씬 프롬프트 (scene_prompts)]
※ 절대 원칙 (인물/캐릭터 얼굴 절대 배제, 순수 시네마틱 애니메이션 배경 아트 & 풍경 & 오브젝트 몽타주):
1. 정통 일본 극장판 애니메이션 배경 화풍 (Authentic Japanese 2D TV/movie anime scenery aesthetic, Kyoto Animation / CloverWorks quality, Makoto Shinkai level cinematic lighting):
   - 【사람/인물/캐릭터 절대 배제】: 사람의 얼굴, 몸, 손, 실루엣, 캐릭터 등을 일체 배제하고 감성적인 배경·풍경·공간·오브젝트로만 화면을 가득 채우세요 (no people, no human, no character, no face, no girl, no boy, pure background scenery).
   - 실사 사진(photorealistic), 3D CGI, 서구권 코믹스 철저 배제 (not 3D, not photorealistic, not semi-realistic, no live-action, no real human photo).
2. 【시네마틱 배경 스토리텔링 몽타주 - 풍경, 공간, 오브젝트의 다채로운 교차】:
   - 가사의 감정선과 분위기에 부합하는 시네마틱 배경 연출을 다채롭게 교차하세요:
     • [B-Roll 감성 정물/오브제]: 빗방울 맺힌 창가, 노을빛 전철 철길, 바람에 날리는 벚꽃잎, 별빛 밤하늘, 건반 위의 따뜻한 조명, 빈 무대의 스탠드 마이크와 앰프, 파도 거품 등
     • [광활한 자연 & 도시 풍경]: 노을빛 해안 도로, 별빛 은하수가 쏟아지는 밤하늘 언덕, 네온사인이 반사되는 비 내리는 도시 거리, 황금빛 일몰의 지평선
     • [다이내믹 라이팅 & 공간 무드]: 렌즈 플레어, 구름 사이로 쏟아지는 찬란한 빛줄기, 반짝이는 수면, 화려한 무대 조명 이펙트
3. 가사 텍스트와 공간 서사의 1:1 직결 연출:
   - 방금 작사한 [lyrics]의 실제 단어, 소재, 감정선과 배경 공간을 1:1로 매핑하세요:
     • [비/우산/물/눈물]: 촉촉이 비 내리는 감성적인 유럽풍 거리, 빗방울 맺힌 유리창, 비를 머금은 젖은 아스팔트와 반사되는 가로등 불빛
     • [밤/별/우주/새벽]: 고풍스러운 앤티크 테라스에서 바라보는 쏟아지는 별빛 은하수 밤하늘, 푸른 새벽녘의 고요한 지평선
     • [질주/탈출/바람/길]: 싱그러운 바람이 불어 풀잎이 파도치는 푸른 초원 언덕길, 수평선이 끝없이 펼쳐진 해안 도로
     • [무대/열정/불꽃/소리쳐]: 화려한 콘서트 라이브 조명과 렌즈 플레어가 쏟아지는 빈 무대, 진공관 앰프와 빈티지 마이크
     • [꽃/봄/온기/사랑]: 벚꽃이나 들꽃이 만발한 햇살 가득한 온실 정원, 바람에 흩날리는 따스한 꽃잎
     • [기억/시간/시계/어제]: 부드러운 햇살이 스며드는 따뜻한 서재, 창가 테이블 위의 앤티크 오르골과 찻잔
4. 씬의 전개:
   - Scene 1 (도입부): 고요하고 서정적인 공간/배경 (새벽녘, 잔잔한 햇살, 빗방울 창가 등)
   - Scene 2 (1절/프리코러스): 감정이 살아나는 공간 (바람에 흔들리는 나뭇잎, 노을빛 거리 등)
   - Scene 3 (후렴): 감정이 폭발하는 가장 화려하고 감동적인 클라이맥스 풍경 (쏟아지는 별빛, 화려한 무대 조명 등)
   - Scene 4 (2절/브릿지): 깊은 감성의 무드 씬 (감성적인 실내 공간, 네온빛 거리 등)
   - Scene 5 (아웃트로): 노을 지는 석양이나 은은한 여명을 비추며 깊은 여운을 남기는 피날레 풍경
(형식: "masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background visual, [가사 파트에 기반한 감성 배경/환경/오브제 상세 묘사], no people, no human, no characters, dynamic Makoto Shinkai cinematic lighting, atmospheric anime environment, sophisticated anime digital shading, crisp modern linework, Kyoto Animation, CloverWorks and MAPPA quality, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa")

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
                            f"masterpiece modern Japanese anime scenery, lonely night city street, rainy reflections, {spec['vibe']}, cinematic lighting, no people, no human, no characters",
                            f"masterpiece modern Japanese anime landscape, breathtaking starry night sky, milky way galaxy, Makoto Shinkai style, no people, no human, no characters",
                            f"masterpiece modern Japanese anime scenery, explosive glowing fireworks, cosmic nebula, vibrant illumination, no people, no human, no characters",
                            f"masterpiece modern Japanese anime scenery, rooftop sunset skyline, nostalgic golden hour, beautiful clouds, no people, no human, no characters",
                            f"masterpiece modern Japanese anime landscape, peaceful sunrise over ocean horizon, warm morning glow, hopeful feeling, no people, no human, no characters"
                        ]
                    shorts_scenes = parsed.get("shorts_scene_prompts", [])
                    if not isinstance(shorts_scenes, list) or len(shorts_scenes) < 2:
                        shorts_scenes = [
                            f"masterpiece modern Japanese anime scenery, dramatic cinematic lighting, glowing neon street with rain puddles, no people, no human, no characters",
                            f"masterpiece modern Japanese anime scenery, concert stage lights or blazing vibrant fireworks over skyline, no people, no human, no characters",
                            f"masterpiece modern Japanese anime landscape, warm glowing stars and cosmic nebula, peaceful cinematic scenery, no people, no human, no characters"
                        ]

                    extra_meta = {
                        "image_prompt": scenes[0],
                        "scene_prompts": scenes,
                        "shorts_scene_prompts": shorts_scenes,
                        "character_profile": None,
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
        lyrics = f"""[Intro: Driving Drums & Electric Guitar Riff]
[Verse 1: Fast Rhythmic Delivery]
어둠 속에 멈춰있던 시계태엽을 감아
Wake up now, 더는 지체할 시간은 없어
{selected_theme}
Don't look back, 망설임 따윈 전부 던져버려

[Pre-Chorus: Building Tension, Drum Rolls]
Can you feel the fire burning inside?
심장박동이 점점 빨라져 오고
더는 숨길 수 없는 우리의 Voice
지금 이 순간, Shout it out loud!

[Chorus: Explosive Melodic Climax, Soaring Belting Vocals]
Run away, 거침없이 온 세상을 흔들어!
Break the dark, 답답했던 어제를 날려버려!
We are burning brighter than the stars
절대 멈추지 않아, 끝까지 날아올라!
Never gonna stop, fly into the sky!

[Verse 2: Funky Bass Groove Breakdown]
아무도 가지 않은 길이라 해도
Step by step, 우리가 밟는 순간 새로운 길이 돼
겁먹지 마, 두려움 따윈 Just fade away

[Bridge: Dramatic Key Change, Blazing Guitar Solo]
(화려한 기타 솔로와 함께 감정의 절정으로 치닫는 브릿지)
하늘 끝까지 닿아라, Our melody echoing high!

[Chorus: Final Grand Climax, High Energy Ad-libs]
Run away, 거침없이 온 세상을 흔들어!
Break the dark, 답답했던 어제를 날려버려!
We are burning brighter than the stars
절대 멈추지 않아, 끝까지 날아올라!
Never gonna stop, we ignite the night!

[Outro: Driving Guitar Riff & Punchy Drum Hit]
This is our moment!
지금부터가 진짜 시작이야."""
    else:
        style_tags = f"{spec['genre']}, {spec['melody_style']}, {spec['instruments']}, {spec['vocal']}, {spec['bpm']} bpm, {spec['texture']}"
        lyrics = f"""[Intro: Soft Piano & Acoustic Guitar Lead]
[Verse 1: Whispering Intimate Voice]
어스름한 가로등 아래를 천천히 걸어가
In the quiet night, 서랍을 조용히 열어
{selected_theme}
Where are we going? 긴 어둠의 터널을 지나

[Pre-Chorus: Gentle Strings Buildup]
Every breath I take, 스쳐 지나가는 바람결마다
남겨진 너의 온기가 피어오르고
Still inside my heart, 전하지 못한 이야기들이
가슴 깊은 곳에서 아련하게 차올라

[Chorus: Soaring Emotional Climax, Full Sound]
'Cause in my memories you still shine,
눈부시게 흩어지던 그 계절처럼
Even when the shadows fall tonight,
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어
I'll never let you fade away

[Verse 2: Gentle Rhythm]
비워낸 마음 한구석에 피어나는
Like a tiny flower in the morning dew
혼자 걷는 골목길 끝에서
담담히 나의 이름을 다시 불러보네

[Bridge: Emotional Key Change & Vocal Climax]
눈을 감으면 번져오는 너의 맑은 미소
All the pain will fade into the wind
다시 불어올 따스한 봄날 속에
We will be shining again

[Chorus: Final Grand Climax]
'Cause in my memories you still shine,
눈부시게 흩어지던 그 계절처럼
Even when the shadows fall tonight,
마음속 꺼지지 않는 선율 하나, 너를 부르고 있어
Forever in my heart, always by your side

[Outro: Soft Fade Out]
새벽이 걷히고 햇살이 비출 때까지...
Until the morning comes.
안녕, 나의 어제여."""

    fallback_scenes = [
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, picturesque romantic coastal town under blue sky with fluffy white clouds, gentle breeze rustling vibrant flower gardens and trees, breathtaking Makoto Shinkai cinematic lighting, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, no people, no human, no characters, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, charming cobblestone European street with warm glowing streetlights and gentle rain puddle reflections, soft cinematic anime lighting, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, no people, no human, no characters, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, grand empty concert arena stage, sweeping colorful spotlights and dramatic lens flare, sparkling stage haze, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, no people, no human, no characters, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, cozy sunlit cafe interior by an open wooden window, steaming ceramic tea cup on rustic wooden table, soft golden hour sunlight, cinematic lighting, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, no people, no human, no characters, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, stone balcony terrace overlooking a breathtaking starry night sky with glowing crescent moon and vibrant cosmic nebula, cinematic lighting, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, no people, no human, no characters, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa"
    ]
    fallback_shorts_scenes = [
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, glowing stage lighting and dramatic beam lasers cutting through misty arena atmosphere, sparkling light particles, dynamic angle, no people, no human, no characters, sophisticated anime digital shading, not photorealistic, not 3D CGI, not semi-realistic, no live-action, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, antique cafe terrace overlooking illuminated night cityscape under twinkling starry sky, gentle breeze, warm ambient lighting, no people, no human, no characters, sophisticated anime digital shading, not photorealistic, not 3D CGI, not semi-realistic, no live-action, not retro anime, not 90s anime, not webtoon, not manhwa",
        f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, rain-streaked cafe glass window reflecting neon city lights and street lamps, tranquil mood, no people, no human, no characters, cinematic lighting, sophisticated anime digital shading, not photorealistic, not 3D CGI, not semi-realistic, no live-action, not retro anime, not 90s anime, not webtoon, not manhwa"
    ]
    extra_meta = {
        "image_prompt": fallback_scenes[0],
        "scene_prompts": fallback_scenes,
        "shorts_scene_prompts": fallback_shorts_scenes,
        "character_profile": None,
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


def detect_storyline_arc(lyrics: str, character_profile: dict = None) -> dict:
    """
    가사 텍스트와 캐릭터 아키타입을 종합 분석하여 뮤직비디오의 메인 스토리 서사(Storyline Arc)를 결정합니다.
    내용이 겹치지 않고 매번 새롭고 다채로운 비주얼을 제공하기 위해 9가지 일본 애니메이션 서사 풀을 운용합니다.
    - starlit_romance: 신카이 마코토 감성의 밤하늘 은하수, 별빛 언덕, 달빛 발코니
    - youth_band: 청춘 인디 밴드 & 라이브 하우스 합주, 옥상 합주, 도심 버스킹
    - rainy_cafe_city: 비 내리는 도쿄 도심 거리, 감성 우드 카페 창가, 투명 우산
    - sunset_coastal: 붉은 노을빛 해안도로 드라이브, 파도치는 백사장, 바닷바람 산책
    - fantasy_magic: 신비로운 마법진과 고대 유적 숲, 환상적인 비행 마법 (프리렌 감성)
    - stage_diva: 화려한 아레나 무빙 라이트와 관객 야광봉 바다, 압도적인 팝 디바 콘서트
    - battle_action: 박진감 넘치는 애니메이션 액션 배틀, 화염과 검기 타격 이펙트
    - cyberpunk_chase: 네온 마천루 사이버펑크 고속 질주 & 도심 탈출
    - swimmer_athlete: 청량한 푸른 수영장 레이스 다이빙과 승리의 터치패드
    """
    lyric_lower = lyrics.lower()
    arch = ""
    outfit_type = ""
    outfit_ko = ""
    outfit_en = ""
    if character_profile:
        arch = character_profile.get("archetype", "").lower()
        outfit_type = character_profile.get("outfit_type", "").lower()
        outfit_ko = character_profile.get("outfit_ko", "").lower()
        outfit_en = character_profile.get("outfit_en", "").lower()

    # 점수제 기반 서사 매칭 풀
    scores = {
        "starlit_romance": 0,
        "youth_band": 0,
        "rainy_cafe_city": 0,
        "sunset_coastal": 0,
        "fantasy_magic": 0,
        "stage_diva": 0,
        "battle_action": 0,
        "cyberpunk_chase": 0,
        "swimmer_athlete": 0
    }

    # 1. 캐릭터 아키타입 기본 가중치
    if arch == "bocchi_rock":
        scores["youth_band"] += 4
        scores["rainy_cafe_city"] += 2
    elif arch == "hoshino":
        scores["stage_diva"] += 4
        scores["sunset_coastal"] += 2
    elif arch == "frieren_mage":
        scores["fantasy_magic"] += 4
        scores["starlit_romance"] += 2
    elif arch == "violet":
        scores["starlit_romance"] += 3
        scores["rainy_cafe_city"] += 3
    elif arch == "cyber_lucy":
        scores["cyberpunk_chase"] += 4
        scores["battle_action"] += 2
    elif arch == "yor":
        scores["battle_action"] += 3
        scores["rainy_cafe_city"] += 2
    elif arch in ("reze", "power", "makima"):
        scores["battle_action"] += 2
        scores["sunset_coastal"] += 1
        scores["youth_band"] += 1

    # 수영복 의상이면 수영선수 가중치
    if "수영복" in outfit_type or "수영복" in outfit_ko or "bikini" in outfit_en or "monokini" in outfit_en:
        scores["swimmer_athlete"] += 5
        scores["sunset_coastal"] += 3

    # 2. 가사 키워드 스코어링
    if any(k in lyric_lower for k in ["별", "은하수", "우주", "새벽", "달빛", "하늘", "star", "night", "sky", "moon", "galaxy"]):
        scores["starlit_romance"] += 3
    if any(k in lyric_lower for k in ["비", "우산", "카페", "커피", "골목", "안개", "서랍", "rain", "cafe", "coffee", "window"]):
        scores["rainy_cafe_city"] += 3
    if any(k in lyric_lower for k in ["밴드", "기타", "베이스", "드럼", "합주", "거리", "guitar", "band", "bass", "acoustic"]):
        scores["youth_band"] += 3
    if any(k in lyric_lower for k in ["노을", "바다", "해변", "파도", "바람", "여름", "ocean", "sea", "beach", "sunset", "breeze"]):
        scores["sunset_coastal"] += 3
    if any(k in lyric_lower for k in ["마법", "기적", "시간", "기억", "차원", "룬", "magic", "wonder", "spell", "ancient", "fantasy"]):
        scores["fantasy_magic"] += 3
    if any(k in lyric_lower for k in ["무대", "마이크", "환호", "조명", "아이돌", "노래", "stage", "spotlight", "sing", "diva", "concert"]):
        scores["stage_diva"] += 3
    if any(k in lyric_lower for k in ["싸움", "전투", "칼", "폭발", "화염", "악마", "격돌", "타격", "fight", "battle", "strike", "blast"]):
        scores["battle_action"] += 3
    if any(k in lyric_lower for k in ["질주", "고속도로", "탈출", "네온", "속도", "엔진", "바이크", "speed", "chase", "highway", "engine"]):
        scores["cyberpunk_chase"] += 3
    if any(k in lyric_lower for k in ["수영", "다이빙", "물속", "스트로크", "접영", "자유형", "물살", "swim", "swimming", "dive"]):
        scores["swimmer_athlete"] += 4

    # 랜덤 가중치 살짝 부여하여 매번 똑같은 아크가 나오지 않도록 방지
    for k in scores:
        scores[k] += random.uniform(0.1, 1.8)

    chosen_arc = max(scores, key=scores.get)

    arc_definitions = {
        "starlit_romance": {
            "arc_type": "starlit_romance",
            "name_ko": "신카이 마코토 감성의 밤하늘 은하수 & 별빛 언덕 (Cosmic Starlit Romance Arc)",
            "theme_en": "breathtaking Makoto Shinkai aesthetic, glowing cosmic milky way across night sky, starlit grassy hilltop observatory, floating shooting stars, poetic sentimental anime romance",
            "keywords": ["starlit night", "milky way galaxy", "shooting star", "observatory terrace", "romantic breeze"]
        },
        "youth_band": {
            "arc_type": "youth_band",
            "name_ko": "청춘 인디 밴드 라이브 & 루프탑 합주 (Youth Indie Band & Rooftop Jam Arc)",
            "theme_en": "youthful contemporary Japanese indie band aesthetic, dynamic electric guitar performance on open rooftop overlooking city, cozy live house rehearsal, energetic rock groove",
            "keywords": ["indie band", "electric guitar", "rooftop sunset jam", "livehouse amplifier", "youthful rock"]
        },
        "rainy_cafe_city": {
            "arc_type": "rainy_cafe_city",
            "name_ko": "비 내리는 도쿄 도심 & 감성 카페 (Rainy Tokyo Street & Cozy Cafe Arc)",
            "theme_en": "poetic rainy Tokyo metropolis streets reflecting warm streetlights, transparent umbrella, cozy wooden sunlit cafe by rain-streaked glass window, warm ambient anime lighting",
            "keywords": ["rainy street", "transparent umbrella", "cozy wooden cafe", "steaming coffee", "rain reflections"]
        },
        "sunset_coastal": {
            "arc_type": "sunset_coastal",
            "name_ko": "노을빛 해안도로 드라이브 & 해변 산책 (Sunset Coastal Highway & Beach Walk Arc)",
            "theme_en": "radiant golden hour sunset horizon over vast sparkling ocean, sea breeze fluttering hair, scenic coastal road, gentle ocean waves crashing against sandy shore",
            "keywords": ["sunset ocean", "coastal road", "crashing waves", "golden hour seaside", "refreshing breeze"]
        },
        "fantasy_magic": {
            "arc_type": "fantasy_magic",
            "name_ko": "신비로운 판타지 유적 탐험 & 마법 비행 (Mystical Fantasy Ruins & Magic Flight Arc)",
            "theme_en": "timeless high fantasy anime aesthetic in Frieren style, ancient overgrown mossy stone ruins, glowing turquoise arcane magic circles illuminating ancient forest, floating magic orbs",
            "keywords": ["fantasy ruins", "ancient forest", "glowing magic circle", "floating runes", "enchanted vista"]
        },
        "stage_diva": {
            "arc_type": "stage_diva",
            "name_ko": "화려한 스타디움 팝 디바 콘서트 (Grand Stadium Pop Diva Concert Arc)",
            "theme_en": "electrifying live arena concert stage in Oshi no Ko style, blazing crisscrossing spotlights, ten thousand glowing audience lightsticks, passionate singing with sparkling stage pyrotechnics",
            "keywords": ["concert arena", "stage spotlight", "audience lightsticks", "glittering mic", "stage pyrotechnics"]
        },
        "battle_action": {
            "arc_type": "battle_action",
            "name_ko": "타격감 넘치는 다이나믹 배틀 액션 (High-Octane Dynamic Anime Combat Arc)",
            "theme_en": "high octane anime combat action choreography in MAPPA style, lethal martial arts strikes, explosive hit sparks, shattered urban battlefield, epic anime fight scene",
            "keywords": ["battle", "combat strike", "explosion", "hit sparks", "shockwaves"]
        },
        "cyberpunk_chase": {
            "arc_type": "cyberpunk_chase",
            "name_ko": "심야 네온 고속 질주 & 도심 탈출 (Midnight Cyberpunk Speed & Drift Arc)",
            "theme_en": "high-speed midnight motorcycle chase across neon cyberpunk metropolis in Studio Trigger style, drifting through rainy asphalt, cyan light trails, exhilarating speed",
            "keywords": ["speed", "motorcycle", "neon city", "chase", "highway"]
        },
        "swimmer_athlete": {
            "arc_type": "swimmer_athlete",
            "name_ko": "불꽃 튀는 수영선수의 도전과 승리 (Swimmer Championship Arc)",
            "theme_en": "competitive champion swimmer athletic journey in Kyoto Animation Free! style, indoor Olympic aquatic stadium, fierce swimming sprint, crystal splashes and thrilling victory",
            "keywords": ["swimming", "dive", "stroke", "water splash", "aquatic center"]
        }
    }

    return arc_definitions[chosen_arc]


def generate_scene_prompts_for_duration(
    lyrics: str,
    duration_sec: float,
    clip_duration: float = 5.0,
    base_prompts: list = None,
    character_profile: dict = None
) -> list:
    """
    곡의 총 재생 시간(duration_sec)을 clip_duration(5초)으로 나눈 N개의 씬에 대해,
    가사와 캐릭터 컨셉에 맞춘 [구체적인 스토리 서사(전투씬, 가수 무대, 수영선수 등)]를 선정하고,
    기승전결(도입 -> 전개 -> 절정 액션/퍼포먼스 -> 피날레 승리/환호)을 갖춘
    한 편의 완성도 높은 일본 2D TV 애니메이션 씬 시퀀스를 생성합니다.
    """
    import math
    char_prompt_base = "no people, no human, no characters, pure Japanese anime background scenery"

    # 1. 스토리 서사(Storyline Arc) 탐지
    story_arc = detect_storyline_arc(lyrics, character_profile=None)
    arc_type = story_arc["arc_type"]
    arc_name_ko = story_arc["name_ko"]
    arc_theme_en = story_arc["theme_en"]

    num_scenes = max(1, math.ceil(duration_sec / clip_duration))
    print(f"\n[Scene Engine] 음원 길이({duration_sec:.1f}초)에 맞춰 {clip_duration:.0f}초 단위 씬 {num_scenes}개 순수 시네마틱 배경 프롬프트 기획 시작...")
    print(f" -> 뮤직비디오 스토리 서사 테마: ★ {arc_name_ko} (풍경·공간·오브젝트) ★")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        for m in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
                prompt_instruction = f"""
당신은 최고 수준의 현대 일본 극장판 및 TV 애니메이션 비주얼 배경 총괄 디렉터(Kyoto Animation, CloverWorks, Ufotable, MAPPA)입니다.
이 곡의 총 길이는 {duration_sec:.1f}초이며, 5초마다 순차적으로 재생될 총 {num_scenes}개의 시네마틱 애니메이션 배경 프롬프트가 필요합니다.

[가사 전문]:
{lyrics}

[★ 이번 뮤직비디오의 메인 스토리 서사 테마]:
- 서사 장르: {arc_name_ko} ({arc_type})
- 서사 디렉션: {arc_theme_en}

[★ 현대 최고 수준의 일본 애니메이션 배경 화풍 + 기승전결 스토리텔링 규칙]:
1. 최정상급 현대 일본 극장판 및 TV 애니메이션 작화 (Contemporary high-end Japanese TV anime scenery aesthetic by Kyoto Animation, CloverWorks, Ufotable, and MAPPA, with Makoto Shinkai cinematic anime lighting):
   - 【사람/인물/캐릭터 얼굴 절대 배제】: 사람의 얼굴, 신체, 손, 캐릭터 등을 일체 배제하고 감성적인 배경·풍경·공간·오브젝트로만 화면을 가득 채우세요 (no people, no human, no character, no face, no girl, no boy, pure background scenery).
   - 고전/복고풍 셀화 및 웹툰 화풍 철저 배제, 실사화/3D 배제 (contemporary anime digital illustration, sophisticated soft anime shading, crisp modern linework, not retro anime, not 90s anime, not 3D, no real photo, not webtoon, not manhwa).
2. 【★ 핵심 원칙: 감성 시네마틱 몽타주 - 풍경, 공간, 오브젝트의 다채로운 교차】:
   - 음악의 호흡과 가사의 서사를 살리기 위해 아래 3가지 타입의 배경 샷을 {num_scenes}개 씬 전체에 걸쳐 유기적으로 교차 배치하세요:
     • [타입 1: 현장감 넘치는 B-Roll & 감성 오브제 매크로 컷 (약 35%)]
       (예: 서사에 맞는 디테일 오브제/이펙트 - 빗방울 창가, 빈티지 앰프와 악기, 피아노 건반, 커피잔, 흩날리는 악보/꽃잎 등)
     • [타입 2: 광활한 자연 & 도시 풍경 와이드 파노라마 컷 (약 35%)]
       (예: 쏟아지는 별빛 밤하늘 은하수, 붉은 노을빛 해안 도로, 네온사인이 반사되는 젖은 아스팔트, 푸른 초원 언덕)
     • [타입 3: 다이내믹 라이팅 & 시네마틱 클라이맥스 환경 컷 (약 30%)]
       (예: 렌즈 플레어, 화려한 무대 조명 이펙트, 폭발하는 불꽃/스파크, 구름 사이로 쏟아지는 빛줄기, 반짝이는 수면)
3. 【스토리의 기승전결 (Narrative Arc Progression)】:
   - 초반(0~25%): [도입] 고요하고 서정적인 분위기의 시작 (새벽빛, 잔잔한 공간, 긴장감 넘치는 분위기)
   - 중반(25~60%): [전개] 빛과 움직임이 살아나는 환경, 스피드감과 현장감 고조
   - 후반(60~85%): [절정/클라이맥스] 가장 폭발적이고 환상적인 비주얼 (화려한 조명 연출 / 전율의 하이라이트)
   - 종반(85~100%): [피날레] 여운을 남기는 평화로운 일몰이나 아침 햇살, 찬란한 빛 속에서의 피날레
4. 프롬프트 형식: 각 씬마다 영문 문자열로 작성:
   - "masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background visual, [스토리 서사에 따른 구체적 배경/환경/오브제/조명 묘사], no people, no human, no characters, dynamic Makoto Shinkai cinematic lighting, atmospheric anime environment, sophisticated anime digital shading, crisp modern linework, Kyoto Animation, CloverWorks and MAPPA quality, not 3D, no real photo, not retro anime, not 90s anime, not webtoon, not manhwa"

반드시 마크다운 코드블록 없이 순수 JSON 배열만 반환하세요:
[
  "Scene 1 영문 프롬프트 (0~5s)",
  "Scene 2 영문 프롬프트 (5~10s)",
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
                        print(f"[Scene Engine] Gemini가 '{arc_name_ko}' 기반 씬 {len(parsed)}개 프롬프트를 완벽하게 기획했습니다!")
                        return parsed[:num_scenes]
                    elif isinstance(parsed, list) and len(parsed) > 0:
                        print(f"[Scene Engine] Gemini 생성 {len(parsed)}개 수령, 목표치 {num_scenes}개로 확장합니다.")
                        prompts = list(parsed)
                        while len(prompts) < num_scenes:
                            prompts.append(prompts[len(prompts) % len(parsed)])
                        return prompts[:num_scenes]
            except Exception as e:
                print(f"[Scene Engine Warn] Gemini 씬 프롬프트 생성 시도 중 예외: {e}")

    # 폴백: 규칙 기반 완벽한 기승전결 스토리 아크 씬 빌더
    print(f"[Scene Engine] 지능형 스토리 서사 엔진({arc_name_ko})으로 {num_scenes}개 씬 시퀀스를 빌드합니다.")
    clean_lines = [l.strip() for l in lyrics.splitlines() if l.strip() and not l.strip().startswith("[") and not l.strip().startswith("(")]
    if not clean_lines:
        clean_lines = ["빛나는 순간", "어둠을 가르는 불꽃", "뜨거운 숨결", "끝없는 질주", "승리의 환호"]

    result_prompts = []
    for i in range(num_scenes):
        progress = i / max(1, num_scenes - 1)  # 0.0 (도입) ~ 1.0 (피날레)
        line_idx = min(int(progress * len(clean_lines)), len(clean_lines) - 1)
        target_line = clean_lines[line_idx]

        # 3단계 시네마틱 몽타주 샷 타입 교차:
        # 0: 인물 액션/퍼포먼스 컷 (Subject Focus & Narrative Action)
        # 1: 감성 풍경 & 스토리 B-Roll 이펙트 컷 (Scenery & Dynamic B-Roll - no people)
        # 2: 광활한 원경 / 환경 롱샷 / 실루엣 컷 (Wide Environmental Long Shot)
        shot_type = i % 3

        if shot_type == 1:
            # [타입 1: 현장감 넘치는 B-Roll & 환경 이펙트 (인물 없음)]
            if arc_type == "starlit_romance":
                if progress < 0.3:
                    broll_desc = "cinematic macro shot of delicate glass wind chimes swaying gently on open wooden balcony under glowing twilight sky with first evening star"
                elif progress < 0.7:
                    broll_desc = "breathtaking panoramic time-lapse view of vibrant cosmic milky way galaxy arching across deep indigo night sky, shimmering nebula dust and falling shooting stars"
                else:
                    broll_desc = "cinematic shot of an antique brass telescope on hilltop terrace overlooking shimmering nocturnal city lights below and crescent moon"
            elif arc_type == "youth_band":
                if progress < 0.3:
                    broll_desc = "cinematic close-up of a vintage tube guitar amplifier with warm glowing vacuum tubes and coiled audio cable on wooden floor, moody rehearsal room lighting"
                elif progress < 0.7:
                    broll_desc = "dynamic high-speed close-up of guitar pick striking vibrating electric guitar strings, flying dust motes glistening in vibrant stage lights"
                else:
                    broll_desc = "poetic shot of musical sheet papers fluttering in the rooftop sunset breeze next to guitar gig bag, golden hour cityscape"
            elif arc_type == "rainy_cafe_city":
                if progress < 0.3:
                    broll_desc = "macro cinematic shot of raindrops gently streaking down cozy cafe window, blurred amber streetlights bokeh outside in rainy dusk"
                elif progress < 0.7:
                    broll_desc = "cinematic close-up of a warm ceramic cup of latte with delicate foam art steaming softly on rustic oak table, gentle tranquil rain mood"
                else:
                    broll_desc = "aesthetic low-angle view of rain puddles on cobblestone alley reflecting vibrant neon signs and warm Japanese street lanterns"
            elif arc_type == "sunset_coastal":
                if progress < 0.3:
                    broll_desc = "cinematic atmospheric shot of turquoise ocean waves gently lapping against fine sandy beach, warm golden sunset light sparkling on water surface"
                elif progress < 0.7:
                    broll_desc = "dynamic shot of white sea foam splashing against coastal sea wall, soaring white seagulls in glowing pink and orange twilight sky"
                else:
                    broll_desc = "poetic wide shot of scenic coastal road guardrail bathed in fiery crimson sunset, gentle evening sea breeze"
            elif arc_type == "fantasy_magic":
                if progress < 0.3:
                    broll_desc = "cinematic shot of ancient moss-covered stone archway in enchanted elven forest, glowing turquoise fireflies dancing softly"
                elif progress < 0.7:
                    broll_desc = "dazzling visual of intricate golden and cyan glowing magical circles revolving in mid-air, floating arcane runic particles and crystalline energy sparks"
                else:
                    broll_desc = "serene vista of ancient fantasy castle ruins atop mist-veiled mountain under twin moons, celestial magical aurora"
            elif arc_type == "stage_diva":
                if progress < 0.3:
                    broll_desc = "atmospheric shot of darkened concert arena, ocean of ten thousand glowing violet and magenta audience lightsticks waving rhythmically"
                elif progress < 0.7:
                    broll_desc = "dynamic visual of blazing stage pyrotechnic sparks bursting upward in sync with music climax, dazzling moving laser beams cutting haze"
                else:
                    broll_desc = "cinematic shot of chrome stage microphone draped in glowing confetti falling gently from arena ceiling"
            elif arc_type == "battle_action":
                if progress < 0.3:
                    broll_desc = "cinematic low-angle close-up of cracked concrete pavement in ruined city, flickering flame sparks drifting through rising smoke"
                elif progress < 0.7:
                    broll_desc = "high-speed dynamic shot of explosive hit sparks and shockwave ripples shattering the air, flying debris and glowing embers"
                else:
                    broll_desc = "breathtaking shot of dissipating red smoke slowly settling over battlefield, glowing crater under dramatic twilight sky"
            elif arc_type == "cyberpunk_chase":
                if progress < 0.3:
                    broll_desc = "cinematic atmospheric shot of rain-slicked asphalt reflecting vivid cyan and magenta holographic billboards of futuristic cyberpunk city"
                elif progress < 0.7:
                    broll_desc = "high-speed close-up of motorcycle tire carving through asphalt leaving glowing neon electric light trails at sonic velocity"
                else:
                    broll_desc = "panoramic vista of futuristic skyscraper skyline with flying drone lights, midnight breeze through elevated highway"
            else: # swimmer_athlete
                if progress < 0.3:
                    broll_desc = "macro cinematic shot of turquoise blue water surface gently rippling against competition lane markers in an Olympic indoor pool"
                elif progress < 0.7:
                    broll_desc = "explosive high-speed macro shot of crystal water splashes bursting violently into the air in slow motion under stadium floodlights"
                else:
                    broll_desc = "cinematic shot of electronic scoreboard flashing '1st PLACE' and the yellow finish touchpad glistening with dripping water drops"

            full_p = (
                f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, "
                f"{broll_desc}, no people, no human, no characters, cinematic storytelling atmosphere, "
                f"breathtaking Makoto Shinkai anime lighting, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation and CloverWorks quality, "
                f"not photorealistic, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa"
            )

        elif shot_type == 2:
            # [타입 2: 광활한 자연 & 도시 풍경 와이드 파노라마 롱샷 (인물 없음)]
            if arc_type == "starlit_romance":
                env_desc = "wide environmental long shot of rolling grassy hill under breathtaking celestial galaxy horizon, shooting stars streaking through cosmic indigo sky"
            elif arc_type == "youth_band":
                env_desc = "wide panoramic shot of open rooftop overlooking distant glowing city skyline bathed in radiant golden sunset light, warm atmospheric haze"
            elif arc_type == "rainy_cafe_city":
                env_desc = "wide environmental long shot of rain-glistening Tokyo intersection, neon street reflections on wet asphalt, cozy amber shopfront lights"
            elif arc_type == "sunset_coastal":
                env_desc = "wide environmental panoramic shot of sandy coastal beach, gentle ocean waves sparkling under fiery crimson sunset, distant lighthouse"
            elif arc_type == "fantasy_magic":
                env_desc = "wide environmental fantasy vista of soaring cliff edge looking over vast ancient enchanted kingdom beneath glowing magical aurora"
            elif arc_type == "stage_diva":
                env_desc = "wide panoramic shot of massive empty concert arena, moving laser light beams cutting through foggy air, sweeping spotlights"
            elif arc_type == "battle_action":
                env_desc = "wide environmental panoramic shot of ruined cityscape at dusk, distant twilight smoke rising above cracked towers under crimson sky"
            elif arc_type == "cyberpunk_chase":
                env_desc = "wide environmental shot of high futuristic skybridge weaving through towering holographic neon skyscrapers, midnight breeze"
            else:
                env_desc = "wide environmental long shot of grand indoor aquatic arena, crystal blue Olympic pool surface glistening under stadium floodlights"

            full_p = (
                f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, "
                f"wide environmental long shot, {env_desc}, spacious cinematic composition, "
                f"breathtaking Makoto Shinkai dramatic lighting, sophisticated soft anime shading, crisp modern anime linework, theatrical anime movie quality, "
                f"no people, no human, no characters, not photorealistic, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa"
            )

        else:
            # [타입 0: 기승전결 서사에 맞춘 다이내믹 라이팅 & 공간 무드 (인물 없음)]
            if arc_type == "starlit_romance":
                if progress < 0.25:
                    action_theme = "antique carved wooden balcony overlooking quiet twilight town, gentle evening breeze rustling sheer curtains"
                elif progress < 0.5:
                    action_theme = "luminous starry night sky with glittering shooting star trails and glowing celestial nebula dust"
                elif progress < 0.8:
                    action_theme = "dramatic lens flare from a radiant full moon casting magical silver light across tranquil starlit lake"
                else:
                    action_theme = "serene dawn breaking over peaceful hill, warm morning sunlight gently dispelling night shadows"
            elif arc_type == "youth_band":
                if progress < 0.25:
                    action_theme = "sunlit rehearsal studio, vintage guitar leaning against wooden stool, afternoon dust motes dancing in sunbeams"
                elif progress < 0.5:
                    action_theme = "dynamic low angle shot of drum set and cymbals glistening under vibrant stage spotlights"
                elif progress < 0.8:
                    action_theme = "explosive burst of stage pyrotechnics and warm golden spotlights illuminating empty live house stage"
                else:
                    action_theme = "peaceful rooftop view at twilight, guitar case lying beside a warm glowing thermos in golden hour breeze"
            elif arc_type == "rainy_cafe_city":
                if progress < 0.25:
                    action_theme = "warm rustic cafe window looking out at gentle misty rain falling on quiet cobblestone street"
                elif progress < 0.5:
                    action_theme = "rain-slicked Tokyo street, neon signs reflecting like liquid jewels on wet asphalt"
                elif progress < 0.8:
                    action_theme = "sudden sunbeams breaking through rainy clouds, golden light illuminating crystal water droplets"
                else:
                    action_theme = "clear puddle reflecting blue sky and fresh green leaves after rain, tranquil peaceful morning"
            elif arc_type == "sunset_coastal":
                if progress < 0.25:
                    action_theme = "coastal cliff overlook, gentle sea breeze swaying wildflowers beside rustic wooden fence"
                elif progress < 0.5:
                    action_theme = "glistening turquoise waves crashing against rocky shoreline, spray of white sea foam catching golden light"
                elif progress < 0.8:
                    action_theme = "breathtaking crimson and violet sunset horizon where ocean meets blazing sky, dramatic cloud layers"
                else:
                    action_theme = "tranquil seashore at dusk, peaceful waves gently washing up on shore under evening twilight"
            elif arc_type == "fantasy_magic":
                if progress < 0.25:
                    action_theme = "ancient overgrown stone ruins nestled deep in enchanted forest, soft glowing moss and gentle mist"
                elif progress < 0.5:
                    action_theme = "intricate glowing magical circle revolving in mid-air, floating arcane turquoise runes and celestial particles"
                elif progress < 0.8:
                    action_theme = "breathtaking radiant explosion of celestial starlight magic illuminating ancient mountain spire"
                else:
                    action_theme = "quiet enchanted glade under twin moons, peaceful stardust settling on tranquil forest lake"
            elif arc_type == "stage_diva":
                if progress < 0.25:
                    action_theme = "illuminated empty stadium stage with chrome microphone stand casting sleek shadow in spotlight"
                elif progress < 0.5:
                    action_theme = "ocean of glowing magenta and cyan audience lightsticks waving in darkened concert hall"
                elif progress < 0.8:
                    action_theme = "magnificent climactic explosion of stage confetti and pyrotechnic sparks falling through laser beams"
                else:
                    action_theme = "peaceful darkened arena after concert, warm single spotlight illuminating confetti-covered stage floor"
            elif arc_type == "battle_action":
                if progress < 0.25:
                    action_theme = "dramatic low angle shot of ruined concrete battlefield, glowing embers and drifting smoke"
                elif progress < 0.5:
                    action_theme = "explosive shockwave ripples distorting the air, blistering hit sparks and fiery debris in mid-air"
                elif progress < 0.8:
                    action_theme = "spectacular blast of fiery crimson explosion illuminating shattered ruins against stormy sky"
                else:
                    action_theme = "dissipating smoke clearing over battlefield to reveal stars shining peacefully through clouds"
            elif arc_type == "cyberpunk_chase":
                if progress < 0.3:
                    action_theme = "rain-slicked elevated highway at midnight, glowing neon holographic billboards reflecting on asphalt"
                elif progress < 0.7:
                    action_theme = "dynamic blur of cyan and magenta light trails streaking across futuristic elevated roadway"
                else:
                    action_theme = "panoramic vista of neon cyberpunk metropolis under starry midnight sky, peaceful glowing skyscrapers"
            else: # swimmer_athlete
                if progress < 0.25:
                    action_theme = "Olympic indoor swimming arena, calm turquoise pool reflecting bright overhead stadium lights"
                elif progress < 0.5:
                    action_theme = "explosive slow-motion crystal water splash erupting from starting block under crisp lighting"
                elif progress < 0.8:
                    action_theme = "dynamic underwater view of churning turquoise water bubbles and glistening light caustics"
                else:
                    action_theme = "peaceful rippling water surface settling calm under warm gold championship lights"

            full_p = (
                f"masterpiece modern Japanese anime scenery, contemporary high-end Japanese TV anime background aesthetic, "
                f"{action_theme}, "
                f"dynamic Makoto Shinkai cinematic lighting, atmospheric anime environment, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, "
                f"no people, no human, no characters, not photorealistic, not 3D CGI, not semi-realistic, no live-action, no real human photo, not retro anime, not 90s anime, not webtoon, not manhwa"
            )

        result_prompts.append(full_p)

    return result_prompts



