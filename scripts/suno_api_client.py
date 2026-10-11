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
                import traceback
                print(f"\n[Suno Engine Error] Kie.ai 오류 발생: {e}")
                print(traceback.format_exc())

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

        print(f"[Kie.ai] Task ID: {task_id} - 음원 생성 대기 중 (최대 360초)...")
        record_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"

        for i in range(72): # 72 * 5초 = 360초 (6분 대기)
            time.sleep(5)
            try:
                r = requests.get(record_url, headers=headers, timeout=20)
            except Exception as req_err:
                print(f"[Kie.ai Polling Warn] 요청 일시적 오류: {req_err}")
                continue

            if r.status_code == 200:
                body = r.json()
                rec_data = body.get("data", {})
                current_state = rec_data.get("state") or rec_data.get("status")

                if i % 4 == 0:
                    print(f"[Kie.ai Progress] 경과 시간: {(i+1)*5}초, 현재 상태: {current_state}")

                if current_state in ["success", "SUCCESS"]:
                    result_json_raw = rec_data.get("resultJson", {})
                    if isinstance(result_json_raw, str):
                        try:
                            result_json = json.loads(result_json_raw)
                        except Exception:
                            result_json = {}
                    else:
                        result_json = result_json_raw or {}

                    # Kie.ai 실데이터 포맷: result_json = {'code': 200, 'data': [{'audio_url': '...', 'image_url': '...'}, ...]}
                    kie_items = result_json.get("data", [])
                    if isinstance(kie_items, list) and kie_items:
                        first_item = kie_items[0]
                        audio_url = first_item.get("audio_url") or first_item.get("stream_audio_url")
                        image_url = first_item.get("image_url")
                    else:
                        audio_url = None
                        image_url = None

                    # 보조 필드 탐색 (resultUrls, resultObject, audio, url 등)
                    if not audio_url:
                        audio_urls = result_json.get("resultUrls", [])
                        audio_url = audio_urls[0] if audio_urls else None

                    if not audio_url:
                        res_obj = result_json.get("resultObject", {})
                        if isinstance(res_obj, dict):
                            audio_url = res_obj.get("audio") or res_obj.get("url") or res_obj.get("audio_url")
                        elif isinstance(res_obj, list) and res_obj:
                            audio_url = res_obj[0].get("audio") or res_obj[0].get("url")

                    if not audio_url:
                        audio_url = result_json.get("audio_url") or result_json.get("audioUrl") or result_json.get("url")

                    if not audio_url:
                        print(f"[Kie.ai Parse Warn] 응답 내용: {rec_data}")
                        raise ValueError(f"Kie.ai 생성 완료되었으나 audio_url을 찾지 못했습니다: {result_json}")

                    if not image_url:
                        image_url = result_json.get("image_url") or result_json.get("imageUrl")

                    return {
                        "provider": "kie.ai",
                        "task_id": task_id,
                        "audio_url": audio_url,
                        "image_url": image_url
                    }

                elif current_state in ["fail", "error", "FAIL"]:
                    fail_code = rec_data.get("failCode")
                    fail_msg = rec_data.get("failMsg")
                    raise RuntimeError(f"Kie.ai 작업 실패 (Code: {fail_code}, Msg: {fail_msg}): {rec_data}")

        raise TimeoutError("Kie.ai 음원 생성 시간 초과 (360초)")

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
