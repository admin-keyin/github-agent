"""
Inkey Studio - Contemporary Japanese Anime Heroine Profile Generator
최신 일본 극장판 및 TV 애니메이션(MAPPA, CloverWorks, Kyoto Animation, Ufotable)의
세련되고 감각적인 비주얼을 기반으로 한 다채로운 히로인 아키타입을 생성합니다.

- 체인소 맨 (Chainsaw Man): 레제(Reze), 마키마(Makima), 파워(Power)
- 스파이 패밀리 (Spy x Family): 요르(Yor) 스타일 우아한 흑발 뷰티
- 바이올렛 에버가든 (Violet Evergarden): 고품격 금발 & 사파이어 눈동자의 감성 뮤즈
- 장송의 프리렌 (Frieren): 신비로운 은백발 트윈테일 판타지 메이지
- 최애의 아이 (Oshi no Ko): 별빛 눈동자와 화려한 팝 아이돌 디바
- 봇치 더 록 (Bocchi the Rock): 몽환적인 감성 인디 밴드 락커
- 사이버펑크 엣지러너 (Cyberpunk): 네온 파스텔 헤어의 미래형 넷러너

옛날 만화(80~90년대 복고풍 셀화, 왕눈이 순정만화)나 한국 웹툰풍을 배제하고,
최신 일본 애니메이션 특유의 섬세한 얼굴 비율, 날렵한 턱선, 영롱한 눈동자 반사광,
그리고 매력적인 20대 초반 성인 여성의 글래머러스 바디라인을 완벽히 구현합니다.
"""

import random

HEROINE_ARCHETYPES = {
    "reze": {
        "archetype": "reze",
        "name_ko": "체인소 맨 레제 (Reze)",
        "official_tag": (
            "Reze from Chainsaw Man, official MAPPA modern anime character design, "
            "exact 100% identical face likeness of Reze from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Reze's iconic dark violet-purple short bob hair with loose parted bangs and wisps at nape, modern Japanese anime styling", "ko": "레제 공식 흑자색/다크 바이올렛 보브 단발"},
            {"en": "Reze's signature deep lavender sleek chin-length bob hair perfectly framing pretty face, MAPPA anime movie quality", "ko": "레제 딥 라벤더 슬릭 보브 단발"},
            {"en": "Reze's dark purple layered natural wavy short bob hair with soft bangs, authentic anime design", "ko": "레제 다크 퍼플 내추럴 레이어드 보브"}
        ],
        "face_eyes": (
            "refined modern Japanese anime facial features, slender delicate jawline, alluring sophisticated emerald-green anime eyes with delicate subtle eyeliner, "
            "soft natural pink blush on cheeks, seductive playful yet bittersweet smile, modern anime chic charm, iconic slender black choker necklace tightly worn around delicate throat"
        ),
        "vibe": "charismatic seductive femme fatale, playful youthfulness and deep emotional wistfulness, dangerous yet captivating bomb girl allure",
        "outfits": [
            {"en": "wearing Reze's iconic tight white sleeveless collared blouse with a slim black necktie hugging very large voluptuous bust with deep cleavage, tucked into dark shorts with suspenders, tiny waist and curvy hips", "ko": "레제 시그니처 민소매 셔츠 & 슬림 블랙 넥타이 (극상 글래머핏)", "type": "원작시그니처"},
            {"en": "wearing a tight white cropped tank top revealing deep cleavage and toned midriff, paired with black shorts and signature black choker necklace, accentuating ultra-voluptuous curves", "ko": "타이트 크롭 탱크탑 & 숏팬츠 & 블랙 초커", "type": "돌핀팬츠"},
            {"en": "wearing an alluring backless black summer sundress with deep sweetheart neckline clinging to extremely voluptuous hourglass curves and large bust", "ko": "백리스 블랙 썸머 선드레스 (글래머 바디콘)", "type": "원피스"},
            {"en": "wearing a revealing sophisticated dark bikini swimsuit accentuating massive voluptuous bust, deep cleavage, and curvy hourglass hips with black choker", "ko": "매혹적인 다크 비키니 수영복 & 초커 (글래머러스)", "type": "수영복"},
            {"en": "wearing a cozy off-shoulder knit sweater dress slipping off shoulder revealing deep cleavage, black choker, and voluptuous silhouette", "ko": "오프숄더 글래머 니트 스웨터 드레스", "type": "니트웨어"},
            {"en": "wearing a stylish unzipped sporty tracksuit jacket over a form-fitting sports bra accentuating cleavage and high-waisted tight joggers", "ko": "집업 트레이닝 셋업 & 스포츠 브라탑", "type": "츄리닝"}
        ]
    },
    "makima": {
        "archetype": "makima",
        "name_ko": "체인소 맨 마키마 (Makima)",
        "official_tag": (
            "Makima from Chainsaw Man, official MAPPA modern anime character design, Public Safety Special Division leader, "
            "exact 100% identical face likeness of Makima from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Makima's iconic soft reddish-pink light auburn hair styled in an elegant loose single long braid resting over shoulder, framing side bangs, modern Japanese anime aesthetic", "ko": "마키마 공식 연한 적갈색/코랄핑크 땋은 롱헤어"},
            {"en": "Makima's gorgeous coral-wine red silky hair falling in an elegant long graceful single braid, MAPPA movie quality", "ko": "마키마 와인코랄 우아한 롱 브레이드"},
            {"en": "Makima's signature radiant light red-orange hair tied into a low sophisticated side braid with soft bangs", "ko": "마키마 시그니처 사이드 땋은머리"}
        ],
        "face_eyes": (
            "refined modern Japanese anime face, sharp sleek jawline, iconic hypnotic yellow-amber ring eyes with distinct concentric circular target pupils, "
            "calm sophisticated penetrating gaze, subtle enigmatic Mona Lisa smile, elegant modern anime facial aesthetics, dignified dominant feminine aura"
        ),
        "vibe": "supreme dominant elegance, enigmatic intellectual allure, calm sophisticated charisma, Public Safety leader presence",
        "outfits": [
            {"en": "wearing Makima's iconic Public Safety uniform: tight crisp white dress shirt with black necktie hugging exceptionally large voluptuous bust with button-straining cleavage, tucked into tailored high-waisted black trousers accentuating hourglass waist and wide curvy hips", "ko": "마키마 시그니처 타이트 화이트 셔츠 & 블랙 타이 & 슬랙스 (극상 글래머핏)", "type": "원작시그니처"},
            {"en": "wearing a sleek tailored dark suit blazer unbuttoned over a form-fitting white shirt and black necktie with a tight tailored pencil mini skirt hugging thick curvy hips", "ko": "테일러드 수트 블레이저 & 슬림 펜슬 미니스커트", "type": "오피스수트"},
            {"en": "wearing an elegant off-shoulder bodycon cocktail dress with deep sweetheart neckline and high leg slit clinging to ultra-voluptuous curves and prominent bust", "ko": "하이 슬릿 오프숄더 글래머 바디콘 드레스", "type": "원피스"},
            {"en": "wearing an alluring elegant black one-piece monokini swimsuit with plunging neckline revealing massive voluptuous bust and attractive hourglass silhouette", "ko": "엘레강스 블랙 플런징 모노키니 수영복", "type": "수영복"},
            {"en": "wearing a sophisticated tight knit dress with deep neckline hugging extraordinarily voluptuous bust and hourglass curves", "ko": "타이트 니트 글래머 바디콘 드레스", "type": "니트웨어"},
            {"en": "wearing a chic college preppy blazer uniform with a fitted knit cardigan over blouse and pleated mini skirt accentuating curvy figure", "ko": "프레피 블레이저 & 플리츠 스커트", "type": "캠퍼스룩"}
        ]
    },
    "power": {
        "archetype": "power",
        "name_ko": "체인소 맨 파워 (Power)",
        "official_tag": (
            "Power from Chainsaw Man, official MAPPA modern anime character design, Blood Fiend, "
            "exact 100% identical face likeness of Power from Chainsaw Man anime by MAPPA, "
            "flawlessly accurate official anime facial features"
        ),
        "hair_list": [
            {"en": "Power's iconic flowing strawberry blonde long hair with soft bangs, adorned with two distinct prominent crimson red devil horns atop her head, modern anime styling", "ko": "파워 공식 딸기 블론드 롱헤어 & 붉은 악마 뿔"},
            {"en": "Power's signature pale reddish-pink flowing long hair with straight bangs, featuring two iconic bright red horns protruding from head, MAPPA quality", "ko": "파워 연분홍/스트로베리 핑크 롱헤어 & 붉은 뿔"},
            {"en": "Power's radiant golden-peach wavy long hair parted casually, featuring two signature crimson red devil horns", "ko": "파워 피치 블론드 루즈 웨이브 & 붉은 뿔"}
        ],
        "face_eyes": (
            "refined modern Japanese anime facial features, sharp sleek jawline, striking yellow-orange anime eyes with distinct sharp red cross-pattern (+) pupils, "
            "bold playful confident smirk, visible cute sharp vampire fangs, gorgeous modern anime aesthetic face with wild energetic charm"
        ),
        "vibe": "wild energetic devil beauty, playful rebellious attitude, irresistible chaotic fiend charm",
        "outfits": [
            {"en": "wearing Power's iconic Public Safety devil hunter look: oversized white collared dress shirt loosely unbuttoned revealing deep cleavage, with a crooked blue necktie and blue jacket, accentuating surprisingly voluptuous large bust and athletic hourglass curves", "ko": "파워 시그니처 루즈핏 언버튼 셔츠 & 블루 타이 (글래머 핏)", "type": "원작시그니처"},
            {"en": "wearing a tight cropped athletic tank top revealing deep cleavage and toned abs, paired with retro dolphin running shorts accentuating thick curvy hips", "ko": "크롭 탱크탑 & 와일드 돌핀팬츠 (글래머러스)", "type": "돌핀팬츠"},
            {"en": "wearing a trendy casual cropped zip-up hoodie over a form-fitting sports bra and high-waisted sweatpants hugging hourglass curves", "ko": "크롭 집업 후드 & 슬림 조거팬츠", "type": "츄리닝"},
            {"en": "wearing a vibrant athletic two-piece bikini swimsuit accentuating extraordinarily voluptuous bust, deep cleavage, and curvy hourglass figure with red horns", "ko": "스포티 투피스 글래머 비키니 수영복 & 붉은 뿔", "type": "수영복"},
            {"en": "wearing a white tennis skirt with a form-fitting polo crop top accentuating very large bust and narrow waist", "ko": "테니스 스커트 & 슬림 폴로탑 (글래머핏)", "type": "테니스룩"},
            {"en": "wearing tight high-waisted denim shorts and a tight ribbed cropped tee hugging voluptuous bust and hourglass waist", "ko": "데님 숏팬츠 & 타이트 립 크롭티", "type": "스트릿캐주얼"}
        ]
    },
    "violet": {
        "archetype": "violet",
        "name_ko": "바이올렛 에버가든풍 감성 뮤즈 (Violet Muse)",
        "official_tag": (
            "masterpiece Japanese anime heroine character design in Kyoto Animation style, "
            "exquisite modern anime visual aesthetics, breathtaking theatrical movie quality"
        ),
        "hair_list": [
            {"en": "gorgeous silky golden blonde hair elegantly styled into intricate low looped braids tied with deep emerald green ribbons and soft face-framing bangs, Kyoto Animation quality", "ko": "실키 골든 블론드 에메랄드 리본 땋은머리"},
            {"en": "flowing radiant honey-blonde silky long wavy hair cascading over shoulders with delicate bangs, Kyoto Animation aesthetic", "ko": "허니 블론드 루즈 웨이브 롱헤어"},
            {"en": "graceful platinum blonde hair braided neatly into an antique romantic chignon with flowing side locks", "ko": "플래티넘 블론드 앤티크 올림머리"}
        ],
        "face_eyes": (
            "exquisite delicate modern Japanese anime face, slender graceful chin, crystal clear sapphire blue anime eyes with mesmerizing luminous reflections, "
            "gentle poignant expression, faint porcelain blush, ethereal emotional beauty and pure cinematic elegance"
        ),
        "vibe": "ethereal poetic elegance, deeply emotional and gentle soul, aristocratic poise, breathtaking romantic anime heroine",
        "outfits": [
            {"en": "wearing a tailored Victorian Prussian blue silk jacket over an elegant ivory ruffled blouse and white pleated skirt accentuating hourglass curves and prominent bust", "ko": "프러시안 블루 자켓 & 아이보리 프릴 블라우스", "type": "클래식드레스"},
            {"en": "wearing an off-shoulder midnight blue velvet evening gown with deep sweetheart neckline accentuating ultra-voluptuous curves and large bust", "ko": "미드나잇 블루 벨벳 오프숄더 드레스", "type": "원피스"},
            {"en": "wearing a soft cream knitted turtleneck sweater hugging extremely voluptuous bust and slim waist, with a long wool skirt", "ko": "크림 니트 터틀넥 & 롱 플리츠 스커트", "type": "니트웨어"},
            {"en": "wearing an elegant white linen summer sundress with thin straps fluttering in the breeze, accentuating shapely curves and cleavage", "ko": "화이트 린넨 썸머 선드레스", "type": "선드레스"}
        ]
    },
    "yor": {
        "archetype": "yor",
        "name_ko": "요르 포저풍 우아한 암살자 (Yor Style)",
        "official_tag": (
            "masterpiece modern Japanese anime heroine, CloverWorks and Wit Studio anime character design, "
            "striking elegant anime beauty"
        ),
        "hair_list": [
            {"en": "glossy raven-black long hair parted neatly with two face-framing locks and a low tied bun adorned with golden rose accessories, modern anime style", "ko": "윤기 나는 흑발 로즈 번 & 사이드 뱅"},
            {"en": "sleek jet-black straight hair falling gracefully to waist with neat natural bangs, high-end Japanese anime aesthetic", "ko": "칠흑색 생머리 슬릭 롱헤어"},
            {"en": "soft wavy black hair tied casually in a half-up ponytail with crimson hair ribbon", "ko": "웨이비 흑발 하프업 포니테일"}
        ],
        "face_eyes": (
            "strikingly gorgeous modern Japanese anime face, refined slender jawline, captivating sharp ruby-red anime cat eyes with intricate highlights, "
            "charming shy blush, seductive innocent smile, gold dangle earrings hanging from delicate earlobes"
        ),
        "vibe": "deadly lethal assassin grace combined with gentle sweet innocence, dignified mature beauty and alluring feminine charm",
        "outfits": [
            {"en": "wearing an iconic backless black haltered cocktail dress with deep sweetheart neckline and red rose lining, clinging to extraordinarily voluptuous hourglass curves and large bust, thigh-high leather boots", "ko": "백리스 블랙 칵테일 드레스 & 싸이하이 부츠 (글래머핏)", "type": "원작시그니처"},
            {"en": "wearing a cozy off-the-shoulder red knit sweater dress revealing deep cleavage and clavicles, paired with black tights hugging curvy hips", "ko": "오프숄더 레드 니트 드레스 & 블랙 타이즈", "type": "니트웨어"},
            {"en": "wearing a sleek tailored dark crimson blazer over a tight black lace top and pencil mini skirt hugging voluptuous curves", "ko": "크림슨 블레이저 & 블랙 레이스 미니스커트", "type": "오피스수트"},
            {"en": "wearing a stylish black bikini swimsuit with criss-cross wrap straps accentuating massive voluptuous bust and hourglass hips", "ko": "블랙 크리스크로스 글래머 비키니", "type": "수영복"}
        ]
    },
    "frieren_mage": {
        "archetype": "frieren_mage",
        "name_ko": "프리렌풍 신비로운 판타지 메이지 (Mage Frieren Style)",
        "official_tag": (
            "masterpiece Japanese anime character design in Madhouse style, "
            "contemporary high-end Japanese TV anime visual aesthetic"
        ),
        "hair_list": [
            {"en": "flowing pure silver-white long twin-tails tied loosely with dark hair ribbons, soft parted bangs framing face, modern anime movie quality", "ko": "퓨어 실버 화이트 트윈테일 롱헤어"},
            {"en": "luminous moonlight silver layered wavy hair cascading down back with delicate elven ear-framing locks", "ko": "달빛 실버 레이어드 루즈 웨이브"},
            {"en": "silky ash-white high side ponytail fluttering in magical breeze with soft bangs", "ko": "애쉬 화이트 사이드 포니테일"}
        ],
        "face_eyes": (
            "delicate exquisite modern Japanese anime face, slender graceful jawline, enchanting deep turquoise-emerald anime eyes with brilliant magical reflections, "
            "serene tranquil smile, faint blush, slightly pointed cute elven ears adorned with red gemstone pendant earrings"
        ),
        "vibe": "timeless mystical mage, calm serene wisdom, ethereal magical elegance, celestial fairy-tale beauty",
        "outfits": [
            {"en": "wearing a white and gold-trimmed fantasy traveler capelet over a form-fitting black sleeveless top accentuating very large voluptuous bust with deep cleavage, paired with a white high-waisted pleated skirt", "ko": "화이트 & 골드 판타지 케이프 & 슬리브리스 탑", "type": "판타지로브"},
            {"en": "wearing an alluring celestial night-blue fantasy dress with silver rune embroideries clinging to ultra-voluptuous hourglass silhouette and large bust", "ko": "나이트 블루 룬 마법사 드레스", "type": "원피스"},
            {"en": "wearing a cozy oversized pastel knit cardigan over a snug camisole and mini shorts, accentuating hourglass waist and curvy figure", "ko": "파스텔 루즈핏 가디건 & 슬립 캐미솔", "type": "캐주얼"}
        ]
    },
    "hoshino": {
        "archetype": "hoshino",
        "name_ko": "최애의 아이풍 아이돌 디바 (Idol Diva Style)",
        "official_tag": (
            "masterpiece modern Japanese anime heroine, Doga Kobo and CloverWorks anime character design, "
            "brilliant contemporary Japanese anime idol visual"
        ),
        "hair_list": [
            {"en": "vibrant magenta-purple gradient long hair styled in a sweeping side ponytail with playful hairpins, modern Japanese anime idol aesthetic", "ko": "마젠타 퍼플 그라데이션 사이드 포니테일"},
            {"en": "dazzling violet and pink two-tone wavy long hair cascading down shoulders with cute parted bangs", "ko": "바이올렛 & 핑크 투톤 루즈 웨이브"},
            {"en": "luminous dark ruby-pink twin-tails fluttering with sparkling stage lighting", "ko": "루비 핑크 트윈테일"}
        ],
        "face_eyes": (
            "radiantly stunning modern Japanese anime face, sharp cute chin, iconic dazzling six-pointed star reflections glowing inside deep violet anime eyes, "
            "irresistible radiant wink and charming smile, sweet idol blush, charismatic anime pop star aura"
        ),
        "vibe": "ultimate charismatic idol, captivating star power, blindingly bright stage presence, irresistible magnetic charm",
        "outfits": [
            {"en": "wearing a dazzling layered idol stage costume: frilly magenta corset top hugging very large voluptuous bust with deep sweetheart neckline, glittery tiered ruffle mini skirt, and matching ribbon chokers", "ko": "글리터 아이돌 스테이지 코르셋 드레스", "type": "무대의상"},
            {"en": "wearing a stylish trendy oversized graphic bomber jacket over a tight white crop top accentuating cleavage and high-waisted pleated skirt", "ko": "오버핏 그래픽 봄버자켓 & 테니스 스커트", "type": "스트릿캐주얼"},
            {"en": "wearing a glamorous off-shoulder party dress with sparkling sequins accentuating ultra-voluptuous curves and hourglass figure", "ko": "글래머 시퀸 오프숄더 미니드레스", "type": "원피스"}
        ]
    },
    "bocchi_rock": {
        "archetype": "bocchi_rock",
        "name_ko": "인디 밴드 기타리스트 (Indie Band Rocker)",
        "official_tag": (
            "masterpiece modern Japanese anime heroine, CloverWorks anime character design, "
            "authentic contemporary Japanese youth band anime visual"
        ),
        "hair_list": [
            {"en": "soft pastel-pink slightly messy natural long hair with cute cube hair ornaments and eye-framing bangs, CloverWorks modern anime look", "ko": "파스텔 핑크 큐브 헤어핀 루즈 롱헤어"},
            {"en": "stylish ash-blonde layered medium wolf cut with wispy bangs, chic Japanese indie band aesthetic", "ko": "애쉬 블론드 레이어드 울프컷"},
            {"en": "dark navy-black natural wavy long hair with blue inner-color highlights and effortless texture", "ko": "네이비 블랙 & 블루 이너컬러 웨이브"}
        ],
        "face_eyes": (
            "delicate expressive modern Japanese anime face, cute slender jawline, deep seafoam-green or bright cyan anime eyes with shimmering reflections, "
            "adorable bashful blush on cheeks, heartfelt earnest expression, youthful rock musician passion"
        ),
        "vibe": "melancholic youthful guitar prodigy, passionate introverted indie rocker, genuine raw emotional appeal",
        "outfits": [
            {"en": "wearing an oversized knitted zip-up jersey cardigan loosely sliding off one shoulder over a snug fitted black camisole accentuating very large voluptuous bust and cleavage, long pleated skirt, carrying an electric guitar gig bag", "ko": "오버핏 집업 가디건 & 블랙 캐미솔 & 기타 케이스", "type": "밴드룩"},
            {"en": "wearing a cool vintage leather biker jacket over a form-fitting band t-shirt hugging large bust and high-waisted skinny jeans with electric guitar", "ko": "빈티지 라이더 레더자켓 & 스키니진", "type": "락시크"},
            {"en": "wearing a stylish street punk outfit: cropped ripped hoodie revealing toned waist, form-fitting sports top accentuating cleavage, and plaid pleated skirt", "ko": "크롭 후디 & 플래드 미니스커트", "type": "스트릿캐주얼"}
        ]
    },
    "cyber_lucy": {
        "archetype": "cyber_lucy",
        "name_ko": "사이버펑크 네온 넷러너 (Cyberpunk Netrunner)",
        "official_tag": (
            "masterpiece Japanese anime character design in Studio Trigger style, "
            "vibrant cutting-edge modern cyberpunk anime visual aesthetic"
        ),
        "hair_list": [
            {"en": "pastel multi-tone rainbow gradient angled short bob hair, icy white fading into pink and cyan tips, sharp modern anime silhouette", "ko": "파스텔 레인보우 그라데이션 앵글드 보브"},
            {"en": "sleek neon-cyan asymmetrical bob hair with razor-sharp ends, futuristic Japanese anime look", "ko": "네온 시안 비대칭 보브"},
            {"en": "pale lilac-violet sleek high ponytail with illuminated optic hair ties", "ko": "라일락 바이올렛 옵틱 포니테일"}
        ],
        "face_eyes": (
            "sharp striking modern Japanese anime face, sleek angular jawline, captivating cat-like dual-tone magenta and cyan glowing anime eyes, "
            "cool confident smirk, delicate cyberware tech marks on temple, magnetic futuristic femme fatale allure"
        ),
        "vibe": "cynical cool hacker, dangerous high-speed adrenaline, rebellious free spirit, breathtaking cyberpunk elegance",
        "outfits": [
            {"en": "wearing an iconic futuristic high-collar cropped leather jacket over a form-fitting high-cut monokini bodysuit hugging extraordinarily voluptuous bust with deep cleavage, sheer cybernetic leggings, and utility harness", "ko": "하이칼라 크롭 레더자켓 & 하이컷 모노키니 바디슈트", "type": "사이버슈트"},
            {"en": "wearing a tight cropped neon techwear tank top revealing deep cleavage and toned abs, paired with low-rise cargo joggers accentuating hourglass hips", "ko": "테크웨어 크롭탑 & 카고 조거팬츠", "type": "테크웨어"},
            {"en": "wearing a sleek glowing holographic bodysuit adhering tightly to ultra-voluptuous curves and prominent bust silhouette", "ko": "홀로그래픽 바디콘 사이버 드레스", "type": "원피스"}
        ]
    }
}


def generate_random_character_profile(genre_category: str = "") -> dict:
    """
    곡 장르와 어울리는 다양한 현대 일본 애니메이션 히로인 아키타입을 우선 매칭하거나,
    랜덤으로 다채롭게 선택합니다.
    - healing_ballad: violet, frieren_mage, reze, bocchi_rock 등 감성/신비로운 캐릭터 우선
    - changpop / battle_epic: reze, makima, power, yor, cyber_lucy 등 역동적 액션/질주 캐릭터 우선
    - indie_band: bocchi_rock, hoshino, yor, reze 등 청춘 밴드/음악/감성 캐릭터 우선
    - ghost_duet: yor, frieren_mage, reze, makima 등 신비롭고 매혹적인 캐릭터 우선
    """
    genre_archetype_mapping = {
        "healing_ballad": ["violet", "frieren_mage", "reze", "bocchi_rock", "makima"],
        "changpop": ["reze", "power", "cyber_lucy", "hoshino", "yor"],
        "indie_band": ["bocchi_rock", "hoshino", "violet", "reze", "yor"],
        "battle_epic": ["yor", "reze", "power", "makima", "cyber_lucy"],
        "ghost_duet": ["frieren_mage", "yor", "makima", "violet", "reze"]
    }

    candidates = genre_archetype_mapping.get(genre_category, list(HEROINE_ARCHETYPES.keys()))
    # 75% 확률로 장르 추천 풀에서, 25% 확률로 전체 풀에서 완전 랜덤 선택
    if random.random() < 0.75:
        archetype_key = random.choice(candidates)
    else:
        archetype_key = random.choice(list(HEROINE_ARCHETYPES.keys()))

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
    현대 최고 수준의 일본 애니메이션(MAPPA, CloverWorks, Kyoto Animation, Ufotable) 화풍을 기반으로,
    세련된 이목구비와 극상 글래머러스(Ultra-Voluptuous Hourglass) 비주얼 프롬프트를 조립합니다.
    - 정통 현대 일본 TV 애니메이션 작화 (Modern Japanese TV anime aesthetic)
    - 섬세하고 날렵한 턱선, 정교한 눈동자 반사광, 세련된 이목구비
    - 옛날 만화(80~90s, vintage retro) 및 한국 웹툰풍 철저 배제
    - 20대 초반 성인 여성 (early twenties, 21-23 years old)
    """
    if not profile or "archetype" not in profile:
        profile = generate_random_character_profile()

    official_tag = profile.get("official_tag", "masterpiece modern Japanese anime heroine")
    hair_en = profile.get("hair_en", "sleek stylish anime hair with soft natural bangs")
    face_eyes = profile.get("face_eyes", "refined modern Japanese anime facial features, sharp sleek jawline, alluring stylish anime eyes")
    outfit_en = profile.get("outfit_en", "wearing a stylish form-fitting outfit")
    vibe = profile.get("vibe", "charismatic sophisticated presence")

    return (
        f"{official_tag}, stunning gorgeous anime woman in her early twenties (around 21 years old), "
        f"masterpiece modern Japanese anime visual style, contemporary high-end Japanese TV anime aesthetic, "
        f"flawlessly refined modern anime face likeness and expressions, "
        f"{face_eyes}, "
        f"{hair_en}, "
        f"{vibe}, "
        f"extraordinarily voluptuous and ultra-glamorous hourglass figure, very large heavy bust, deep alluring cleavage, "
        f"tiny snatched slender waist, wide voluptuous curvy feminine hips, mature bombshell body proportions, "
        f"{outfit_en} hugging breathtakingly curvy body silhouette, "
        f"high-end contemporary Japanese anime illustration, sophisticated anime digital shading, beautiful Makoto Shinkai cinematic lighting, crisp modern anime linework, "
        f"Kyoto Animation, Ufotable, CloverWorks, and MAPPA contemporary anime production quality, "
        f"not a child, not underage, not a little girl, no loli, not childish, not middle-aged, not an older woman, not matronly, "
        f"not retro anime, not 90s anime, not 80s anime, not vintage anime, not old fashioned cel animation, not oversized bug eyes, not webtoon, not manhwa, not western comic"
    )
