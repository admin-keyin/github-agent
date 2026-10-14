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
    "답답했던 일상과 한계를 부수고 시원하게 터져 나오는 통쾌한 질주와 해방감",
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

[★ 2. 중독적인 가사 (lyrics) 작사 규칙]
1. 곡 제목(title)은 온전한 한국어 곡명으로 짓고, 절대 '#1', '#91' 같은 해시태그나 임의의 숫자 번호를 붙이지 마세요.
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

[★ 3. 작사된 가사 파트에 맞춘 감성 동물 / 자연 / 우주 / 풍경 애니메이션 씬 프롬프트 (scene_prompts)]
※ 가장 중요한 연출 규칙 (★사람 얼굴 클로즈업 배제, 동물/자연/우주/풍경 중심★):
1. 어색한 사람 얼굴을 억지로 등장시키지 마세요! 가사의 감정과 분위기에 어울리는 '귀엽거나 신비로운 동물(예: 길고양이, 철새 무리, 여우, 고래, 나비 등)', '웅장한 자연환경(비 내리는 숲, 파도치는 바다, 노을빛 언덕)', 또는 '환상적인 우주와 밤하늘(은하수, 오로라, 별똥별, 네온 도시 야경)'을 적극 활용하세요.
2. 특정 고정된 캐릭터에 얽매이지 말고, 가사 전개에 따라 배경과 피사체가 자유롭고 유기적으로 바뀌도록 연출하세요:
   - Scene 1 (도입부): 가사의 시작 분위기를 여는 자연/도시 정경 (예: 비 내리는 창가에 앉아 바깥을 바라보는 작은 고양이, 빗방울 떨어지는 수면)
   - Scene 2 (1절): 가사의 전개와 서사 (예: 숲속을 천천히 거니는 사슴, 나뭇잎 사이로 쏟아지는 햇살, 바람에 흔들리는 풀잎)
   - Scene 3 (후렴): 감정의 폭발과 환상적인 클라이맥스 (예: 밤하늘 가득 터지는 찬란한 오로라와 은하수 바다를 유영하는 거대한 우주 고래, 쏟아지는 별똥별)
   - Scene 4 (2절/브릿지): 깊고 몽환적인 분위기 반전 (예: 네온 불빛이 번지는 심야 도시 지붕 위를 달리는 검은 고양이, 안개 자욱한 호숫가)
   - Scene 5 (아웃트로): 따스한 위로와 여운의 피날레 (예: 황금빛 일출이 번지는 바다 수평선 위로 날아오르는 새들, 평화롭고 광활한 자연)
(형식: "masterpiece 2D anime music video visual, [가사 분위기에 맞는 동물/자연/우주 묘사], breathtaking scenery, atmospheric depth, cinematic lighting, no human face")

[★ 5. 유튜브 시청자를 울리는 감성 곡 설명 에세이 (story_description) 작성 규칙]
단순한 템플릿이 아닌, 이 곡을 듣는 사람의 마음에 깊은 울림을 주는 3~5단락의 아름다운 한국어 곡 소개 에세이/시놉시스를 작성하세요:
- 감성을 자극하는 시적인 한 줄 헤드카피 (예: "불 꺼진 방, 귓가에 조용히 스며드는 우리들의 지나간 계절")
- 곡이 탄생하게 된 서사와 화자의 감정선, 음악적 메시지
- 이 곡을 들으면 좋은 순간들 (새벽 드라이브, 지친 하루의 퇴근길, 눈물 흘리고 싶은 밤 등)

[★ 6. 숏츠용 킬링파트 문구 (shorts_concept)]
숏츠 영상에서 시선을 강탈할 1줄의 임팩트 있는 문구 및 하이라이트 가사 안내

반드시 마크다운 코드블록(```json) 없이 순수 JSON만 출력하세요:
{{
  "title": "독창적이고 매력적인 한글 곡 제목 (필요시 부제 병기)",
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
                        "shorts_concept": parsed.get("shorts_concept", f"{parsed['title']} 하이라이트 킬링파트"),
                        "genre_name": spec["name"],
                        "category": spec["category"]
                    }
                    return parsed["title"], parsed["style_tags"], parsed["lyrics"], extra_meta
            except Exception as e:
                print(f"[Lyric Engine Warn] {model_name} 호출 중 오류 발생: {e}")
                continue

    # 2. Gemini 미연동 또는 실패 시 다채로운 룰베이스 동적 폴백 생성기
    seed = int(time.time() * 1000) % 10000

    if spec["category"] == "changpop":
        prefixes = ["모두가 잠든 밤의", "거침없는", "멈추지 않는", "심장을 뛰게 할", "통쾌한", "푸른 불꽃의", "전력질주", "마침내 찾아온", "한계를 부수는", "눈부신 속도의"]
        subjects = ["하이라이트", "오버드라이브", "질주", "스파크", "돌파구", "새벽탈출", "시그널", "엔진소리", "플레이리스트", "카운트다운"]
        title = f"{random.choice(prefixes)} {random.choice(subjects)}"
        
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
        prefixes = ["우리가 머물던", "어느 늦은 밤의", "푸른 새벽의", "바람이 머무는", "달빛 스케치", "비 내리는 오후", "기억의 파도", "너에게 닿는", "계절의 끝자락", "소란한 밤의", "마지막 정거장의"]
        subjects = ["정거장", "노랫소리", "고백", "온기", "발자국", "그림자", "풍경", "기억", "바람", "빛", "계절", "여름밤", "일기장"]
        title = f"{random.choice(prefixes)} {random.choice(subjects)}"
        
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
        f"masterpiece 2D anime music video visual, quiet coastal train platform at twilight, glowing pastel ocean horizon, calm water reflections, cinematic atmospheric lighting, no human face",
        f"masterpiece 2D anime music video visual, cute little cat sheltering under a glowing bus stop in gentle evening rain, puddles reflecting city lights, heartwarming mood, no human face",
        f"masterpiece 2D anime music video visual, breathtaking starry galaxy night sky with blooming vibrant aurora and falling shooting stars, cosmic fantasy landscape, dynamic cinematic lighting, no human face",
        f"masterpiece 2D anime music video visual, flock of migrating birds flying over misty forest canopy and tranquil lake at dusk, deep ambient depth, no human face",
        f"masterpiece 2D anime music video visual, sunlit golden flower field on a high hill overlooking endless sunrise ocean, warm morning glow, inspiring peaceful ending, no human face"
    ]
    fallback_shorts_scenes = [
        f"masterpiece 2D anime music video visual, glowing jellyfish swimming through starry night sky above peaceful clouds, no human face",
        f"masterpiece 2D anime music video visual, radiant aurora borealis over snowy pine mountains with glowing fireflies, no human face",
        f"masterpiece 2D anime music video visual, calm cat resting on window sill looking at soft morning sunrise, warm cinematic anime, no human face"
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
    가사 흐름과 감정선에 맞춘 2D 애니메이션 프롬프트 N개를 생성합니다. (사람 얼굴 배제, 동물/자연/우주 중심)
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
당신은 최고급 2D 시네마틱 애니메이션 뮤직비디오 비주얼 디렉터입니다.
이 곡의 총 길이는 {duration_sec:.1f}초이며, 10초 단위 비디오 씬을 총 {num_scenes}개 생성해야 합니다.
노래의 기승전결(도입부 -> 1절 -> 후렴 -> 2절/브릿지 -> 클라이맥스 후렴 -> 아웃트로)과 가사 내용에 맞춰,
각 10초 구간(총 {num_scenes}개 씬)의 애니메이션 프롬프트를 작성해주세요.

[가사]:
{lyrics[:1800]}

[★ 절대 준수 연출 규칙]:
1. 사람 얼굴 클로즈업 절대 금지 (no human face close-up, no human face):
   가사의 감정과 정서에 부합하는 동물(고양이, 사슴, 여우, 고래, 나비, 철새 등), 아름다운 자연 풍경(비, 숲, 바다, 석양, 호수, 들꽃), 신비로운 우주/밤하늘(은하수, 오로라, 별똥별, 네온 도시 풍경)을 가사의 분위기에 맞게 가변적으로 배치하세요.
2. 씬 흐름이 시간에 따라 자연스럽게 발전하며 기승전결이 있도록 구성하세요:
   - 0~20s: 잔잔하고 서정적인 도입부 정경 (예: 비 내리는 창가의 고양이, 빗방울 수면)
   - 중간: 가사의 감정선과 리듬에 맞춘 역동적이거나 따뜻한 풍경 (예: 숲속 사슴, 바람 부는 해안가)
   - 후렴/클라이맥스: 웅장한 은하수, 오로라, 유성우, 빛나는 바다를 유영하는 우주 고래 등 환상적인 비주얼 폭발
   - 마지막 씬: 따스한 여운을 주는 일출/노을 피날레
3. 모든 프롬프트는 영문으로 작성하며, 다음 형식을 준수하세요:
   "masterpiece 2D anime music video visual, [구체적 동물/자연/우주 묘사], atmospheric depth, beautiful cinematic lighting, no human face"

반드시 마크다운 코드블록 없이 순수 JSON 배열만 반환하세요:
[
  "씬 1 영문 프롬프트 (0~10s)",
  "씬 2 영문 프롬프트 (10~20s)",
  ... (정확히 {num_scenes}개의 문자열 리스트)
]
"""
                payload = {
                    "contents": [{"parts": [{"text": prompt_instruction}]}],
                    "generationConfig": {"temperature": 0.8}
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
                        print(f"[Scene Engine] Gemini가 10초 단위 맞춤 씬 {len(parsed)}개 프롬프트를 완벽하게 기획했습니다!")
                        return parsed[:num_scenes]
                    elif isinstance(parsed, list) and len(parsed) > 0:
                        print(f"[Scene Engine] Gemini 생성 {len(parsed)}개 수령, 목표치 {num_scenes}개로 확장합니다.")
                        prompts = list(parsed)
                        while len(prompts) < num_scenes:
                            prompts.append(prompts[len(prompts) % len(parsed)])
                        return prompts[:num_scenes]
            except Exception as e:
                print(f"[Scene Engine Warn] Gemini 씬 프롬프트 생성 시도 중 예외: {e}")

    # 폴백: 지능형 시네마틱 팔레트 순차 생성
    print(f"[Scene Engine] 내장 시네마틱 팔레트로 {num_scenes}개 씬 시퀀스를 빌드합니다.")
    palette = [
        "quiet coastal train platform at twilight, glowing pastel ocean horizon, calm water reflections, cinematic atmospheric lighting, no human face",
        "cute little cat sheltering under a glowing bus stop in gentle evening rain, puddles reflecting city lights, heartwarming mood, no human face",
        "misty morning pine forest with a gentle white deer walking softly through sunbeams filtering through trees, serene atmosphere, no human face",
        "sunlight breaking through green canopy leaves, gentle breeze swaying lush meadow wildflowers, cinematic depth, no human face",
        "coastal cliffs overlooking endless sapphire ocean with distant glowing lighthouse and soft foaming waves, golden hour lighting, no human face",
        "flock of migrating birds soaring across warm amber sunset clouds towards horizon, epic cinematic view, no human face",
        "evening city skyline transition to deep purple twilight with neon glow reflections on rain-soaked rooftops, quiet black cat silhouette, no human face",
        "glowing jellyfish gracefully drifting through starry night sky clouds, surreal whimsical fantasy art, no human face",
        "breathtaking starry galaxy night sky with blooming vibrant aurora borealis and falling shooting stars, cosmic fantasy landscape, no human face",
        "majestic cosmic whale swimming silently through glittering stardust and glowing nebula clouds in deep cosmos, majestic scale, no human face",
        "meteor shower trailing across midnight blue sky over snow-capped mountains and tranquil reflective lake, sparkling starlight, no human face",
        "golden flower field on a high hill overlooking endless sunrise ocean, warm morning glow, floating dandelion seeds, inspiring peaceful ending, no human face"
    ]

    source_pool = list(base_prompts) if base_prompts else []
    source_pool.extend(palette)

    cam_variations = [
        "slow cinematic camera push-in",
        "wide atmospheric panoramic view",
        "smooth low angle tracking shot",
        "gentle wind motion, ethereal lighting",
        "epic cinematic aerial view",
        "soft ambient glow, peaceful depth"
    ]

    result_prompts = []
    for i in range(num_scenes):
        base_p = source_pool[i % len(source_pool)]
        cam_mod = cam_variations[i % len(cam_variations)]
        full_p = f"masterpiece 2D anime music video visual, {base_p}, {cam_mod}"
        result_prompts.append(full_p)

    return result_prompts



