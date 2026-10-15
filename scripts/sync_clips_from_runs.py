"""
Inkey Studio - Synchronize Anime Clips from GitHub Actions Logs
과거에 성공적으로 완료된 GitHub Actions 실행 로그를 파싱하여,
생성되었던 ByteDance SeaDance V1 Pro 애니메이션 비디오(MP4)를 다운로드하고,
정규화된 파일명([머리색]_[복장]_[배경]_[동작]_[해시].mp4)으로 assets/anime_library/ 에 보관한 뒤
Git Commit & Push를 수행합니다.
"""

import os
import sys
import re
import json
import subprocess
import requests
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.clip_library import (
    save_clip_to_library,
    load_manifest,
    ensure_library_dir,
    LIBRARY_DIR
)


def parse_run_log(run_id: str):
    """
    단일 run_id에 대해 로그를 조회하고 캐릭터 프로필 및 씬 매핑 정보를 파싱합니다.
    """
    print(f"\n[Run {run_id}] GitHub Actions 로그 조회 중...")
    cmd = ["gh", "run", "view", str(run_id), "--log", "-R", "admin-keyin/github-agent"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Run {run_id} Err] 로그 조회 실패: {res.stderr[:200]}")
        return None, []

    lines = res.stdout.splitlines()

    hair_info = None
    outfit_info = None
    scene_prompts = {}
    scene_urls = {}
    last_url = None

    for line in lines:
        if "-> 헤어:" in line:
            m = re.search(r'-> 헤어:\s*(.*?)\s*\((.*?)\)', line)
            if m:
                hair_info = {"ko": m.group(1).strip(), "en": m.group(2).strip()}
        elif "-> 의상:" in line:
            m = re.search(r'-> 의상:\s*(.*?)\s*\[(.*?)\]\s*\((.*?)\)', line)
            if m:
                outfit_info = {"ko": m.group(1).strip(), "type": m.group(2).strip(), "en": m.group(3).strip()}
        elif "SeaDance V1 Pro 10초 렌더링 요청:" in line:
            m_req = re.search(r'Scene\s*(\d+)/\d+.*?SeaDance V1 Pro 10초 렌더링 요청:\s*(.*)', line)
            if m_req:
                s_idx = int(m_req.group(1)) - 1
                scene_prompts[s_idx] = m_req.group(2).strip()
        elif "비디오 생성 완료! 다운로드 중:" in line:
            m_dl = re.search(r'다운로드 중:\s*(https://tempfile\.aiquickdraw\.com/seedance/[^\s]+)', line)
            if m_dl:
                last_url = m_dl.group(1).strip()
        elif "[Scene " in line and "성공] 저장 완료:" in line and last_url:
            m_succ = re.search(r'\[Scene\s*(\d+)/\d+\s*성공\]\s*저장 완료:\s*temp/videos_full/scene_(\d+)\.mp4', line)
            if m_succ:
                s_idx = int(m_succ.group(2))
                scene_urls[s_idx] = last_url
                last_url = None

    # 만약 캐릭터 프로필이 명시적으로 출력되지 않은 구버전 run의 경우 기본 프로필 추정
    if not hair_info:
        hair_info = {"ko": "은발/라벤더빛 긴 생머리 & 리본", "en": "silky long silver-lavender hair with cute ribbons"}
    if not outfit_info:
        outfit_info = {"ko": "오픈 버스트 메이드 드레스", "type": "메이드복", "en": "wearing a stylish form-fitting cute maid corset dress"}

    profile = {
        "hair_ko": hair_info["ko"],
        "hair_en": hair_info["en"],
        "outfit_ko": outfit_info["ko"],
        "outfit_type": outfit_info.get("type", "일반의상"),
        "outfit_en": outfit_info["en"],
        "korean_summary": f"{hair_info['ko']} + {outfit_info['ko']}"
    }

    matched_scenes = []
    for s_idx, url in sorted(scene_urls.items()):
        prompt = scene_prompts.get(s_idx, "masterpiece Japanese 2D anime girl, cute and sexy, emotional scene")
        matched_scenes.append({
            "scene_idx": s_idx,
            "url": url,
            "prompt": prompt
        })

    print(f"[Run {run_id}] 캐릭터: {profile['korean_summary']} | 발견된 씬 클립: {len(matched_scenes)}개")
    return profile, matched_scenes


def download_clip(url: str, dest_path: str, timeout: int = 45) -> bool:
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
        if resp.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            print(f" [Download Err] HTTP {resp.status_code} for {url}")
            return False
    except Exception as e:
        print(f" [Download Exception] {url} -> {e}")
        return False


def git_push_batch(count: int):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    subprocess.run(["git", "add", "assets/anime_library"], cwd=repo_root, check=True)
    res = subprocess.run(["git", "status", "--porcelain", "assets/anime_library"], cwd=repo_root, capture_output=True, text=True)
    if not res.stdout.strip():
        print("[Git Push] 커밋할 변경사항이 없습니다.")
        return

    commit_msg = f"chore(assets): archive {count} anime clips from past action runs to library [skip ci]"
    print(f"[Git Push] 커밋 생성 중: {commit_msg}")
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_root, check=True)
    print("[Git Push] 원격 저장소로 푸시 중...")
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=repo_root, check=False)
    push_res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, capture_output=True, text=True)
    if push_res.returncode == 0:
        print("[Git Push] ✅ 푸시 성공!")
    else:
        print(f"[Git Push Warn] {push_res.stderr.strip()[:200]}")


def main():
    ensure_library_dir()
    os.makedirs("temp/downloaded_clips", exist_ok=True)

    # 최근 성공한 주요 액션 run ID 리스트
    target_runs = [
        "38655200811",  # 24개 클립 (흑발 히메컷 + 테니스룩)
        "38621214615",  # 24개 클립
        "38582582142",  # 25개 클립
        "38579251742",  # 19개 클립
        "38578326458",  # 17개 클립
    ]

    existing_manifest = load_manifest()
    known_prompts = {item.get("prompt", "")[:80] for item in existing_manifest}

    total_added = 0
    batch_count = 0
    batch_limit = 15  # 15개마다 나누어 커밋 & 푸시하여 Git 100MB 푸시 용량 제한 안전 확보

    for run_id in target_runs:
        profile, scenes = parse_run_log(run_id)
        if not scenes:
            continue

        for sc in scenes:
            url = sc["url"]
            prompt = sc["prompt"]

            # 임시 파일 경로
            tmp_filename = os.path.basename(url.split("?")[0])
            tmp_path = os.path.join("temp/downloaded_clips", tmp_filename)

            print(f" -> 클립 다운로드 중: {url[:75]}...")
            if not os.path.exists(tmp_path):
                ok = download_clip(url, tmp_path)
                if not ok:
                    continue

            # 라이브러리 저장
            saved_path = save_clip_to_library(
                source_clip_path=tmp_path,
                character_profile=profile,
                scene_prompt=prompt,
                duration_sec=10.0,
                resolution="480p"
            )

            if saved_path:
                total_added += 1
                batch_count += 1
                print(f"    [보관 성공 #{total_added}] {os.path.basename(saved_path)}")

                # 배치 푸시
                if batch_count >= batch_limit:
                    git_push_batch(batch_count)
                    batch_count = 0

    # 잔여 클립 푸시
    if batch_count > 0:
        git_push_batch(batch_count)

    print(f"\n=================================================")
    print(f" [완료] 총 {total_added}개의 애니메이션 비디오 클립이 에셋 라이브러리에 저장 및 푸시되었습니다!")
    print(f"=================================================\n")


if __name__ == "__main__":
    main()
