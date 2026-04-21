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

    # 다국어 및 상태별 텍스트 설정
    config = {
        "ko": {
            "Success": {"badge": "성공", "title": "작업이 성공적으로 완료되었습니다", "desc": "에이전트가 요청하신 작업을 마쳤습니다.", "sub_label": "작업 제목", "spec_label": "구현 상세 내용", "btn": "결과 확인하기"},
            "Denied": {"badge": "권한 부족", "title": "저장소 접근 권한이 없습니다", "desc": "비공개 저장소에 접근할 수 없습니다. 권한을 확인해주세요.", "sub_label": "작업 제목", "spec_label": "안내 사항", "btn": "저장소로 이동"}
        },
        "en": {
            "Success": {"badge": "Success", "title": "Task Completed Successfully", "desc": "GitHub Agent has finished the requested work.", "sub_label": "Subject", "spec_label": "Implementation Details", "btn": "Review Pull Request"},
            "Denied": {"badge": "Denied", "title": "Access Denied to Repository", "desc": "The agent cannot access the private repository. Please grant access.", "sub_label": "Subject", "spec_label": "Information", "btn": "Go to Repository"}
        },
        "ja": {
            "Success": {"badge": "成功", "title": "作業が正常に完了しました", "desc": "エージェントが依頼された作業を完了しました。", "sub_label": "作業件名", "spec_label": "実装の詳細", "btn": "結果を確認する"},
            "Denied": {"badge": "アクセス拒否", "title": "リポジトリへのアクセス権限がありません", "desc": "非公開リポジトリにアクセスできません。権限を確認してください。", "sub_label": "作業件名", "spec_label": "案内事項", "btn": "リポジトリへ移動"}
        }
    }
    
    lang = config.get(lang_code, config["en"])
    t = lang.get(status, lang["Success"])
    badge_color = "#22c55e" if status == "Success" else "#ef4444"
    btn_color = "#6366f1" if status == "Success" else "#1e293b"

    html_body = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #334155; line-height: 1.6;">
  <div style="max-width: 600px; margin: 20px auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <div style="background-color: #1e293b; padding: 32px 24px; text-align: center;">
      <div style="display: inline-block; background-color: {badge_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px;">
        {t['badge']}
      </div>
      <h1 style="color: #ffffff; font-size: 22px; margin: 0; font-weight: 700;">{t['title']}</h1>
      <p style="color: #94a3b8; font-size: 14px; margin-top: 8px;">{t['desc']}</p>
    </div>
    <div style="padding: 32px 24px; background-color: #ffffff;">
      <div style="margin-bottom: 24px;">
        <label style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">{t['sub_label']}</label>
        <h2 style="font-size: 18px; color: #1e293b; margin: 4px 0 0 0;">{subject}</h2>
      </div>
      <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 24px 0;" />
      <div style="margin-bottom: 32px;">
        <label style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">{t['spec_label']}</label>
        <div style="margin-top: 12px; padding: 16px; background-color: #f8fafc; border-left: 4px solid {btn_color}; border-radius: 4px; color: #475569; white-space: pre-wrap;">{spec}</div>
      </div>
      <div style="text-align: center; margin-top: 40px;">
        <a href="{result_url}" target="_blank" style="background-color: {btn_color}; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">
          {t['btn']}
        </a>
        <p style="margin-top: 16px; font-size: 13px; color: #94a3b8;">Receiver: <span style="color: #64748b;">{to_email}</span></p>
      </div>
    </div>
    <div style="text-align: center; background-color: #f1f5f9; padding: 24px; border-top: 1px solid #e2e8f0;">
      <p style="margin: 0; font-size: 13px; color: #64748b;">This is an automated report generated by <strong>GitHub Agent</strong>.</p>
    </div>
  </div>
</div>
"""
    data = {
        "service_id": service_id, "template_id": template_id, "user_id": public_key, "accessToken": private_key,
        "template_params": {"to_email": to_email, "subject": f"[{t['badge']}] {subject}", "html_body": html_body}
    }
    try:
        res = requests.post("https://api.emailjs.com/api/v1.0/email/send", json=data, timeout=15)
        if res.status_code == 200: print(f"📧 이메일({status}) 발송 성공!")
    except Exception as e: print(f"❌ 이메일 에러: {e}")

def run_command_list(args, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_repo_contents(work_dir):
    context = ""
    if not os.path.exists(work_dir): return "New Repository"
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
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    git_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    is_new_repo = False
    
    if git_match:
        repo_full_name = git_match.group(1).replace(".git", "")
        auth_url = f"https://oauth2:{GITHUB_PAT}@github.com/{repo_full_name}.git"
    else:
        repo_name = f"agent-task-{int(time.time())}"
        repo_full_name, clone_url = create_github_repo(repo_name)
        if not repo_full_name: return
        auth_url = clone_url.replace("https://", f"https://oauth2:{GITHUB_PAT}@")
        is_new_repo = True

    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print(f"🚀 에이전트 가동: {repo_full_name}")
    update_task_status("running")

    try:
        # 1. 저장소 접근 시도
        _, stderr, code = run_command_list(["git", "clone", auth_url, work_dir])
        if code != 0:
            if "terminal" in stderr or "authenticate" in stderr or "repository not found" in stderr:
                print("❌ 접근 권한 부족")
                reason = "저장소에 접근할 수 없습니다. 에이전트 계정에 협업자(Collaborator) 권한을 추가해주세요." if lang_code == "ko" else "Access denied. Please add the agent account as a collaborator."
                send_agent_email(sender, subject, reason, f"https://github.com/{repo_full_name}", lang_code, "Denied")
                update_task_status("failed")
                return
            else:
                raise Exception(f"Git Clone Error: {stderr}")

        repo_context = get_repo_contents(work_dir) if not is_new_repo else "New Project Scaffolding"
        
        # 2. 전략 및 코드
        plan = call_gemini_cli(f"Lang: {lang_code}\nRepo: {repo_context}\nTask: {subject}\n{body}\n\n결과 형식: {{\"explanation\": \"상세 사양\", \"lang\": \"{lang_code}\"}}", "전략 수립")
        spec = plan.get('explanation', 'Processing...')
        actual_lang = plan.get('lang', lang_code)

        impl = call_gemini_cli(f"Lang: {actual_lang}\nSpec: {spec}\n\n전체 코드 포함 JSON: {{\"changes\": [{{ \"path\": \"...\", \"content\": \"...\" }}]}}", "코드 작성")
        
        for c in impl.get('changes', []):
            path = os.path.join(work_dir, c['path'].lstrip('./'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f: f.write(c['content'])

        # 3. Git Push
        branch_name = "main" if is_new_repo else f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "Agent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "agent@internal.com"], cwd=work_dir)
        if not is_new_repo: run_command_list(["git", "checkout", "-b", branch_name], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {subject}"], cwd=work_dir)
        _, _, p_code = run_command_list(["git", "push", "origin", branch_name, "--force" if is_new_repo else ""], cwd=work_dir)

        if p_code == 0:
            result_url = f"https://github.com/{repo_full_name}"
            if not is_new_repo:
                pr = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {GITHUB_PAT}"}, json={"title": f"🚀 {subject}", "body": spec, "head": branch_name, "base": "main"}).json()
                result_url = pr.get('html_url', result_url)
            
            update_task_status("completed", branch_name=branch_name, pr_url=result_url)
            send_agent_email(sender, subject, spec, result_url, actual_lang, "Success")

    except Exception:
        print(f"❌ 에러: {traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
