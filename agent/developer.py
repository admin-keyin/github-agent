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

def send_completion_email(to_email, subject, spec, result_url, lang_code="ko"):
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")
    private_key = os.getenv("EMAILJS_PRIVATE_KEY")
    
    if not all([service_id, template_id, public_key, private_key]):
        print("⚠️ EmailJS 설정이 누락되었습니다.")
        return

    to_email = to_email.strip() if to_email else ""
    if not to_email: return

    # 언어별 문구 설정
    texts = {
        "ko": {"title": "🚀 작업 성공 리포트", "msg": "요청하신 작업이 성공적으로 완료되었습니다.", "btn": "결과 확인하기", "footer": "본 메일은 자동 발송되었습니다."},
        "en": {"title": "🚀 Task Completion Report", "msg": "The requested task has been successfully completed.", "btn": "View Results", "footer": "This is an automated email."},
        "ja": {"title": "🚀 作業完了レポート", "msg": "ご依頼いただいた作業が正常に完了しました。", "btn": "結果を確認する", "footer": "このメールは自動送信되었습니다."},
    }
    t = texts.get(lang_code, texts["en"])

    print(f"📤 EmailJS 발송 시도... (수신자: {to_email}, 언어: {lang_code})")
    
    html_content = f"""
    <div style="font-family: sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #2e7d32; text-align: center;">{t['title']}</h2>
        <p><b>"{subject}"</b> {t['msg']}</p>
        
        <div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #2196f3; margin: 20px 0;">
            <p style="white-space: pre-wrap; color: #555; font-size: 0.95em;">{spec}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{result_url}" style="background: #2196f3; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                📦 {t['btn']}
            </a>
        </div>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;"/>
        <p style="font-size: 0.85em; color: #888; text-align: center;">{t['footer']}</p>
    </div>
    """

    url = "https://api.emailjs.com/api/v1.0/email/send"
    data = {
        "service_id": service_id, "template_id": template_id, "user_id": public_key, "accessToken": private_key,
        "template_params": {
            "to_email": to_email,
            "subject": f"✅ {subject}",
            "html_body": html_content # 템플릿에서 {{html_body}} 사용 권장
        }
    }
    
    try:
        res = requests.post(url, json=data, timeout=15)
        if res.status_code == 200: print(f"📧 이메일 발송 성공!")
        else: print(f"❌ 이메일 발송 실패: {res.status_code} - {res.text}")
    except Exception as e: print(f"❌ 이메일 예외: {e}")

def run_command_list(args, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_repo_contents(work_dir):
    context = ""
    if not os.path.exists(work_dir): return "New Repository (Empty)"
    for root, _, files in os.walk(work_dir):
        if any(x in root for x in ['node_modules', '.git', '.next']): continue
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.json', '.md')):
                rel_path = os.path.relpath(os.path.join(root, file), work_dir)
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        context += f"\n-- File: {rel_path} --\n{f.read()}\n"
                except: pass
    return context or "Empty Project"

def extract_json(text):
    match = re.search(r"(\{.*?\})", text, re.DOTALL)
    if not match:
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start:end+1]
    return match.group(1) if match else text

def call_gemini_cli(prompt, phase_name="Thinking"):
    print(f"🧠 Gemini가 {phase_name} 중...")
    full_prompt = f"Output ONLY JSON. No talk. Language: Follow user's input language.\n\nTask: {prompt}"
    cmd = ["gemini", "-m", GEMINI_MODEL, "--raw-output", "--yolo", "-p", full_prompt]
    stdout, _, code = run_command_list(cmd)
    if code != 0: return {}
    try:
        return json.loads(extract_json(stdout))
    except:
        try: return json.loads(re.search(r"\{.*\}", stdout, re.DOTALL).group())
        except: return {}

def create_github_repo(name):
    print(f"🆕 새 저장소 생성 중: {name}")
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "vnd.github.v3+json"}
    res = requests.post(url, headers=headers, json={"name": name, "private": False, "auto_init": True})
    return res.json().get("full_name"), res.json().get("clone_url")

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    sender = os.getenv("SENDER", "")
    
    # 언어 감지 (단순 키워드 기반 또는 AI에게 위임)
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    git_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    is_new_repo = False
    
    if git_match:
        repo_full_name = git_match.group(1).replace(".git", "")
        auth_url = f"https://oauth2:{GITHUB_PAT}@github.com/{repo_full_name}.git"
    else:
        repo_name = f"agent-task-{int(time.time())}"
        repo_full_name, clone_url = create_github_repo(repo_name)
        if not repo_full_name:
            print("❌ 저장소 생성 실패")
            return
        auth_url = clone_url.replace("https://", f"https://oauth2:{GITHUB_PAT}@")
        is_new_repo = True

    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 에이전트 가동: {repo_full_name} (New: {is_new_repo})")
    update_task_status("running")

    try:
        # 1. 컨텍스트 수집 (새 저장소면 생략)
        if not is_new_repo:
            run_command_list(["git", "clone", auth_url, work_dir])
            repo_context = get_repo_contents(work_dir)
        else:
            os.makedirs(work_dir, exist_ok=True)
            run_command_list(["git", "clone", auth_url, work_dir]) # auto_init=True 이므로 클론 가능
            repo_context = "New Repository. Provide full scaffolding (e.g. Next.js, README)."

        # 2. 전략 수립
        plan_prompt = f"Lang: {lang_code}\nRepo: {repo_context}\nTask: {subject}\n{body}\n\n결과 형식: {{\"explanation\": \"상세 사양 (요청자 언어로)\", \"lang\": \"{lang_code}\"}}"
        plan = call_gemini_cli(plan_prompt, "전략 수립")
        spec = plan.get('explanation', 'Processing...')
        actual_lang = plan.get('lang', lang_code)

        # 3. 코드 작성
        impl_prompt = f"Lang: {actual_lang}\nSpec: {spec}\n\n모든 파일의 전체 코드를 포함한 JSON을 생성하세요. 형식: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\" }}]}}"
        impl = call_gemini_cli(impl_prompt, "코드 작성")
        
        changes = impl.get('changes', [])
        for c in changes:
            path = os.path.join(work_dir, c['path'].lstrip('./'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f: f.write(c['content'])
            print(f"🛠 파일 작성: {c['path']}")

        # 4. Git & Push
        branch_name = "main" if is_new_repo else f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "Agent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "agent@internal.com"], cwd=work_dir)
        
        if not is_new_repo:
            run_command_list(["git", "checkout", "-b", branch_name], cwd=work_dir)
        
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {subject}"], cwd=work_dir)
        _, _, code = run_command_list(["git", "push", "origin", branch_name, "--force" if is_new_repo else ""], cwd=work_dir)

        if code == 0:
            if is_new_repo:
                result_url = f"https://github.com/{repo_full_name}"
            else:
                pr_res = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {GITHUB_PAT}"}, json={"title": f"🚀 {subject}", "body": spec, "head": branch_name, "base": "main"}).json()
                result_url = pr_res.get('html_url', f"https://github.com/{repo_full_name}")

            print(f"✅ 완료: {result_url}")
            update_task_status("completed", branch_name=branch_name, pr_url=result_url)
            if sender:
                send_completion_email(sender, subject, spec, result_url, actual_lang)

    except Exception:
        print(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
