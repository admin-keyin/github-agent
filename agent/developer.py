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
GITHUB_PAT_ENV = os.getenv("GITHUB_PAT")
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

def send_agent_email(to_email, subject, spec, result_url, lang_code="ko", status="Success"):
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")
    private_key = os.getenv("EMAILJS_PRIVATE_KEY")
    
    if not all([service_id, template_id, public_key, private_key]):
        print("⚠️ EmailJS 설정 누락")
        return

    to_email = to_email.strip() if to_email else ""
    if not to_email: return

    config = {
        "ko": {
            "Success": {"badge": "성공", "title": "작업이 성공적으로 완료되었습니다", "desc": "에이전트가 요청하신 작업을 마쳤습니다.", "sub_label": "작업 제목", "spec_label": "구현 상세 내용", "btn": "결과 확인하기"},
            "Denied": {"badge": "권한 부족", "title": "저장소 접근 권한이 없습니다", "desc": "비공개 저장소에 접근할 수 없습니다. 권한을 확인해주세요.", "sub_label": "작업 제목", "spec_label": "안내 사항", "btn": "저장소로 이동"}
        },
        "en": {
            "Success": {"badge": "Success", "title": "Task Completed Successfully", "desc": "GitHub Agent has finished the requested work.", "sub_label": "Subject", "spec_label": "Implementation Details", "btn": "Review Results"},
            "Denied": {"badge": "Denied", "title": "Access Denied to Repository", "desc": "The agent cannot access the private repository. Please grant access.", "sub_label": "Subject", "spec_label": "Information", "btn": "Go to Repository"}
        }
    }
    
    lang = config.get(lang_code, config["en"])
    t = lang.get(status, lang["Success"])
    badge_color = "#22c55e" if status == "Success" else "#ef4444"
    btn_color = "#6366f1" if status == "Success" else "#1e293b"

    html_body = f"""
<div style="font-family: -apple-system, sans-serif; font-size: 15px; color: #334155; line-height: 1.6;">
  <div style="max-width: 600px; margin: 20px auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <div style="background-color: #1e293b; padding: 32px 24px; text-align: center;">
      <div style="display: inline-block; background-color: {badge_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 12px;">{t['badge']}</div>
      <h1 style="color: #ffffff; font-size: 22px; margin: 0;">{t['title']}</h1>
      <p style="color: #94a3b8; font-size: 14px; margin-top: 8px;">{t['desc']}</p>
    </div>
    <div style="padding: 32px 24px; background-color: #ffffff;">
      <div style="margin-bottom: 24px;">
        <label style="font-size: 12px; color: #64748b; font-weight: bold;">{t['sub_label']}</label>
        <h2 style="font-size: 18px; color: #1e293b; margin: 4px 0;">{subject}</h2>
      </div>
      <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 24px 0;" />
      <div style="margin-bottom: 32px;">
        <label style="font-size: 12px; color: #64748b; font-weight: bold;">{t['spec_label']}</label>
        <div style="margin-top: 12px; padding: 16px; background-color: #f8fafc; border-left: 4px solid {btn_color}; border-radius: 4px; color: #475569; white-space: pre-wrap;">{spec}</div>
      </div>
      <div style="text-align: center; margin-top: 40px;">
        <a href="{result_url}" target="_blank" style="background-color: {btn_color}; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">{t['btn']}</a>
      </div>
    </div>
  </div>
</div>
"""
    data = {
        "service_id": service_id, "template_id": template_id, "user_id": public_key, "accessToken": private_key,
        "template_params": {"to_email": to_email, "subject": f"[{t['badge']}] {subject}", "html_body": html_body}
    }
    try: requests.post("https://api.emailjs.com/api/v1.0/email/send", json=data, timeout=15)
    except: pass

def run_command_list(args, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_repo_contents(work_dir):
    context = ""
    for root, _, files in os.walk(work_dir):
        if any(x in root for x in ['node_modules', '.git', '.next']): continue
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.json', '.md')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        context += f"\n-- File: {os.path.relpath(os.path.join(root, file), work_dir)} --\n{f.read()}\n"
                except: pass
    return context or "New Project"

def extract_from_body(body, key):
    # 키워드: 값 형식 또는 키워드=값 형식을 모두 찾음
    match = re.search(fr"{key}\s*[:=]\s*(\S+)", body, re.IGNORECASE)
    return match.group(1) if match else None

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    sender = os.getenv("SENDER", "")
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    # 메일본문에서 인증 정보 추출 (Override)
    ml_github_token = extract_from_body(body, "GITHUB_TOKEN")
    ml_gitlab_token = extract_from_body(body, "GITLAB_TOKEN")
    ml_bitbucket_user = extract_from_body(body, "BITBUCKET_USER")
    ml_bitbucket_pass = extract_from_body(body, "BITBUCKET_PASS")

    # URL 감지 및 인증 정보 조합
    url_match = re.search(r"https://([\w\-.]+)/([\w\-]+/[\w\-.]+)", body)
    is_new_repo = False
    
    if url_match:
        domain = url_match.group(1)
        repo_path = url_match.group(2).replace(".git", "")
        
        if "github.com" in domain:
            token = ml_github_token or GITHUB_PAT_ENV
            auth_url = f"https://oauth2:{token}@github.com/{repo_path}.git"
        elif "gitlab.com" in domain:
            token = ml_gitlab_token
            auth_url = f"https://oauth2:{token}@gitlab.com/{repo_path}.git"
        elif "bitbucket.org" in domain:
            auth_url = f"https://{ml_bitbucket_user}:{ml_bitbucket_pass}@bitbucket.org/{repo_path}.git"
        else:
            auth_url = f"https://{domain}/{repo_path}.git" # 기본 시도
        repo_full_name = repo_path
    else:
        # URL 없으면 GitHub에 새 저장소 생성 (기본)
        repo_name = f"agent-task-{int(time.time())}"
        url = "https://api.github.com/user/repos"
        headers = {"Authorization": f"token {GITHUB_PAT_ENV}", "Accept": "vnd.github.v3+json"}
        res = requests.post(url, headers=headers, json={"name": repo_name, "private": False, "auto_init": True}).json()
        repo_full_name = res.get("full_name")
        auth_url = res.get("clone_url", "").replace("https://", f"https://oauth2:{GITHUB_PAT_ENV}@")
        is_new_repo = True

    if not auth_url: return
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 에이전트 가동: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. 클론 및 권한 체크
        _, stderr, code = run_command_list(["git", "clone", auth_url, work_dir])
        if code != 0:
            reason = "인증 실패: 메일본문에 토큰/비밀번호가 올바른지 확인해주세요." if lang_code == "ko" else "Auth Failed: Please check your token/password in the email."
            send_agent_email(sender, subject, reason, f"https://{domain}/{repo_full_name}" if url_match else "", lang_code, "Denied")
            update_task_status("failed")
            return

        # 2. 작업 진행
        repo_context = get_repo_contents(work_dir) if not is_new_repo else "New Scaffolding"
        cmd = ["gemini", "-m", GEMINI_MODEL, "--raw-output", "--yolo", "-p", f"Output JSON ONLY. Lang: {lang_code}\nRepo: {repo_context}\nTask: {subject}\n\n사양서와 변경사항을 작성하세요. 형식: {{\"explanation\":\"...\", \"changes\":[{{\"path\":\"...\",\"content\":\"...\"}}]}}"]
        stdout, _, _ = run_command_list(cmd)
        
        try:
            res_data = json.loads(re.search(r"\{.*\}", stdout, re.DOTALL).group())
            spec = res_data.get('explanation', 'Done.')
            for c in res_data.get('changes', []):
                p = os.path.join(work_dir, c['path'].lstrip('./'))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f: f.write(c['content'])
        except: raise Exception("AI 응답 파싱 실패")

        # 3. 푸시 (메인 또는 브랜치)
        branch_name = "main" if is_new_repo else f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "Agent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "agent@internal.com"], cwd=work_dir)
        if not is_new_repo: run_command_list(["git", "checkout", "-b", branch_name], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {subject}"], cwd=work_dir)
        _, _, p_code = run_command_list(["git", "push", "origin", branch_name, "--force" if is_new_repo else ""], cwd=work_dir)

        if p_code == 0:
            res_url = f"https://{domain}/{repo_full_name}" if url_match else f"https://github.com/{repo_full_name}"
            # GitHub의 경우만 PR 생성 시도 (GitLab/Bitbucket은 푸시 주소만 리포트)
            if "github.com" in auth_url and not is_new_repo:
                pr = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {token}"}, json={"title": f"🚀 {subject}", "body": spec, "head": branch_name, "base": "main"}).json()
                res_url = pr.get('html_url', res_url)
            
            update_task_status("completed", branch_name=branch_name, pr_url=res_url)
            send_agent_email(sender, subject, spec, res_url, lang_code, "Success")

    except Exception:
        print(f"❌ 에러: {traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
