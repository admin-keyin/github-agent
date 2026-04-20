import { Octokit } from "@octokit/rest";
import { NextResponse } from "next/server";
import { supabase } from "@/utils/supabase";

export async function POST(req) {
  try {
    const payload = await req.json();
    console.log("Full Webhook Payload:", JSON.stringify(payload)); // 전체 페이로드 로깅

    // 1. 발신자(from) 추출 전략: envelope -> top-level from -> headers.from 순서
    let from = "";
    if (payload.envelope && payload.envelope.from) {
      from = payload.envelope.from;
    } else if (payload.from) {
      from = payload.from;
    } else if (payload.headers && payload.headers.from) {
      from = payload.headers.from;
    }

    // "Name <email@address>" 형태에서 이메일 주소만 추출
    const emailMatch = from.match(/<([^>]+)>/) || from.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
    if (emailMatch) {
      from = emailMatch[1] || emailMatch[0];
    }
    from = from.trim().toLowerCase();

    // 2. 제목(subject) 및 본문(body) 추출
    const subject = payload.subject || (payload.headers && payload.headers.subject) || "No Subject";
    const taskBody = payload.plain || payload.text || payload.body || "";

    console.log(`Extracted Info - From: ${from}, Subject: ${subject}`);

    // 3. 보안 체크 및 유효성 검사
    const ALLOWED_SENDER = process.env.ALLOWED_SENDER;
    if (!from || (ALLOWED_SENDER !== "*" && from !== ALLOWED_SENDER)) {
      console.error(`Rejected unauthorized or empty sender: "${from}"`);
      return NextResponse.json({ error: "Unauthorized or missing sender email" }, { status: 403 });
    }

    // 4. DB에 작업 이력 기록
    const { data: task, error: dbError } = await supabase
      .from('agent_tasks')
      .insert([
        { sender_email: from, subject, body: taskBody, status: 'pending' }
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
