"""
Inkey Studio - Dynamic Character Profile Generator
매 곡마다 머리색, 헤어스타일, 의상(수영복, 캠퍼스룩, 원피스, 돌핀팬츠, 츄리닝 등)을
무작위로 다양하게 조합하여 곡마다 고유하고 매력적인 2D 성인 여성(20대 초반의 성숙하면서도 싱그러운 미녀) 비주얼을 제공합니다.
너무 어린 아이(로리) 같거나 중년(아줌마) 느낌이 나지 않는, 20대 초반의 세련되고 글래머러스한 성인 여성 비주얼을 고정합니다.
한 곡 내에서는 선택된 프로필이 모든 씬에 일관되게 유지됩니다.
"""

import random

# 다채로운 헤어 컬러 및 스타일 리스트 (20대 성인 여성에게 어울리는 세련되고 매혹적인 스타일)
HAIR_STYLES = [
    {"en": "silky long silver-lavender hair flowing gracefully with delicate satin ribbon", "ko": "은발/라벤더빛 긴 생머리 & 새틴 리본"},
    {"en": "glamorous pastel pink wavy hair styled in a high ponytail with delicate framing bangs", "ko": "파스텔 핑크 웨이브 하이 포니테일"},
    {"en": "long flowing raven black hair with elegant refined hime cut", "ko": "윤기 나는 흑발 우아한 히메컷 롱헤어"},
    {"en": "silky platinum blonde swept-back high ponytail with delicate side bangs", "ko": "플래티넘 금발 하이 포니테일"},
    {"en": "chic vibrant cyan blue bob hair with sophisticated side part", "ko": "세련된 시안 블루 보브 단발"},
    {"en": "soft chestnut brown voluminous wavy long hair cascading over shoulders", "ko": "내추럴 밤색 풍성한 웨이브 롱헤어"},
    {"en": "pastel mint green hair tied in an elegant loose side ponytail", "ko": "민트그린 우아한 사이드 포니테일"},
    {"en": "gorgeous crimson wine-red layered long wavy hair", "ko": "매혹적인 와인레드 레이어드 롱 웨이브"},
    {"en": "radiant sun-kissed golden honey hair falling gracefully in loose waves", "ko": "골든 허니 블론드 루즈 웨이브"},
    {"en": "soft lilac purple long voluminous wavy hair with gentle side bangs", "ko": "라일락 퍼플 볼륨 웨이브 롱헤어"},
    {"en": "snow-white sleek bob hair with stylish delicate hair clip", "ko": "순백색 시크 단발 & 헤어핀"},
    {"en": "warm peach-coral voluminous wavy hair fluttering softly", "ko": "피치 코랄 풍성한 웨이브 헤어"},
    {"en": "rich chocolate brown half-up hair tied with a chic ribbon", "ko": "초콜릿 브라운 하프업 반묶음 헤어"},
    {"en": "ash grey long hair with subtle violet balayage highlights", "ko": "애쉬 그레이 & 연보라 발레아쥬 롱헤어"}
]

# 다채로운 의상 스타일 리스트 (20대 성숙미와 세련미를 강조하는 스타일)
OUTFIT_STYLES = [
    # 1. 수영복 (Swimsuit)
    {"en": "wearing an alluring sophisticated bikini swimsuit accentuating voluptuous curves and cleavage", "ko": "세련되고 매혹적인 비키니 수영복", "type": "수영복"},
    {"en": "wearing a stylish form-fitting one-piece monokini swimsuit revealing attractive hourglass silhouette", "ko": "슬림핏 모노키니 수영복", "type": "수영복"},
    {"en": "wearing an alluring ruffled bikini with a translucent beach pareo wrap hugging glamorous curves", "ko": "프릴 비키니 & 시스루 파레오", "type": "수영복"},
    {"en": "wearing a chic athletic two-piece swimwear accentuating toned waist and bust", "ko": "시크 스포티 투피스 비키니", "type": "수영복"},

    # 2. 캠퍼스 / 프레피룩 (College & Preppy Look - 어린 교복 탈피)
    {"en": "wearing a chic college preppy blazer look with a fitted blouse, silk tie, and stylish pleated mini skirt", "ko": "세련된 캠퍼스 블레이저 프레피룩", "type": "캠퍼스룩"},
    {"en": "wearing a sophisticated academy styling with a fitted knit cardigan over button-up shirt and mini pleated skirt", "ko": "슬림핏 가디건 & 플리츠 미니스커트", "type": "캠퍼스룩"},
    {"en": "wearing a stylish collegiate summer uniform with a form-fitting short-sleeved blouse and plaid mini skirt", "ko": "슬림 셔츠 & 체크 미니스커트", "type": "캠퍼스룩"},

    # 3. 원피스 & 드레스 (Dress)
    {"en": "wearing an elegant form-fitting white summer sundress with sweetheart neckline fluttering in the breeze", "ko": "화이트 썸머 선드레스", "type": "원피스"},
    {"en": "wearing a sophisticated sexy off-shoulder knit bodycon dress hugging glamorous hourglass curves", "ko": "오프숄더 슬림 니트 바디콘 원피스", "type": "원피스"},
    {"en": "wearing an alluring floral silk slip dress with delicate lace straps accentuating attractive figure", "ko": "플로럴 실크 슬립 원피스", "type": "원피스"},
    {"en": "wearing a sophisticated cocktail dress with a graceful high leg slit highlighting curvy silhouette", "ko": "하이 슬릿 칵테일 바디콘 드레스", "type": "원피스"},

    # 4. 돌핀팬츠 (Dolphin Shorts)
    {"en": "wearing chic retro dolphin shorts with white trim and a tight cropped tank top revealing midriff and glamorous curves", "ko": "돌핀팬츠 & 크롭 탱크탑", "type": "돌핀팬츠"},
    {"en": "wearing alluring athletic dolphin running shorts with a form-fitting sporty crop top accentuating waist and bust", "ko": "스포티 돌핀팬츠 & 타이트 크롭탑", "type": "돌핀팬츠"},
    {"en": "wearing stylish pastel dolphin shorts with a knotted casual tee accentuating hourglass silhouette", "ko": "파스텔 돌핀팬츠 & 묶음 크롭 티셔츠", "type": "돌핀팬츠"},

    # 5. 츄리닝 / 스포티 (Tracksuit & Athleisure)
    {"en": "wearing a trendy stylish sporty tracksuit with an unzipped fitted track jacket over a sports bra accentuating cleavage", "ko": "집업 츄리닝 & 스포츠 브라탑", "type": "츄리닝"},
    {"en": "wearing a cozy oversized hoodie slipping off one shoulder paired with tight athletic leggings hugging curvy hips", "ko": "오프숄더 루즈핏 후드티 & 슬림 레깅스", "type": "츄리닝"},
    {"en": "wearing an alluring sporty tracksuit set with a cropped zip-up hoodie and high-waisted joggers accentuating hourglass waist", "ko": "크롭 트레이닝 집업 & 조거팬츠", "type": "츄리닝"},

    # 6. 매력적인 성인 스타일 (Maid, Bunny, Tennis, Casual)
    {"en": "wearing a stylish form-fitting maid corset dress with alluring bust cutout accentuating cleavage", "ko": "오픈 버스트 메이드 드레스", "type": "메이드복"},
    {"en": "wearing a stylish white tennis skirt with a form-fitting polo crop top accentuating toned glamorous figure", "ko": "테니스 스커트 & 슬림 폴로탑", "type": "테니스룩"},
    {"en": "wearing an alluring chic bunny girl costume with bowtie and playful ears accentuating curvaceous figure", "ko": "바니걸 의상", "type": "바니걸"},
    {"en": "wearing an alluring oversized knit sweater dress exposing delicate shoulders and collarbone", "ko": "오프숄더 오버핏 니트 스웨터 드레스", "type": "니트웨어"},
    {"en": "wearing stylish form-fitting high-waisted denim shorts and a tight ribbed cropped t-shirt", "ko": "하이웨이스트 데님 숏팬츠 & 립 크롭티", "type": "스트릿캐주얼"}
]


def generate_random_character_profile() -> dict:
    """
    곡 생성 시마다 호출되어 새로운 헤어스타일과 의상을 무작위로 추첨합니다.
    추첨된 프로필은 해당 곡의 모든 씬 프롬프트에 고정되어 사용됩니다.
    20대 초반 성인 여성의 성숙하고 매력적인 비주얼을 제공합니다.
    """
    hair = random.choice(HAIR_STYLES)
    outfit = random.choice(OUTFIT_STYLES)

    korean_summary = f"{hair['ko']} + {outfit['ko']} ({outfit['type']})"
    return {
        "hair_en": hair["en"],
        "hair_ko": hair["ko"],
        "outfit_en": outfit["en"],
        "outfit_ko": outfit["ko"],
        "outfit_type": outfit["type"],
        "korean_summary": korean_summary
    }


def build_character_prompt(profile: dict = None) -> str:
    """
    프로필 딕셔너리를 받아 비디오 생성용 핵심 캐릭터 프롬프트 문자열을 생성합니다.
    - 20대 초반(20~23세)의 성숙하고 매혹적이면서도 싱그러운 여성미
    - 너무 어린 아이(로리/어린이)나 너무 늙은 중년(아줌마) 배제
    """
    if not profile:
        profile = generate_random_character_profile()

    hair_en = profile.get("hair_en", "silky long silver-lavender hair flowing gracefully with delicate satin ribbon")
    outfit_en = profile.get("outfit_en", "wearing a sophisticated bodycon dress highlighting curvy silhouette")

    return (
        f"stunning alluring young adult anime woman in her early twenties (around 21 years old), "
        f"mature feminine elegance yet youthful fresh beauty, "
        f"refined captivating pretty face, large expressive luminous anime eyes with delicate long eyelashes, "
        f"alluring sophisticated gaze, subtle confident charming smile, "
        f"{hair_en}, "
        f"extremely glamorous tall hourglass figure, voluptuous mature curves, graceful slender waist, "
        f"{outfit_en} and attractive feminine body silhouette, "
        f"not a child, not underage, not a little girl, no loli, not childish, not middle-aged, not an older woman, not matronly"
    )
