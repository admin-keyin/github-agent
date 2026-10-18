"""
Kie.ai Wan 3.0 / Wan 2.6 기반 지브리풍 감성 비디오 생성 클라이언트 모듈.
- 가사 서사(기승전결)에 맞춘 고화질 애니메이션 비디오 생성 (480P 경제 모드 지원)
- 비디오 생성 실패 또는 키 미제공 시 안전한 폴백 지원
"""

import os
import time
import json
import requests
from typing import Optional, Dict, Any, List

try:
    from scripts.character_profile import generate_random_character_profile, build_character_prompt
except ImportError:
    from character_profile import generate_random_character_profile, build_character_prompt

class KieVideoGenerator:
    def __init__(self):
        self.kie_api_key = os.getenv("KIE_API_KEY", "").strip()

    def has_api_key(self) -> bool:
        return bool(self.kie_api_key)

    def generate_video_clip(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        output_path: str = ""
    ) -> Optional[str]:
        """
        Kie.ai의 비디오 모델(ByteDance SeaDance V1 Pro / Kling / Wan)을 호출하여 5초 단위 비디오 클립을 생성합니다.
        duration: 5초 기본 (스피디하고 다이나믹한 컷 전환 & 크레딧 50% 절약)
        resolution: "480p" (가장 경제적이고 효율적)
        """
        if not self.has_api_key():
            print("[Kie Video Warn] KIE_API_KEY가 설정되지 않아 비디오 생성을 건너뜁니다.")
            return None

        headers = {
            "Authorization": f"Bearer {self.kie_api_key}",
            "Content-Type": "application/json"
        }

        # 정통 일본 2D 애니메이션 배경/풍경 화풍 (인물/캐릭터 배제)
        if "Japanese" in prompt or "masterpiece" in prompt:
            anime_prompt = prompt
        else:
            anime_prompt = (
                f"masterpiece modern Japanese anime background visual, contemporary high-end Japanese TV anime scenery, "
                f"{prompt}, "
                f"breathtaking Makoto Shinkai cinematic lighting, atmospheric anime environment, sophisticated anime digital shading, crisp modern anime linework, Kyoto Animation, CloverWorks and MAPPA quality, "
                f"no people, no human, no characters, no girl, no boy, not photorealistic, not realistic photography, not 3D CGI, not semi-realistic, no live-action, no real human photo, no watermark"
            )

        create_url = "https://api.kie.ai/api/v1/jobs/createTask"
        
        # ByteDance SeaDance V1 Pro (초당 2.8 크레딧, 가성비 끝판왕) -> Kling Omni -> Wan 순차 시도
        candidate_models = [
            "bytedance/v1-pro-text-to-video",
            "kling-3.0-omni/text-to-video",
            "wan/3-0-video"
        ]

        task_id = None
        target_res = "480p"  # 가장 경제적이고 안정적인 480p
        dur_int = int(duration) if duration else 5

        for model in candidate_models:
            input_params = {
                "prompt": anime_prompt[:2500],
                "aspect_ratio": aspect_ratio,
                "resolution": target_res,
                "negative_prompt": "people, person, human, girl, boy, woman, man, face, character, portrait, body, limbs, photorealistic, realistic photography, real life photograph, live action footage, camera selfie, 3D CGI, 3D render, semi-realistic, real human skin, webtoon, manhwa, korean webtoon, western comic, retro anime, 90s anime, 80s anime, vintage anime, classic anime, retro manga, old fashioned cartoon, oversized eyes, giant bug eyes, flat cel shading, goofy face, 1990s aesthetic, deformed, disfigured, bad anatomy, bad hands, blurry, low quality, ugly, watermark"
            }
            if "bytedance" in model:
                # SeaDance 규격: "5s" 또는 "10s", camera_fixed: false
                input_params["duration"] = f"{dur_int}s"
                input_params["camera_fixed"] = False
            elif "kling" in model:
                input_params["duration"] = str(dur_int)
                input_params["audio"] = False
                input_params["resolution"] = "720p"
            elif "wan" in model:
                input_params["duration"] = dur_int
                input_params["resolution"] = "480P"
                input_params["audio"] = False

            payload = {
                "model": model,
                "input": input_params
            }
            try:
                res = requests.post(create_url, headers=headers, json=payload, timeout=30)
                data = {}
                try:
                    data = res.json()
                except Exception:
                    pass

                if res.status_code == 200:
                    data_field = data.get("data")
                    if isinstance(data_field, dict):
                        task_id = data_field.get("taskId") or data_field.get("task_id")
                    elif isinstance(data_field, str):
                        task_id = data_field
                    else:
                        task_id = data.get("taskId") or data.get("task_id")

                    if task_id:
                        print(f"[Kie Video Engine] {model} 작업 요청 성공 (Task ID: {task_id}, 길이: {duration}초)")
                        break
                    else:
                        print(f"[Kie Video Warn] {model} 200 OK이나 taskId 없음: {data}")
                else:
                    print(f"[Kie Video Warn] {model} 요청 실패 (HTTP {res.status_code}): {data or res.text[:200]}")
            except Exception as e:
                print(f"[Kie Video Warn] {model} 요청 중 예외: {e}")

        if not task_id:
            print("[Kie Video Error] 모든 비디오 모델에 대한 작업 요청에 실패했습니다.")
            return None

        # 상태 폴링 (최대 12분 대기)
        record_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
        max_attempts = 144  # 144 * 5초 = 720초 (12분)
        print(f"[Kie Video Engine] 비디오 렌더링 대기 중 (Task: {task_id})...")

        for attempt in range(max_attempts):
            time.sleep(5)
            try:
                r = requests.get(record_url, headers=headers, timeout=20)
                if r.status_code != 200:
                    continue
                body = r.json()
                bdata = body.get("data") or {}
                
                # 상태 확인
                state = (
                    bdata.get("state") or 
                    bdata.get("status") or 
                    bdata.get("task_status") or 
                    ""
                ).lower()

                if attempt % 6 == 0:
                    print(f"[Kie Video Progress] 대기 {attempt * 5}초... 상태: {state or 'processing'}")

                if state in ["success", "succeed", "completed", "finish"]:
                    # 결과 URL 추출 (Kie.ai의 resultJson, info.resultUrls, response.video_url 등 모든 규격 지원)
                    result_urls = []
                    
                    # 1. resultJson (직렬화된 JSON 문자열 형태인 경우)
                    if bdata.get("resultJson"):
                        try:
                            rj = json.loads(bdata["resultJson"]) if isinstance(bdata["resultJson"], str) else bdata["resultJson"]
                            if isinstance(rj, dict) and rj.get("resultUrls"):
                                result_urls.extend(rj["resultUrls"])
                            elif isinstance(rj, list):
                                result_urls.extend(rj)
                        except Exception as parse_err:
                            print(f"[Kie Video Warn] resultJson 파싱 실패: {parse_err}")

                    # 2. info dict 내부
                    info = bdata.get("info") or {}
                    if isinstance(info, dict) and info.get("resultUrls"):
                        result_urls.extend(info.get("resultUrls"))

                    # 3. response dict 내부
                    resp_dict = bdata.get("response") or {}
                    if isinstance(resp_dict, dict):
                        if resp_dict.get("video_url"):
                            result_urls.append(resp_dict["video_url"])
                        if resp_dict.get("resultUrls"):
                            result_urls.extend(resp_dict["resultUrls"])

                    # 4. 최상위 필드들
                    for k in ["resultUrls", "video_url", "videoUrl", "url", "download_url"]:
                        val = bdata.get(k)
                        if isinstance(val, list):
                            result_urls.extend(val)
                        elif isinstance(val, str) and val.startswith("http"):
                            result_urls.append(val)

                    # 중복 제거 및 유효 url 필터링
                    valid_urls = [u for u in result_urls if isinstance(u, str) and u.startswith("http")]

                    if valid_urls:
                        video_url = valid_urls[0]
                        print(f"[Kie Video Success] 비디오 생성 완료! 다운로드 중: {video_url}")
                        v_res = requests.get(video_url, stream=True, timeout=60)
                        if v_res.status_code == 200:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                for chunk in v_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            print(f"[Kie Video Saved] 저장 완료: {output_path}")
                            return output_path
                        else:
                            print(f"[Kie Video Warn] 비디오 다운로드 실패 (HTTP {v_res.status_code}): {video_url}")
                    else:
                        print(f"[Kie Video Warn] 상태는 success이나 비디오 URL을 찾을 수 없습니다. 응답: {bdata}")
                    err_msg = bdata.get("msg") or bdata.get("fail_reason") or body.get("msg")
                    print(f"[Kie Video Fail] 비디오 생성 실패: {err_msg}")
                    return None

            except Exception as poll_err:
                print(f"[Kie Video Polling Warn] 상태 확인 중 일시 오류: {poll_err}")
                continue

        print(f"[Kie Video Timeout] 비디오 생성 대기 시간이 초과되었습니다 (Task: {task_id})")
        return None
