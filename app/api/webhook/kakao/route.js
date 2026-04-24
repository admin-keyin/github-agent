import { Octokit } from "@octokit/rest";
import { NextResponse } from "next/server";
import { supabase } from "@/utils/supabase";

export async function POST(req) {
  try {
    const payload = await req.json();
    // 카카오 챗봇은 userRequest.utterance에 메시지가 담겨 옵니다.
    const userMessage = payload.userRequest.utterance;
    const userId = payload.userRequest.user.id; // 카카오 사용자 고유 ID

    console.log(`[Kakao] Message: ${userMessage}, User: ${userId}`);

    // 1. 임시로 등록된 이메일이나 사용자 정보를 찾습니다.
    // (실제 서비스에서는 카카오 ID와 이메일을 연동하는 과정이 필요합니다.)
    const sender_email = "kakao_user@example.com"; 

    // 2. DB에 기록
    const { data: task, error: dbError } = await supabase
      .from('agent_tasks')
      .insert([
        { 
          sender_email: sender_email, 
          subject: "카카오톡 요청 작업", 
          body: userMessage, 
          status: 'pending' 
        }
      ])
      .select()
      .single();

    if (dbError) throw dbError;

    // 3. GitHub Action 트리거
    const octokit = new Octokit({ auth: process.env.GITHUB_PAT });
    await octokit.repos.createDispatchEvent({
      owner: process.env.GITHUB_OWNER,
      repo: process.env.GITHUB_REPO,
      event_type: "email-task", // 기존 이벤트 타입 재활용
      client_payload: {
        id: task.id,
        from: sender_email,
        subject: "카카오톡 작업 요청",
        body: userMessage,
        source: "kakao" // 출처 기록
      },
    });

    // 4. 카카오 챗봇에게 즉시 응답 (작업 시작 알림)
    return NextResponse.json({
      version: "2.0",
      template: {
        outputs: [
          {
            simpleText: {
              text: "✅ 에이전트가 작업을 시작했습니다! 완료되면 카카오톡으로 다시 알려드릴게요."
            }
          }
        ]
      }
    });
  } catch (error) {
    console.error("Kakao Webhook Error:", error);
    return NextResponse.json({
      version: "2.0",
      template: {
        outputs: [{ simpleText: { text: "❌ 작업 요청 중 오류가 발생했습니다." } }]
      }
    });
  }
}
