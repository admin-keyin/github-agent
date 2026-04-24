# 🤖 Gemini Email-to-Code Agent

이 프로젝트는 이메일로 수신된 작업 요청을 분석하여 소스 코드를 자동으로 수정하고, Pull Request를 생성한 후 결과를 보고하는 자율형 에이전트입니다.

## 🛠 주요 기능
- **자율 코드 수정**: Gemini CLI를 사용하여 복잡한 요구사항을 코드로 구현.
- **보안 자격 증명 관리**: 사용자의 Git PAT(Personal Access Token)를 암호화하여 Supabase에 보관.
- **멀티 채널 보고**: 작업 완료 후 이메일 및 카카오톡으로 리포트 발송.
- **이메일 기반 권한 제어**: 요청자 이메일과 일치하는 보안 설정만 조회하여 보안 강화.

---

## 🔐 보안 설정 가이드

### 1. 환경 변수 설정 (`.env`)
Self-hosted Runner 또는 로컬 실행 환경의 `.env` 파일에 아래 내용을 설정해야 합니다.

```env
# Supabase 설정
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_or_service_key

# 보안 키 (가장 중요)
# 이 키를 사용하여 Supabase의 민감 정보를 암복호화합니다.
MASTER_ENCRYPTION_KEY=your_secure_master_password

# 보고 서비스 설정
EMAILJS_SERVICE_ID=...
SOLAPI_API_KEY=...
```

### 2. 수동 자격 증명(PAT) 추가 방법
사용자가 Supabase에 직접 Git 토큰을 추가하려면, 반드시 에이전트가 사용하는 알고리즘으로 **암호화**해서 넣어야 합니다.

#### 🔐 암호화 도구 사용법
```bash
# 1. 필수 라이브러리 설치 (이미 설치했다면 생략 가능)
pip install cryptography

# 2. 암호화 도구 실행
python3 utils/encrypt_tool.py
```
1. 실행 후 `MASTER_ENCRYPTION_KEY`를 확인합니다. (.env에 설정되어 있으면 자동 인식)
2. 암호화할 **실제 Git PAT**를 입력합니다.
3. 출력된 **암호문(gAAAAABm...)**을 복사하여 Supabase의 `user_credentials` 테이블 내 `key_value` 컬럼에 붙여넣습니다.

---

## 🚀 운영 워크플로우

1. **사용자 요청**: 사용자가 본인의 이메일로 작업 지시서(Git URL 포함)를 발송합니다.
2. **트리거**: GitHub Action이 실행되어 에이전트(`agent/developer.py`)를 가동합니다.
3. **보안 조회**: 에이전트가 발신자 이메일을 확인하고, Supabase에서 해당 사용자의 암호화된 토큰을 가져와 `MASTER_ENCRYPTION_KEY`로 복호화합니다.
4. **작업 수행**: Gemini CLI가 저장소를 클론하고 코드를 수정합니다.
5. **완료 보고**: PR을 생성하고 사용자에게 알림을 보냅니다.

## 📂 주요 파일 구조
- `agent/developer.py`: 메인 에이전트 로직 및 암복호화 엔진.
- `utils/encrypt_tool.py`: 수동 데이터 입력을 위한 평문 암호화 도구.
- `.github/workflows/dev-agent.yml`: GitHub Runner 워크플로우 설정.
- `SYSTEM_ARCHITECTURE.md`: 시스템 아키텍처 및 보안 상세 설계 문서.

---
**주의**: `MASTER_ENCRYPTION_KEY`가 유출되거나 분실될 경우, Supabase에 저장된 모든 토큰을 다시 설정해야 합니다. 키 관리에 유의하세요.
