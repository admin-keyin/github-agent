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
GITHUB_PAT = os.getenv("GITHUB_PAT") # 반드시 외부 레포 권한이 있는 PAT이어야 함

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

def run_command(command, cwd=None):
    print(f"Executing: {command} (cwd: {cwd})")
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command Failed: {result.stderr}")
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def extract_git_url(text):
    match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", text)
    if match:
        url = match.group(0)
        if url.endswith('.'): url = url[:-1]
        if not url.endswith('.git'): url += '.git'
        return url
    return None

def extract_target_branch(text):
    match = re.search(r"(?:target branch|대상 브랜치|브랜치):\s*([\w\-/.]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "main"

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    
    target_base_branch = extract_target_branch(body)
    print(f"🚀 작업 시작: {subject} (Target Branch: {target_base_branch})")
    update_task_status("running")
    
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    try:
        # 1. 대상 레포지토리 추출
        target_repo_url = extract_git_url(body)
        if not target_repo_url:
            raise Exception("이메일 본문에서 대상 프로젝트(GitHub URL)를 찾을 수 없습니다. 형식을 확인하세요.")
        
        print(f"📦 타겟 레포지토리 발견: {target_repo_url}")
        
        # 2. 클론 (PAT 인증 포함)
        auth_url = target_repo_url.replace("https://", f"https://{GITHUB_PAT}@")
        _, err, code = run_command(f"git clone -b {target_base_branch} {auth_url} {work_dir}")
        if code != 0:
            print("⚠️ 지정 브랜치 클론 실패, 기본 브랜치로 재시도...")
            _, _, code = run_command(f"git clone {auth_url} {work_dir}")
            if code != 0: raise Exception(f"클론 실패: {err}")
            target_base_branch = "main"

        # 레포 전체 이름 추출 (owner/repo)
        repo_match = re.search(r"github\.com/([\w\-]+/[\w\-.]+)", target_repo_url)
        repo_full_name = repo_match.group(1).replace(".git", "")

        # 3. 컨텍스트 파악 및 AI 호출
        tree, _, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'", cwd=work_dir)
        
        # 전략 수립
        plan_prompt = f"요구사항: {subject} / {body}\n파일 구조: {tree}\n형식: {{\"explanation\": \"...\"}}"
        plan_raw = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": OLLAMA_MODEL, "prompt": plan_prompt + "\nJSON으로만 답변.", "stream": False, "format": "json"}, timeout=600).json().get('response', '{}')
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan.get('explanation', '계획 없음')}")

        # 구현
        impl_prompt = f"전략: {plan.get('explanation')}\n요구사항: {subject}\n형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\" }}]}}"
        impl_raw = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": OLLAMA_MODEL, "prompt": impl_prompt + "\nJSON으로만 답변.", "stream": False, "format": "json"}, timeout=600).json().get('response', '{}')
        impl = json.loads(impl_raw)
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./').lstrip('/'))
            print(f"🛠 파일 수정: {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 4. Git 커밋 및 푸시
        branch_name = f"agent/fix-{int(time.time())}"
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f'git commit -m "feat: {subject}"', cwd=work_dir)
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code != 0:
            raise Exception(f"대상 레포지토리로 푸시 실패 (권한 확인 필요): {err}")

        # 5. PR 생성
        print(f"🚀 PR 생성 중: {repo_full_name}")
        pr_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github+json"}
        pr_data = {"title": f"🚀 [에이전트] {subject}", "body": f"작업 내용: {body}", "head": branch_name, "base": target_base_branch}
        pr_res = requests.post(pr_url, headers=headers, json=pr_data).json()
        
        if "html_url" in pr_res:
            final_url = pr_res["html_url"]
            print(f"✅ 성공: {final_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=final_url)
        else:
            print(f"❌ PR 생성 실패 상세: {json.dumps(pr_res)}")
            update_task_status("completed", branch_name=branch_name, pr_url="PR 생성 실패 (권한/중복)")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
