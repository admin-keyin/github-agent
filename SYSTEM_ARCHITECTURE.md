# 🚀 Email-to-Code Agent System Architecture

이 시스템은 이메일을 통해 전달된 작업을 GitHub Runner가 수신하여, 보안이 강화된 환경에서 자율적으로 코드를 수정하고 결과를 보고하는 자동화 엔진입니다.

## 1. 전체 워크플로우 (End-to-End)

1.  **이메일 수신 및 트리거**:
    *   사용자가 특정 형식(Git 주소, PAT, 작업 내용 포함)으로 이메일을 발송합니다.
    *   이메일 서비스(또는 외부 스케줄러)가 GitHub Repository Dispatch를 트리거합니다.
    *   GitHub Action이 실행되며 이메일의 발신자(`sender`), 제목(`subject`), 본문(`body`)을 페이로드로 전달받습니다.

2.  **보안 설정 조회 (Supabase & Encryption)**:
    *   **동일 이메일 검증**: Runner는 수신된 이메일 주소를 키로 사용하여 Supabase의 `user_credentials` 테이블에서 해당 사용자의 암호화된 설정을 조회합니다.
    *   **복호화**: GitHub Secrets에 저장된 `ENCRYPTION_KEY`(Master Key)를 사용하여 조회된 토큰(PAT 등)을 메모리 내에서 복호화합니다.
    *   **보안 규칙**: 각 사용자는 본인의 이메일로 저장된 정보만 참조할 수 있으며, 실제 정보는 Supabase에 암호화된 상태로 보관됩니다.

3.  **자율 작업 (Gemini CLI)**:
    *   복호화된 PAT를 사용하여 대상 저장소를 `self-hosted` 러너에 클론합니다.
    *   **Gemini CLI**가 실행되어 본문의 요구사항을 분석하고 소스 코드를 직접 수정합니다. (`--yolo` 모드)

4.  **결과 보고**:
    *   수정된 내용을 새 브랜치에 푸시하고 Pull Request를 생성합니다.
    *   작업 완료 리포트(수정 요약 및 PR 링크)를 사용자의 이메일(EmailJS) 및 카카오톡(Solapi)으로 발송합니다.

## 2. 보안 설계 (Security Measures)

### 🔒 데이터 암호화 (Encryption)
*   **알고리즘**: `AES-256-GCM` (또는 CBC)
*   **키 관리**: GitHub Secrets에 `MASTER_ENCRYPTION_KEY`를 보관하고, Runner 실행 시에만 환경 변수로 주입합니다.
*   **저장 데이터**: Git PAT, 프라이빗 설정 정보 등 민감 정보는 모두 암호화되어 Supabase에 저장됩니다.

### 🛡️ 접근 제어 (Access Control)
*   **Supabase RLS (Row Level Security)**: `user_email` 컬럼을 기준으로 정책을 설정하여, 권한 없는 조회를 원천 차단합니다.
*   **휘발성 환경**: 작업 종료 후 Runner의 작업 디렉토리 및 메모리 내 복호화 데이터는 즉시 삭제됩니다.

## 3. 주요 구성 요소 및 파일

*   `.github/workflows/dev-agent.yml`: GitHub Action 워크플로우 정의 (트리거 및 환경 설정)
*   `agent/developer.py`: 메인 에이전트 로직 (암호화/복호화, 저장소 제어, Gemini 호출)
*   `utils/supabase.js`: Supabase 연동 유틸리티 (웹 관리용)
*   `SYSTEM_ARCHITECTURE.md`: 시스템 설계 및 운영 가이드 (본 문서)

## 4. 환경 변수 요구사항
*   `SUPABASE_URL`, `SUPABASE_KEY`: 데이터베이스 연동
*   `MASTER_ENCRYPTION_KEY`: 민감 정보 암복호화용 마스터 키
*   `EMAILJS_*`, `SOLAPI_*`: 결과 보고 서비스 키
*   `GEMINI_API_KEY`: Gemini 모델 실행 키
