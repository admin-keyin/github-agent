'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import Link from 'next/link';

export default function EventCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    setLoading(true);
    const { data } = await supabase
      .from('events')
      .select('*')
      .order('start_date', { ascending: true });
    
    if (data) setEvents(data);
    setLoading(false);
  };

  const getStatus = (start, end) => {
    const today = new Date().toISOString().split('T')[0];
    if (today < start) return { label: '예정', color: 'bg-blue-500' };
    if (today > end) return { label: '종료', color: 'bg-gray-400' };
    return { label: '진행 중', color: 'bg-green-500' };
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-gray-900">
      <header className="p-8 bg-black text-white rounded-b-[3rem]">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <Link href="/" className="text-2xl font-black italic tracking-tighter">DUCKTEM 🦆</Link>
          <h1 className="text-3xl font-black tracking-tight">이벤트 달력</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-8">
        <div className="space-y-6">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <div key={i} className="h-32 bg-white animate-pulse rounded-3xl" />)}
            </div>
          ) : (
            events.map(event => {
              const status = getStatus(event.start_date, event.end_date);
              return (
                <div key={event.id} className="bg-white p-8 rounded-[2rem] shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center gap-6 group hover:shadow-md transition-shadow">
                  <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-2xl min-w-[100px]">
                    <span className="text-xs font-bold text-gray-400 uppercase">{new Date(event.start_date).getFullYear()}</span>
                    <span className="text-2xl font-black">{new Date(event.start_date).getMonth() + 1}/{new Date(event.start_date).getDate()}</span>
                    <span className="text-[10px] font-black text-gray-300 mt-1">START</span>
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`${status.color} text-white text-[10px] font-black px-2 py-0.5 rounded-full uppercase`}>
                        {status.label}
                      </span>
                      <span className="text-xs font-bold text-indigo-500">POP-UP STORE</span>
                    </div>
                    <h3 className="text-2xl font-black mb-2">{event.title}</h3>
                    <p className="text-gray-500 font-medium text-sm flex items-center gap-4">
                      <span>📍 {event.location}</span>
                      <span>🗓️ {event.start_date} ~ {event.end_date}</span>
                    </p>
                  </div>

                  {event.detail_link && (
                    <a href={event.detail_link} target="_blank" rel="noopener noreferrer" 
                       className="px-6 py-3 bg-gray-900 text-white rounded-xl font-bold text-sm hover:bg-black transition-colors text-center">
                      상세보기
                    </a>
                  )}
                </div>
              );
            })
          )}
          {events.length === 0 && (
            <div className="py-40 text-center">
              <p className="text-gray-300 text-xl font-black mb-4">등록된 일정이 아직 없어요.</p>
              <p className="text-gray-400 text-sm font-bold">크롤러가 열심히 찾고 있는 중입니다! 🔍</p>
            </div>
          )}
        </div>
      </main>

      <footer className="p-12 text-center text-gray-400 font-bold text-sm">
        이벤트 정보는 공식 SNS와 홈페이지를 바탕으로 업데이트됩니다. 🦆
      </footer>
    </div>
  );
}
