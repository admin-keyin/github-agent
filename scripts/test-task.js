// scripts/test-task.js
const fetch = require('node-fetch');

async function simulateEmail() {
  const payload = {
    from: process.env.ALLOWED_SENDER || "ich019012@gmail.com", // 본인의 이메일로 변경하세요
    subject: "메인 페이지 헤더 업데이트 요청",
    body: "app/page.js 파일의 <h1 className=\"text-3xl font-bold tracking-tight\"> 부분을 <h1 className=\"text-4xl font-extrabold text-indigo-600\"> 로 변경하고, 'AI 에이전트 대시보드' 텍스트를 'Super AI 대시보드'로 바꿔주세요."
  };

  try {
    // 로컬 Next.js 서버의 Webhook 주소로 전송
    const res = await fetch('http://localhost:3000/api/webhook/email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    console.log("웹훅 전송 결과:", res.status, data);

    if (res.ok && data.taskId) {
      console.log(`\n🎉 작업이 성공적으로 접수되었습니다. ID: ${data.taskId}`);
      console.log("Supabase 대시보드 또는 http://localhost:3000 에서 상태가 'PENDING'으로 변경된 것을 확인하세요.");
      console.log("이후 GitHub Actions가 실행되며 상태가 'RUNNING' -> 'COMPLETED'로 변경됩니다.");
    }
  } catch (error) {
    console.error("웹훅 호출 실패. Next.js 서버(npm run dev)가 실행 중인지 확인하세요.", error);
  }
}

simulateEmail();
