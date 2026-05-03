'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import Link from 'next/link';

export default function Home() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [credentials, setCredentials] = useState([]);
  
  // Credential Form State
  const [newKey, setNewKey] = useState({ provider: 'GITHUB', value: '', git_url: '' });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);
      if (session?.user) {
        fetchData();
      }
    };

    checkUser();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchData();
      } else {
        setTasks([]);
        setCredentials([]);
      }
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const fetchData = async () => {
    await Promise.all([fetchTasks(), fetchCredentials()]);
  };

  const fetchTasks = async () => {
    const { data } = await supabase
      .from('agent_tasks')
      .select('*')
      .order('created_at', { ascending: false });
    if (data) setTasks(data);
  };

  const fetchCredentials = async () => {
    const { data } = await supabase
      .from('user_credentials')
      .select('id, key_name, scope, created_at')
      .order('created_at', { ascending: false });
    if (data) setCredentials(data);
  };

  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    });
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  const saveCredential = async (e) => {
    e.preventDefault();
    if (!newKey.provider || !newKey.value || !newKey.git_url) {
      alert('모든 필드를 입력해주세요.');
      return;
    }

    setIsSaving(true);
    const { error } = await supabase
      .from('user_credentials')
      .upsert([
        { 
          user_email: user.email, 
          key_name: newKey.provider, 
          key_value: newKey.value, 
          scope: newKey.git_url 
        }
      ], { onConflict: 'user_email,key_name,scope' });

    if (error) {
      alert('저장 실패: ' + error.message);
    } else {
      setNewKey({ provider: 'GITHUB', value: '', git_url: '' });
      fetchCredentials();
      alert('성공적으로 저장되었습니다.');
    }
    setIsSaving(false);
  };

  const deleteCredential = async (id) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    const { error } = await supabase.from('user_credentials').delete().eq('id', id);
    if (!error) fetchCredentials();
  };

  if (loading) return <div className="p-8 text-center">준비 중...</div>;

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-black tracking-tight">AGENT VAULT</h1>
            <p className="text-gray-500 mt-2 font-medium">관리자 전용 AI 에이전트 및 자격 증명 관리 시스템</p>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/ducktem" className="px-6 py-3 bg-yellow-400 text-yellow-900 rounded-xl font-black hover:bg-yellow-500 transition-all shadow-md flex items-center gap-2">
              🦆 DUCKTEM 이동
            </Link>
            {user ? (
            <div className="flex items-center gap-4 bg-white p-2 px-4 rounded-full shadow-sm border border-gray-100">
              <span className="text-sm font-bold text-indigo-600">{user.email}</span>
              <button onClick={handleLogout} className="text-xs font-bold text-gray-400 hover:text-red-500 transition-colors uppercase">Logout</button>
            </div>
          ) : (
            <button onClick={handleLogin} className="px-6 py-3 bg-black text-white rounded-lg font-bold hover:bg-gray-800 transition-all shadow-lg flex items-center gap-3">
              Google 계정으로 접속
            </button>
          )}
          </div>
        </header>

        {!user ? (
          <div className="bg-white p-20 rounded-3xl border-2 border-dashed border-gray-200 text-center">
            <h2 className="text-2xl font-bold mb-4">로그인이 필요합니다</h2>
            <p className="text-gray-500">자격 증명을 관리하고 에이전트 상태를 보려면 로그인하세요.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 좌측: 자격 증명 관리 */}
            <div className="lg:col-span-1 space-y-8">
              <section className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="p-1.5 bg-indigo-100 rounded-lg">🔑</span> 자격 증명 등록
                </h2>
                <form onSubmit={saveCredential} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Git Provider</label>
                    <select 
                      value={newKey.provider}
                      onChange={e => setNewKey({...newKey, provider: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm font-bold"
                    >
                      <option value="GITHUB">GitHub</option>
                      <option value="GITLAB">GitLab</option>
                      <option value="BITBUCKET">Bitbucket</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Git Repository URL</label>
                    <input 
                      type="text" 
                      placeholder="https://github.com/owner/repo"
                      value={newKey.git_url}
                      onChange={e => setNewKey({...newKey, git_url: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-mono text-sm"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Personal Access Token (API Key)</label>
                    <input 
                      type="password" 
                      placeholder="비밀 토큰을 입력하세요"
                      value={newKey.value}
                      onChange={e => setNewKey({...newKey, value: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm"
                      required
                    />
                  </div>
                  <button 
                    disabled={isSaving}
                    className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100"
                  >
                    {isSaving ? '저장 중...' : '연결 정보 저장'}
                  </button>
                </form>
              </section>

              <section className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="p-1.5 bg-green-100 rounded-lg">📜</span> 내 연결 목록
                </h2>
                <div className="space-y-3">
                  {credentials.map(cred => (
                    <div key={cred.id} className="p-4 bg-gray-50 rounded-xl border border-gray-100 group relative">
                      <div className="flex justify-between items-start mb-1">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-black 
                          ${cred.key_name === 'GITHUB' ? 'bg-black text-white' : ''}
                          ${cred.key_name === 'GITLAB' ? 'bg-orange-500 text-white' : ''}
                          ${cred.key_name === 'BITBUCKET' ? 'bg-blue-600 text-white' : ''}
                        `}>
                          {cred.key_name}
                        </span>
                        <button 
                          onClick={() => deleteCredential(cred.id)}
                          className="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all absolute top-4 right-4"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                      <div className="text-xs font-bold text-gray-800 break-all pr-6">{cred.scope}</div>
                      <div className="text-[10px] text-gray-400 mt-1">Saved: {new Date(cred.created_at).toLocaleDateString()}</div>
                    </div>
                  ))}
                  {credentials.length === 0 && <p className="text-center text-gray-400 text-sm py-4">저장된 연결 정보가 없습니다.</p>}
                </div>
              </section>
            </div>

            {/* 우측: 작업 히스토리 */}
            <div className="lg:col-span-2">
              <section className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                  <h2 className="text-xl font-bold">에이전트 작업 기록</h2>
                  <button onClick={fetchTasks} className="p-2 hover:bg-white rounded-full transition-all">🔄</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-gray-50/50">
                      <tr>
                        <th className="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest">Status</th>
                        <th className="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest">Task Detail</th>
                        <th className="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest">Requester</th>
                        <th className="px-6 py-4 text-right text-[10px] font-bold text-gray-400 uppercase tracking-widest">Time</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-50">
                      {tasks.map((task) => (
                        <tr key={task.id} className="hover:bg-gray-50/50 transition-colors">
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded-md text-[10px] font-black uppercase
                              ${task.status === 'completed' ? 'bg-green-100 text-green-700' : ''}
                              ${task.status === 'running' ? 'bg-blue-100 text-blue-700 animate-pulse' : ''}
                              ${task.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : ''}
                              ${task.status === 'failed' ? 'bg-red-100 text-red-700' : ''}
                            `}>
                              {task.status}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm font-bold text-gray-900">{task.subject}</div>
                            <div className="text-xs text-gray-400 truncate max-w-xs font-medium">{task.body}</div>
                          </td>
                          <td className="px-6 py-4 text-xs font-medium text-gray-500">{task.sender_email}</td>
                          <td className="px-6 py-4 text-right text-xs font-mono text-gray-300">
                            {new Date(task.created_at).toLocaleTimeString('ko-KR', { hour12: false, hour: '2-digit', minute: '2-digit' })}
                          </td>
                        </tr>
                      ))}
                      {tasks.length === 0 && (
                        <tr><td colSpan="4" className="px-6 py-20 text-center text-gray-400 text-sm font-medium">활동 내역이 없습니다.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
