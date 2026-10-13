"""
Kie.ai Wan 3.0 / Wan 2.6 기반 지브리풍 감성 비디오 생성 클라이언트 모듈.
- 가사 서사(기승전결)에 맞춘 고화질 애니메이션 비디오 생성 (480P 경제 모드 지원)
- 비디오 생성 실패 또는 키 미제공 시 안전한 폴백 지원
"""

import os
import time
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

        # 지브리 특유의 2D 감성 수채화 애니메이션 프롬프트 강화
        ghibli_prompt = (
            f"Studio Ghibli aesthetic, anime animation style, masterpiece, {prompt}, "
            f"Hayao Miyazaki direction, soft pastel watercolor texture, gentle natural motion, "
            f"cinematic lighting, hand-drawn anime aesthetic, warm emotional atmosphere, 24fps smooth motion, no watermark"
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
                    # 결과 URL 추출
                    result_urls = []
                    info = bdata.get("info") or {}
                    if isinstance(info, dict) and info.get("resultUrls"):
                        result_urls = info.get("resultUrls")
                    elif bdata.get("resultUrls"):
                        result_urls = bdata.get("resultUrls")
                    elif bdata.get("video_url"):
                        result_urls = [bdata.get("video_url")]
                    elif bdata.get("url"):
                        result_urls = [bdata.get("url")]

                    if result_urls and len(result_urls) > 0:
                        video_url = result_urls[0]
                        print(f"[Kie Video Success] 비디오 생성 완료! 다운로드 중: {video_url}")
                        v_res = requests.get(video_url, stream=True, timeout=60)
                        if v_res.status_code == 200:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                for chunk in v_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            print(f"[Kie Video Saved] 저장 완료: {output_path}")
                            return output_path

                elif state in ["fail", "failed", "error"]:
                    err_msg = bdata.get("msg") or bdata.get("fail_reason") or body.get("msg")
                    print(f"[Kie Video Fail] 비디오 생성 실패: {err_msg}")
                    return None

            except Exception as poll_err:
                print(f"[Kie Video Polling Warn] 상태 확인 중 일시 오류: {poll_err}")
                continue

        print(f"[Kie Video Timeout] 비디오 생성 대기 시간이 초과되었습니다 (Task: {task_id})")
        return None
