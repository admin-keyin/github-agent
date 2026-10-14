"""
Inkey Studio - Dynamic Character Profile Generator
매 곡마다 머리색, 헤어스타일, 의상(수영복, 교복, 원피스, 돌핀팬츠, 츄리닝 등)을
무작위로 다양하게 조합하여 곡마다 고유하고 매력적인 2D 미소녀 캐릭터 비주얼을 제공합니다.
한 곡 내에서는 선택된 프로필이 모든 씬에 일관되게 유지됩니다.
"""

import random

# 다채로운 헤어 컬러 및 스타일 리스트
HAIR_STYLES = [
    {"en": "silky long silver-lavender hair with cute ribbons", "ko": "은발/라벤더빛 긴 생머리 & 리본"},
    {"en": "silky pastel pink twin tails hair with adorable bows", "ko": "파스텔 핑크 트윈테일 & 리본"},
    {"en": "long flowing raven black hair with soft hime cut", "ko": "윤기 나는 흑발 히메컷 롱헤어"},
    {"en": "silky platinum blonde ponytail hair with delicate side bangs", "ko": "플래티넘 금발 하이 포니테일"},
    {"en": "vibrant cyan blue bob hair with cute hairpins", "ko": "청량한 시안 블루 단발 보브컷"},
    {"en": "soft chestnut brown wavy long hair with charming bangs", "ko": "내추럴 밤색 웨이브 롱헤어"},
    {"en": "pastel mint green hair tied in an adorable side ponytail", "ko": "민트그린 사이드 포니테일"},
    {"en": "gorgeous crimson wine-red layered long hair", "ko": "와인레드 레이어드 롱헤어"},
    {"en": "radiant sun-kissed golden honey hair with loose braids", "ko": "골든 허니 블론드 루즈 브레이드"},
    {"en": "soft lilac purple long wavy hair with charming bangs", "ko": "라일락 퍼플 웨이브 롱헤어"},
    {"en": "snow-white short bob hair with cute frilled headband", "ko": "순백색 단발 & 프릴 헤어밴드"},
    {"en": "warm peach-coral wavy hair with charming hair clips", "ko": "피치 코랄 웨이브 헤어"},
    {"en": "rich chocolate brown twin tails tied with satin ribbons", "ko": "초콜릿 브라운 트윈테일"},
    {"en": "ash grey long hair with soft purple highlights", "ko": "애쉬 그레이 & 연보라 투톤 롱헤어"}
]

# 다채로운 의상 스타일 리스트 (수영복, 교복, 원피스, 돌핀팬츠, 츄리닝, 메이드 등)
OUTFIT_STYLES = [
    # 1. 수영복 (Swimsuit)
    {"en": "wearing an alluring cute bikini swimsuit accentuating voluptuous curves and cleavage", "ko": "귀엽고 섹시한 비키니 수영복", "type": "수영복"},
    {"en": "wearing a stylish form-fitting one-piece monokini swimsuit revealing attractive hourglass silhouette", "ko": "슬림핏 모노키니 수영복", "type": "수영복"},
    {"en": "wearing a cute pastel ruffled bikini with translucent beach pareo skirt hugging glamorous curves", "ko": "파스텔 프릴 비키니 & 시스루 파레오", "type": "수영복"},
    {"en": "wearing a sporty two-piece athletic bikini accentuating toned waist and bust", "ko": "스포티 투피스 비키니", "type": "수영복"},

    # 2. 교복 (School Uniform)
    {"en": "wearing a cute sexy Japanese sailor school uniform with a short pleated skirt and fitted blouse accentuating curves", "ko": "세라복 교복 & 플리츠 스커트", "type": "교복"},
    {"en": "wearing a stylish high-school blazer uniform with a fitted cardigan and mini pleated skirt", "ko": "블레이저 교복 & 니트 가디건", "type": "교복"},
    {"en": "wearing a charming summer school uniform with a short-sleeved fitted shirt, ribbon tie, and plaid mini skirt", "ko": "하복 셔츠 리본 & 체크 미니스커트", "type": "교복"},

    # 3. 원피스 (One-Piece Dress)
    {"en": "wearing a charming form-fitting white summer sundress with sweetheart neckline fluttering in the breeze", "ko": "화이트 썸머 원피스", "type": "원피스"},
    {"en": "wearing an elegant sexy off-shoulder knit one-piece dress hugging glamorous hourglass curves", "ko": "오프숄더 슬림 니트 원피스", "type": "원피스"},
    {"en": "wearing a lovely floral pastel mini dress with delicate lace straps accentuating attractive figure", "ko": "플로럴 파스텔 미니 원피스", "type": "원피스"},
    {"en": "wearing a sophisticated bodycon cocktail dress with a graceful side slit highlighting curvy silhouette", "ko": "슬릿 바디콘 원피스", "type": "원피스"},

    # 4. 돌핀팬츠 (Dolphin Shorts)
    {"en": "wearing cute retro dolphin shorts with white trim and a tight cropped tank top revealing midriff and glamorous curves", "ko": "돌핀팬츠 & 크롭 탱크탑", "type": "돌핀팬츠"},
    {"en": "wearing sexy athletic dolphin running shorts with a form-fitting sporty crop top accentuating waist and bust", "ko": "스포티 돌핀팬츠 & 타이트 크롭탑", "type": "돌핀팬츠"},
    {"en": "wearing vibrant pastel dolphin shorts with a tied-up casual tee accentuating hourglass silhouette", "ko": "파스텔 돌핀팬츠 & 묶음 크롭 티셔츠", "type": "돌핀팬츠"},

    # 5. 츄리닝 / 스포티 (Tracksuit & Athleisure)
    {"en": "wearing a trendy stylish sporty tracksuit with an unzipped fitted track jacket over a sports bra accentuating cleavage", "ko": "집업 츄리닝 & 스포츠 브라탑", "type": "츄리닝"},
    {"en": "wearing a cute cozy oversized hoodie slipping off one shoulder paired with tight athletic sweatpants hugging curvy hips", "ko": "오프숄더 루즈핏 후드티 & 슬림 스웨트팬츠", "type": "츄리닝"},
    {"en": "wearing an alluring sporty tracksuit set with a cropped zip-up hoodie and high-waisted joggers accentuating hourglass waist", "ko": "크롭 트레이닝 집업 & 조거팬츠", "type": "츄리닝"},

    # 6. 기타 매력적인 스타일 (Maid, Bunny, Tennis, Casual)
    {"en": "wearing a stylish form-fitting cute maid corset dress with alluring bust cutout accentuating cleavage", "ko": "오픈 버스트 메이드 드레스", "type": "메이드복"},
    {"en": "wearing a cute tennis skirt with a fitted polo crop top accentuating youthful charming figure", "ko": "테니스 스커트 & 슬림 폴로탑", "type": "테니스룩"},
    {"en": "wearing an alluring cute bunny girl costume with bowtie and playful ears accentuating curvaceous figure", "ko": "바니걸 의상", "type": "바니걸"},
    {"en": "wearing cozy oversized knit sweater dress exposing delicate shoulders and collarbone", "ko": "오프숄더 오버핏 니트 스웨터 드레스", "type": "니트웨어"},
    {"en": "wearing stylish form-fitting high-waisted denim shorts and a tight ribbed cropped t-shirt", "ko": "하이웨이스트 데님 숏팬츠 & 립 크롭티", "type": "스트릿캐주얼"}
]


def generate_random_character_profile() -> dict:
    """
    곡 생성 시마다 호출되어 새로운 헤어스타일과 의상을 무작위로 추첨합니다.
    추첨된 프로필은 해당 곡의 모든 씬 프롬프트에 고정되어 사용됩니다.
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
    """
    if not profile:
        profile = generate_random_character_profile()

    hair_en = profile.get("hair_en", "silky long silver-lavender hair with cute ribbons")
    outfit_en = profile.get("outfit_en", "wearing a stylish form-fitting cute maid corset dress with alluring bust cutout accentuating cleavage")

    return (
        f"gorgeous cute and sexy moe anime girl protagonist, adorable pretty face, "
        f"large expressive luminous anime eyes with delicate eyelashes, charming captivating gaze, "
        f"{hair_en}, charming sweet smile, "
        f"extremely glamorous hourglass figure, voluptuous curves, "
        f"{outfit_en} and attractive body silhouette"
    )
