import os
import requests
import json
import subprocess
import traceback
import time

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")

GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2")
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

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

def call_gemini(prompt):
    """Google Gemini API 호출 (1.5-flash + v1 정식 엔드포인트)"""
    # RPM 제한 방지를 위한 넉넉한 대기
    time.sleep(12) 
    
    last_error = None
    for i, api_key in enumerate(GEMINI_KEYS):
        # v1 정식 엔드포인트와 gemini-1.5-flash는 무료 티어에서 가장 안정적입니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            res_json = response.json()
            
            if response.status_code == 200:
                return res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                error_msg = res_json.get('error', {}).get('message', 'Unknown Error')
                print(f"❌ API 키 {i+1}번 실패 (HTTP {response.status_code}): {error_msg}")
                last_error = f"HTTP {response.status_code} - {error_msg}"
                continue
        except Exception as e:
            last_error = str(e)
            continue
            
    raise Exception(f"모든 Gemini API 키가 실패했습니다.\n사유: {last_error}")

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def get_repo_context():
    tree, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'")
    return tree

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "No Body")
    
    print(f"🚀 작업 시작 (Stable Mode): {subject}")
    update_task_status("running")
    
    try:
        context = get_repo_context()
        
        # 1. 전략 수립
        plan_prompt = f"당신은 시니어 개발자입니다. 다음 요구사항의 해결 계획을 JSON으로 답변하세요.\n요구사항: {subject} / {body}\n구조: {context}\n형식: {{\"explanation\": \"...\", \"new_branch\": \"...\"}}"
        plan_raw = call_gemini(plan_prompt)
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan['explanation']}")
        
        time.sleep(12)

        # 2. 구현
        implementation_prompt = f"다음 전략에 따라 코드를 작성하세요.\n전략: {plan['explanation']}\n요구사항: {subject}\n반드시 전체 파일 내용을 포함한 JSON으로 응답하세요.\n형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\", \"action\": \"update\" }}]}}"
        implementation_raw = call_gemini(implementation_prompt)
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
