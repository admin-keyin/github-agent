"""
Inkey Studio - Safe Anime Library Manifest Merger & Git Push
GitHub Actions 러너 또는 로컬에서 실행 시,
원격 저장소(origin/main)의 manifest.json과 로컬의 신규 클립 엔트리를
JSON ID 기준으로 자동 중복 제거 병합(Smart JSON Array Merge)하여
Git 충돌(Merge Conflict) 없이 안전하게 커밋 & 푸시합니다.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIBRARY_DIR = os.path.join(REPO_ROOT, "assets", "anime_library")
MANIFEST_PATH = os.path.join(LIBRARY_DIR, "manifest.json")


def load_json_file(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_manifests(local_items, remote_items):
    merged_map = {}
    # 원격 항목 먼저 등록
    for item in remote_items:
        key = item.get("filename") or item.get("id")
        if key:
            merged_map[key] = item
    # 로컬 항목으로 덮어쓰거나 추가 (로컬에서 새로 생성된 항목 포함)
    for item in local_items:
        key = item.get("filename") or item.get("id")
        if key:
            merged_map[key] = item
    return list(merged_map.values())


def sync_and_push(max_retries=3):
    os.chdir(REPO_ROOT)
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=False)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=False)

    for attempt in range(1, max_retries + 1):
        print(f"\n[Safe Sync] Git 동기화 및 푸시 시도 ({attempt}/{max_retries})...")
        try:
            # 1. 현재 로컬의 manifest 항목 기억
            local_items = load_json_file(MANIFEST_PATH)

            # 2. 원격 최신 커밋 fetch
            fetch_res = subprocess.run(["git", "fetch", "origin", "main"], capture_output=True, text=True)
            if fetch_res.returncode != 0:
                print(f"[Safe Sync Warn] git fetch 실패: {fetch_res.stderr[:200]}")

            # 3. 원격 origin/main의 manifest.json 내용 읽기
            show_res = subprocess.run(
                ["git", "show", "origin/main:assets/anime_library/manifest.json"],
                capture_output=True,
                text=True
            )
            remote_items = []
            if show_res.returncode == 0 and show_res.stdout.strip():
                try:
                    remote_items = json.loads(show_res.stdout.strip())
                except Exception:
                    remote_items = []

            # 4. JSON 레벨에서 중복 제거 및 병합
            merged = merge_manifests(local_items, remote_items)
            save_json_file(MANIFEST_PATH, merged)
            print(f"[Safe Sync] manifest.json 병합 완료: 총 {len(merged)}개 엔트리 (로컬 {len(local_items)}개, 원격 {len(remote_items)}개)")

            # 5. Stash/Soft sync to origin/main head
            # rebase 중인 상태가 남아있다면 중단
            subprocess.run(["git", "rebase", "--abort"], capture_output=True, text=True)
            subprocess.run(["git", "merge", "--abort"], capture_output=True, text=True)

            # 6. Git Add
            subprocess.run(["git", "add", "assets/anime_library"], check=True)

            # 상태 확인
            status_res = subprocess.run(
                ["git", "status", "--porcelain", "assets/anime_library"],
                capture_output=True,
                text=True,
                check=True
            )
            if not status_res.stdout.strip():
                print("[Safe Sync] 커밋할 신규 애니메이션 클립 또는 메타데이터 변경사항이 없습니다.")
                return True

            # 7. Commit
            commit_msg = "chore(assets): save newly generated anime clips to library [skip ci]"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            # 8. Rebase pull with ours strategy for safety
            pull_res = subprocess.run(
                ["git", "pull", "--rebase", "-X", "ours", "origin", "main"],
                capture_output=True,
                text=True
            )
            if pull_res.returncode != 0:
                print(f"[Safe Sync Warn] Rebase 실패, abort 후 재시도: {pull_res.stderr[:200]}")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True, text=True)
                time.sleep(2)
                continue

            # 9. Push
            push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if push_res.returncode == 0:
                print("[Safe Sync] ✅ GitHub Push 성공! 애니메이션 에셋이 충돌 없이 안전하게 반영되었습니다.")
                return True
            else:
                print(f"[Safe Sync Warn] Push 실패 ({push_res.stderr.strip()[:200]}), 잠시 후 재시도합니다...")
                time.sleep(2 * attempt)
        except Exception as e:
            print(f"[Safe Sync Error] 예외 발생: {e}")
            time.sleep(2 * attempt)

    print("[Safe Sync] 최대 재시도 초과: 푸시 실패 (다음 워크플로우에서 자동 동기화됩니다).")
    return False


if __name__ == "__main__":
    success = sync_and_push()
    if not success:
        sys.exit(0)  # 워크플로우 전체 실패로 번지지 않도록 0으로 정상 종료
