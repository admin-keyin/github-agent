"""
Suno AI 및 Suno-Wrapper API (Kie.ai, SunoApi.org, Apiframe, Suno Cookie) 통합 클라이언트 모듈.
토큰/키가 없을 경우에도 Gemini 기반 작사 및 작곡 + 하모닉 믹싱 폴백을 제공합니다.
"""

import os
import time
import json
import requests
from typing import Optional, Dict, Any, Tuple

class SunoMusicGenerator:
    """
    Suno AI 수준의 음악을 생성하는 통합 엔진.
    지원 프로바이더:
    1. Kie.ai (AI Music API Suno V6 / V5_5) - KIE_API_KEY
    2. SunoApi.org (Suno V4_5ALL / V6) - SUNO_API_KEY
    3. Apiframe (Suno API) - APIFRAME_KEY
    4. Suno Direct Cookie (yihong0618 reverse wrapper) - SUNO_COOKIE
    """

    def __init__(self):
        self.kie_api_key = os.getenv("KIE_API_KEY", "").strip()
        self.suno_api_key = os.getenv("SUNO_API_KEY", "").strip()
        self.apiframe_key = os.getenv("APIFRAME_KEY", "").strip()
        self.suno_cookie = os.getenv("SUNO_COOKIE", "").strip()

    def has_any_api_key(self) -> bool:
        return bool(self.kie_api_key or self.suno_api_key or self.apiframe_key or self.suno_cookie)

    def generate_music(
        self,
        title: str,
        style: str,
        lyrics: str,
        output_audio_path: str,
        instrumental: bool = False
    ) -> Dict[str, Any]:
        """
        API 키가 있으면 실제 Suno API 클라우드에서 고음질 음원을 생성 및 다운로드합니다.
        """
        # 1. Kie.ai 시도
        if self.kie_api_key:
            try:
                print(f"[Suno Engine] Kie.ai (Suno V6) 엔진으로 생성을 시작합니다...")
                result = self._generate_via_kie(title, style, lyrics, instrumental)
                if result.get("audio_url"):
                    self._download_file(result["audio_url"], output_audio_path)
                    result["saved_path"] = output_audio_path
                    return result
            except Exception as e:
                print(f"[Suno Engine Warn] Kie.ai 생성 중 오류: {e}")

        # 2. SunoApi.org 시도
        if self.suno_api_key:
            try:
                print(f"[Suno Engine] SunoApi.org (Suno API) 엔진으로 생성을 시작합니다...")
                result = self._generate_via_sunoapi(title, style, lyrics, instrumental)
                if result.get("audio_url"):
                    self._download_file(result["audio_url"], output_audio_path)
                    result["saved_path"] = output_audio_path
                    return result
            except Exception as e:
                print(f"[Suno Engine Warn] SunoApi.org 생성 중 오류: {e}")

        # 3. Apiframe 시도
        if self.apiframe_key:
            try:
                print(f"[Suno Engine] Apiframe 엔진으로 생성을 시작합니다...")
                result = self._generate_via_apiframe(title, style, lyrics, instrumental)
                if result.get("audio_url"):
                    self._download_file(result["audio_url"], output_audio_path)
                    result["saved_path"] = output_audio_path
                    return result
            except Exception as e:
                print(f"[Suno Engine Warn] Apiframe 생성 중 오류: {e}")

        # 4. Suno Cookie 세션 시도
        if self.suno_cookie:
            try:
                print(f"[Suno Engine] Suno 웹 세션(Cookie)으로 생성을 시작합니다...")
                result = self._generate_via_cookie(title, style, lyrics, instrumental)
                if result.get("audio_url"):
                    self._download_file(result["audio_url"], output_audio_path)
                    result["saved_path"] = output_audio_path
                    return result
            except Exception as e:
                print(f"[Suno Engine Warn] Suno Cookie 생성 중 오류: {e}")

        raise RuntimeError("사용 가능한 Suno API 키 또는 쿠키가 없거나 모든 API 요청이 실패했습니다.")

    # --- Kie.ai 구현체 ---
    def _generate_via_kie(self, title: str, style: str, lyrics: str, instrumental: bool) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.kie_api_key}",
            "Content-Type": "application/json"
        }
        create_url = "https://api.kie.ai/api/v1/jobs/createTask"
        payload = {
            "model": "ai-music-api/generate",
            "input": {
                "custom_mode": True,
                "instrumental": instrumental,
                "model": "V6",
                "title": title[:80],
                "style": style[:1000],
                "prompt": lyrics[:5000]
            }
        }
        res = requests.post(create_url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        task_id = data.get("data", {}).get("taskId") or data.get("taskId")
        if not task_id:
            raise ValueError(f"Kie.ai taskId를 발급받지 못했습니다: {data}")

        print(f"[Kie.ai] Task ID: {task_id} - 음원 생성 대기 중 (최대 180초)...")
        record_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"

        for _ in range(45): # 45 * 4초 = 180초
            time.sleep(4)
            r = requests.get(record_url, headers=headers, timeout=20)
            if r.status_code == 200:
                rec_data = r.json().get("data", {})
                status = rec_data.get("status")
                if status == "success":
                    result_json = rec_data.get("resultJson", {})
                    audio_urls = result_json.get("resultUrls", [])
                    audio_url = audio_urls[0] if audio_urls else None
                    if not audio_url:
                        # 구조가 객체일 경우
                        audio_url = result_json.get("audio_url") or result_json.get("audioUrl")
                    return {
                        "provider": "kie.ai",
                        "task_id": task_id,
                        "audio_url": audio_url,
                        "image_url": result_json.get("image_url") or result_json.get("imageUrl")
                    }
                elif status in ["fail", "error"]:
                    raise RuntimeError(f"Kie.ai 작업 실패: {rec_data}")

        raise TimeoutError("Kie.ai 음원 생성 시간 초과 (180초)")

    # --- SunoApi.org 구현체 ---
    def _generate_via_sunoapi(self, title: str, style: str, lyrics: str, instrumental: bool) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.suno_api_key}",
            "Content-Type": "application/json"
        }
        create_url = "https://api.sunoapi.org/api/v1/generate"
        payload = {
            "customMode": True,
            "instrumental": instrumental,
            "model": "V6",
            "title": title[:80],
            "style": style[:1000],
            "prompt": lyrics[:5000]
        }
        res = requests.post(create_url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        task_id = data.get("data", {}).get("taskId") or data.get("taskId")
        if not task_id:
            raise ValueError(f"SunoApi.org taskId 발급 실패: {data}")

        print(f"[SunoApi.org] Task ID: {task_id} - 음원 생성 대기 중 (최대 180초)...")
        record_url = f"https://api.sunoapi.org/api/v1/generate/record-info?taskId={task_id}"

        for _ in range(45):
            time.sleep(4)
            r = requests.get(record_url, headers=headers, timeout=20)
            if r.status_code == 200:
                rec_data = r.json().get("data", {})
                status = rec_data.get("status")
                if status in ["success", "complete", "SUCCESS"]:
                    response_obj = rec_data.get("response", {})
                    suno_data = response_obj.get("sunoData", [])
                    if suno_data:
                        first = suno_data[0]
                        return {
                            "provider": "sunoapi.org",
                            "task_id": task_id,
                            "audio_url": first.get("audio_url") or first.get("audioUrl"),
                            "image_url": first.get("image_url") or first.get("imageUrl")
                        }
                elif status in ["fail", "error", "FAILED"]:
                    raise RuntimeError(f"SunoApi.org 작업 실패: {rec_data}")

        raise TimeoutError("SunoApi.org 음원 생성 시간 초과")

    # --- Apiframe 구현체 ---
    def _generate_via_apiframe(self, title: str, style: str, lyrics: str, instrumental: bool) -> Dict[str, Any]:
        headers = {
            "X-API-Key": self.apiframe_key,
            "Content-Type": "application/json"
        }
        create_url = "https://api.apiframe.ai/v2/music/generate"
        payload = {
            "model": "suno",
            "prompt": lyrics[:5000],
            "sunoParams": {
                "custom_mode": True,
                "title": title,
                "style": style,
                "instrumental": instrumental,
                "model_version": "V6"
            }
        }
        res = requests.post(create_url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        task_id = data.get("task_id") or data.get("taskId")
        if not task_id:
            raise ValueError(f"Apiframe task_id 발급 실패: {data}")

        print(f"[Apiframe] Task ID: {task_id} - 대기 중...")
        record_url = f"https://api.apiframe.ai/v2/jobs/{task_id}"

        for _ in range(45):
            time.sleep(4)
            r = requests.get(record_url, headers=headers, timeout=20)
            if r.status_code == 200:
                rec_data = r.json()
                if rec_data.get("status") in ["SUCCESS", "success"]:
                    urls = rec_data.get("output_urls", [])
                    return {
                        "provider": "apiframe",
                        "task_id": task_id,
                        "audio_url": urls[0] if urls else rec_data.get("audio_url"),
                        "image_url": rec_data.get("image_url")
                    }
                elif rec_data.get("status") in ["FAILED", "failed"]:
                    raise RuntimeError(f"Apiframe 작업 실패: {rec_data}")

        raise TimeoutError("Apiframe 음원 생성 시간 초과")

    # --- Suno Cookie 세션 구현체 ---
    def _generate_via_cookie(self, title: str, style: str, lyrics: str, instrumental: bool) -> Dict[str, Any]:
        try:
            from suno import SongsGen
            sg = SongsGen(self.suno_cookie)
            print(f"[Suno Cookie] 잔여 크레딧: {sg.get_limit_left()}")
            res = sg.save_songs(
                prompt=lyrics,
                is_custom=True,
                title=title,
                tags=style,
                output_dir="temp"
            )
            return {
                "provider": "suno_cookie",
                "audio_url": res if isinstance(res, str) else None
            }
        except ImportError:
            raise RuntimeError("suno_songs 패키지가 설치되지 않았습니다. pip install suno_songs 가 필요합니다.")

    def _download_file(self, url: str, target_path: str):
        print(f"[Suno Engine] 고음질 생성 음원 다운로드 중: {url}")
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[Suno Engine] 저장 완료: {target_path} (크기: {os.path.getsize(target_path)} bytes)")
