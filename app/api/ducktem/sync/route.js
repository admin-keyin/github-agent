import { NextResponse } from 'next/server';

export async function POST(req) {
  try {
    // GitHub API를 통해 'Ducktem Goods Crawler' 워크플로우 즉시 실행
    const response = await fetch(`https://api.github.com/repos/${process.env.GITHUB_OWNER}/${process.env.GITHUB_REPO}/actions/workflows/ducktem-crawler.yml/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_PAT}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ref: 'main', // 실행할 브랜치
      }),
    });

    if (response.ok) {
      return NextResponse.json({ success: true, message: '글로벌 동기화 워크플로우가 시작되었습니다.' });
    } else {
      const error = await response.text();
      return NextResponse.json({ success: false, error }, { status: 500 });
    }
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
