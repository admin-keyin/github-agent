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

class KieVideoGenerator:
    def __init__(self):
        self.kie_api_key = os.getenv("KIE_API_KEY", "").strip()

    def has_api_key(self) -> bool:
        return bool(self.kie_api_key)

    def generate_video_clip(
        self,
        prompt: str,
        duration: int = 15,
        resolution: str = "480p",
        aspect_ratio: str = "16:9",
        output_path: str = ""
    ) -> Optional[str]:
        """
        Kie.ai의 Wan 비디오 모델을 호출하여 비디오 클립을 생성하고 다운로드합니다.
        duration: 5~30초 (단일 씬)
        resolution: "480p" (가장 경제적이고 효율적)
        """
        if not self.has_api_key():
            print("[Kie Video Warn] KIE_API_KEY가 설정되지 않아 비디오 생성을 건너뜁니다.")
            return None

        headers = {
            "Authorization": f"Bearer {self.kie_api_key}",
            "Content-Type": "application/json"
        }

        # 배경/풍경은 감성적 수채화 빛감, 인물은 트렌디한 일본 현대 극장판 애니메이션 스타일 (신카이 마코토 / 쿄애니 감성)
        ghibli_prompt = (
            f"modern anime animation aesthetic, Makoto Shinkai style, Kyoto Animation quality, {prompt}, "
            f"gorgeous cinematic lighting, beautifully drawn anime character, delicate face features, "
            f"rich painterly watercolor landscape background, glowing natural atmosphere, 4k master animation, 24fps smooth motion, no watermark"
        )

        create_url = "https://api.kie.ai/api/v1/jobs/createTask"
        
        # Wan 3.0 우선 시도, 실패시 wan 2.6 및 kling 순차 시도
        candidate_models = [
            "wan/3-0-video",
            "wan/2-6-text-to-video",
            "kling-3.0/video"
        ]

        task_id = None
        # Wan 3.0 공식 스펙: resolution="480P", duration=5~30 (정수), audio=True/False
        norm_resolution = resolution.upper() if resolution.lower().endswith("p") else resolution

        for model in candidate_models:
            input_params = {
                "prompt": ghibli_prompt[:2500],
                "duration": int(duration),
                "resolution": norm_resolution,
                "aspect_ratio": aspect_ratio
            }
            if model == "wan/3-0-video":
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
