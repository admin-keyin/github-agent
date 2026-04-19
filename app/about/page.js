import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900 font-sans">
      <div className="max-w-3xl mx-auto">
        <header className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold text-indigo-600 tracking-tight">프로젝트 소개</h1>
          <p className="text-gray-500 mt-4 text-lg">AI 기반 개발 자동화 에이전트: Freelance Agent v1.0</p>
        </header>

        <section className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 space-y-6">
          <div>
            <h2 className="text-xl font-bold mb-2">🚀 무엇을 하나요?</h2>
            <p className="text-gray-600 leading-relaxed">
              이 에이전트는 사용자의 이메일 의뢰를 분석하여 자동으로 코드를 작성하고, 
              테스트를 거쳐 GitHub에 Pull Request를 생성하는 "완전 자동화 프리랜서"입니다.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-indigo-50 rounded-xl">
              <span className="block text-indigo-700 font-bold">비용 절감</span>
              <span className="text-sm text-indigo-600">로컬 LLM 활용 (0원)</span>
            </div>
            <div className="p-4 bg-green-50 rounded-xl">
              <span className="block text-green-700 font-bold">고성능</span>
              <span className="text-sm text-green-600">M3 Pro 자원 최적화</span>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold mb-2">🛠 기술 스택</h2>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              <li>Next.js 15 (Dashboard & API)</li>
              <li>Supabase (Database)</li>
              <li>GitHub Actions (Workflow)</li>
              <li>Ollama (Qwen2.5-Coder-32B)</li>
            </ul>
          </div>
        </section>

        <footer className="mt-12 text-center">
          <Link href="/" className="inline-flex items-center text-indigo-600 hover:text-indigo-800 font-medium">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            대시보드로 돌아가기
          </Link>
        </footer>
      </div>
    </main>
  );
}
