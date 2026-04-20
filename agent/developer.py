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
    print(f"Executing: {' '.join(args)}")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    env["GEMINI_CLI_NON_INTERACTIVE"] = "true"
    
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def clean_json_output(text):
    """설명이 섞인 텍스트에서 JSON 블록만 정밀하게 추출"""
    # 1. ```json ... ``` 또는 ``` ... ``` 블록 우선 추출
    code_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1].strip() # 가장 마지막 블록 반환
    
    # 2. { ... } 형태의 가장 큰 블록 찾기
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    return text.strip()

def call_gemini_cli(prompt, phase_name="Thinking"):
    print(f"🧠 Gemini ({GEMINI_MODEL})가 {phase_name} 중...")
    
    # 지시사항 강화: 서론/결론 금지
    full_prompt = f"System: 당신은 시니어 개발자입니다. 절대 친절한 설명이나 서론을 적지 마세요. 오직 요청한 JSON 데이터만 출력하세요.\n\nUser: {prompt}\n\n결과는 반드시 쌍따옴표(\")를 사용한 순수 JSON이어야 합니다."
    
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
        print(f"DEBUG: AI 응답 원본 (첫 300자):\n{stdout[:300]}...")
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

    print(f"🚀 Gemini 2.5 고품질 에이전트 시작: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. Google 검색
        search_results = search_google(f"Latest React components and best practices for {subject}")

        # 2. 클론
        run_command_list(["git", "clone", auth_url, work_dir])
        
        # 3. 전략 수립
        plan_prompt = f"참고자료:\n{search_results}\n\n요구사항: {subject}\n본문: {body}\n구현 계획을 JSON으로 작성하세요. 형식: {{\"explanation\": \"...\"}}"
        plan = call_gemini_cli(plan_prompt, "전략 수립")
        explanation = plan.get('explanation', '작업 진행')

        # 4. 구현
        impl_prompt = f"전략: {explanation}\n요구사항: {subject}\n전체 소스 코드를 포함한 JSON 형식으로 작성하세요. 형식: {{\"changes\": [{{\"path\": \"...\", \"content\": \"...\"}}]}}"
        impl = call_gemini_cli(impl_prompt, "코드 작성")
        
        has_changes = False
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content:
                has_changes = True
                if isinstance(content, (dict, list)): content = json.dumps(content, indent=2, ensure_ascii=False)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f: f.write(content)
                print(f"🛠 파일 수정됨: {change['path']} ({len(content)} bytes)")

        if not has_changes:
            print("⚠️ 변경된 사항이 없어 작업을 중단합니다.")
            update_task_status("completed", pr_url="변경 사항 없음")
            return

        # 5. Git 작업 및 푸시
        branch_name = f"agent/gemini-fix-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "github-actions[bot]"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=work_dir)
        run_command_list(["git", "checkout", "-b", branch_name], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        
        # 변경사항 실제 존재 확인
        diff_out, _, _ = run_command_list(["git", "diff", "--staged"], cwd=work_dir)
        if not diff_out:
            print("⚠️ 커밋할 내용이 없습니다.")
            update_task_status("completed", pr_url="커밋 내용 없음")
            return

        run_command_list(["git", "commit", "-m", f"feat: improved via {GEMINI_MODEL}"], cwd=work_dir)
        run_command_list(["git", "remote", "set-url", "origin", auth_url], cwd=work_dir)
        
        print(f"📡 푸시 중: {branch_name}")
        _, _, push_code = run_command_list(["git", "push", "origin", branch_name], cwd=work_dir)
        
        if push_code == 0:
            # 6. PR 생성
            print(f"🚀 PR 생성 중 (Base: main)")
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", 
                                   headers={"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github+json"},
                                   json={
                                       "title": f"🚀 [Gemini] {subject}",
                                       "body": f"### 💡 구현 내용\n{explanation}\n\n### 🔍 참고 자료\n{search_results}",
                                       "head": branch_name, "base": "main"
                                   }).json()
            
            if "html_url" in pr_res:
                final_url = pr_res["html_url"]
                print(f"✅ 성공: {final_url}")
                update_task_status("completed", branch_name=branch_name, pr_url=final_url)
            else:
                print(f"❌ PR 생성 실패: {pr_res.get('message')}")
                update_task_status("completed", branch_name=branch_name, pr_url="PR 생성 실패")
        else:
            raise Exception("푸시 실패")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
