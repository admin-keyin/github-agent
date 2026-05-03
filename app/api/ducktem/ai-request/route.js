import { NextResponse } from 'next/server';

export async function POST(req) {
  try {
    const { keyword } = await req.json();
    
    // GitHub API를 통해 Workflow 트리거
    const response = await fetch(`https://api.github.com/repos/${process.env.GITHUB_OWNER}/${process.env.GITHUB_REPO}/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_PAT}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        event_type: 'ducktem-ai-request',
        client_payload: { keyword }
      }),
    });

    if (response.ok) {
      return NextResponse.json({ success: true });
    } else {
      const error = await response.text();
      return NextResponse.json({ success: false, error }, { status: 500 });
    }
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
