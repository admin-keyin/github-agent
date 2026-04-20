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

GEMINI_MODEL = "gemini-2.5-flash-lite"

def update_task_status(status, branch_name=None, pr_url=None):
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID:
        return
    url = f"{SUPABASE_URL}/rest/v1/agent_tasks?id=eq.{TASK_ID}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    data = {"status": status}
    if branch_name: data["branch_name"] = branch_name
    if pr_url: data["pr_url"] = pr_url
    try: requests.patch(url, headers=headers, json=data, timeout=10)
    except: pass

def run_command_list(args, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    env["GEMINI_CLI_NON_INTERACTIVE"] = "true"
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_repo_contents(work_dir):
    """주요 파일들의 실제 내용을 수집하여 AI에게 전달"""
    context = ""
    for root, _, files in os.walk(work_dir):
        if any(x in root for x in ['node_modules', '.git', '.next']): continue
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.json', '.md')):
                rel_path = os.path.relpath(os.path.join(root, file), work_dir)
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        context += f"\n-- File: {rel_path} --\n{content}\n"
                except: pass
    return context

def clean_json_output(text):
    code_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_blocks: return code_blocks[-1].strip()
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match: return json_match.group(1).strip()
    return text.strip()

def call_gemini_cli(prompt, phase_name="Thinking"):
    print(f"🧠 Gemini가 {phase_name} 중...")
    full_prompt = f"System: 당신은 세계 최고의 시니어 풀스택 개발자입니다. 코드를 생략하거나 '나머지 코드 생략'과 같은 주석을 절대 사용하지 마세요. 모든 파일은 즉시 프로덕션에 배포 가능한 수준으로 완벽하게 작성해야 합니다.\n\nUser: {prompt}\n\n응답은 반드시 JSON 형식을 엄격히 지켜야 합니다."
    cmd = ["gemini", "-m", GEMINI_MODEL, "--raw-output", "--yolo", "-p", full_prompt]
    
    start_time = time.time()
    stdout, stderr, code = run_command_list(cmd)
    if code != 0: return {}
    
    try:
        cleaned = clean_json_output(stdout)
        result = json.loads(cleaned)
        print(f"✅ {phase_name} 완료! ({time.time() - start_time:.1f}초)")
        return result
    except:
        print(f"❌ {phase_name} 파싱 실패. 원본: {stdout[:200]}...")
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

    print(f"🚀 [고품질 모드] 에이전트 가동: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. Google 검색
        search_results = requests.post("https://google.serper.dev/search", headers={'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}, json={"q": f"Next.js professional dashboard with circular graphs recharts guide {subject}"}).json()
        search_data = "\n".join([f"- {i['title']}: {i['snippet']}" for i in search_results.get('organic', [])[:3]])

        # 2. 클론 및 컨텍스트 수집
        run_command_list(["git", "clone", auth_url, work_dir])
        repo_context = get_repo_contents(work_dir)
        
        # 3. 전략 수립 (사양서 작성)
        plan_prompt = f"현재 코드:\n{repo_context}\n\n검색 정보:\n{search_data}\n\n요구사항: {subject} / {body}\n구현할 파일 목록과 구체적인 로직을 포함한 계획을 JSON으로 작성하세요. 형식: {{\"explanation\": \"...\"}}"
        plan = call_gemini_cli(plan_prompt, "전략 수립")
        spec = plan.get('explanation', '')

        # 4. 고품질 구현 (강력한 지시)
        impl_prompt = f"사양서: {spec}\n요구사항: {subject}\n\n" + \
                      "위 사양서에 따라 전체 코드를 작성하세요. 절대 샘플 코드가 아닌 '실제 완성된 코드'여야 합니다.\n" + \
                      "1. 원형 그래프는 'recharts' 또는 'chart.js'를 사용하여 화려하게 구현하세요.\n" + \
                      "2. package.json에 필요한 의존성을 모두 추가하세요.\n" + \
                      "3. 필요한 모든 신규 파일을 생성하고 기존 파일을 업데이트하세요.\n" + \
                      "형식: {\"changes\": [{\"path\": \"경로\", \"content\": \"전체코드\"}]}"
        impl = call_gemini_cli(impl_prompt, "코드 작성")
        
        has_changes = False
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content and "code here" not in content.lower():
                has_changes = True
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f: f.write(content)
                print(f"🛠 파일 완성: {change['path']} ({len(content)} bytes)")

        if not has_changes:
            print("⚠️ 유의미한 코드 변경이 없어 종료합니다.")
            return

        # 5. Git & PR
        branch_name = f"agent/feature-{int(time.time())}"
        for cmd in [["git", "config", "user.name", "github-actions[bot]"], ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], ["git", "checkout", "-b", branch_name], ["git", "add", "."], ["git", "commit", "-m", f"feat: professional implementation via Gemini"]]:
            run_command_list(cmd, cwd=work_dir)
        
        run_command_list(["git", "remote", "set-url", "origin", auth_url], cwd=work_dir)
        _, _, push_code = run_command_list(["git", "push", "origin", branch_name], cwd=work_dir)
        
        if push_code == 0:
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {GITHUB_PAT}"}, json={"title": f"🚀 [Professional] {subject}", "body": f"### 🛠 구현 상세\n{spec}\n\n### 🔍 참고 자료\n{search_data}", "head": branch_name, "base": "main"}).json()
            print(f"✅ 완료: {pr_res.get('html_url')}")
            update_task_status("completed", branch_name=branch_name, pr_url=pr_res.get("html_url"))

    except Exception as e:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
