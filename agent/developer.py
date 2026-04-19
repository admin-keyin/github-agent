import os
import requests
import json
import subprocess
import traceback

# --- 설정 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Gemini 2.0 Flash 모델 사용 (빠르고 무료 티어 제공)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def call_gemini(prompt):
    """Google Gemini API 호출"""
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
        }
    }
    response = requests.post(GEMINI_URL, json=payload)
    res_json = response.json()
    try:
        # Gemini 응답 파싱
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini API 응답 오류: {res_json}")
        raise e

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def get_repo_context():
    """파일 구조 추출"""
    # GitHub Action 환경에 맞는 find 명령어
    tree, _ = run_command("find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'")
    return tree

def main():
    subject = os.getenv("TASK_SUBJECT", "No Subject")
    body = os.getenv("TASK_BODY", "No Body")
    
    print(f"🚀 작업 시작 (Cloud Mode): {subject}")
    update_task_status("running")
    
    try:
        # 1. 컨텍스트 파악
        context = get_repo_context()
        
        # 2. 에이전트 전략 수립
        plan_prompt = f"""
        당신은 시니어 풀스택 개발자입니다. 다음 요구사항을 해결하기 위한 상세 계획을 JSON으로 답변하세요.
        요구사항: {subject} / {body}
        현재 프로젝트 구조:
        {context}
        
        응답 형식:
        {{
          "explanation": "작업 전략 설명",
          "new_branch": "agent/feature-task"
        }}
        """
        plan_raw = call_gemini(plan_prompt)
        plan = json.loads(plan_raw)
        print(f"📝 전략: {plan['explanation']}")
        
        # 3. 브랜치 생성
        branch_name = f"agent/task-{os.urandom(4).hex()}"
        run_command(f"git checkout -b {branch_name}")

        # 4. 파일 구현
        implementation_prompt = f"""
        요구사항: {subject} / {body}
        전략: {plan['explanation']}
        
        위 내용을 바탕으로 실제 코딩을 수행하세요. 반드시 전체 파일 내용을 포함한 JSON으로 응답하세요.
        응답 형식:
        {{
          "changes": [
            {{"path": "경로", "content": "전체 코드", "action": "create|update"}}
          ]
        }}
        """
        implementation_raw = call_gemini(implementation_prompt)
        implementation = json.loads(implementation_raw)
        
        for change in implementation.get('changes', []):
            path = change['path']
            print(f"🛠  파일 수정 중: {path}")
            # 보안: .env 파일 등은 수정하지 못하도록 방어 로직 추가 가능
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, "w") as f:
                f.write(change['content'])

        # 5. Git 커밋
        run_command("git config user.name 'github-actions[bot]'")
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'")
        run_command("git add .")
        run_command(f'git commit -m "feat: {subject}"')
        run_command(f"git push origin {branch_name}")
        
        print(f"✅ 작업 완료! 브랜치: {branch_name}")
        update_task_status("completed", branch_name=branch_name)

    except Exception as e:
        print(f"❌ 에이전트 실행 중 오류 발생:\n{traceback.format_exc()}")
        update_task_status("failed")

if __name__ == "__main__":
    main()
