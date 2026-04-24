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
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# 환경 변수 로드 (절대 경로 및 상대 경로 모두 탐색)
dotenv_paths = [
    ".env.local", 
    ".env", 
    "/Users/celebe/WebstormProjects/untitled2/.env.local", 
    os.path.expanduser("~/.env.local")
]

for path in dotenv_paths:
    if os.path.exists(path):
        load_dotenv(dotenv_path=path)
        print(f"✅ 환경 변수 로드 완료: {path}")

def log(msg):
    print(msg, flush=True)

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT_ENV = os.getenv("GITHUB_PAT") or os.getenv("MY_GITHUB_PAT")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
MASTER_ENCRYPTION_KEY = os.getenv("MASTER_ENCRYPTION_KEY")

if not MASTER_ENCRYPTION_KEY:
    log("⚠️ 경고: MASTER_ENCRYPTION_KEY를 찾지 못해 기본값을 사용합니다.")
    MASTER_ENCRYPTION_KEY = "default-secret-key-for-local-test"
else:
    log(f"🔑 마스터 키 로드 성공 (앞 3글자: {MASTER_ENCRYPTION_KEY[:3]}...)")

# 암호화 엔진 초기화
def get_cipher():
    """마스터 키를 기반으로 암호화 키를 생성합니다."""
    salt = b'static_salt_for_now'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(MASTER_ENCRYPTION_KEY.encode()))
    return Fernet(key)

CIPHER = get_cipher()

def encrypt_value(value):
    if not value: return None
    return CIPHER.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value):
    if not encrypted_value: return None
    try:
        return CIPHER.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return None

# 솔라피 설정
SOLAPI_API_KEY = os.getenv("SOLAPI_API_KEY")
SOLAPI_API_SECRET = os.getenv("SOLAPI_API_SECRET")
SOLAPI_FROM_NUMBER = os.getenv("SOLAPI_FROM_NUMBER")

GEMINI_MODEL = "gemini-2.5-flash-lite"

def get_solapi_header():
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET: return {}
    date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    salt = str(uuid.uuid4().hex)
    combined = date + salt
    signature = hmac.new(SOLAPI_API_SECRET.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    return {'Authorization': f'HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}', 'Content-Type': 'application/json; charset=utf-8'}

def send_kakao_report(to_number, subject, spec_summary, result_url):
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET or not SOLAPI_FROM_NUMBER: return
    target_number = re.sub(r'[^0-9]', '', str(to_number))
    if not target_number: return
    short_spec = spec_summary[:100] + "..." if len(spec_summary) > 100 else spec_summary
    message_text = f"✅ [에이전트 작업 완료]\n\n제목: {subject}\n요약: {short_spec}\n\n결과 확인: {result_url}"
    url = "https://api.solapi.com/messages/v4/send-many"
    data = {"messages": [{"to": target_number, "from": SOLAPI_FROM_NUMBER, "text": message_text}]}
    try: requests.post(url, headers=get_solapi_header(), json=data, timeout=15)
    except: pass

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
    if not all([SUPABASE_URL, SUPABASE_KEY, email, value, git_url]): return
    encrypted_value = encrypt_value(value)
    url = f"{SUPABASE_URL}/rest/v1/git_credentials"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    data = {"email": email, "encrypted_config": encrypted_value, "scope": git_url}
    try: requests.post(f"{url}?on_conflict=email,scope", headers=headers, json=data, timeout=10)
    except: pass

def get_credential_from_vault(email, provider, git_url):
    if not all([SUPABASE_URL, SUPABASE_KEY, email, git_url]): return None
    search_email = email.strip().lower()
    clean_url = git_url.replace(".git", "").rstrip("/")
    domain_match = re.search(r"(https?://[\w\-.]+)", clean_url)
    domain_url = domain_match.group(1).lower() if domain_match else clean_url
    scopes_to_check = [clean_url, git_url, domain_url, f"{clean_url}.git"]
    log(f"🔎 Supabase 조회 시작 (Email: {search_email})")
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    for scope in scopes_to_check:
        url = f"{SUPABASE_URL}/rest/v1/git_credentials"
        params = {"email": f"eq.{search_email}", "scope": f"eq.{scope}"}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data:
                    decrypted = decrypt_value(data[0].get("encrypted_config"))
                    if decrypted:
                        log(f"🔓 복호화 성공! (Scope: {scope})")
                        return decrypted
        except: pass
    return None

def get_latest_scope_from_vault(email, provider):
    if not all([SUPABASE_URL, SUPABASE_KEY, email]): return None
    search_email = email.strip().lower()
    agent_repo = "github-agent"
    url = f"{SUPABASE_URL}/rest/v1/git_credentials"
    params = {"email": f"eq.{search_email}", "scope": f"not.ilike.*{agent_repo}*", "select": "scope", "order": "created_at.desc", "limit": "1"}
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10).json()
        if res and res[0].get("scope"):
            log(f"✅ 자동 탐색 성공 (대상: {res[0].get('scope')})")
            return res[0].get("scope")
    except: pass
    return None

def send_agent_email(to_email, subject, spec, result_url, lang_code="ko", status="Success"):
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")
    private_key = os.getenv("EMAILJS_PRIVATE_KEY")
    if not all([service_id, template_id, public_key, private_key]): return
    config = {
        "ko": {
            "Success": {"badge": "성공", "title": "작업 완료 리포트", "desc": "작업이 성공적으로 완료되었습니다.", "spec_label": "구현 상세", "btn": "결과 확인하기"},
            "Denied": {"badge": "거부", "title": "접근 권한 부족", "desc": "해당 저장소에 접근할 권한이 없거나 인증 토큰이 유효하지 않아 작업을 수행할 수 없습니다.", "spec_label": "에러 상세", "btn": "권한 설정 가이드"}
        },
        "en": {
            "Success": {"badge": "Success", "title": "Task Completed", "desc": "Finished the work successfully.", "spec_label": "Details", "btn": "Review Results"},
            "Denied": {"badge": "Denied", "title": "Access Denied", "desc": "You do not have permission or the token is invalid.", "spec_label": "Error Details", "btn": "Security Guide"}
        }
    }
    lang = config.get(lang_code, config["en"]); t = lang.get(status, lang["Success"])
    color = "#6366f1" if status == "Success" else "#ef4444"
    html_body = f"<div style='font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;'><h2>{t['title']}</h2><p>{t['desc']}</p><div style='padding: 15px; background: #f9f9f9; border-left: 4px solid {color};'>{spec}</div><br/><a href='{result_url}' style='padding: 10px 20px; background: #6366f1; color: #fff; text-decoration: none; border-radius: 5px;'>{t['btn']}</a></div>"
    data = {"service_id": service_id, "template_id": template_id, "user_id": public_key, "accessToken": private_key, "template_params": {"to_email": to_email, "subject": f"[{t['badge']}] {subject}", "html_body": html_body}}
    try: requests.post("https://api.emailjs.com/api/v1.0/email/send", json=data, timeout=15)
    except: pass

def run_command_list(args, cwd=None, input_data=None):
    clean_args = [str(arg) for arg in args if arg and str(arg).strip()]
    env = os.environ.copy(); env["GIT_TERMINAL_PROMPT"] = "0"
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
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    gh_token = extract_from_body(body, "GITHUB_TOKEN"); gl_token = extract_from_body(body, "GITLAB_TOKEN")
    bb_user = extract_from_body(body, "BITBUCKET_USER"); bb_pass = extract_from_body(body, "BITBUCKET_PASS")
    base_br = extract_from_body(body, "BASE_BRANCH") or "main"
    pr_title = extract_from_body(body, "PR_TITLE")

    url_match = re.search(r"https://([\w\-.]+)/([a-zA-Z0-9.\-_/]+)", body)
    provider = "GITHUB"
    if url_match:
        domain = url_match.group(1).lower(); repo_path = url_match.group(2).replace(".git", "").strip()
        full_git_url = f"https://{domain}/{repo_path}"
        if "gitlab" in domain: provider = "GITLAB"
    else:
        log("🔎 본문에 URL이 없어 Supabase 검색 시도...")
        found_scope = get_latest_scope_from_vault(sender, "GITHUB") or get_latest_scope_from_vault(sender, "GITLAB")
        if found_scope:
            full_git_url = found_scope
            m = re.search(r"https://([\w\-.]+)/([a-zA-Z0-9.\-_/]+)", full_git_url)
            if m:
                domain = m.group(1).lower(); repo_path = m.group(2).replace(".git", "").strip()
                if "gitlab" in domain: provider = "GITLAB"
        else:
            domain = "github.com"; repo_path = f"{owner}/{repo}"; full_git_url = f"https://github.com/{repo_path}"

    if provider == "GITHUB" and gh_token: upsert_credential(sender, provider, gh_token, full_git_url)
    elif provider == "GITLAB" and gl_token: upsert_credential(sender, provider, gl_token, full_git_url)

    final_token = get_credential_from_vault(sender, provider, full_git_url) or (GITHUB_PAT_ENV if provider == "GITHUB" else None)
    if not final_token:
        send_agent_email(sender, subject, "인증 정보 부족", full_git_url, lang_code, "Denied")
        update_task_status("failed"); sys.exit(1)

    auth_url = f"https://oauth2:{final_token}@{domain}/{repo_path}.git"
    update_task_status("running")
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    try:
        log(f"📡 저장소 접근: {full_git_url}")
        _, stderr, code = run_command_list(["git", "clone", "--depth", "1", auth_url, work_dir])
        if code != 0:
            send_agent_email(sender, subject, f"인증 실패: {stderr}", full_git_url, lang_code, "Denied")
            update_task_status("failed"); sys.exit(1)

        run_command_list(["git", "fetch", "origin", base_br], cwd=work_dir)
        run_command_list(["git", "checkout", base_br], cwd=work_dir)

        log("🤖 Gemini 작업 시작...")
        instr = f"[TASK]\nSubject: {subject}\nBody: {body}\n\n[INSTRUCTION]\n1. {work_dir} 기준 작업.\n2. '/src/views/guide/pages/pub'와 실제 구현 화면 비교.\n3. 분석 결과를 리포트에 상세히 기록."
        stdout, _, code = run_command_list(["gemini", "-m", GEMINI_MODEL, "--raw-output", "--accept-raw-output-risk", "--yolo", "--include-directories", work_dir, "-p", instr])
        
        # 변경 사항 확인
        st, _, _ = run_command_list(["git", "status", "--porcelain"], cwd=work_dir)
        if not st.strip():
            log("ℹ️ 변경 사항 없음."); send_agent_email(sender, subject, "변경 사항 없음", full_git_url, lang_code, "Success"); update_task_status("completed"); return

        new_branch = f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "inchAgent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "admin.key.in@gmail.com"], cwd=work_dir)
        run_command_list(["git", "checkout", "-b", new_branch], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {subject}"], cwd=work_dir)
        p_out, p_err, p_code = run_command_list(["git", "push", "origin", new_branch], cwd=work_dir)

        if p_code == 0:
            res_url = full_git_url
            if provider == "GITHUB":
                pr = requests.post(f"https://api.github.com/repos/{repo_path}/pulls", headers={"Authorization": f"token {final_token}"}, json={"title": f"🚀 {subject}", "body": stdout, "head": new_branch, "base": base_br}).json()
                res_url = pr.get('html_url', res_url)
            update_task_status("completed", branch_name=new_branch, pr_url=res_url)
            if source == "kakao": send_kakao_report(sender, subject, stdout, res_url)
            send_agent_email(sender, subject, stdout, res_url, lang_code, "Success")
        else: raise Exception(f"Push failed: {p_err}")
    except Exception:
        log(f"❌ 에러: {traceback.format_exc()}"); update_task_status("failed"); sys.exit(1)

if __name__ == "__main__": main()
