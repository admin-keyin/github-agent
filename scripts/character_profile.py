"""
Inkey Studio - Chainsaw Man Official-Style Heroine Profile Generator
실제 체인소 맨(Chainsaw Man) MAPPA 애니메이션의 공식 캐릭터 디자인(레제, 마키마, 파워)과
직접적으로 유사하게 고품질 2D 애니메이션 비주얼을 생성합니다.

- 레제 (Reze from Chainsaw Man):
  MAPPA 공식 레제 비주얼, 흑자색 보브 단발, 에메랄드 눈동자, 시그니처 블랙 초커, 뺨의 홍조, 매혹적인 팜므파탈
- 마키마 (Makima from Chainsaw Man):
  MAPPA 공식 마키마 비주얼, 연한 적갈색 롱 브레이드(땋은머리), 상징적인 금빛 동심원 링 눈동자, 공안 데빌헌터 정장 수트핏 & 신비로운 카리스마
- 파워 (Power from Chainsaw Man):
  MAPPA 공식 파워 비주얼, 딸기 블론드 롱헤어 & 머리 위 선명한 붉은 뿔(Red Horns), 노란 십자 눈동자, 덧니/송곳니, 자유분방한 루즈핏 셔츠&타이

20대 초반(약 21~23세)의 성숙하고 매혹적이며 글래머러스한 원작 그대로의 여성미를 완벽하게 재현합니다.
"""

import random

HEROINE_ARCHETYPES = {
    "reze": {
        "archetype": "reze",
        "name_ko": "체인소 맨 레제 (Reze from Chainsaw Man)",
        "official_tag": "Reze from Chainsaw Man (official character design by MAPPA anime, bomb girl)",
        "hair_list": [
            {"en": "Reze's iconic dark violet-purple short bob hair with loose natural bangs and delicate wisps at nape", "ko": "레제 시그니처 흑자색/다크 바이올렛 보브 단발"},
            {"en": "deep lavender sleek chin-length bob hair framing pretty face with soft bangs", "ko": "딥 라벤더 슬릭 보브 단발"},
            {"en": "dark purple layered messy wavy short bob hair with casual soft styling", "ko": "다크 퍼플 내추럴 레이어드 보브헤어"}
        ],
        "face_eyes": (
            "Reze's authentic beautiful face, soft blush on cheeks, alluring expressive emerald-green anime eyes with delicate long eyelashes, "
            "gentle playful yet bittersweet seductive smile, iconic slender black choker necklace tightly around delicate throat"
        ),
        "vibe": "charismatic seductive femme fatale, playful youthfulness and deep emotional wistfulness, dangerous yet captivating bomb girl allure",
        "outfits": [
            {"en": "wearing Reze's iconic form-fitting white sleeveless collared blouse with a slim black necktie, tucked into dark shorts with suspenders, highlighting graceful collarbone and shoulders", "ko": "레제 시그니처 민소매 셔츠 & 슬림 블랙 넥타이 & 숏팬츠", "type": "원작시그니처"},
            {"en": "wearing a sexy fitted white cropped tank top revealing toned midriff and black shorts with signature black choker necklace", "ko": "크롭 탱크탑 & 숏팬츠 & 블랙 초커", "type": "돌핀팬츠"},
            {"en": "wearing an alluring backless black summer sundress fluttering softly, hugging glamorous hourglass curves", "ko": "백리스 블랙 썸머 선드레스", "type": "원피스"},
            {"en": "wearing an alluring sophisticated dark bikini swimsuit accentuating voluptuous bust and hourglass waist with black choker", "ko": "매혹적인 다크 비키니 수영복 & 초커", "type": "수영복"},
            {"en": "wearing a cozy oversized off-shoulder knit sweater dress slipping off one shoulder revealing black choker", "ko": "오프숄더 오버핏 니트 스웨터 드레스", "type": "니트웨어"},
            {"en": "wearing a stylish unzipped sporty tracksuit jacket over a fitted sports bra and high-waisted joggers", "ko": "집업 트레이닝 셋업 & 스포츠 브라탑", "type": "츄리닝"}
        ]
    },
    "makima": {
        "archetype": "makima",
        "name_ko": "체인소 맨 마키마 (Makima from Chainsaw Man)",
        "official_tag": "Makima from Chainsaw Man (official character design by MAPPA anime, Public Safety Devil Hunter)",
        "hair_list": [
            {"en": "Makima's iconic soft reddish-pink light auburn hair styled in an elegant loose single long braid resting over shoulder, with framing bangs", "ko": "마키마 시그니처 연한 적갈색/코랄핑크 땋은 롱헤어"},
            {"en": "gorgeous coral-wine red silky hair falling in a long graceful braid with soft temple wisps", "ko": "와인코랄 우아한 롱 브레이드"},
            {"en": "radiant light red-orange hair tied into Makima's signature low sophisticated side braid", "ko": "라이트 레드오렌지 시그니처 사이드 땋은머리"}
        ],
        "face_eyes": (
            "Makima's authentic gorgeous mature face, striking hypnotic golden yellow ring eyes with concentric circular pupils, "
            "calm piercing captivating gaze, subtle enigmatic Mona Lisa smile, dignified dominant feminine aura"
        ),
        "vibe": "supreme dominant elegance, enigmatic intellectual allure, calm sophisticated charisma, Public Safety leader presence",
        "outfits": [
            {"en": "wearing Makima's iconic Public Safety uniform: crisp form-fitting white dress shirt with black necktie, tucked into tailored high-waisted black trousers highlighting exceptionally voluptuous hourglass curves", "ko": "마키마 시그니처 슬림핏 화이트 드레스셔츠 & 블랙 타이 & 블랙 정장 슬랙스", "type": "원작시그니처"},
            {"en": "wearing a sleek tailored dark suit blazer over a form-fitting white collared shirt and black necktie with a tailored pencil mini skirt", "ko": "테일러드 수트 블레이저 & 펜슬 미니스커트", "type": "오피스수트"},
            {"en": "wearing an elegant off-shoulder bodycon cocktail dress with a graceful high leg slit highlighting curvy silhouette", "ko": "하이 슬릿 오프숄더 바디콘 드레스", "type": "원피스"},
            {"en": "wearing an alluring elegant black one-piece monokini swimsuit revealing attractive hourglass silhouette", "ko": "엘레강스 블랙 모노키니 수영복", "type": "수영복"},
            {"en": "wearing a sophisticated slim knit dress with deep sweetheart neckline hugging voluptuous curves", "ko": "슬림핏 니트 바디콘 드레스", "type": "니트웨어"},
            {"en": "wearing a chic college preppy blazer uniform with fitted cardigan and pleated mini skirt", "ko": "프레피 블레이저 & 플리츠 스커트", "type": "캠퍼스룩"}
        ]
    },
    "power": {
        "archetype": "power",
        "name_ko": "체인소 맨 파워 (Power from Chainsaw Man)",
        "official_tag": "Power from Chainsaw Man (official character design by MAPPA anime, Blood Fiend)",
        "hair_list": [
            {"en": "Power's iconic flowing strawberry blonde long hair with soft bangs, adorned with two distinct cute crimson red devil horns atop her head", "ko": "파워 시그니처 딸기 블론드 롱헤어 & 붉은 악마 뿔"},
            {"en": "pale reddish-pink flowing long hair with straight bangs, adorned with two iconic bright red horns protruding from head", "ko": "연분홍/스트로베리 핑크 롱헤어 & 붉은 뿔"},
            {"en": "radiant golden-peach wavy long hair parted casually, featuring two signature crimson red devil horns", "ko": "피치 블론드 루즈 웨이브 & 붉은 뿔"}
        ],
        "face_eyes": (
            "Power's authentic striking yellow-orange anime eyes with distinct sharp red cross-pattern pupils, "
            "bold playful confident smirk, subtle cute sharp canine teeth / vampire fangs, gorgeous face with wild energetic charm"
        ),
        "vibe": "wild energetic devil beauty, playful rebellious attitude, irresistible chaotic fiend charm",
        "outfits": [
            {"en": "wearing Power's iconic Public Safety devil hunter look: oversized white collared dress shirt loosely unbuttoned at collar with a crooked blue necktie, draped in an oversized blue jacket", "ko": "파워 시그니처 루즈핏 화이트 셔츠 & 비뚤어진 블루 타이 & 블루 재킷", "type": "원작시그니처"},
            {"en": "wearing a sporty cropped athletic tank top revealing toned abs and retro dolphin running shorts accentuating curvy hips", "ko": "크롭 탱크탑 & 와일드 돌핀팬츠", "type": "돌핀팬츠"},
            {"en": "wearing a trendy casual cropped zip-up hoodie over a sports bra and high-waisted sweatpants", "ko": "크롭 집업 후드 & 슬림 조거팬츠", "type": "츄리닝"},
            {"en": "wearing a vibrant athletic two-piece bikini swimsuit accentuating voluptuous hourglass figure with red horns", "ko": "스포티 투피스 비키니 수영복 & 붉은 뿔", "type": "수영복"},
            {"en": "wearing a stylish white tennis skirt with a form-fitting polo crop top accentuating toned figure", "ko": "테니스 스커트 & 슬림 폴로탑", "type": "테니스룩"},
            {"en": "wearing alluring fitted high-waisted denim shorts and tight ribbed cropped tee accentuating hourglass waist", "ko": "데님 숏팬츠 & 타이트 립 크롭티", "type": "스트릿캐주얼"}
        ]
    }
}


def generate_random_character_profile() -> dict:
    """
    곡 생성 시마다 호출되어 체인소 맨의 레제, 마키마, 파워 중 하나를 무작위로 선택하고,
    해당 캐릭터의 공식 원작 설정(헤어, 눈동자, 시그니처 의상)을 생성합니다.
    선택된 캐릭터는 해당 곡의 모든 씬에 일관되게 고정됩니다.
    """
    archetype_key = random.choice(["reze", "makima", "power"])
    arch = HEROINE_ARCHETYPES[archetype_key]

    hair = random.choice(arch["hair_list"])
    outfit = random.choice(arch["outfits"])

    korean_summary = f"[{arch['name_ko']}] {hair['ko']} + {outfit['ko']} ({outfit['type']})"

    return {
        "archetype": arch["archetype"],
        "archetype_name": arch["name_ko"],
        "official_tag": arch["official_tag"],
        "hair_en": hair["en"],
        "hair_ko": hair["ko"],
        "face_eyes": arch["face_eyes"],
        "vibe": arch["vibe"],
        "outfit_en": outfit["en"],
        "outfit_ko": outfit["ko"],
        "outfit_type": outfit["type"],
        "korean_summary": korean_summary
    }


def build_character_prompt(profile: dict = None) -> str:
    """
    체인소 맨의 레제, 마키마, 파워 캐릭터 원형의 정밀 비주얼 프롬프트를 조립합니다.
    - MAPPA 공식 체인소 맨 작화 스타일 명시
    - 20대 초반 성인 여성 (early twenties, 21-23 years old)
    - 캐릭터별 공식 원작 시그니처(눈동자, 헤어, 뿔, 초커, 의상) 100% 반영
    - 어린아이(로리) 및 중년(아줌마) 엄격 배제
    """
    if not profile or "archetype" not in profile:
        profile = generate_random_character_profile()

    official_tag = profile.get("official_tag", "Reze from Chainsaw Man (official MAPPA anime design)")
    hair_en = profile.get("hair_en", "dark violet-purple short bob hair with loose natural bangs")
    face_eyes = profile.get("face_eyes", "alluring expressive emerald-green anime eyes, black choker necklace")
    outfit_en = profile.get("outfit_en", "wearing a form-fitting white sleeveless collared blouse with a slim black necktie")
    vibe = profile.get("vibe", "charismatic seductive femme fatale")

    return (
        f"{official_tag}, stunning gorgeous anime woman in her early twenties (around 21 years old), "
        f"authentic official character look from Chainsaw Man animated by MAPPA, "
        f"{face_eyes}, "
        f"{hair_en}, "
        f"{vibe}, "
        f"extremely glamorous tall hourglass figure, voluptuous mature curves, graceful slender waist, "
        f"{outfit_en} and attractive feminine body silhouette, "
        f"clean 2D cel shading, crisp dynamic anime linework, MAPPA animation studio quality, "
        f"not a child, not underage, not a little girl, no loli, not childish, not middle-aged, not an older woman, not matronly"
    )
