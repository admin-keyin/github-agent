import os
import requests
import json
import subprocess
import traceback
import time
import re

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def update_task_status(status, branch_name=None):
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID:
        return
    url = f"{SUPABASE_URL}/rest/v1/agent_tasks?id=eq.{TASK_ID}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {"status": status}
    if branch_name:
        data["branch_name"] = branch_name
    try:
        requests.patch(url, headers=headers, json=data, timeout=10)
    except:
        pass

def parse_json_garbage(text):
    """Ollama가 응답에 섞어놓은 마크다운 코드 블록 등을 제거하고 순수 JSON만 추출"""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def call_ollama(prompt, retry=1):
    """Local Ollama API 호출"""
    url = f"{OLLAMA_HOST}/api/generate"
    
    # JSON 강제 옵션 제거 (일부 모델에서 빈 응답 유발 가능)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 출력하세요.",
        "stream": False
        # "format": "json"  <-- 제거
    }
    
    try:
        print(f"📡 Ollama 요청 중... (Model: {OLLAMA_MODEL})")
        response = requests.post(url, json=payload, timeout=180)
        res_json = response.json()
        
        if response.status_code == 200:
            raw_text = res_json.get('response', '')
            if not raw_text.strip():
                if retry > 0:
                    print(f"⚠️ 빈 응답 수신. 재시도 중... (남은 횟수: {retry})")
                    time.sleep(2)
                    return call_ollama(prompt, retry - 1)
                raise Exception("Empty response from Ollama after retries")
            
            print(f"📥 Ollama 응답 수신 (길이: {len(raw_text)})")
            return parse_json_garbage(raw_text)
        else:
            error_msg = res_json.get('error', 'Unknown Error')
            raise Exception(f"HTTP {response.status_code} - {error_msg}")
    except Exception as e:
        if retry > 0:
            print(f"❌ 에러 발생 ({str(e)}). 재시도 중...")
            time.sleep(2)
            return call_ollama(prompt, retry - 1)
        raise e

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def get_repo_context():
    tree, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'")
    return tree

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "No Body")
    
    print(f"🚀 작업 시작 (Ollama Mode): {subject}")
    update_task_status("running")
    
    try:
        context = get_repo_context()
        
        # 1. 전략 수립
        plan_prompt = f"""당신은 시니어 개발자입니다. 다음 요구사항의 해결 계획을 JSON으로 답변하세요.
요구사항: {subject} / {body}
파일 구조: {context}

반드시 다음 JSON 형식을 엄격히 지켜서 답변하세요:
{{
  "explanation": "작업 계획 설명",
  "new_branch": "기능구현_브랜치명"
}}"""
        plan_raw = call_ollama(plan_prompt)
        print(f"DEBUG: Raw Plan: {plan_raw}")
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan['explanation']}")
        
        time.sleep(1)

        # 2. 구현
        implementation_prompt = f"""다음 전략에 따라 코드를 작성하세요.
전략: {plan['explanation']}
요구사항: {subject} / {body}

반드시 다음 JSON 형식을 엄격히 지켜서 전체 파일 내용을 포함해 답변하세요:
{{
  "changes": [
    {{
      "path": "./path/to/file.js",
      "content": "전체 파일 내용...",
      "action": "update"
    }}
  ]
}}
**중요: 경로는 반드시 './'로 시작하는 상대 경로여야 합니다.**"""
        implementation_raw = call_ollama(implementation_prompt)
        print(f"DEBUG: Raw Implementation: {implementation_raw}")
        implementation = json.loads(implementation_raw)
        
        for change in implementation.get('changes', []):
            path = change['path'].lstrip('/') # 절대 경로 방지 (앞의 / 제거)
            # 프로젝트 외부 경로 접근 방지 (.. 제거 등)
            path = os.path.normpath(path).replace("../", "")
            
            print(f"🛠 파일 수정 중: {path}")
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        print(f"✅ 파일 수정 완료")
        update_task_status("completed")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
