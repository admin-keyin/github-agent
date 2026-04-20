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

def run_command(command, cwd=None):
    print(f"Executing: {command} (cwd: {cwd})")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"❌ Command Failed: {result.stderr}")
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def accept_repo_invitation(repo_full_name):
    """대기 중인 레포지토리 초대를 자동으로 수락"""
    if not GITHUB_PAT:
        print("❌ GITHUB_PAT이 설정되지 않았습니다.")
        return False

    print(f"🔍 '{repo_full_name}' 초대 확인 중...")
    url = "https://api.github.com/user/repository_invitations"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github+json"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"❌ 초대 목록 조회 실패 (HTTP {res.status_code}): {res.text}")
            return False
            
        invites = res.json()
        if not isinstance(invites, list):
            print(f"❌ 응답이 리스트 형식이 아닙니다: {invites}")
            return False
            
        for invite in invites:
            repo_info = invite.get('repository', {})
            if not isinstance(repo_info, dict): continue
            
            full_name = repo_info.get('full_name', '')
            if full_name.lower() == repo_full_name.lower():
                invite_id = invite.get('id')
                print(f"📦 초대 발견 (ID: {invite_id}). 수락 진행...")
                accept_url = f"https://api.github.com/user/repository_invitations/{invite_id}"
                accept_res = requests.patch(accept_url, headers=headers)
                if accept_res.status_code == 204:
                    print("✅ 초대 수락 성공!")
                    return True
                else:
                    print(f"❌ 초대 수락 실패 (HTTP {accept_res.status_code}): {accept_res.text}")
                    return False
    except Exception as e:
        print(f"⚠️ 초대 확인 중 에러: {e}")
    return False

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
    
    if not GITHUB_PAT:
        print("CRITICAL ERROR: GITHUB_PAT environment variable is missing!")
    
    target_base_branch = extract_target_branch(body)
    print(f"🚀 작업 시작: {subject} (Target: {target_base_branch})")
    update_task_status("running")
    
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    try:
        # 1. 대상 레포지토리 추출
        target_repo_url = extract_git_url(body)
        if not target_repo_url:
            raise Exception("이메일 본문에서 대상 프로젝트(GitHub URL)를 찾을 수 없습니다.")
        
        # 레포 명 추출 (owner/repo)
        repo_match = re.search(r"github\.com/([\w\-]+/[\w\-.]+)", target_repo_url)
        repo_full_name = repo_match.group(1).replace(".git", "")

        # 2. 초대 자동 수락
        accept_repo_invitation(repo_full_name)
        
        # 3. 클론 (인증 정보 포함)
        print(f"📦 타겟 레포지토리 클론 시도: {target_repo_url}")
        auth_url = target_repo_url.replace("https://", f"https://{GITHUB_PAT}@")
        _, err, code = run_command(f"git clone -b {target_base_branch} {auth_url} {work_dir}")
        if code != 0:
            print("⚠️ 지정 브랜치 클론 실패, 기본 브랜치로 재시도...")
            _, _, code = run_command(f"git clone {auth_url} {work_dir}")
            if code != 0: raise Exception(f"클론 실패: {err}")
            target_base_branch = "main"

        # 4. 컨텍스트 파악 및 AI 호출
        tree, _, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'", cwd=work_dir)
        
        # 전략 및 구현 (Ollama 호출)
        def call_ai(prompt):
            res = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt + "\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 출력하세요.", "stream": False, "format": "json"}, timeout=600)
            return json.loads(res.json().get('response', '{}'))

        plan = call_ai(f"요구사항: {subject} / {body}\n파일 구조: {tree}\n형식: {{\"explanation\": \"...\"}}")
        print(f"📝 전략: {plan.get('explanation', '계획 수립 완료')}")

        impl = call_ai(f"전략: {plan.get('explanation')}\n요구사항: {subject}\n형식: {{\"changes\": [{\"path\": \"...\", \"content\": \"...\"}]}}")
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./').lstrip('/'))
            print(f"🛠 파일 수정: {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 5. Git 작업 및 푸시
        branch_name = f"agent/fix-{int(time.time())}"
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command(f"git checkout -b {branch_name}", cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command(f'git commit -m "feat: {subject}"', cwd=work_dir)
        
        # 원격지 URL 업데이트 (인증 정보 명시)
        run_command(f"git remote set-url origin {auth_url}", cwd=work_dir)
        print(f"📡 푸시 시도 중: {branch_name}")
        _, err, code = run_command(f"git push origin {branch_name}", cwd=work_dir)
        
        if code != 0:
            raise Exception(f"푸시 실패: {err}")

        # 6. PR 생성
        print(f"🚀 PR 생성 중: {repo_full_name}")
        pr_url_api = f"https://api.github.com/repos/{repo_full_name}/pulls"
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github+json"}
        pr_data = {"title": f"🚀 [에이전트] {subject}", "body": f"작업 내용: {body}", "head": branch_name, "base": target_base_branch}
        pr_res = requests.post(pr_url_api, headers=headers, json=pr_data).json()
        
        if "html_url" in pr_res:
            final_url = pr_res["html_url"]
            print(f"✅ 성공: {final_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=final_url)
        else:
            print(f"❌ PR 실패: {json.dumps(pr_res)}")
            update_task_status("completed", branch_name=branch_name, pr_url="PR 생성 실패")

    except Exception as e:
        print(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
