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

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT_ENV = os.getenv("GITHUB_PAT")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
MASTER_ENCRYPTION_KEY = os.getenv("MASTER_ENCRYPTION_KEY", "default-secret-key-for-local-test")

# 암호화 엔진 초기화
def get_cipher():
    """마스터 키를 기반으로 암호화 키를 생성합니다."""
    salt = b'static_salt_for_now' # 운영 시에는 별도 보관 권장
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
    
    encrypted_value = encrypt_value(value)
    log(f"🔒 Credential 암호화 완료 (대상: {email})")
    
    url = f"{SUPABASE_URL}/rest/v1/user_credentials"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    data = {"user_email": email, "key_name": provider.upper(), "key_value": encrypted_value, "scope": git_url}
    try: requests.post(f"{url}?on_conflict=user_email,key_name,scope", headers=headers, json=data, timeout=10)
    except: pass

def get_credential_from_vault(email, provider, git_url):
    if not all([SUPABASE_URL, SUPABASE_KEY, email, provider, git_url]): return None
    url = f"{SUPABASE_URL}/rest/v1/user_credentials?user_email=eq.{email}&key_name=eq.{provider.upper()}&scope=eq.{git_url}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res: 
            encrypted_value = res[0].get("key_value")
            decrypted = decrypt_value(encrypted_value)
            if decrypted:
                log(f"🔓 Credential 복호화 성공 (대상: {email})")
                return decrypted
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
    lang = config.get(lang_code, config["en"])
    t = lang.get(status, lang["Success"])
    
    color = "#6366f1" if status == "Success" else "#ef4444"
    html_body = f"<div style='font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;'><h2>{t['title']}</h2><p>{t['desc']}</p><div style='padding: 15px; background: #f9f9f9; border-left: 4px solid {color};'>{spec}</div><br/><a href='{result_url}' style='padding: 10px 20px; background: #6366f1; color: #fff; text-decoration: none; border-radius: 5px;'>{t['btn']}</a></div>"
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
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    gh_token = extract_from_body(body, "GITHUB_TOKEN")
    gl_token = extract_from_body(body, "GITLAB_TOKEN")
    bb_user = extract_from_body(body, "BITBUCKET_USER")
    bb_pass = extract_from_body(body, "BITBUCKET_PASS")
    base_br = extract_from_body(body, "BASE_BRANCH") or "main"
    pr_title = extract_from_body(body, "PR_TITLE")

    # URL 추출
    url_match = re.search(r"https://([\w\-.]+)/([a-zA-Z0-9.\-_/]+)", body)
    if url_match:
        domain = url_match.group(1).lower()
        repo_path = url_match.group(2).replace(".git", "").strip()
        full_git_url = f"https://{domain}/{repo_path}"
    else:
        domain = "github.com"; repo_path = f"{owner}/{repo}"; full_git_url = f"https://github.com/{repo_path}"

    provider = "GITHUB"
    if "gitlab" in domain: provider = "GITLAB"
    elif "bitbucket" in domain: provider = "BITBUCKET"

    # 1. 이메일에 포함된 토큰이 있으면 우선 저장
    if provider == "GITHUB" and gh_token: upsert_credential(sender, provider, gh_token, full_git_url)
    elif provider == "GITLAB" and gl_token: upsert_credential(sender, provider, gl_token, full_git_url)
    elif provider == "BITBUCKET" and bb_user and bb_pass: upsert_credential(sender, provider, f"{bb_user}:{bb_pass}", full_git_url)

    # 2. Supabase에서 조회 (이메일별 n개 가능)
    vault_token = get_credential_from_vault(sender, provider, full_git_url)
    
    # 3. Supabase에 없으면 환경 변수 기본 키(Default) 사용
    final_token = vault_token or (GITHUB_PAT_ENV if provider == "GITHUB" else None)

    if not final_token:
        log("❌ 인증 정보가 없습니다.")
        send_agent_email(sender, subject, "사용자 계정 또는 시스템 기본 인증 정보를 찾을 수 없습니다.", full_git_url, lang_code, "Denied")
        update_task_status("failed")
        sys.exit(1)

    auth_url = f"https://oauth2:{final_token}@{domain}/{repo_path}.git"
    if provider == "BITBUCKET": auth_url = f"https://{final_token}@{domain}/{repo_path}.git"
    
    update_task_status("running")
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    try:
        log(f"📡 저장소 접근 시도: {full_git_url}")
        _, stderr, code = run_command_list(["git", "clone", "--depth", "1", auth_url, work_dir])
        
        # 4. 권한 부족 감지 및 메일 발송
        if code != 0:
            if any(err in stderr.lower() for err in ["401", "403", "authentication failed", "fatal: could not read"]):
                log(f"❌ 권한 거부: {stderr}")
                send_agent_email(sender, subject, f"Git 인증 실패(권한 부족): {stderr}", full_git_url, lang_code, "Denied")
                update_task_status("failed")
                sys.exit(1)
            raise Exception(f"Clone failed: {stderr}")

        run_command_list(["git", "fetch", "origin", base_br], cwd=work_dir)
        run_command_list(["git", "checkout", base_br], cwd=work_dir)

        log("🤖 Gemini 자율 작업 시작...")
        instruction = f"[TASK]\nSubject: {subject}\nBody: {body}\n\n[INSTRUCTION]\n1. Go to: {work_dir}\n2. Explore and apply requested changes.\n3. Verify results."
        stdout, _, code = run_command_list(["gemini", "-m", GEMINI_MODEL, "--raw-output", "--accept-raw-output-risk", "--yolo", "--include-directories", work_dir, "-p", instruction])
        if code != 0: raise Exception("Gemini process failed")

        spec = stdout or "작업 완료"
        log("🛠 작업 완료 (파일 수정됨)")

        new_branch = f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "inchAgent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "admin.key.in@gmail.com"], cwd=work_dir)
        run_command_list(["git", "checkout", "-b", new_branch], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {re.sub(r'^(fwd|re|fw)\s* : \s*', '', subject, flags=re.IGNORECASE).strip()}"], cwd=work_dir)
        
        log("📤 푸시 중...")
        _, stderr, p_code = run_command_list(["git", "push", "origin", new_branch], cwd=work_dir)

        if p_code == 0:
            res_url = full_git_url
            if provider == "GITHUB":
                pr = requests.post(f"https://api.github.com/repos/{repo_path}/pulls", headers={"Authorization": f"token {final_token}"}, json={"title": pr_title or f"🚀 {subject}", "body": spec, "head": new_branch, "base": base_br}).json()
                res_url = pr.get('html_url', res_url)
            log(f"✅ 성공! URL: {res_url}")
            update_task_status("completed", branch_name=new_branch, pr_url=res_url)
            if source == "kakao": send_kakao_report(sender, subject, spec, res_url)
            send_agent_email(sender, subject, spec, res_url, lang_code, "Success")
        else:
            raise Exception(f"Git Push Failed: {stderr}")
    except Exception:
        log(f"❌ 에러 발생:\n{traceback.format_exc()}")
        update_task_status("failed")
        sys.exit(1)

if __name__ == "__main__": main()
