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
        "Authorization": "Bearer " + str(SUPABASE_KEY),
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
    print("Executing: " + command)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "true"
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print("❌ Command Failed: " + str(result.stderr))
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def call_ai(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt + "\n\n반드시 다른 설명 없이 오직 순수 JSON 데이터만 답변하세요. 마크다운 기호 없이 { 로 시작해서 } 로 끝나야 합니다.",
        "stream": False,
        "format": "json"
    }
    try:
        res = requests.post(OLLAMA_HOST + "/api/generate", json=payload, timeout=600)
        text = res.json().get('response', '{}')
        return json.loads(text)
    except Exception as e:
        print("❌ AI 호출/파싱 실패: " + str(e))
        return {}

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "")
    
    if not GITHUB_PAT:
        print("🚨 GITHUB_PAT 미설정")
        update_task_status("failed")
        return
    
    git_match = re.search(r"https://github\.com/([\w\-]+/[\w\-.]+)", body)
    if not git_match:
        print("❌ URL 미발견")
        update_task_status("failed")
        return
        
    repo_full_name = git_match.group(1).replace(".git", "")
    auth_url = "https://oauth2:" + str(GITHUB_PAT) + "@github.com/" + repo_full_name + ".git"
    work_dir = os.path.join(os.getcwd(), "external_repo")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)

    print("🚀 작업 시작: " + repo_full_name)
    update_task_status("running")

    try:
        # 초대 수락 시도
        requests.get("https://api.github.com/user/repository_invitations", headers={"Authorization": "token " + str(GITHUB_PAT)})

        # 클론
        run_command("git clone " + auth_url + " " + work_dir)
        
        # 전략 수립 프롬프트
        plan_prompt = "당신은 시니어 개발자입니다. 다음 요구사항을 해결하기 위한 구체적인 파일 목록과 수정 계획을 세우세요.\n요구사항: " + subject + "\n상세: " + body + "\n형식: {\"explanation\": \"...\"}"
        plan = call_ai(plan_prompt)
        explanation = plan.get('explanation', 'Next.js 패키지 구성')
        print("📝 전략: " + explanation)

        # 구현 프롬프트 (가장 중요: 실행 가능성 강제)
        impl_prompt = "다음 전략에 따라 '실제 실행 가능한' 코드를 작성하세요: " + explanation + "\n" + \
                      "요구사항: " + subject + "\n\n" + \
                      "**반드시 준수할 사항:**\n" + \
                      "1. package.json에는 'next', 'react', 'react-dom'이 반드시 포함되어야 합니다.\n" + \
                      "2. package.json에 'dev', 'build', 'start' 스크립트를 반드시 넣으세요.\n" + \
                      "3. 소스 코드는 생략 없이 전체 내용을 작성하세요.\n" + \
                      "4. 'public/favicon.ico'나 'styles/globals.css' 같은 기본 파일도 필요하다면 포함하세요.\n\n" + \
                      "형식: {\"changes\": [{\"path\": \"package.json\", \"content\": \"...\"}, {\"path\": \"pages/index.js\", \"content\": \"...\"}]}"
        
        impl = call_ai(impl_prompt)
        changes = impl.get('changes', [])
        
        if not changes:
            raise Exception("AI가 변경 사항을 생성하지 못했습니다. (Empty changes)")

        for change in changes:
            path = os.path.join(work_dir, change['path'].lstrip('./'))
            content = change.get('content', '')
            if not content:
                print("⚠️ 경고: " + change['path'] + " 의 내용이 비어있습니다. 스킵합니다.")
                continue
            
            print("🛠 파일 생성/수정: " + change['path'] + " (" + str(len(content)) + " bytes)")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)

        # Git 푸시
        branch_name = "agent/setup-" + str(int(time.time()))
        run_command("git config user.name 'github-actions[bot]'", cwd=work_dir)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=work_dir)
        run_command("git checkout -b " + branch_name, cwd=work_dir)
        run_command("git add .", cwd=work_dir)
        run_command("git commit -m 'feat: initial next.js setup'", cwd=work_dir)
        run_command("git remote set-url origin " + auth_url, cwd=work_dir)
        _, err, code = run_command("git push origin " + branch_name, cwd=work_dir)
        
        if code != 0: raise Exception("푸시 실패: " + err)

        # PR 생성
        pr_res = requests.post("https://api.github.com/repos/" + repo_full_name + "/pulls", 
                               headers={"Authorization": "token " + str(GITHUB_PAT)},
                               json={"title": "🚀 [에이전트] " + subject, "body": body, "head": branch_name, "base": "main"}).json()
        
        final_url = pr_res.get("html_url", "PR 생성 확인 필요")
        print("✅ 완료: " + final_url)
        update_task_status("completed", branch_name=branch_name, pr_url=final_url)

    except Exception as e:
        print("❌ 에러 발생:\n" + traceback.format_exc())
        update_task_status("failed")

if __name__ == "__main__":
    main()
