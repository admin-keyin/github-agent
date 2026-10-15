"""
Inkey Studio - Anime Clip Asset Library & Reusability Manager
생성된 10초 SeaDance V1 Pro 애니메이션 비디오를 고유 메타데이터(머리색, 복장, 배경, 동작) 기반 파일명으로 라이브러리에 저장하고,
향후 유사한 씬 생성 시 기존 클립을 재사용하여 Kie.ai API 크레딧을 절약하며,
생성된 에셋을 GitHub Repository로 자동 커밋 & 푸시하여 영구 보존 및 재사용할 수 있도록 관리합니다.
"""

import os
import json
import re
import hashlib
import shutil
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List

LIBRARY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "anime_library"))
MANIFEST_PATH = os.path.join(LIBRARY_DIR, "manifest.json")


def ensure_library_dir():
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    if not os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_manifest() -> List[Dict[str, Any]]:
    ensure_library_dir()
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"[Clip Library Warn] 매니페스트 로드 중 에러: {e}")
        return []


def save_manifest(manifest: List[Dict[str, Any]]):
    ensure_library_dir()
    try:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Clip Library Warn] 매니페스트 저장 중 에러: {e}")


def extract_slug_parts(character_profile: Optional[Dict[str, Any]], scene_prompt: str) -> Dict[str, str]:
    """
    캐릭터 프로필과 씬 프롬프트 텍스트에서
    머리색(hair), 복장(outfit), 배경(bg), 동작(action) 슬러그를 추출합니다.
    """
    # 1. 머리색 / 아키타입 슬러그
    hair_slug = "silver_lavender"
    if character_profile:
        arch = character_profile.get("archetype", "").lower()
        h_en = character_profile.get("hair_en", "").lower()
        h_ko = character_profile.get("hair_ko", "").lower()

        if arch == "reze" or "레제" in h_ko or "violet-purple" in h_en:
            hair_slug = "reze_violet_bob"
        elif arch == "makima" or "마키마" in h_ko or "braid" in h_en or "auburn" in h_en:
            hair_slug = "makima_red_braid"
        elif arch == "power" or "파워" in h_ko or "horns" in h_en or "strawberry blonde" in h_en:
            hair_slug = "power_blonde_horns"
        elif "pink" in h_en or "핑크" in h_ko:
            hair_slug = "pink_twintails"
        elif "black" in h_en or "흑발" in h_ko:
            hair_slug = "black_himecut"
        elif "blonde" in h_en or "금발" in h_ko:
            hair_slug = "blonde_ponytail"
        elif "cyan" in h_en or "blue" in h_en or "시안" in h_ko or "청량" in h_ko:
            hair_slug = "cyan_bob"
        elif "mint" in h_en or "민트" in h_ko:
            hair_slug = "mint_sideponytail"
        elif "wine" in h_en or "crimson" in h_en or "와인" in h_ko:
            hair_slug = "wine_red_long"
        elif "golden" in h_en or "골든" in h_ko:
            hair_slug = "golden_braids"
        elif "lilac" in h_en or "라일락" in h_ko:
            hair_slug = "lilac_wavy"
        elif "white" in h_en or "순백" in h_ko:
            hair_slug = "white_bob"
        elif "coral" in h_en or "peach" in h_en or "피치" in h_ko:
            hair_slug = "peach_coral"
        elif "chocolate" in h_en or "초콜릿" in h_ko:
            hair_slug = "chocolate_twintails"
        elif "grey" in h_en or "gray" in h_en or "애쉬" in h_ko:
            hair_slug = "ash_grey"
        elif "brown" in h_en or "밤색" in h_ko:
            hair_slug = "brown_wavy"

    # 2. 복장 슬러그
    outfit_slug = "signature_outfit"
    if character_profile:
        o_en = character_profile.get("outfit_en", "").lower()
        o_type = character_profile.get("outfit_type", "").lower()
        o_ko = character_profile.get("outfit_ko", "").lower()
        if "sleeveless" in o_en or "민소매" in o_ko:
            outfit_slug = "reze_sleeveless_tie"
        elif "trousers" in o_en or "오피스" in o_type or "수트" in o_ko or "blazer" in o_en:
            outfit_slug = "makima_suit_tie"
        elif "oversized" in o_en and "tie" in o_en or "루즈핏" in o_ko:
            outfit_slug = "power_loose_shirt"
        elif "bikini" in o_en or "monokini" in o_en or "수영복" in o_type:
            outfit_slug = "swimsuit_bikini"
        elif "sailor" in o_en or "교복" in o_type or "캠퍼스" in o_type:
            outfit_slug = "campus_preppy"
        elif "dolphin" in o_en or "돌핀팬츠" in o_type:
            outfit_slug = "dolphin_shorts"
        elif "sundress" in o_en or "dress" in o_en or "원피스" in o_type:
            outfit_slug = "onepiece_dress"
        elif "tracksuit" in o_en or "hoodie" in o_en or "츄리닝" in o_type:
            outfit_slug = "tracksuit_sporty"
        elif "bunny" in o_en or "바니걸" in o_type:
            outfit_slug = "bunny_girl"
        elif "tennis" in o_en or "테니스" in o_type:
            outfit_slug = "tennis_skirt"
        elif "knit" in o_en or "니트" in o_type:
            outfit_slug = "knit_sweater"
        elif "denim" in o_en or "스트릿" in o_type:
            outfit_slug = "denim_shorts"
        elif "maid" in o_en or "메이드" in o_type:
            outfit_slug = "maid_dress"

    # 3. 배경 슬러그 (씬 프롬프트 분석)
    p_lower = scene_prompt.lower()
    bg_slug = "scenic_terrace"
    if "dragon" in p_lower or "castle" in p_lower:
        bg_slug = "castle_balcony"
    elif "rapier" in p_lower or "fortress" in p_lower or "sword" in p_lower:
        bg_slug = "fortress_wall"
    elif "clock" in p_lower or "cogs" in p_lower:
        bg_slug = "clocktower_library"
    elif "galaxy" in p_lower or "stars" in p_lower or "observatory" in p_lower:
        bg_slug = "galaxy_observatory"
    elif "ruins" in p_lower or "cathedral" in p_lower:
        bg_slug = "ancient_ruins"
    elif "cliff" in p_lower or "mountain" in p_lower:
        bg_slug = "mountain_cliff"
    elif "jellyfish" in p_lower or "aquatic" in p_lower:
        bg_slug = "aquatic_hall"
    elif "beach" in p_lower or "ocean" in p_lower or "seaside" in p_lower:
        bg_slug = "seaside_promenade"
    elif "train" in p_lower or "carriage" in p_lower:
        bg_slug = "vintage_train"
    elif "snow" in p_lower or "winter" in p_lower:
        bg_slug = "snowy_village"
    elif "umbrella" in p_lower or "rain" in p_lower:
        bg_slug = "rainy_street"
    elif "bench" in p_lower or "garden" in p_lower:
        bg_slug = "starlit_garden"
    elif "forest" in p_lower or "leaves" in p_lower:
        bg_slug = "sunlit_forest"
    elif "blossom" in p_lower or "cherry" in p_lower:
        bg_slug = "cherry_blossom_garden"
    elif "bedroom" in p_lower or "sunlight" in p_lower:
        bg_slug = "morning_balcony"
    elif "stage" in p_lower or "concert" in p_lower or "lights" in p_lower:
        bg_slug = "concert_stage"

    # 4. 동작 슬러그
    action_slug = "gazing"
    if "singing" in p_lower or "microphone" in p_lower:
        action_slug = "singing"
    elif "walking" in p_lower or "strolling" in p_lower:
        action_slug = "walking"
    elif "holding" in p_lower or "rapier" in p_lower or "umbrella" in p_lower:
        action_slug = "holding_prop"
    elif "catching" in p_lower or "cupping" in p_lower:
        action_slug = "catching_petals"
    elif "leaning" in p_lower:
        action_slug = "leaning_window"
    elif "sitting" in p_lower:
        action_slug = "sitting"
    elif "basking" in p_lower or "smile" in p_lower:
        action_slug = "basking_smiling"
    elif "standing" in p_lower:
        action_slug = "standing"

    return {
        "hair": hair_slug,
        "outfit": outfit_slug,
        "background": bg_slug,
        "action": action_slug
    }


def generate_clip_slug(character_profile: Optional[Dict[str, Any]], scene_prompt: str, seed_str: str = "") -> str:
    """
    사용자 요구사항 반영:
    [머리색]_[복장]_[배경]_[동작]_[해시4자리].mp4 구조의 직관적이고 고유한 슬러그를 생성합니다.
    """
    parts = extract_slug_parts(character_profile, scene_prompt)
    hash_seed = seed_str or scene_prompt
    short_hash = hashlib.md5(hash_seed.encode("utf-8")).hexdigest()[:4]

    slug = f"{parts['hair']}_{parts['outfit']}_{parts['background']}_{parts['action']}_{short_hash}"
    # 혹시 모를 비정상 문자 제거
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '', slug)
    return slug


def save_clip_to_library(
    source_clip_path: str,
    character_profile: Optional[Dict[str, Any]],
    scene_prompt: str,
    duration_sec: float = 10.0,
    resolution: str = "480p"
) -> Optional[str]:
    """
    새로 생성된 비디오 클립을 명명 규칙에 맞춰 assets/anime_library/ 에 저장하고,
    manifest.json 메타데이터에 등록합니다.
    저장된 라이브러리 파일 경로를 반환합니다.
    """
    if not source_clip_path or not os.path.exists(source_clip_path):
        return None

    ensure_library_dir()
    slug_parts = extract_slug_parts(character_profile, scene_prompt)
    # 파일 내용 기반 해시 생성으로 중복 방지
    try:
        with open(source_clip_path, "rb") as f:
            file_hash = hashlib.md5(f.read(8192)).hexdigest()[:4]
    except Exception:
        file_hash = hashlib.md5(scene_prompt.encode("utf-8")).hexdigest()[:4]

    clip_id = f"{slug_parts['hair']}_{slug_parts['outfit']}_{slug_parts['background']}_{slug_parts['action']}_{file_hash}"
    filename = f"{clip_id}.mp4"
    target_path = os.path.join(LIBRARY_DIR, filename)

    # 라이브러리 디렉토리에 복사
    try:
        shutil.copy2(source_clip_path, target_path)
    except Exception as e:
        print(f"[Clip Library] 클립 복사 실패 ({target_path}): {e}")
        return None

    # 매니페스트 업데이트
    manifest = load_manifest()
    # 중복 ID 여부 확인
    existing_idx = next((i for i, item in enumerate(manifest) if item.get("id") == clip_id or item.get("filename") == filename), None)

    metadata = {
        "id": clip_id,
        "filename": filename,
        "rel_path": f"assets/anime_library/{filename}",
        "hair_slug": slug_parts["hair"],
        "outfit_slug": slug_parts["outfit"],
        "bg_slug": slug_parts["background"],
        "action_slug": slug_parts["action"],
        "character_summary": character_profile.get("korean_summary", "") if character_profile else "",
        "hair_ko": character_profile.get("hair_ko", "") if character_profile else "",
        "outfit_ko": character_profile.get("outfit_ko", "") if character_profile else "",
        "outfit_type": character_profile.get("outfit_type", "") if character_profile else "",
        "prompt": scene_prompt[:300],
        "duration_sec": duration_sec,
        "resolution": resolution,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    if existing_idx is not None:
        manifest[existing_idx] = metadata
    else:
        manifest.append(metadata)

    save_manifest(manifest)
    print(f"[Clip Library] 📦 새 애니메이션 클립 라이브러리 보관 완료: assets/anime_library/{filename}")
    return target_path


def find_reusable_clip(
    character_profile: Optional[Dict[str, Any]],
    scene_prompt: str,
    exclude_paths: Optional[List[str]] = None
) -> Optional[str]:
    """
    생성하려는 씬(캐릭터 프로필, 배경, 동작)과 일치하는 기존 클립이
    assets/anime_library/ 에 있는지 검색합니다.
    일치하는 클립이 발견되면 해당 파일 경로를 반환하여 SeaDance V1 Pro API 생성을 건너뛰고
    크레딧을 절약합니다.
    """
    manifest = load_manifest()
    if not manifest:
        return None

    exclude_set = set(os.path.abspath(p) for p in (exclude_paths or []))
    target_parts = extract_slug_parts(character_profile, scene_prompt)

    # 1단계: 헤어 + 복장 + 배경 일치 (동작까지 일치하면 최우선)
    candidate_perfect = []
    candidate_scene_match = []
    candidate_profile_match = []

    for item in manifest:
        filename = item.get("filename")
        if not filename:
            continue
        clip_path = os.path.join(LIBRARY_DIR, filename)
        if not os.path.exists(clip_path):
            continue
        if os.path.abspath(clip_path) in exclude_set:
            continue

        h_match = (item.get("hair_slug") == target_parts["hair"])
        o_match = (item.get("outfit_slug") == target_parts["outfit"])
        b_match = (item.get("bg_slug") == target_parts["background"])
        a_match = (item.get("action_slug") == target_parts["action"])

        if h_match and o_match and b_match and a_match:
            candidate_perfect.append(clip_path)
        elif h_match and o_match and b_match:
            candidate_scene_match.append(clip_path)
        elif h_match and o_match:
            candidate_profile_match.append(clip_path)

    # 가장 높은 일치도의 클립 선택
    chosen = None
    if candidate_perfect:
        chosen = candidate_perfect[0]
        match_level = "완벽 일치 (헤어+복장+배경+동작)"
    elif candidate_scene_match:
        chosen = candidate_scene_match[0]
        match_level = "배경 일치 (헤어+복장+배경)"
    elif candidate_profile_match:
        chosen = candidate_profile_match[0]
        match_level = "캐릭터 일치 (헤어+복장)"

    if chosen:
        print(f"[Clip Library] 🎯 기존 애니메이션 클립 매칭 성공! [{match_level}] -> {os.path.basename(chosen)} (크레딧 절약)")
        return chosen

    return None


def git_commit_and_push_library(commit_message: str = "chore(assets): save newly generated anime clips to library"):
    """
    assets/anime_library/ 에 새로 추가되거나 변경된 클립과 manifest.json을
    현재 git 레포지토리에 커밋하고 원격으로 푸시합니다.
    로컬 실행 또는 워크플로우 실행 시 호출됩니다.
    """
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # 변경사항 체크
        subprocess.run(["git", "add", "assets/anime_library"], cwd=repo_root, check=True)
        status_res = subprocess.run(
            ["git", "status", "--porcelain", "assets/anime_library"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        if not status_res.stdout.strip():
            print("[Clip Library Git] 새로 커밋할 애니메이션 클립 변경사항이 없습니다.")
            return True

        print("[Clip Library Git] 🚀 신규 애니메이션 에셋을 Git 저장소에 커밋 & 푸시합니다...")
        subprocess.run(["git", "commit", "-m", f"{commit_message} [skip ci]"], cwd=repo_root, check=True)
        # Pull rebase 후 Push
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=repo_root, check=False)
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, capture_output=True, text=True)

        if push_res.returncode == 0:
            print("[Clip Library Git] ✅ GitHub Push 성공! 애니메이션 에셋이 안전하게 레포지토리에 저장되었습니다.")
            return True
        else:
            print(f"[Clip Library Git Warn] Push 중 알림: {push_res.stderr.strip()[:200]}")
            return False
    except Exception as e:
        print(f"[Clip Library Git] 커밋/푸시 시도 중 예외 발생 (작업 계속 진행): {e}")
        return False
