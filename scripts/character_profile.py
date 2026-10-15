"""
Inkey Studio - Chainsaw Man Inspired Heroine Profile Generator
레제(Reze), 마키마(Makima), 파워(Power) 스타일의 매혹적이고 성숙한 20대 초반 캐릭터 원형을 제공합니다.
- 레제(Reze): 흑자색 보브 단발, 초커, 에메랄드 눈동자, 치명적인 팜므파탈 & 아련한 청춘의 스파이 미녀
- 마키마(Makima): 연한 적갈색 땋은 롱헤어, 신비로운 금빛 동심원 눈동자, 완벽한 수트핏 & 고혹적인 지성미
- 파워(Power): 딸기 블론드 롱헤어 & 붉은 뿔, 십자 눈동자, 자유분방하고 와일드하며 글래머러스한 악마 미녀

너무 어린아이(로리) 같지 않고, 너무 나이 든(아줌마) 느낌도 없는,
20대 초반(21~23세)의 세련되고 성숙하며 글래머러스한 최고의 여성미를 구현합니다.
"""

import random

HEROINE_ARCHETYPES = {
    "reze": {
        "name_ko": "레제(Reze) 스타일 - 치명적인 팜므파탈 & 아련한 보브컷 미녀",
        "archetype": "reze",
        "hair_list": [
            {"en": "dark violet-purple short bob hair with loose natural bangs and wisps at nape", "ko": "흑자색/다크 바이올렛 단발 보브컷"},
            {"en": "silky deep lavender chin-length sleek bob hair framing attractive face", "ko": "딥 라벤더 슬릭 보브 단발"},
            {"en": "dark purple layered wavy short bob hair with casual soft styling", "ko": "다크 퍼플 내추럴 레이어드 보브헤어"}
        ],
        "face_eyes": (
            "alluring expressive emerald-green anime eyes with delicate long eyelashes, "
            "refined captivating pretty face, gentle playful yet bittersweet seductive smile, "
            "slender black choker necklace accentuating delicate throat and collarbones"
        ),
        "vibe": "charismatic seductive femme fatale with playful youthfulness and deep emotional wistfulness",
        "outfits": [
            {"en": "wearing a form-fitting white sleeveless collared blouse with a slim black necktie, tucked into stylish dark shorts, highlighting graceful shoulders and collarbone", "ko": "시그니처 민소매 셔츠 & 슬림 블랙 타이", "type": "시그니처룩"},
            {"en": "wearing a sexy fitted white cropped tank top revealing toned midriff and retro dark dolphin shorts with black choker", "ko": "크롭 탱크탑 & 돌핀팬츠 & 초커", "type": "돌핀팬츠"},
            {"en": "wearing a sophisticated backless black summer sundress fluttering softly, hugging hourglass curves", "ko": "백리스 블랙 썸머 선드레스", "type": "원피스"},
            {"en": "wearing an alluring sophisticated dark bikini swimsuit accentuating voluptuous bust and hourglass waist", "ko": "매혹적인 다크 비키니 수영복", "type": "수영복"},
            {"en": "wearing an alluring oversized off-shoulder knit sweater dress slipping off one shoulder", "ko": "오프숄더 오버핏 니트 스웨터 드레스", "type": "니트웨어"},
            {"en": "wearing a stylish unzipped sporty tracksuit jacket over a fitted sports bra and high-waisted joggers", "ko": "집업 트레이닝 셋업 & 스포츠 브라탑", "type": "츄리닝"}
        ]
    },
    "makima": {
        "name_ko": "마키마(Makima) 스타일 - 신비로운 금빛 동심원 & 고혹적인 수트 미녀",
        "archetype": "makima",
        "hair_list": [
            {"en": "soft reddish-pink light auburn hair styled in an elegant loose single long braid resting over shoulder, with framing side bangs", "ko": "연한 적갈색/코랄핑크 땋은 롱헤어"},
            {"en": "gorgeous coral-wine red silky hair falling in a long graceful braid with soft temple wisps", "ko": "와인코랄 우아한 롱 브레이드"},
            {"en": "radiant light red-orange hair tied into a low sophisticated side braid", "ko": "라이트 레드오렌지 사이드 땋은머리"}
        ],
        "face_eyes": (
            "striking hypnotic golden ring eyes with concentric circular pupils, calm piercing captivating gaze, "
            "exquisitely refined mature facial features, subtle enigmatic Mona Lisa smile, dignified dominant allure"
        ),
        "vibe": "supreme dominant elegance, enigmatic intellectual allure, calm sophisticated charisma",
        "outfits": [
            {"en": "wearing a crisp form-fitting white dress shirt with black necktie, tucked into tailored high-waisted black trousers highlighting glamorous hourglass curves", "ko": "시그니처 슬림핏 화이트 셔츠 & 블랙 타이 & 슬랙스", "type": "오피스수트"},
            {"en": "wearing a sleek tailored dark blazer over a form-fitting white collared shirt and black necktie with a tailored mini pencil skirt", "ko": "테일러드 수트 블레이저 & 펜슬 미니스커트", "type": "오피스수트"},
            {"en": "wearing an elegant off-shoulder bodycon cocktail dress with a graceful high leg slit highlighting curvy silhouette", "ko": "하이 슬릿 오프숄더 바디콘 드레스", "type": "원피스"},
            {"en": "wearing an alluring elegant black one-piece monokini swimsuit revealing attractive hourglass silhouette", "ko": "엘레강스 블랙 모노키니 수영복", "type": "수영복"},
            {"en": "wearing a sophisticated slim knit dress with deep sweetheart neckline hugging voluptuous curves", "ko": "슬림핏 니트 바디콘 드레스", "type": "니트웨어"},
            {"en": "wearing chic collegiate preppy blazer uniform with fitted cardigan and pleated mini skirt", "ko": "프레피 블레이저 & 플리츠 스커트", "type": "캠퍼스룩"}
        ]
    },
    "power": {
        "name_ko": "파워(Power) 스타일 - 딸기 블론드 & 붉은 뿔, 와일드 악마 미녀",
        "archetype": "power",
        "hair_list": [
            {"en": "flowing strawberry blonde long hair with soft bangs, adorned with two distinct cute crimson red devil horns atop her head", "ko": "딸기 블론드 롱헤어 & 붉은 악마 뿔"},
            {"en": "pale reddish-pink flowing long hair with straight bangs, adorned with two iconic bright red horns", "ko": "연분홍/스트로베리 핑크 롱헤어 & 붉은 뿔"},
            {"en": "radiant golden-peach wavy long hair parted casually, featuring two signature crimson red horns", "ko": "피치 블론드 루즈 웨이브 & 붉은 뿔"}
        ],
        "face_eyes": (
            "striking yellow-orange eyes with distinct sharp cross-pattern pupils, bold playful confident smirk, "
            "subtle cute sharp canine teeth, stunning gorgeous face with wild energetic charm"
        ),
        "vibe": "wild energetic devil beauty, playful rebellious attitude, irresistible mischievous allure",
        "outfits": [
            {"en": "wearing an oversized white collared dress shirt loosely unbuttoned at collar with a crooked blue necktie, draped in a blue jacket", "ko": "시그니처 루즈핏 화이트 셔츠 & 블루 타이 룩", "type": "시그니처룩"},
            {"en": "wearing a sporty cropped athletic tank top revealing toned abs and retro dolphin running shorts accentuating curvy hips", "ko": "크롭 탱크탑 & 와일드 돌핀팬츠", "type": "돌핀팬츠"},
            {"en": "wearing a trendy casual cropped zip-up hoodie over a sports bra and high-waisted sweatpants", "ko": "크롭 집업 후드 & 슬림 조거팬츠", "type": "츄리닝"},
            {"en": "wearing a vibrant athletic two-piece bikini swimsuit accentuating voluptuous hourglass figure", "ko": "스포티 투피스 비키니 수영복", "type": "수영복"},
            {"en": "wearing a stylish white tennis skirt with a form-fitting polo crop top accentuating toned figure", "ko": "테니스 스커트 & 슬림 폴로탑", "type": "테니스룩"},
            {"en": "wearing an alluring fitted denim shorts and tight ribbed cropped tee accentuating hourglass waist", "ko": "데님 숏팬츠 & 타이트 립 크롭티", "type": "스트릿캐주얼"}
        ]
    }
}


def generate_random_character_profile() -> dict:
    """
    곡 생성 시마다 호출되어 레제, 마키마, 파워 스타일 중 하나를 무작위로 선택하고,
    해당 캐릭터의 고유 헤어/눈동자/의상 조합을 생성합니다.
    선택된 캐릭터는 해당 곡의 모든 씬에 일관되게 고정됩니다.
    """
    archetype_key = random.choice(["reze", "makima", "power"])
    arch = HEROINE_ARCHETYPES[archetype_key]

    hair = random.choice(arch["hair_list"])
    outfit = random.choice(arch["outfits"])

    korean_summary = f"[{arch['name_ko'].split(' - ')[0]}] {hair['ko']} + {outfit['ko']} ({outfit['type']})"

    return {
        "archetype": arch["archetype"],
        "archetype_name": arch["name_ko"],
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
    레제, 마키마, 파워 캐릭터 원형의 핵심 비주얼 프롬프트를 조립합니다.
    - 20대 초반 성인 여성 (early twenties, 21-23 years old)
    - 캐릭터별 고유 눈동자/표정/헤어/시그니처 매력 반영
    - 어린아이(로리) 및 중년(아줌마) 엄격 배제
    """
    if not profile or "archetype" not in profile:
        profile = generate_random_character_profile()

    hair_en = profile.get("hair_en", "dark violet-purple short bob hair with loose natural bangs")
    face_eyes = profile.get("face_eyes", "alluring expressive emerald-green anime eyes, black choker necklace")
    outfit_en = profile.get("outfit_en", "wearing a form-fitting white sleeveless collared blouse with a slim black necktie")
    vibe = profile.get("vibe", "charismatic seductive femme fatale")

    return (
        f"stunning alluring young adult anime woman in her early twenties (around 21 years old), "
        f"mature feminine elegance yet youthful fresh beauty, "
        f"{face_eyes}, "
        f"{hair_en}, "
        f"{vibe}, "
        f"extremely glamorous tall hourglass figure, voluptuous mature curves, graceful slender waist, "
        f"{outfit_en} and attractive feminine body silhouette, "
        f"not a child, not underage, not a little girl, no loli, not childish, not middle-aged, not an older woman, not matronly"
    )
