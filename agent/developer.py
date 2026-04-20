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

# 최신 Gemini 2.5 Flash-Lite 모델 강제 지정
GEMINI_MODEL = "gemini-2.5-flash-lite"

def update_task_status(status, branch_name=None, pr_url=None):
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID:
        return
    url = f"{SUPABASE_URL}/rest/v1/agent_tasks?id=eq.{TASK_ID}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + str(SUPABASE_KEY),
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {"status": status}
    if branch_name: data["branch_name"] = branch_name
    if pr_url: data["pr_url"] = pr_url
    try:
        requests.patch(url, headers=headers, json=data, timeout=10)
    except: pass

def run_command(command, cwd=None):
    print(f"Executing: {command}")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    # Gemini CLI용 추가 환경 변수 (IDE 연동 에러 방지)
    env["GEMINI_CLI_NON_INTERACTIVE"] = "true"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def search_google(query):
    if not SERPER_API_KEY: return "검색 키 없음"
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.post(url, headers=headers, json={"q": query, "num": 5}, timeout=10)
        items = res.json().get('organic', [])
        return "\n".join([f"- {i['title']}: {i['snippet']}" for i in items])
    except: return "검색 실패"

def call_gemini_cli(prompt, phase_name="Thinking"):
    """로컬에 로그인된 gemini CLI를 호출 (최신 모델 고정)"""
    print(f"🧠 Gemini ({GEMINI_MODEL})가 {phase_name} 중...")
    
    full_prompt = f"{prompt}\n\n결과는 반드시 다른 설명 없이 순수 JSON 데이터만 반환하세요."
    
    prompt_path = "/tmp/gemini_prompt.txt"
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(full_prompt)
    
    # --raw-output과 --prompt를 사용하여 비대화형 모드로 실행
    cmd = f"gemini -m {GEMINI_MODEL} --raw-output -p \"$(cat {prompt_path})\""
    
    start_time = time.time()
    stdout, stderr, code = run_command(cmd)
    
    if code != 0:
        # 에러 로그에서 불필요한 IDE 에러는 스킵하고 진짜 에러만 출력
        if "ModelNotFoundError" in stderr:
            print(f"❌ 모델 {GEMINI_MODEL}을 찾을 수 없습니다. CLI 버전을 확인하세요.")
        else:
            print(f"❌ Gemini CLI 호출 실패: {stderr[:200]}...")
        return {}
    
    try:
        # JSON 추출 로직 강화
        json_match = re.search(r"(\{.*\})", stdout, re.DOTALL)
        if json_match:
            clean_json = json_match.group(1).strip()
            result = json.loads(clean_json)
            print(f"✅ {phase_name} 완료! ({time.time() - start_time:.1f}초)")
            return result
        else:
            print(f"⚠️ JSON 형식을 찾을 수 없습니다. 원본: {stdout[:100]}...")
            return {}
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return {}

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
        search_results = search_google(f"Latest Next.js 15 best practices for {subject}")

        # 2. 클론
        run_command(f"git clone {auth_url} {work_dir}")
        
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
                if isinstance(content, (dict, list)): content = json.dumps(content, indent=2)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f: f.write(content)

        # 5. 푸시 및 PR
        branch_name = f"agent/gemini-25-{int(time.time())}"
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f"git commit -m 'feat: updated via {GEMINI_MODEL}'", cwd=work_dir)
        run_command(f"git remote set-url origin {auth_url}", cwd=work_dir)
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code == 0:
            pr_data = {
                "title": f"🚀 [{GEMINI_MODEL}] {subject}",
                "body": f"### 💡 구현 내용\n{explanation}\n\n### 🔍 검색 참고\n{search_results}",
                "head": branch_name, "base": "main"
            }
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", 
                                   headers={"Authorization": f"token {GITHUB_PAT}"},
                                   json=pr_data).json()
            update_task_status("completed", branch_name=branch_name, pr_url=pr_res.get("html_url"))
            print(f"✅ 성공: {pr_res.get('html_url')}")
        else:
            raise Exception(f"푸시 실패: {err}")

    except Exception as e:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
