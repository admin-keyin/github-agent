import os
import requests
import json
import subprocess
import traceback
import time
import re
import shutil

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT = os.getenv("GITHUB_PAT")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 최신 Gemini 2.5 모델
GEMINI_MODEL = "gemini-2.5-flash-lite"

def update_task_status(status, branch_name=None, pr_url=None):
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID:
        return
    url = f"{SUPABASE_URL}/rest/v1/agent_tasks?id=eq.{TASK_ID}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"status": status}
    if branch_name: data["branch_name"] = branch_name
    if pr_url: data["pr_url"] = pr_url
    try:
        requests.patch(url, headers=headers, json=data, timeout=10)
    except: pass

def run_command_list(args, cwd=None):
    """리스트 형태의 인자로 명령어를 실행 (안전함)"""
    print(f"Executing: {' '.join(args)}")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    env["GEMINI_CLI_NON_INTERACTIVE"] = "true"
    
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"❌ Command Failed: {result.stderr}")
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def clean_json_output(text):
    """응답에서 순수 JSON만 추출하고 정제"""
    # 1. 마크다운 코드 블록 제거
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    # 2. { 로 시작해서 } 로 끝나는 가장 큰 블록 찾기
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        # 3. 제어 문자(줄바꿈 제외) 제거
        json_str = "".join(c for c in json_str if ord(c) >= 32 or c in "\n\r\t")
        return json_str
    return text

def call_gemini_cli(prompt, phase_name="Thinking"):
    print(f"🧠 Gemini ({GEMINI_MODEL})가 {phase_name} 중...")
    
    full_prompt = f"{prompt}\n\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 반환하세요. 키와 값에는 반드시 쌍따옴표(\")를 사용하세요."
    
    # CLI 호출 (리스트 방식 사용으로 따옴표 문제 해결)
    cmd = ["gemini", "-m", GEMINI_MODEL, "--raw-output", "--yolo", "-p", full_prompt]
    
    start_time = time.time()
    stdout, stderr, code = run_command_list(cmd)
    
    if code != 0:
        print(f"❌ Gemini CLI 호출 실패: {stderr[:200]}")
        return {}
    
    cleaned = clean_json_output(stdout)
    try:
        result = json.loads(cleaned)
        print(f"✅ {phase_name} 완료! ({time.time() - start_time:.1f}초)")
        return result
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {str(e)[:50]}")
        print(f"DEBUG: 원본 응답 요약: {stdout[:200]}...")
        # 최후의 수단: 싱글 쿼테이션 등을 교체 시도 (필요 시)
        return {}

def search_google(query):
    if not SERPER_API_KEY: return "검색 키 없음"
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.post(url, headers=headers, json={"q": query, "num": 5}, timeout=10)
        items = res.json().get('organic', [])
        return "\n".join([f"- {i['title']}: {i['snippet']}" for i in items])
    except: return "검색 실패"

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    
    git_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    if not git_match: return
        
    repo_full_name = git_match.group(1).replace(".git", "")
    auth_url = f"https://oauth2:{GITHUB_PAT}@github.com/{repo_full_name}.git"
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 Gemini 2.5 기반 에이전트 시작: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. Google 검색
        search_results = search_google(f"Latest Next.js 15, Tailwind v4 best practices for {subject}")

        # 2. 클론
        run_command_list(["git", "clone", auth_url, work_dir])
        
        # 3. 전략 수립
        plan_prompt = f"참고자료:\n{search_results}\n\n요구사항: {subject}\n본문: {body}\n파일 구조를 고려한 구현 계획을 JSON으로 작성하세요. 형식: {{\"explanation\": \"...\"}}"
        plan = call_gemini_cli(plan_prompt, "전략 수립")
        explanation = plan.get('explanation', '작업 진행')

        # 4. 구현
        impl_prompt = f"전략: {explanation}\n요구사항: {subject}\n전체 소스 코드를 포함한 JSON 형식으로 작성하세요. 형식: {{\"changes\": [{{\"path\": \"...\", \"content\": \"...\"}}]}}"
        impl = call_gemini_cli(impl_prompt, "코드 작성")
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content:
                if isinstance(content, (dict, list)): content = json.dumps(content, indent=2, ensure_ascii=False)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f: f.write(content)

        # 5. Git 푸시
        branch_name = f"agent/gemini-25-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "github-actions[bot]"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=work_dir)
        run_command_list(["git", "checkout", "-b", branch_name], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: high quality update via {GEMINI_MODEL}"], cwd=work_dir)
        run_command_list(["git", "remote", "set-url", "origin", auth_url], cwd=work_dir)
        
        print(f"📡 타겟 레포지토리로 브랜치 푸시 중: {branch_name}")
        _, push_err, push_code = run_command_list(["git", "push", "origin", branch_name], cwd=work_dir)
        
        if push_code == 0:
            # 6. PR 생성 (Target: main)
            print(f"🚀 PR 생성 요청 중: {repo_full_name} (Base: main)")
            pr_api_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
            headers = {
                "Authorization": f"token {GITHUB_PAT}",
                "Accept": "application/vnd.github+json"
            }
            pr_data = {
                "title": f"🚀 [Gemini] {subject}",
                "body": f"### 💡 구현 계획\n{explanation}\n\n### 🔍 기술 정보\n{search_results}\n\n---\n*이 PR은 AI 에이전트에 의해 자동 생성되었습니다.*",
                "head": branch_name,
                "base": "main" # 메인 브랜치 대상
            }
            
            pr_res = requests.post(pr_api_url, headers=headers, json=pr_data).json()
            
            if "html_url" in pr_res:
                final_pr_url = pr_res["html_url"]
                print(f"✅ PR 생성 성공: {final_pr_url}")
                update_task_status("completed", branch_name=branch_name, pr_url=final_pr_url)
            else:
                error_msg = pr_res.get('message', '알 수 없는 에러')
                print(f"❌ PR 생성 실패: {error_msg}")
                # 이미 PR이 있거나 변경사항이 없는 경우를 위해 상세 로깅
                if "errors" in pr_res:
                    print(f"상세 에러: {json.dumps(pr_res['errors'])}")
                update_task_status("completed", branch_name=branch_name, pr_url="PR 생성 실패")
        else:
            raise Exception(f"푸시 실패: {push_err}")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
