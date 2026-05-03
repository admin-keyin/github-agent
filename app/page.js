'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import Link from 'next/link';

export default function DucktemHome() {
  const [recentGoods, setRecentGoods] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const [goodsRes, eventsRes] = await Promise.all([
      supabase.from('goods').select('*').order('created_at', { ascending: false }).limit(4),
      supabase.from('events').select('*').gte('end_date', new Date().toISOString().split('T')[0]).order('start_date', { ascending: true }).limit(3)
    ]);

    if (goodsRes.data) setRecentGoods(goodsRes.data);
    if (eventsRes.data) setUpcomingEvents(eventsRes.data);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#FFF9E6] text-[#333]">
      {/* Hero Section */}
      <header className="bg-yellow-400 p-8 rounded-b-[3rem] shadow-lg">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-5xl font-black text-white italic tracking-tighter drop-shadow-md">
              DUCKTEM <span className="text-2xl not-italic ml-2">🦆 덕템</span>
            </h1>
            <p className="text-yellow-900 font-bold mt-2 opacity-80">애니 굿즈 & 팝업스토어 정보 통합 플랫폼</p>
          </div>
          <nav className="flex gap-4">
            <Link href="/goods" className="px-6 py-3 bg-white rounded-2xl font-black hover:scale-105 transition-transform shadow-sm">
              굿즈 탐색
            </Link>
            <Link href="/calendar" className="px-6 py-3 bg-white rounded-2xl font-black hover:scale-105 transition-transform shadow-sm">
              이벤트 달력
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-8 space-y-12">
        {/* Recent Goods */}
        <section>
          <div className="flex justify-between items-end mb-6">
            <h2 className="text-3xl font-black flex items-center gap-2">
              <span className="text-4xl">✨</span> 실시간 신규 굿즈
            </h2>
            <Link href="/ducktem/goods" className="text-sm font-bold text-gray-500 hover:text-black">전체보기 →</Link>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map(i => <div key={i} className="aspect-square bg-white animate-pulse rounded-3xl" />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {recentGoods.map(item => (
                <a key={item.id} href={item.source_url} target="_blank" rel="noopener noreferrer" 
                   className="bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl transition-all hover:-translate-y-2">
                  <div className="aspect-square relative overflow-hidden bg-gray-100">
                    <img src={item.image_url} alt={item.title} className="w-full h-full object-cover" />
                    <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 text-white text-[10px] font-bold rounded-lg backdrop-blur-sm">
                      {item.source_platform}
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="font-bold text-sm line-clamp-2 mb-2 h-10">{item.title}</h3>
                    <p className="text-orange-500 font-black text-lg">{item.price?.toLocaleString()}원</p>
                  </div>
                </a>
              ))}
              {recentGoods.length === 0 && <p className="col-span-full py-20 text-center text-gray-400 font-bold">수집된 굿즈가 없습니다.</p>}
            </div>
          )}
        </section>

        {/* Upcoming Events */}
        <section className="bg-white p-8 rounded-[3rem] shadow-sm border border-yellow-100">
          <div className="flex justify-between items-end mb-8">
            <h2 className="text-3xl font-black flex items-center gap-2">
              <span className="text-4xl">📅</span> 다가오는 이벤트
            </h2>
            <Link href="/ducktem/calendar" className="text-sm font-bold text-gray-500 hover:text-black">달력에서 보기 →</Link>
          </div>

          <div className="space-y-4">
            {upcomingEvents.map(event => (
              <div key={event.id} className="flex items-center gap-6 p-6 bg-[#FFF9E6] rounded-2xl border border-yellow-200 group cursor-pointer hover:bg-yellow-50 transition-colors">
                <div className="flex flex-col items-center justify-center bg-yellow-400 text-white p-4 rounded-xl min-w-[80px]">
                  <span className="text-xs font-black uppercase">{new Date(event.start_date).toLocaleString('en', { month: 'short' })}</span>
                  <span className="text-2xl font-black">{new Date(event.start_date).getDate()}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-black text-xl mb-1">{event.title}</h3>
                  <p className="text-gray-500 font-bold flex items-center gap-1 text-sm">
                    📍 {event.location} | 🗓️ {event.start_date} ~ {event.end_date}
                  </p>
                </div>
                <div className="text-2xl opacity-0 group-hover:opacity-100 transition-opacity">➡️</div>
              </div>
            ))}
            {upcomingEvents.length === 0 && <p className="py-10 text-center text-gray-400 font-bold">진행 예정인 이벤트가 없습니다.</p>}
          </div>
        </section>
      </main>

      <footer className="p-12 text-center flex flex-col items-center gap-4">
        <p className="text-gray-400 font-bold text-sm">© 2024 DUCKTEM. All rights reserved. 🦆</p>
        <Link href="/agent" className="text-xs font-bold text-gray-300 hover:text-gray-500 transition-colors uppercase tracking-widest">
          Admin Agent Vault →
        </Link>
      </footer>
    </div>
  );
}
