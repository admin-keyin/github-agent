import os
import requests
import json
import subprocess
import traceback
import time
import re
import shutil
import sys

# --- 설정 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TASK_ID = os.getenv("TASK_ID")
GITHUB_PAT_ENV = os.getenv("GITHUB_PAT")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash-lite"

def log(msg):
    # 민감한 정보가 포함된 로그는 생략하거나 마스킹
    print(msg, flush=True)

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
        log("⚠️ EmailJS 설정 누락")
        return

    to_email = to_email.strip() if to_email else ""
    if not to_email: return

    config = {
        "ko": {
            "Success": {"badge": "성공", "title": "작업 완료 리포트", "desc": "요청하신 작업이 성공적으로 완료되었습니다.", "spec_label": "구현 상세", "btn": "결과 확인하기"},
            "Denied": {"badge": "오류", "title": "인증 또는 권한 오류", "desc": "저장소에 접근할 수 없습니다. 아래 양식을 확인해주세요.", "spec_label": "오류 내용", "btn": "저장소 확인"}
        },
        "en": {
            "Success": {"badge": "Success", "title": "Task Completed", "desc": "GitHub Agent has finished the work successfully.", "spec_label": "Details", "btn": "Review Results"},
            "Denied": {"badge": "Error", "title": "Auth/Access Error", "desc": "Cannot access the repository. Check the form below.", "spec_label": "Error Msg", "btn": "Check Repo"}
        }
    }
    
    lang = config.get(lang_code, config["en"])
    t = lang.get(status, lang["Success"])
    
    guide_html = ""
    if status == "Denied":
        guide_html = """
        <div style="margin-top: 20px; padding: 15px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; font-size: 13px;">
            <b style="color: #92400e;">💡 사용 가능한 변수 양식 (메일 본문에 포함)</b><br/>
            <code>GITHUB_TOKEN: ghp_xxx</code><br/>
            <code>GITLAB_TOKEN: glpat-xxx</code><br/>
            <code>BITBUCKET_USER: my_id</code><br/>
            <code>BITBUCKET_PASS: app_pass</code><br/>
            <code>BASE_BRANCH: develop</code>
        </div>
        """

    html_body = f"""
<div style="font-family: -apple-system, sans-serif; font-size: 15px; color: #334155; line-height: 1.6; max-width: 600px; margin: 20px auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;">
    <div style="background-color: #1e293b; padding: 32px 24px; text-align: center;">
      <div style="display: inline-block; background-color: {'#22c55e' if status == 'Success' else '#ef4444'}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 12px;">{t['badge']}</div>
      <h1 style="color: #ffffff; font-size: 22px; margin: 0;">{t['title']}</h1>
      <p style="color: #94a3b8; font-size: 14px; margin-top: 8px;">{t['desc']}</p>
    </div>
    <div style="padding: 32px 24px; background-color: #ffffff;">
      <label style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">Subject</label>
      <h2 style="font-size: 18px; color: #1e293b; margin: 4px 0 24px 0;">{subject}</h2>
      <label style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">{t['spec_label']}</label>
      <div style="margin-top: 12px; padding: 16px; background-color: #f8fafc; border-left: 4px solid #6366f1; border-radius: 4px; color: #475569; white-space: pre-wrap;">{spec}</div>
      {guide_html}
      <div style="text-align: center; margin-top: 40px;">
        <a href="{result_url}" target="_blank" style="background-color: #6366f1; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">{t['btn']}</a>
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
        if res.status_code == 200: log("📧 이메일 발송 완료!")
    except: pass

def run_command_list(args, cwd=None, input_data=None):
    clean_args = [str(arg) for arg in args if arg and str(arg).strip()]
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    # 프롬프트가 너무 길 경우 CMD 로그에서는 생략
    log(f"💻 CMD: {' '.join(clean_args[:10])}{' ...' if len(clean_args) > 10 else ''}")
    result = subprocess.run(clean_args, capture_output=True, text=True, cwd=cwd, env=env, input=input_data)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_repo_contents(work_dir):
    context = ""
    for root, _, files in os.walk(work_dir):
        if any(x in root for x in ['node_modules', '.git', '.next', 'dist', 'build', '.cache']): continue
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.html', '.css', '.vue', '.java', '.py')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        context += f"\n-- File: {os.path.relpath(os.path.join(root, file), work_dir)} --\n{f.read()}\n"
                except: pass
    return context or "Empty Project"

def extract_from_body(body, key):
    patterns = [fr"\[{key}\]\s*(\S+)", fr"{key}\s*[:=]\s*(\S+)"]
    for p in patterns:
        match = re.search(p, body, re.IGNORECASE)
        if match: return match.group(1)
    return None

def extract_json(text):
    # 1. ```json ... ``` 블록 찾기
    code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block:
        target = code_block.group(1)
    else:
        # 2. 블록이 없다면 가장 바깥쪽의 { } 찾기
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            target = text[start:end+1]
        else:
            log(f"⚠️ JSON 시작 기호({{)를 찾을 수 없습니다. 원본 길이: {len(text)}")
            return ""

    # 3. 비정상적인 따옴표 처리 및 줄바꿈 처리
    def repair_quotes(match):
        content = match.group(1).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{content}"'
    
    repaired = re.sub(r"'''(.*?)'''", repair_quotes, target, flags=re.DOTALL)
    return repaired

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    sender = os.getenv("SENDER", "")
    lang_code = "ko" if any(ord(c) > 0x1100 for c in body) else "en"

    vars = {
        "gh_token": extract_from_body(body, "GITHUB_TOKEN"),
        "gl_token": extract_from_body(body, "GITLAB_TOKEN"),
        "bb_user": extract_from_body(body, "BITBUCKET_USER"),
        "bb_pass": extract_from_body(body, "BITBUCKET_PASS"),
        "base_br": extract_from_body(body, "BASE_BRANCH") or "main",
        "pr_title": extract_from_body(body, "PR_TITLE")
    }

    url_match = re.search(r"https://([\w\-.]+)/(\S+)", body)
    is_new_repo = False
    domain = "github.com"
    token = vars['gh_token'] or GITHUB_PAT_ENV
    
    if url_match:
        domain = url_match.group(1)
        repo_path = url_match.group(2).replace(".git", "")
        if "github.com" in domain: auth_url = f"https://oauth2:{token}@github.com/{repo_path}.git"
        elif "gitlab" in domain: auth_url = f"https://oauth2:{vars['gl_token']}@{domain}/{repo_path}.git"
        elif "bitbucket" in domain: auth_url = f"https://{vars['bb_user']}:{vars['bb_pass']}@{domain}/{repo_path}.git"
        else: auth_url = f"https://{domain}/{repo_path}.git"
        repo_full_name = repo_path
    else:
        repo_name = f"agent-task-{int(time.time())}"
        headers = {"Authorization": f"token {GITHUB_PAT_ENV}", "Accept": "vnd.github.v3+json"}
        res = requests.post("https://api.github.com/user/repos", headers=headers, json={"name": repo_name, "auto_init": True}).json()
        repo_full_name = res.get("full_name")
        auth_url = res.get("clone_url", "").replace("https://", f"https://oauth2:{GITHUB_PAT_ENV}@")
        is_new_repo = True

    log(f"🚀 가동: {repo_full_name} (Base: {vars['base_br']})")
    update_task_status("running")

    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    try:
        log("📡 클론 중...")
        _, stderr, code = run_command_list(["git", "clone", auth_url, work_dir])
        if code != 0:
            send_agent_email(sender, subject, f"접근 실패: {stderr}", "", lang_code, "Denied")
            update_task_status("failed")
            return

        if not is_new_repo:
            log(f"🌿 브랜치 이동: {vars['base_br']}")
            run_command_list(["git", "fetch", "origin", vars['base_br']], cwd=work_dir)
            run_command_list(["git", "checkout", vars['base_br']], cwd=work_dir)

        log("📂 Gemini 호출 중 (Large Context)...")
        repo_context = get_repo_contents(work_dir)
        
        system_instruction = "You are a specialized JSON generator for code changes. DO NOT TALK. DO NOT EXPLAIN. ONLY OUTPUT VALID JSON."
        
        prompt = f"""### EXAMPLE INPUT ###
Subject: Update footer text
Body: Change '© 2024' to '© 2025' in footer.vue
Context: -- File: footer.vue --\n<div>© 2024 My App</div>

### EXAMPLE OUTPUT ###
{{
  "thought": "Update copyright year to 2025",
  "explanation": "Updated footer copyright year.",
  "changes": [
    {{ "path": "footer.vue", "content": "<div>© 2025 My App</div>" }}
  ]
}}

### REAL TASK ###
Subject: {subject}
Body: {body}

### CODE CONTEXT ###
{repo_context}

### FINAL JSON OUTPUT ###
"""
        
        log("🤖 Gemini CLI 실행 중...")
        # 프롬프트 파일 저장
        prompt_file = os.path.join(os.getcwd(), f".prompt_{int(time.time())}.txt")
        try:
            # 시스템 지시어를 프롬프트 본문에 직접 포함
            full_prompt = f"SYSTEM: {system_instruction}\n\n{prompt}"
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(full_prompt)
            
            # 지원되는 옵션만 사용
            stdout, stderr, code = run_command_list(
                [
                    "gemini", "-m", GEMINI_MODEL, 
                    "--raw-output", "--accept-raw-output-risk", "--yolo",
                    "-p", f"@{prompt_file}"
                ],
                cwd=os.getcwd()
            )
        finally:
            if os.path.exists(prompt_file):
                os.remove(prompt_file)
        
        if code != 0:
            log(f"❌ Gemini 실패: {stderr}")
            raise Exception("Gemini process error")

        try:
            res_data = json.loads(extract_json(stdout))
            spec = res_data.get('explanation', '작업 완료')
            changes = res_data.get('changes', [])
            if not changes: raise Exception("Empty Changes")
            for c in changes:
                p = os.path.join(work_dir, c['path'].lstrip('./'))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f: f.write(c['content'])
                log(f"🛠 파일 작성: {c['path']}")
        except:
            log(f"❌ 파싱 실패. 원본:\n{stdout[:1000]}...")
            raise Exception("JSON 파싱 실패")

        log("📤 푸시 중...")
        new_branch = "main" if is_new_repo else f"agent/task-{int(time.time())}"
        run_command_list(["git", "config", "user.name", "Agent"], cwd=work_dir)
        run_command_list(["git", "config", "user.email", "agent@internal.com"], cwd=work_dir)
        if not is_new_repo: run_command_list(["git", "checkout", "-b", new_branch], cwd=work_dir)
        run_command_list(["git", "add", "."], cwd=work_dir)
        run_command_list(["git", "commit", "-m", f"feat: {subject}"], cwd=work_dir)
        
        push_args = ["git", "push", "origin", new_branch]
        if is_new_repo: push_args.append("--force")
        _, stderr, p_code = run_command_list(push_args, cwd=work_dir)

        if p_code == 0:
            res_url = f"https://{domain}/{repo_full_name}"
            if "github.com" in domain and not is_new_repo:
                pr = requests.post(f"https://api.github.com/repos/{repo_full_name}/pulls", headers={"Authorization": f"token {token}"}, json={"title": vars['pr_title'] or f"🚀 {subject}", "body": spec, "head": new_branch, "base": vars['base_br']}).json()
                res_url = pr.get('html_url', res_url)
            log(f"✅ 성공! URL: {res_url}")
            update_task_status("completed", branch_name=new_branch, pr_url=res_url)
            send_agent_email(sender, subject, spec, res_url, lang_code, "Success")
        else:
            log(f"❌ 푸시 실패: {stderr}")
            raise Exception("Git Push Failed")

    except Exception:
        log(f"❌ 에러:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__": main()
