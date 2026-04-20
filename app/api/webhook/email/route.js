import { Octokit } from "@octokit/rest";
import { NextResponse } from "next/server";
import { supabase } from "@/utils/supabase";

export async function POST(req) {
  try {
    const payload = await req.json();
    console.log("RAW PAYLOAD:", JSON.stringify(payload));

    // 1. 발신자(from) 추출 - 모든 가능성 동원
    let fromRaw = "";
    
    // 우선순위 1: envelope
    if (payload.envelope && payload.envelope.from) {
      fromRaw = payload.envelope.from;
    } 
    // 우선순위 2: top-level
    else if (payload.from) {
      fromRaw = payload.from;
    } 
    // 우선순위 3: headers (대소문자 무관하게 찾기)
    else if (payload.headers) {
      fromRaw = payload.headers.from || payload.headers.From || payload.headers.sender || payload.headers.Sender || "";
    }

    // 이메일 주소만 정규식으로 정밀 추출
    let from = "";
    const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/;
    const match = fromRaw.match(emailRegex);
    if (match) {
      from = match[1].toLowerCase();
    } else {
      // 최후의 수단: 이메일이 없으면 unknown 부여 (DB 에러 방지)
      from = "unknown@sender.com";
      console.warn("Could not extract email from:", fromRaw);
    }

    // 2. 제목 및 본문 추출
    const subject = payload.subject || (payload.headers && (payload.headers.subject || payload.headers.Subject)) || "No Subject";
    const taskBody = payload.plain || payload.text || payload.body || "";

    console.log(`FINAL EXTRACTED -> From: ${from}, Subject: ${subject}`);

    // 3. 보안 체크 (unknown일 경우 테스트를 위해 허용하거나 차단)
    const ALLOWED_SENDER = process.env.ALLOWED_SENDER;
    if (ALLOWED_SENDER !== "*" && from !== ALLOWED_SENDER && from !== "unknown@sender.com") {
      return NextResponse.json({ error: `Unauthorized sender: ${from}` }, { status: 403 });
    }

    // 4. DB에 작업 이력 기록 (sender_email이 절대 null이 되지 않도록 함)
    const { data: task, error: dbError } = await supabase
      .from('agent_tasks')
      .insert([
        { sender_email: from, subject: String(subject), body: String(taskBody), status: 'pending' }
      ])
      .select()
      .single();

    if (dbError) throw dbError;

    // 3. GitHub Action 트리거 (task_id 포함)
    const octokit = new Octokit({ auth: process.env.GITHUB_PAT });
    
    await octokit.repos.createDispatchEvent({
      owner: process.env.GITHUB_OWNER,
      repo: process.env.GITHUB_REPO,
      event_type: "email-task",
      client_payload: {
        id: task.id, // Supabase에서 발급된 작업 고유 ID
        from,
        subject,
        body: taskBody,
      },
    });

    return NextResponse.json({ message: "Agent triggered successfully", taskId: task.id });
  } catch (error) {
    console.error("Error triggering agent:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
