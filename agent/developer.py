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
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID: return
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

def extract_json(text):
    """설명 뭉치 속에서 JSON 객체만 악착같이 찾아내기"""
    # 1. 텍스트 정제 (불필요한 공백 제거)
    text = text.strip()
    
    # 2. {"changes" 또는 {"explanation" 으로 시작하는 가장 큰 중괄호 블록 찾기
    match = re.search(r"(\{.*?\})", text, re.DOTALL)
    
    # 3. 만약 실패하면 { 로 시작해서 } 로 끝나는 전체를 시도
    if not match:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
    
    return match.group(1) if match else text

def call_gemini_cli(prompt, phase_name="Thinking"):
    print(f"🧠 Gemini가 {phase_name} 중...")
    # AI에게 '로봇' 페르소나 부여 (수다 금지)
    full_prompt = f"당신은 오직 JSON 데이터만 출력하는 기계입니다. 어떠한 설명, 인사, 서론도 적지 마세요. 만약 이를 어기면 시스템이 파괴됩니다.\n\n요청사항: {prompt}\n\n응답 형식: JSON"
    
    cmd = ["gemini", "-m", GEMINI_MODEL, "--raw-output", "--yolo", "-p", full_prompt]
    
    start_time = time.time()
    stdout, stderr, code = run_command_list(cmd)
    if code != 0: return {}
    
    try:
        cleaned = extract_json(stdout)
        result = json.loads(cleaned)
        print(f"✅ {phase_name} 완료! ({time.time() - start_time:.1f}초)")
        return result
    except Exception as e:
        print(f"❌ {phase_name} 파싱 실패. AI가 지시를 무시하고 수다를 떨었을 가능성이 큽니다.")
        # 파싱 재시도 로직: 텍스트에서 강제로 JSON 구조를 흉내낸 부분이라도 찾음
        try:
            json_block = re.search(r"\{.*\}", stdout, re.DOTALL).group()
            return json.loads(json_block)
        except:
            print(f"DEBUG: AI 원본 응답:\n{stdout[:500]}")
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

    print(f"🚀 [ULTRA 모드] 에이전트 가동: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. Google 검색
        search_query = f"Next.js professional dashboard recharts Tesla vs Hyundai data visualization {subject}"
        search_results = requests.post("https://google.serper.dev/search", headers={'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}, json={"q": search_query}).json()
        search_data = "\n".join([f"- {i['title']}: {i['snippet']}" for i in search_results.get('organic', [])[:3]])

        # 2. 클론 및 컨텍스트 수집
        run_command_list(["git", "clone", auth_url, work_dir])
        repo_context = get_repo_contents(work_dir)
        
        # 3. 전략 수립 (사양서)
        plan_prompt = f"현재코드:\n{repo_context}\n검색정보:\n{search_data}\n요구사항: {subject} / {body}\n\n위 내용을 바탕으로 구현할 파일과 로직을 JSON으로 작성하세요. 형식: {{\"explanation\": \"...\"}}"
        plan = call_gemini_cli(plan_prompt, "전략 수립")
        spec = plan.get('explanation', '작업을 진행합니다.')

        # 4. 구현 (절대 생략 금지)
        impl_prompt = f"사양서: {spec}\n요구사항: {subject}\n\n**필수:** 'changes' 리스트 안에 모든 파일의 '전체 소스 코드'를 넣으세요. placeholder나 생략 주석을 쓰면 실패 처리됩니다. 테슬라와 현대차의 가짜 판매량 데이터를 포함한 리차트(recharts) 코드를 작성하세요. 형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\" }}]}}"
        impl = call_gemini_cli(impl_prompt, "코드 작성")
        
        changes = impl.get('changes', [])
        has_real_changes = False
        for change in changes:
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content and len(content) > 50: # 유의미한 길이 체크
                has_real_changes = True
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f: f.write(content)
                print(f"🛠 파일 완성: {change['path']} ({len(content)} bytes)")

        if not has_real_changes:
            raise Exception("AI가 유의미한 코드를 생성하지 않았습니다. (생략 또는 빈 응답)")

        # 5. Git & PR
        branch_name = f"agent/dashboard-{int(time.time())}"
        for cmd in [["git", "config", "user.name", "github-actions[bot]"], ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], ["git", "checkout", "-b", branch_name], ["git", "add", "."], ["git", "commit", "-m", f"feat: pro dashboard with Tesla/Hyundai charts"]]:
            run_command_list(cmd, cwd=work_dir)
        
        run_command_list(["git", "remote", "set-url", "origin", auth_url], cwd=work_dir)
        _, _, push_code = run_command_list(["git", "push", "origin", branch_name], cwd=work_dir)
        
        if push_code == 0:
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {GITHUB_PAT}"}, json={"title": f"🚀 [Dashboard] {subject}", "body": f"### 📊 구현 내용\n{spec}\n\n### 🔍 참고 자료\n{search_data}", "head": branch_name, "base": "main"}).json()
            print(f"✅ 완료: {pr_res.get('html_url')}")
            update_task_status("completed", branch_name=branch_name, pr_url=pr_res.get("html_url"))

    except Exception as e:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
