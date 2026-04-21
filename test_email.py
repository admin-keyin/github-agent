import os
from agent.developer import send_completion_email

# 임의의 설정값 (실제 테스트 시 본인의 키로 교체 필요)
os.environ["EMAILJS_SERVICE_ID"] = "service_test"
os.environ["EMAILJS_TEMPLATE_ID"] = "template_test"
os.environ["EMAILJS_PUBLIC_KEY"] = "public_test"
os.environ["EMAILJS_PRIVATE_KEY"] = "private_test"

send_completion_email(
    to_email="ich019012@gmail.com",
    subject="에이전트 이메일 테스트",
    spec="이것은 테스트 구현 내용입니다.",
    pr_url="https://github.com/vitas-brc20/agent-test/pull/1"
)
