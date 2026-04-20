import os
import requests
import json
import subprocess
import traceback
import time
import re
import shutil
from duckduckgo_search import DDGS

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT = os.getenv("GITHUB_PAT")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")

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
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def search_web(query):
    """DuckDuckGo를 통해 웹 검색 수행"""
    print(f"🔍 웹 검색 중: {query}")
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=3)
        if not results: return "검색 결과가 없습니다."
        formatted = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
        return formatted
    except Exception as e:
        print(f"⚠️ 검색 실패: {e}")
        return "검색 결과를 가져오지 못했습니다."

def call_ai(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 답변하세요.",
        "stream": False,
        "format": "json"
    }
    try:
        res = requests.post(OLLAMA_HOST + "/api/generate", json=payload, timeout=600)
        return json.loads(res.json().get('response', '{}'))
    except Exception as e:
        print(f"❌ AI 호출 실패: {e}")
        return {}

def safe_str(data):
    """데이터가 리스트면 합쳐주고, 아니면 문자열로 변환"""
    if isinstance(data, list):
        return " ".join(map(str, data))
    return str(data)

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    
    if not GITHUB_PAT:
        print("🚨 GITHUB_PAT 미설정")
        return
    
    git_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    if not git_match:
        print("❌ URL 미발견")
        return
        
    repo_full_name = git_match.group(1).replace(".git", "")
    auth_url = f"https://oauth2:{GITHUB_PAT}@github.com/{repo_full_name}.git"
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 고품질 작업 시작: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. 웹 검색
        search_query = f"Latest Next.js and Tailwind CSS boilerplate code for {subject}"
        search_results = search_web(search_query)

        # 2. 클론
        run_command(f"git clone {auth_url} {work_dir}")
        
        # 3. 전략 수립
        plan_prompt = f"기술자료:\n{search_results}\n\n요구사항: {subject}\n본문: {body}\n계획을 JSON으로 세우세요. 형식: {{\"explanation\": \"...\"}}"
        plan = call_ai(plan_prompt)
        explanation = safe_str(plan.get('explanation', '작업 진행'))
        print(f"📝 전략: {explanation}")

        # 4. 구현
        impl_prompt = f"전략: {explanation}\n요구사항: {subject}\n전체 소스 코드를 포함한 JSON 형식으로 작성하세요."
        impl = call_ai(impl_prompt)
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content:
                print(f"🛠 파일 수정: {change['path']} ({len(content)} bytes)")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f: f.write(content)

        # 5. 푸시 및 PR
        branch_name = f"agent/feature-{int(time.time())}"
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f"git commit -m 'feat: {subject}'", cwd=work_dir)
        run_command(f"git remote set-url origin {auth_url}", cwd=work_dir)
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code == 0:
            pr_data = {
                "title": f"🚀 [고품질 에이전트] {subject}",
                "body": f"웹 검색 결과가 적용된 코드입니다.\n\n참고한 정보:\n{search_results}",
                "head": branch_name,
                "base": "main"
            }
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", 
                                   headers={"Authorization": f"token {GITHUB_PAT}"},
                                   json=pr_data).json()
            final_url = pr_res.get("html_url", "PR 주소 확인 불가")
            print(f"✅ 성공: {final_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=final_url)
        else:
            raise Exception(f"푸시 실패: {err}")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
