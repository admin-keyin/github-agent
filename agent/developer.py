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

def call_ollama(prompt):
    """Local Ollama API 호출"""
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\n반드시 다른 설명 없이 순수 JSON 형식으로만 답변하세요.",
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        res_json = response.json()
        
        if response.status_code == 200:
            raw_text = res_json.get('response', '')
            return parse_json_garbage(raw_text)
        else:
            error_msg = res_json.get('error', 'Unknown Error')
            print(f"❌ Ollama 호출 실패 (HTTP {response.status_code}): {error_msg}")
            raise Exception(f"HTTP {response.status_code} - {error_msg}")
    except Exception as e:
        print(f"❌ Ollama 연결 에러: {str(e)}")
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
        plan_prompt = f"당신은 시니어 개발자입니다. 다음 요구사항의 해결 계획을 JSON으로 답변하세요.\n요구사항: {subject} / {body}\n구조: {context}\n형식: {{\"explanation\": \"...\", \"new_branch\": \"...\"}}"
        plan_raw = call_ollama(plan_prompt)
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan['explanation']}")
        
        # Ollama는 로컬 실행이므로 Gemini와 달리 대기 시간이 크게 필요하지 않을 수 있음
        time.sleep(2)

        # 2. 구현
        implementation_prompt = f"다음 전략에 따라 코드를 작성하세요.\n전략: {plan['explanation']}\n요구사항: {subject}\n반드시 전체 파일 내용을 포함한 JSON으로 응답하세요.\n형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\", \"action\": \"update\" }}]}}"
        implementation_raw = call_ollama(implementation_prompt)
        implementation = json.loads(implementation_raw)
        
        for change in implementation.get('changes', []):
            path = change['path']
            print(f"🛠 파일 수정 중: {path}")
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 3. Git 작업
        run_command("git config user.name 'github-actions[bot]'")
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'")
        run_command("git add .")
        run_command(f'git commit -m "feat: {subject}"')
        
        branch_name = f"agent/task-{os.urandom(2).hex()}"
        run_command(f"git checkout -b {branch_name}")
        run_command(f"git push origin {branch_name}")
        
        print(f"✅ 작업 완료: {branch_name}")
        update_task_status("completed", branch_name=branch_name)

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
