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
SERPER_API_KEY = os.getenv("SERPER_API_KEY") # 구글 검색용 API 키

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

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

def search_google(query):
    """Serper.dev를 사용하여 Google 검색 수행 (고품질 데이터)"""
    if not SERPER_API_KEY:
        print("⚠️ SERPER_API_KEY가 없어 구글 검색을 스킵합니다.")
        return "구글 검색 키가 설정되지 않았습니다."

    print(f"🔍 Google에서 최신 기술 검색 중: {query}...")
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"q": query, "num": 5})

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        results = response.json()
        
        search_data = []
        # 유기적 검색 결과 추출
        for item in results.get('organic', []):
            search_data.append(f"- {item.get('title')}: {item.get('snippet')} ({item.get('link')})")
        
        # 답변 박스(지식 패널) 정보가 있으면 추가
        if results.get('answerBox'):
            answer = results['answerBox'].get('answer') or results['answerBox'].get('snippet')
            if answer: search_data.insert(0, f"[Quick Answer] {answer}")

        return "\n".join(search_data) if search_data else "검색 결과가 없습니다."
    except Exception as e:
        print(f"⚠️ 구글 검색 실패: {e}")
        return "검색 중 오류가 발생했습니다."

def call_ai(prompt, phase_name="Thinking"):
    print(f"🧠 AI가 {phase_name} 중... (Model: {OLLAMA_MODEL})")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 답변하세요.",
        "stream": False,
        "format": "json"
    }
    try:
        res = requests.post(OLLAMA_HOST + "/api/generate", json=payload, timeout=900)
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
    auth_url = f"https://oauth2:{GITHUB_PAT}@github.com/{repo_full_name}.git"
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 고품질 구글 에이전트 시작: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. Google 검색 (최신 기술 동향 파악)
        search_query = f"Latest Next.js 15, Tailwind v4 best practices for {subject} {body[:30]}"
        google_results = search_google(search_query)

        # 2. 클론
        run_command(f"git clone {auth_url} {work_dir}")
        
        # 3. 전략 수립 (Google 검색 결과 주입)
        plan_prompt = f"""당신은 세계 최고의 시니어 개발자입니다. 
다음 [Google 검색 결과]를 참고하여 요구사항을 해결하기 위한 '가장 현대적이고 효율적인' 계획을 세우세요.

[Google 검색 결과]
{google_results}

[요구사항]
{subject} / {body}

형식: {{"explanation": "구글 검색을 통해 파악한 최신 기술과 적용 계획을 상세히 설명"}}"""
        plan = call_ai(plan_prompt, "전략 수립")
        explanation = str(plan.get('explanation', '작업 진행'))
        print(f"📝 전략: {explanation}")

        # 4. 구현
        impl_prompt = f"""전략: {explanation}
요구사항: {subject}

**고품질 구현 지시:**
1. Next.js 15/App Router 표준을 따르세요.
2. Tailwind CSS v4 등 최신 스타일링 기법을 적용하세요.
3. package.json에 최신 버전의 의존성을 명시하세요.
4. 모든 코드는 즉시 실행 가능한 '전체 코드'여야 합니다.

형식: {{"changes": [{{"path": "경로", "content": "전체코드"}}]}}"""
        impl = call_ai(impl_prompt, "코드 작성")
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if content:
                print(f"🛠 파일 생성: {change['path']} ({len(content)} bytes)")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f: f.write(content)

        # 5. 푸시 및 PR
        branch_name = f"agent/google-quality-{int(time.time())}"
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f"git commit -m 'feat: google-searched high quality code'", cwd=work_dir)
        run_command(f"git remote set-url origin {auth_url}", cwd=work_dir)
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code == 0:
            pr_data = {
                "title": f"🚀 [Google 고품질 에이전트] {subject}",
                "body": f"### 💡 구글 검색 기반 구현\n{explanation}\n\n### 🔍 검색 참고 자료\n{google_results}",
                "head": branch_name, "base": "main"
            }
            pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", 
                                   headers={"Authorization": f"token {GITHUB_PAT}"},
                                   json=pr_data).json()
            final_url = pr_res.get("html_url", "PR 완료")
            print(f"✅ 성공: {final_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=final_url)
        else:
            raise Exception(f"푸시 실패: {err}")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
