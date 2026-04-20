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

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")

def update_task_status(status, branch_name=None, pr_url=None):
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
    if branch_name: data["branch_name"] = branch_name
    if pr_url: data["pr_url"] = pr_url
    try:
        requests.patch(url, headers=headers, json=data, timeout=10)
    except: pass

def parse_json_garbage(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def call_ollama(prompt, retry=1):
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 출력하세요.",
        "stream": False
    }
    try:
        print(f"📡 Ollama 요청 중... (Model: {OLLAMA_MODEL})")
        response = requests.post(url, json=payload, timeout=600)
        res_json = response.json()
        if response.status_code == 200:
            raw_text = res_json.get('response', '')
            if not raw_text.strip():
                if retry > 0: return call_ollama(prompt, retry - 1)
                raise Exception("Empty response from Ollama")
            return parse_json_garbage(raw_text)
        else:
            raise Exception(f"HTTP {response.status_code}")
    except Exception as e:
        if retry > 0: return call_ollama(prompt, retry - 1)
        raise e

def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout, result.stderr

def extract_git_url(text):
    # https://github.com/owner/repo 형태 추출
    match = re.search(r"https://github\.com/[\w\-/.]+", text)
    if match:
        url = match.group(0)
        if url.endswith('.'): url = url[:-1]
        if not url.endswith('.git'): url += '.git'
        return url
    return None

def extract_target_branch(text):
    # 'target branch: develop' 또는 '대상 브랜치: develop' 형태 추출
    match = re.search(r"(?:target branch|대상 브랜치):\s*([\w\-/.]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "main" # 기본값

def create_github_pr(repo_full_name, branch, title, body, base_branch="main"):
    url = f"https://api.github.com/repos/{repo_full_name}/pulls"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "title": title,
        "body": body,
        "head": branch,
        "base": base_branch
    }
    res = requests.post(url, headers=headers, json=data)
    return res.json()

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")

    # 타겟 브랜치 결정
    target_base_branch = extract_target_branch(body)
    print(f"🚀 외부 프로젝트 작업 시작: {subject} (Target: {target_base_branch})")
    update_task_status("running")

    # 작업 디렉토리 설정
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    try:
        # 1. 대상 레포지토리 추출 및 클론
        target_repo_url = extract_git_url(body)
        if not target_repo_url:
            print("⚠️ URL 미발견. 현재 레포지토리 대상 작업.")
            target_repo_url = run_command("git remote get-url origin")[0].strip()

        print(f"📦 타겟 레포지토리: {target_repo_url} (Base: {target_base_branch})")
        auth_url = target_repo_url.replace("https://", f"https://{GITHUB_PAT}@")

        # 지정된 타겟 브랜치로 클론 시도
        clone_res = run_command(f"git clone -b {target_base_branch} {auth_url} {work_dir}")
        if "fatal" in clone_res[1]: # 브랜치가 없으면 기본 클론 후 체크
            print(f"⚠️ 브랜치 '{target_base_branch}'를 찾을 수 없어 기본 브랜치로 클론합니다.")
            run_command(f"git clone {auth_url} {work_dir}")
            target_base_branch = "main" # 폴백
...
        # 6. PR 생성
        pr_res = create_github_pr(repo_full_name, branch_name, f"🚀 [에이전트] {subject}", f"작업 내용: {body}", base_branch=target_base_branch)
        pr_url = pr_res.get("html_url", "PR 생성 실패 (권한 또는 브랜치 확인)")
        # 3. 전략 수립
        plan_prompt = f"요구사항: {subject} / {body}\n구조: {tree}\n형식: {{\"explanation\": \"...\"}}"
        plan = json.loads(call_ollama(plan_prompt))
        print(f"📝 전략: {plan['explanation']}")

        # 4. 구현 및 파일 수정
        impl_prompt = f"전략: {plan['explanation']}\n형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\" }}]}}"
        impl = json.loads(call_ollama(impl_prompt))
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./').lstrip('/'))
            print(f"🛠 파일 수정: {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 5. Git 커밋 및 푸시
        branch_name = f"agent/fix-{int(time.time())}"
        run_command(f"git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command(f"git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f'git commit -m "feat: {subject}"', cwd=work_dir)
        run_command(f"git push origin {branch_name}", cwd=work_dir)

        # 6. PR 생성
        pr_res = create_github_pr(repo_full_name, branch_name, f"🚀 [에이전트] {subject}", f"작업 내용: {body}")
        pr_url = pr_res.get("html_url", "PR 생성 실패 (권한 또는 브랜치 확인)")
        
        print(f"✅ 완료: {pr_url}")
        update_task_status("completed", branch_name=branch_name, pr_url=pr_url)

    except Exception as e:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
