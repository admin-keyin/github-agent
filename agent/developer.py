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
    if not GITHUB_PAT:
        print("❌ GITHUB_PAT이 비어있습니다. 초대를 수락할 수 없습니다.")
        return False

    print(f"🔍 '{repo_full_name}' 초대 확인 중...")
    url = "https://api.github.com/user/repository_invitations"
    headers = {
        "Authorization": "token " + str(GITHUB_PAT),
        "Accept": "application/vnd.github+json"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 401:
            print("❌ GITHUB_PAT 인증 실패 (Bad credentials)")
            return False
        
        invites = res.json()
        if not isinstance(invites, list): return False
            
        for invite in invites:
            full_name = invite.get('repository', {}).get('full_name', '')
            if full_name.lower() == repo_full_name.lower():
                invite_id = invite.get('id')
                print(f"📦 초대 발견 (ID: {invite_id}). 수락 진행...")
                accept_url = "https://api.github.com/user/repository_invitations/" + str(invite_id)
                requests.patch(accept_url, headers=headers)
                print("✅ 초대 수락 완료!")
                return True
    except Exception as e:
        print(f"⚠️ 초대 확인 중 에러: {e}")
    return False

def call_ai(prompt):
    """Ollama API 호출 (JSON 포맷 강제)"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 출력하세요.",
        "stream": False,
        "format": "json"
    }
    res = requests.post(OLLAMA_HOST + "/api/generate", json=payload, timeout=600)
    response_text = res.json().get('response', '{}')
    return json.loads(response_text)

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    
    if not GITHUB_PAT:
        print("🚨 경고: GITHUB_PAT이 비어있습니다. 외부 레포 작업이 불가능합니다.")
    
    # URL 추출
    git_url_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    if not git_url_match:
        print("❌ 대상 프로젝트 URL을 찾을 수 없습니다.")
        update_task_status("failed")
        return
        
    target_repo_url = git_url_match.group(0)
    if target_repo_url.endswith('.'): target_repo_url = target_repo_url[:-1]
    if not target_repo_url.endswith('.git'): target_repo_url += '.git'
    
    repo_full_name = git_url_match.group(1).replace(".git", "")
    target_base_branch = "main"
    branch_match = re.search(r"(?:대상 브랜치|target branch):\s*([\w\-/.]+)", body, re.I)
    if branch_match: target_base_branch = branch_match.group(1).strip()

    print(f"🚀 작업 시작: {repo_full_name} (Target: {target_base_branch})")
    update_task_status("running")
    
    accept_repo_invitation(repo_full_name)
    
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    try:
        # 클론
        auth_url = target_repo_url.replace("https://", "https://oauth2:" + str(GITHUB_PAT) + "@")
        _, err, code = run_command("git clone -b " + target_base_branch + " " + auth_url + " " + work_dir)
        if code != 0:
            print("⚠️ 기본 브랜치로 재시도...")
            run_command("git clone " + auth_url + " " + work_dir)
            target_base_branch = "main"

        # 파일 구조 파악
        tree, _, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'", cwd=work_dir)
        
        # 전략 수립
        plan_prompt = "요구사항: " + subject + "\n본문: " + body + "\n구조:\n" + tree + "\n형식: {\"explanation\": \"...\"}"
        plan = call_ai(plan_prompt)
        print("📝 전략: " + plan.get('explanation', '계획 수립 완료'))

        # 구현
        impl_prompt = "전략: " + plan.get('explanation', '') + "\n요구사항: " + subject + "\n형식: {\"changes\": [{\"path\": \"...\", \"content\": \"...\"}]}"
        impl = call_ai(impl_prompt)
        
        for change in impl.get('changes', []):
            path = os.path.join(work_dir, change['path'].lstrip('./').lstrip('/'))
            print("🛠 파일 수정: " + path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f: f.write(change['content'])

        # 푸시
        branch_name = "agent/fix-" + str(int(time.time()))
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command("git checkout -b " + branch_name, cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command('git commit -m "feat: ' + subject + '"', cwd=work_dir)
        run_command("git remote set-url origin " + auth_url, cwd=work_dir)
        _, err, code = run_command("git push origin " + branch_name, cwd=work_dir)
        
        if code != 0: raise Exception("푸시 실패: " + err)

        # PR 생성
        pr_url_api = "https://api.github.com/repos/" + repo_full_name + "/pulls"
        headers = {"Authorization": "token " + str(GITHUB_PAT), "Accept": "application/vnd.github+json"}
        pr_data = {"title": "🚀 [에이전트] " + subject, "body": body, "head": branch_name, "base": target_base_branch}
        pr_res = requests.post(pr_url_api, headers=headers, json=pr_data).json()
        
        final_url = pr_res.get("html_url", "PR 생성 실패")
        print("✅ 결과: " + final_url)
        update_task_status("completed", branch_name=branch_name, pr_url=final_url)

    except Exception as e:
        print("❌ 에러 발생:\n" + traceback.format_exc())
        update_task_status("failed")

if __name__ == "__main__":
    main()
