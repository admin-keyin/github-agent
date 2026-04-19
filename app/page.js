import { supabase } from "@/utils/supabase";
import Link from "next/link";

export const revalidate = 0; // 실시간 반영을 위해 SSR 캐시 비활성화

export default async function Home() {
  const { data: tasks, error } = await supabase
    .from("agent_tasks")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    return <div className="p-8 text-red-500">Error loading tasks: {error.message}</div>;
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-5xl mx-auto">
        <header className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">AI 에이전트 대시보드</h1>
          <p className="text-gray-500 mt-2">이메일로 수신된 작업 의뢰와 현재 처리 상태를 모니터링합니다.</p>
        </header>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">작업명</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">요청자</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">의뢰 시간</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">PR 브랜치</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks?.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                      ${task.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                      ${task.status === 'running' ? 'bg-blue-100 text-blue-800 animate-pulse' : ''}
                      ${task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : ''}
                      ${task.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {task.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{task.subject}</div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">{task.body}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{task.sender_email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(task.created_at).toLocaleString('ko-KR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {task.branch_name ? (
                      <span className="text-indigo-600 hover:text-indigo-900 font-mono text-xs bg-indigo-50 px-2 py-1 rounded">
                        {task.branch_name}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {(!tasks || tasks.length === 0) && (
                <tr>
                  <td colSpan="5" className="px-6 py-10 text-center text-gray-500 text-sm">
                    아직 수신된 이메일 작업이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <footer className="mt-8 flex justify-center">
          <Link href="/about" className="text-gray-400 hover:text-indigo-600 text-sm flex items-center transition-colors">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            프로젝트 소개 보기
          </Link>
        </footer>
      </div>
    </main>
  );
}
