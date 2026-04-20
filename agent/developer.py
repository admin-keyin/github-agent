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
    print("Executing: " + command)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def search_web(query):
    """DuckDuckGo를 통해 웹 검색 수행"""
    print(f"🔍 웹 검색 중: {query}")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            formatted = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
            return formatted
    except Exception as e:
        print(f"⚠️ 검색 실패: {e}")
        return "검색 결과를 가져오지 못했습니다."

def call_ai(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 답변하세요.",
        "stream": False,
        "format": "json"
    }
    try:
        res = requests.post(OLLAMA_HOST + "/api/generate", json=payload, timeout=600)
        return json.loads(res.json().get('response', '{}'))
    except Exception as e:
        print(f"❌ AI 호출 실패: {e}")
        return {}

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
    auth_url = "https://oauth2:" + str(GITHUB_PAT) + "@github.com/" + repo_full_name + ".git"
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 고품질 작업 시작: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. 웹 검색 단계 (기술 조사)
        search_query = f"Latest best practices and boilerplate for {subject} {body[:50]}"
        search_results = search_web(search_query)

        # 2. 클론
        run_command("git clone " + auth_url + " " + work_dir)
        
        # 3. 전략 수립 (검색 결과 반영)
        plan_prompt = f"""당신은 세계 최고의 시니어 개발자입니다. 
다음 검색된 최신 기술 정보를 참고하여 요구사항을 해결하기 위한 완벽한 계획을 세우세요.

[최신 기술 참고자료]
{search_results}

[요구사항]
{subject} / {body}

형식: {{"explanation": "작업 계획 및 적용할 최신 기술 설명"}}"""
        plan = call_ai(plan_prompt)
        print("📝 전략: " + plan.get('explanation', '진행 중'))

        # 4. 구현 (실행 가능한 코드 강제)
        impl_prompt = f"""전략: {plan.get('explanation')}
요구사항: {subject}

**중요 지시사항:**
1. 'package.json'에는 최신 버전의 next, react, react-dom을 포함하세요.
2. 실행 스크립트(dev, build, start)를 반드시 넣으세요.
3. 소스 코드는 placeholder 없이 완벽한 전체 내용을 작성하세요.
4. 파일 구조는 최신 Next.js 표준을 따르세요.

형식: {{"changes": [{{"path": "경로", "content": "코드전체"}}]}}"""
        impl = call_ai(impl_prompt)
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content:
                print(f"🛠 파일 생성: {change['path']} ({len(content)} bytes)")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f: f.write(content)

        # 5. 푸시 및 PR
        branch_name = "agent/quality-update-" + str(int(time.time()))
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f"git commit -m 'feat: high-quality code update via agent'", cwd=work_dir)
        run_command(f"git remote set-url origin {auth_url}", cwd=work_dir)
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code == 0:
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", 
                                   headers={"Authorization": f"token {GITHUB_PAT}"},
                                   json={"title": f"🚀 [고품질 에이전트] {subject}", "body": f"웹 검색 결과 및 최신 기술이 적용된 코드입니다.\n\n참고한 정보:\n{search_results}", "head": branch_name, "base": "main"}).json()
            final_url = pr_res.get("html_url", "PR 완료")
            print(f"✅ 완료: {final_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=final_url)
        else:
            raise Exception(f"푸시 실패: {err}")

    except Exception as e:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
