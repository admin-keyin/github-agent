"""
Inkey Studio - Chainsaw Man Authentic Heroine Profile Generator
실제 체인소 맨(Chainsaw Man) MAPPA 공식 애니메이션 캐릭터(레제, 마키마, 파워)와
100% 일치하는 정밀한 얼굴 싱크로율과 압도적인 글래머러스(Ultra-Voluptuous Hourglass) 바디라인을 생성합니다.

- 레제 (Reze):
  원작 100% 일치 얼굴, 흑자색 단발, 에메랄드 캣아이즈, 볼의 핑크 홍조, 시그니처 블랙 초커,
  압도적인 글래머러스 바디라인 (풍만한 가슴과 얇은 개미허리, 골반 라인).
- 마키마 (Makima):
  원작 100% 일치 얼굴, 상징적인 금빛 동심원 타겟 링 눈동자, 연한 적갈색 땋은머리, 신비로운 미소,
  슬림핏 셔츠를 터뜨릴 듯한 대단히 글래머러스한 볼륨감과 우아한 수트핏.
- 파워 (Power):
  원작 100% 일치 얼굴, 붉은 십자(+) 동공의 황금빛 눈동자, 머리 위 선명한 진홍색 뿔, 뾰족한 송곳니 덧니,
  탄탄하고 대단히 볼륨감 넘치는 글래머러스 바디라인.

어린아이(로리)나 중년(아줌마) 느낌이 전혀 없는, 20대 초반 성인 여성의 극상 글래머러스 뷰티를 구현합니다.
"""

import random

HEROINE_ARCHETYPES = {
    "reze": {
        "archetype": "reze",
        "name_ko": "체인소 맨 레제 (Reze from Chainsaw Man)",
        "official_tag": (
            "Reze from Chainsaw Man, official MAPPA anime character design, "
            "exact 100% identical face likeness of Reze from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Reze's iconic dark violet-purple short bob hair with loose parted bangs and wisps at nape, exact official anime hair look", "ko": "레제 공식 흑자색/다크 바이올렛 보브 단발"},
            {"en": "Reze's signature deep lavender sleek chin-length bob hair perfectly framing pretty face, official MAPPA style", "ko": "레제 딥 라벤더 슬릭 보브 단발"},
            {"en": "Reze's dark purple layered natural wavy short bob hair with soft bangs, authentic anime design", "ko": "레제 다크 퍼플 내추럴 레이어드 보브"}
        ],
        "face_eyes": (
            "Reze's authentic beautiful face, soft cute pink blush on cheeks, alluring expressive emerald-green anime eyes with delicate long eyelashes, "
            "seductive playful yet bittersweet smile, iconic slender black choker necklace tightly worn around delicate throat"
        ),
        "vibe": "charismatic seductive femme fatale, playful youthfulness and deep emotional wistfulness, dangerous yet captivating bomb girl allure",
        "outfits": [
            {"en": "wearing Reze's iconic tight white sleeveless collared blouse with a slim black necktie hugging very large voluptuous bust with deep cleavage, tucked into dark shorts with suspenders, tiny waist and curvy hips", "ko": "레제 시그니처 민소매 셔츠 & 슬림 블랙 넥타이 (극상 글래머핏)", "type": "원작시그니처"},
            {"en": "wearing a tight white cropped tank top revealing deep cleavage and toned midriff, paired with black shorts and signature black choker necklace, accentuating ultra-voluptuous curves", "ko": "타이트 크롭 탱크탑 & 숏팬츠 & 블랙 초커", "type": "돌핀팬츠"},
            {"en": "wearing an alluring backless black summer sundress with deep sweetheart neckline clinging to extremely voluptuous hourglass curves and large bust", "ko": "백리스 블랙 썸머 선드레스 (글래머 바디콘)", "type": "원피스"},
            {"en": "wearing a revealing sophisticated dark bikini swimsuit accentuating massive voluptuous bust, deep cleavage, and curvy hourglass hips with black choker", "ko": "매혹적인 다크 비키니 수영복 & 초커 (글래머러스)", "type": "수영복"},
            {"en": "wearing a cozy off-shoulder knit sweater dress slipping off shoulder revealing deep cleavage, black choker, and voluptuous silhouette", "ko": "오프숄더 글래머 니트 스웨터 드레스", "type": "니트웨어"},
            {"en": "wearing a stylish unzipped sporty tracksuit jacket over a form-fitting sports bra accentuating cleavage and high-waisted tight joggers", "ko": "집업 트레이닝 셋업 & 스포츠 브라탑", "type": "츄리닝"}
        ],
        "combat_actions": {
            "prep": "standing ready in sleek combat stance, miniature fiery sparks and faint smoke dancing playfully around delicate fingertips, alluring confident smirk",
            "strike": "delivering an explosive dynamic high kick enveloped in a massive burst of fiery shockwaves and blast sparks, sleek lethal martial arts movement",
            "climax": "detonating a breathtaking fiery explosion behind her, leaping forward with explosive velocity, bomb devil fireworks and blistering hit sparks",
            "finish": "landing gracefully amidst dissipating embers and smoke, wiping her mouth with a seductive breathless smile"
        }
    },
    "makima": {
        "archetype": "makima",
        "name_ko": "체인소 맨 마키마 (Makima from Chainsaw Man)",
        "official_tag": (
            "Makima from Chainsaw Man, official MAPPA anime character design, Public Safety Special Division leader, "
            "exact 100% identical face likeness of Makima from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Makima's iconic soft reddish-pink light auburn hair styled in an elegant loose single long braid resting over shoulder, framing side bangs, exact official anime hair look", "ko": "마키마 공식 연한 적갈색/코랄핑크 땋은 롱헤어"},
            {"en": "Makima's gorgeous coral-wine red silky hair falling in an elegant long graceful single braid, official MAPPA design", "ko": "마키마 와인코랄 우아한 롱 브레이드"},
            {"en": "Makima's signature radiant light red-orange hair tied into a low sophisticated side braid with soft bangs", "ko": "마키마 시그니처 사이드 땋은머리"}
        ],
        "face_eyes": (
            "Makima's authentic gorgeous mature face, iconic hypnotic yellow-amber ring eyes with distinct concentric circular target pupils, "
            "calm piercing captivating gaze, subtle enigmatic Mona Lisa smile, dignified dominant feminine aura"
        ),
        "vibe": "supreme dominant elegance, enigmatic intellectual allure, calm sophisticated charisma, Public Safety leader presence",
        "outfits": [
            {"en": "wearing Makima's iconic Public Safety uniform: tight crisp white dress shirt with black necktie hugging exceptionally large voluptuous bust with button-straining cleavage, tucked into tailored high-waisted black trousers accentuating hourglass waist and wide curvy hips", "ko": "마키마 시그니처 타이트 화이트 셔츠 & 블랙 타이 & 슬랙스 (극상 글래머핏)", "type": "원작시그니처"},
            {"en": "wearing a sleek tailored dark suit blazer unbuttoned over a form-fitting white shirt and black necktie with a tight tailored pencil mini skirt hugging thick curvy hips", "ko": "테일러드 수트 블레이저 & 슬림 펜슬 미니스커트", "type": "오피스수트"},
            {"en": "wearing an elegant off-shoulder bodycon cocktail dress with deep sweetheart neckline and high leg slit clinging to ultra-voluptuous curves and prominent bust", "ko": "하이 슬릿 오프숄더 글래머 바디콘 드레스", "type": "원피스"},
            {"en": "wearing an alluring elegant black one-piece monokini swimsuit with plunging neckline revealing massive voluptuous bust and attractive hourglass silhouette", "ko": "엘레강스 블랙 플런징 모노키니 수영복", "type": "수영복"},
            {"en": "wearing a sophisticated tight knit dress with deep neckline hugging extraordinarily voluptuous bust and hourglass curves", "ko": "타이트 니트 글래머 바디콘 드레스", "type": "니트웨어"},
            {"en": "wearing a chic college preppy blazer uniform with a fitted knit cardigan over blouse and pleated mini skirt accentuating curvy figure", "ko": "프레피 블레이저 & 플리츠 스커트", "type": "캠퍼스룩"}
        ],
        "combat_actions": {
            "prep": "standing composed and majestic amidst city ruins, slowly lifting right hand and forming a finger-gun pointing forward, hypnotic circular target eyes glowing",
            "strike": "whispering 'Bang' as an invisible devastating kinetic shockwave craters the concrete ground and shatters the air with sheer atmospheric distortion",
            "climax": "radiating an overwhelming commanding aura, invisible crushing gravity flattening the battlefield, her dark coat billowing dramatically behind her",
            "finish": "calmly smoothing down her tie and crisp white shirt, gazing forward with an unflinching enigmatic dominant smile"
        }
    },
    "power": {
        "archetype": "power",
        "name_ko": "체인소 맨 파워 (Power from Chainsaw Man)",
        "official_tag": (
            "Power from Chainsaw Man, official MAPPA anime character design, Blood Fiend, "
            "exact 100% identical face likeness of Power from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Power's iconic flowing strawberry blonde long hair with soft bangs, adorned with two distinct prominent crimson red devil horns atop her head, exact official anime hair look", "ko": "파워 공식 딸기 블론드 롱헤어 & 붉은 악마 뿔"},
            {"en": "Power's signature pale reddish-pink flowing long hair with straight bangs, featuring two iconic bright red horns protruding from head, official MAPPA design", "ko": "파워 연분홍/스트로베리 핑크 롱헤어 & 붉은 뿔"},
            {"en": "Power's radiant golden-peach wavy long hair parted casually, featuring two signature crimson red devil horns", "ko": "파워 피치 블론드 루즈 웨이브 & 붉은 뿔"}
        ],
        "face_eyes": (
            "Power's authentic striking yellow-orange anime eyes with distinct sharp red cross-pattern (+) pupils, "
            "bold playful confident smirk, visible sharp cute vampire fangs/canines, stunning gorgeous face with wild energetic charm"
        ),
        "vibe": "wild energetic devil beauty, playful rebellious attitude, irresistible chaotic fiend charm",
        "outfits": [
            {"en": "wearing Power's iconic Public Safety devil hunter look: oversized white collared dress shirt loosely unbuttoned revealing deep cleavage, with a crooked blue necktie and blue jacket, accentuating surprisingly voluptuous large bust and athletic hourglass curves", "ko": "파워 시그니처 루즈핏 언버튼 셔츠 & 블루 타이 (글래머 핏)", "type": "원작시그니처"},
            {"en": "wearing a tight cropped athletic tank top revealing deep cleavage and toned abs, paired with retro dolphin running shorts accentuating thick curvy hips", "ko": "크롭 탱크탑 & 와일드 돌핀팬츠 (글래머러스)", "type": "돌핀팬츠"},
            {"en": "wearing a trendy casual cropped zip-up hoodie over a form-fitting sports bra and high-waisted sweatpants hugging hourglass curves", "ko": "크롭 집업 후드 & 슬림 조거팬츠", "type": "츄리닝"},
            {"en": "wearing a vibrant athletic two-piece bikini swimsuit accentuating extraordinarily voluptuous bust, deep cleavage, and curvy hourglass figure with red horns", "ko": "스포티 투피스 글래머 비키니 수영복 & 붉은 뿔", "type": "수영복"},
            {"en": "wearing a white tennis skirt with a form-fitting polo crop top accentuating very large bust and narrow waist", "ko": "테니스 스커트 & 슬림 폴로탑 (글래머핏)", "type": "테니스룩"},
            {"en": "wearing tight high-waisted denim shorts and a tight ribbed cropped tee hugging voluptuous bust and hourglass waist", "ko": "데님 숏팬츠 & 타이트 립 크롭티", "type": "스트릿캐주얼"}
        ],
        "combat_actions": {
            "prep": "laughing maniacally with sharp red fangs showing, raising both hands as crimson blood coalesces into a gargantuan jagged war hammer",
            "strike": "leaping aggressively into the air and slamming down the massive crimson blood hammer with catastrophic impact, rock debris and red shockwaves erupting",
            "climax": "unleashing a wild hurricane of summoned floating blood spears launching at sonic speed, crimson energy streaks tearing through the battlefield",
            "finish": "resting the blood weapon nonchalantly over her shoulder, sticking her tongue out playfully with blood on her cheek in wild chaotic triumph"
        }
    }
}


def generate_random_character_profile() -> dict:
    """
    곡 생성 시마다 호출되어 체인소 맨의 레제, 마키마, 파워 중 하나를 무작위로 선택하고,
    해당 캐릭터의 공식 원작 설정(얼굴 100% 일치 + 극상 글래머러스 바디라인)을 생성합니다.
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
        "combat_actions": arch.get("combat_actions", {}),
        "korean_summary": korean_summary
    }


def build_character_prompt(profile: dict = None) -> str:
    """
    체인소 맨의 레제, 마키마, 파워 캐릭터 원형의 100% 싱크로율 얼굴 및
    극상 글래머러스(Ultra-Voluptuous Hourglass) 비주얼 프롬프트를 조립합니다.
    - MAPPA 공식 체인소 맨 작화 스타일 및 얼굴 싱크로율 100% 명시
    - 대단히 풍만한 가슴, 깊은 클리비지, 잘록한 개미허리, 볼륨감 넘치는 골반 라인
    - 20대 초반 성인 여성 (early twenties, 21-23 years old)
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
        f"flawlessly identical official anime face likeness and expressions, "
        f"{face_eyes}, "
        f"{hair_en}, "
        f"{vibe}, "
        f"extraordinarily voluptuous and ultra-glamorous hourglass figure, very large heavy bust, deep alluring cleavage, "
        f"tiny snatched slender waist, wide voluptuous curvy feminine hips, mature bombshell body proportions, "
        f"{outfit_en} hugging breathtakingly curvy body silhouette, "
        f"clean 2D cel shading, crisp dynamic anime linework, authentic MAPPA anime studio quality, "
        f"not a child, not underage, not a little girl, no loli, not childish, not middle-aged, not an older woman, not matronly"
    )
