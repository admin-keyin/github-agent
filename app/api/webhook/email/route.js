import { Octokit } from "@octokit/rest";
import { NextResponse } from "next/server";
import { supabase } from "@/utils/supabase";

export async function POST(req) {
  try {
    const payload = await req.json();
    
    const { from, subject, text, body } = payload;
    const taskBody = text || body || '';

    // 1. 보안 체크
    const ALLOWED_SENDER = process.env.ALLOWED_SENDER;
    if (from !== ALLOWED_SENDER && ALLOWED_SENDER !== "*") {
      return NextResponse.json({ message: "Unauthorized sender" }, { status: 403 });
    }

    // 2. DB에 작업 이력 기록 (status: pending)
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
