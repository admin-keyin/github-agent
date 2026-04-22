import os
import requests
import json
import subprocess
import traceback
import time
import re
import shutil
import sys
import uuid
import hmac
import hashlib

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT_ENV = os.getenv("GITHUB_PAT")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 솔라피 설정 (환경변수에서만 참조)
SOLAPI_API_KEY = os.getenv("SOLAPI_API_KEY")
SOLAPI_API_SECRET = os.getenv("SOLAPI_API_SECRET")
SOLAPI_FROM_NUMBER = os.getenv("SOLAPI_FROM_NUMBER")

GEMINI_MODEL = "gemini-2.5-flash-lite"

def log(msg):
    print(msg, flush=True)

def get_solapi_header():
    """솔라피 v4 인증 헤더를 생성합니다."""
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET:
        return {}
    date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    salt = str(uuid.uuid4().hex)
    combined = date + salt
    signature = hmac.new(
        SOLAPI_API_SECRET.encode('utf-8'),
        combined.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        'Authorization': f'HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}',
        'Content-Type': 'application/json; charset=utf-8'
    }

def send_kakao_report(to_number, subject, spec_summary, result_url):
    """솔라피 API를 사용하여 카카오톡 결과를 발송합니다."""
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET or not SOLAPI_FROM_NUMBER:
        log("⚠️ 솔라피 설정(Key, Secret, From Number)이 누락되었습니다. .env를 확인하세요.")
        return

    target_number = re.sub(r'[^0-9]', '', str(to_number))
    if not target_number: return

    log(f"📱 카카오톡(솔라피) 결과 발송 시도 (대상: {target_number})")
    
    short_spec = spec_summary[:100] + "..." if len(spec_summary) > 100 else spec_summary
    message_text = f"✅ [에이전트 작업 완료]\n\n제목: {subject}\n요약: {short_spec}\n\n결과 확인: {result_url}"
    
    url = "https://api.solapi.com/messages/v4/send-many"
    data = {
        "messages": [
            {
                "to": target_number,
                "from": SOLAPI_FROM_NUMBER,
                "text": message_text
            }
        ]
    }
    
    try:
        res = requests.post(url, headers=get_solapi_header(), json=data, timeout=15)
        if res.status_code == 200: log("📧 카카오톡 메시지 발송 완료!")
        else: log(f"❌ 카카오톡 발송 실패: {res.json()}")
    except Exception as e:
        log(f"❌ 카카오톡 발송 중 에러: {e}")

# ... (기존 helper 함수 및 main 로직은 동일) ...

def update_task_status(status, branch_name=None, pr_url=None):
    if not SUPABASE_URL or not SUPABASE_KEY or not TASK_ID: return
    url = f"{SUPABASE_URL}/rest/v1/agent_tasks?id=eq.{TASK_ID}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    data = {"status": status}
    if branch_name: data["branch_name"] = branch_name
    if pr_url: data["pr_url"] = pr_url
    try: requests.patch(url, headers=headers, json=data, timeout=10)
    except: pass

def upsert_credential(email, provider, value, git_url):
    if not all([SUPABASE_URL, SUPABASE_KEY, email, provider, value, git_url]): return
    url = f"{SUPABASE_URL}/rest/v1/user_credentials"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    data = {"user_email": email, "key_name": provider.upper(), "key_value": value, "scope": git_url}
    try: requests.post(f"{url}?on_conflict=user_email,key_name,scope", headers=headers, json=data, timeout=10)
    except: pass

def get_credential_from_vault(email, provider, git_url):
    if not all([SUPABASE_URL, SUPABASE_KEY, email, provider, git_url]): return None
    url = f"{SUPABASE_URL}/rest/v1/user_credentials?user_email=eq.{email}&key_name=eq.{provider.upper()}&scope=eq.{git_url}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res: return res[0].get("key_value")
    except: pass
    return None

def send_agent_email(to_email, subject, spec, result_url, lang_code="ko", status="Success"):
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")
    private_key = os.getenv("EMAILJS_PRIVATE_KEY")
    if not all([service_id, template_id, public_key, private_key]): return
    to_email = to_email.strip() if to_email else ""
    if not to_email: return
    config = {"ko": {"Success": {"badge": "성공", "title": "작업 완료 리포트", "desc": "작업이 성공적으로 완료되었습니다.", "spec_label": "구현 상세", "btn": "결과 확인하기"}}, "en": {"Success": {"badge": "Success", "title": "Task Completed", "desc": "Finished the work successfully.", "spec_label": "Details", "btn": "Review Results"}}}
    lang = config.get(lang_code, config["en"]); t = lang["Success"]
    html_body = f"<div style='font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;'><h2>{t['title']}</h2><p>{t['desc']}</p><div style='padding: 15px; background: #f9f9f9; border-left: 4px solid #6366f1;'>{spec}</div><br/><a href='{result_url}' style='padding: 10px 20px; background: #6366f1; color: #fff; text-decoration: none; border-radius: 5px;'>{t['btn']}</a></div>"
    data = {"service_id": service_id, "template_id": template_id, "user_id": public_key, "accessToken": private_key, "template_params": {"to_email": to_email, "subject": f"[{t['badge']}] {subject}", "html_body": html_body}}
    try: requests.post("https://api.emailjs.com/api/v1.0/email/send", json=data, timeout=15)
    except: pass

def run_command_list(args, cwd=None, input_data=None):
    clean_args = [str(arg) for arg in args if arg and str(arg).strip()]
    env = os.environ.copy(); env["GIT_TERMINAL_PROMPT"] = "0"
    log(f"💻 CMD: {' '.join(clean_args[:10])}")
    result = subprocess.run(clean_args, capture_output=True, text=True, cwd=cwd, env=env, input=input_data)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def extract_from_body(body, key):
    patterns = [fr"\[{key}\]\s*(\S+)", fr"{key}\s*[:=]\s*(\S+)"]
    for p in patterns:
        match = re.search(p, body, re.IGNORECASE)
        if match: return match.group(1)
    return None

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    sender = os.getenv("SENDER", "")
    source = os.getenv("SOURCE", "email")
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    gh_token = extract_from_body(body, "GITHUB_TOKEN")
    gl_token = extract_from_body(body, "GITLAB_TOKEN")
    bb_user = extract_from_body(body, "BITBUCKET_USER")
    bb_pass = extract_from_body(body, "BITBUCKET_PASS")
    base_br = extract_from_body(body, "BASE_BRANCH") or "main"
    pr_title = extract_from_body(body, "PR_TITLE")

    url_match = re.search(r"https://([\w\-.]+)/(\S+)", body)
    if not url_match: return

    domain = url_match.group(1).lower()
    repo_path = url_match.group(2).replace(".git", "").strip()
    full_git_url = f"https://{domain}/{repo_path}"
    provider = "GITHUB"
    if "gitlab" in domain: provider = "GITLAB"
    elif "bitbucket" in domain: provider = "BITBUCKET"

    current_token = None
    if provider == "GITHUB" and gh_token:
        upsert_credential(sender, provider, gh_token, full_git_url); current_token = gh_token
    elif provider == "GITLAB" and gl_token:
        upsert_credential(sender, provider, gl_token, full_git_url); current_token = gl_token
    elif provider == "BITBUCKET" and bb_user and bb_pass:
        combined = f"{bb_user}:{bb_pass}"; upsert_credential(sender, provider, combined, full_git_url); current_token = combined

    if not current_token: current_token = get_credential_from_vault(sender, provider, full_git_url)
    final_token = current_token or (GITHUB_PAT_ENV if provider == "GITHUB" else None)

    if not final_token:
        send_agent_email(sender, subject, "인증 토큰 누락", full_git_url, lang_code, "Denied")
        return

    if provider == "GITHUB": auth_url = f"https://oauth2:{final_token}@github.com/{repo_path}.git"
    elif provider == "GITLAB": auth_url = f"https://oauth2:{final_token}@{domain}/{repo_path}.git"
    elif provider == "BITBUCKET": auth_url = f"https://{final_token}@{domain}/{repo_path}.git"
    
    update_task_status("running")
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    try:
        run_command_list(["git", "clone", auth_url, work_dir])
        run_command_list(["git", "fetch", "origin", base_br], cwd=work_dir)
        run_command_list(["git", "checkout", base_br], cwd=work_dir)

        instruction = f"[TASK]\nSubject: {subject}\nBody: {body}\n\n[INSTRUCTION]\n1. Go to: {work_dir}\n2. Apply changes.\n3. Verify."
        stdout, _, code = run_command_list(["gemini", "-m", GEMINI_MODEL, "--raw-output", "--accept-raw-output-risk", "--yolo", "--include-directories", work_dir, "-p", instruction])
        if code != 0: raise Exception("Gemini failed")

        spec = stdout or "작업 완료"
        new_branch = f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "inchAgent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "admin.key.in@gmail.com"], cwd=work_dir)
        run_command_list(["git", "checkout", "-b", new_branch], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {re.sub(r'^(fwd|re|fw)\s*:\s*', '', subject, flags=re.IGNORECASE).strip()}"], cwd=work_dir)
        _, stderr, p_code = run_command_list(["git", "push", "origin", new_branch], cwd=work_dir)

        if p_code == 0:
            res_url = full_git_url
            if provider == "GITHUB":
                pr = requests.post(f"https://api.github.com/repos/{repo_path}/pulls", headers={"Authorization": f"token {final_token}"}, json={"title": pr_title or f"🚀 {subject}", "body": spec, "head": new_branch, "base": base_br}).json()
                res_url = pr.get('html_url', res_url)
            update_task_status("completed", branch_name=new_branch, pr_url=res_url)
            if source == "kakao": send_kakao_report(sender, subject, spec, res_url)
            send_agent_email(sender, subject, spec, res_url, lang_code, "Success")
    except Exception:
        update_task_status("failed")

if __name__ == "__main__": main()
