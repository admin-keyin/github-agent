import os
import requests
import json
import subprocess
import traceback

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")

# 여러 개의 Gemini API 키 리스트로 관리 (Fallback Mechanism)
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2")
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

def update_task_status(status, branch_name=None):
    """Supabase REST API를 통해 상태를 업데이트합니다."""
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID:
        print(f"⚠️ 상태 업데이트 스킵 (환경변수 부족): URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}, ID={bool(TASK_ID)}")
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
        res = requests.patch(url, headers=headers, json=data, timeout=10)
        print(f"📡 상태 업데이트 완료: {status} (HTTP {res.status_code})")
    except Exception as e:
        print(f"❌ 상태 업데이트 실패: {e}")

def call_gemini(prompt):
    """Google Gemini API 호출 (키 자동 전환 기능 포함)"""
    last_error = None
    
    for i, api_key in enumerate(GEMINI_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            res_json = response.json()
            
            if response.status_code == 200:
                return res_json['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                print(f"⚠️ API 키 {i+1}번 사용량 초과. 다음 키로 전환합니다...")
                continue
            else:
                print(f"❌ API 키 {i+1}번 에러 ({response.status_code}): {res_json}")
                last_error = res_json
                continue
        except Exception as e:
            print(f"⚠️ API 키 {i+1}번 호출 중 예외 발생: {e}")
            last_error = e
            continue
            
    raise Exception(f"모든 Gemini API 키가 실패했습니다. 마지막 에러: {last_error}")

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def get_repo_context():
    """파일 구조 추출 (GitHub Actions 환경 최적화)"""
    tree, _ = run_command("find . -maxdepth 3 -not -path '*/.*' -not -path './node_modules*'")
    return tree

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "No Body")
    
    print(f"🚀 작업 시작 (Cloud Mode): {subject}")
    update_task_status("running")
    
    try:
        # 1. 컨텍스트 파악
        context = get_repo_context()
        
        # 2. 에이전트 전략 수립
        plan_prompt = f"""
        당신은 시니어 풀스택 개발자입니다. 다음 요구사항을 해결하기 위한 상세 계획을 JSON으로 답변하세요.
        요구사항: {subject} / {body}
        현재 프로젝트 구조:
        {context}
        
        응답 형식:
        {{
          "explanation": "작업 전략 설명",
          "new_branch": "agent/feature-task"
        }}
        """
        plan_raw = call_gemini(plan_prompt)
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan['explanation']}")
        
        # 3. 브랜치 생성
        branch_name = f"agent/task-{os.urandom(4).hex()}"
        run_command(f"git checkout -b {branch_name}")

        # 4. 파일 구현
        implementation_prompt = f"""
        요구사항: {subject} / {body}
        전략: {plan['explanation']}
        현재 프로젝트 구조: {context}
        
        위 내용을 바탕으로 실제 코딩을 수행하세요. 반드시 전체 파일 내용을 포함한 JSON으로 응답하세요.
        응답 형식:
        {{
          "changes": [
            {{"path": "경로", "content": "전체 코드", "action": "create|update"}}
          ]
        }}
        """
        implementation_raw = call_gemini(implementation_prompt)
        implementation = json.loads(implementation_raw)
        
        for change in implementation.get('changes', []):
            path = change['path']
            print(f"🛠  파일 수정 중: {path}")
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 5. Git 커밋 & 푸시
        run_command("git config user.name 'github-actions[bot]'")
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'")
        run_command("git add .")
        run_command(f'git commit -m "feat: {subject}"')
        run_command(f"git push origin {branch_name}")
        
        print(f"✅ 작업 완료! 브랜치: {branch_name}")
        update_task_status("completed", branch_name=branch_name)

    except Exception as e:
        print(f"❌ 에이전트 실행 중 오류 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
