'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase';
import Link from 'next/link';

export default function GoodsExplorer() {
  const [goods, setGoods] = useState([]);
  const [animations, setAnimations] = useState([]);
  const [selectedAnim, setSelectedAnim] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [isRequesting, setIsRequesting] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchGoods();
    }, 300);
    return () => clearTimeout(timer);
  }, [selectedAnim, searchTerm]);

  const fetchInitialData = async () => {
    const { data } = await supabase.from('animations').select('*').order('title');
    if (data) setAnimations(data);
  };

  const fetchGoods = async () => {
    setLoading(true);
    let query = supabase.from('goods').select('*').order('created_at', { ascending: false });
    
    if (selectedAnim !== 'all') {
      query = query.eq('animation_id', selectedAnim);
    }

    if (searchTerm) {
      query = query.ilike('title', `%${searchTerm}%`);
    }

    const { data } = await query;
    if (data) setGoods(data);
    setLoading(false);
  };

  const triggerAIRequest = async () => {
    const keyword = searchTerm || prompt('어떤 굿즈를 찾으시나요? (예: 나루토 원단)');
    if (!keyword) return;
    
    setIsRequesting(true);
    try {
      const response = await fetch('/api/ducktem/ai-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword })
      });
      if (response.ok) alert(`🚀 [${keyword}] 글로벌 AI 추적이 시작되었습니다! 잠시 후 데이터가 추가됩니다.`);
      else alert('요청 중 오류가 발생했습니다.');
    } catch (err) {
      alert('AI 크롤러 가동 요청이 전송되었습니다.');
    }
    setIsRequesting(false);
  };

  const getCountryFlag = (code) => {
    const flags = { 
      'KR': '🇰🇷', 'JP': '🇯🇵', 'US': '🇺🇸', 'CN': '🇨🇳', 
      'VN': '🇻🇳', 'PH': '🇵🇭', 'HK': '🇭🇰', 'TW': '🇹🇼', 'TH': '🇹🇭' 
    };
    return flags[code?.toUpperCase()] || '🌐';
  };

  return (
    <div className="min-h-screen bg-[#FDFDFD] text-gray-900">
      {/* 고정 헤더 */}
      <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-xl border-b border-gray-100 p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-4 justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/ducktem" className="text-3xl font-black italic tracking-tighter text-yellow-500">DUCKTEM 🦆</Link>
          </div>
          
          <div className="relative w-full md:max-w-xl flex gap-2">
            <div className="relative flex-1">
              <input 
                type="text" 
                placeholder="나루토 원단, 치이카와 인형 등 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-6 py-3.5 bg-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-yellow-400 font-bold text-base transition-all pl-12"
              />
              <span className="absolute left-4 top-4 text-xl opacity-30">🔍</span>
            </div>
            <button 
              onClick={triggerAIRequest}
              disabled={isRequesting}
              className="px-6 py-3 bg-indigo-600 text-white rounded-2xl font-black hover:bg-indigo-700 transition-all shadow-md whitespace-nowrap flex items-center gap-2"
            >
              {isRequesting ? 'Searching...' : '🤖 AI 수집 요청'}
            </button>
          </div>

          <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-hide">
            <button 
              onClick={() => setSelectedAnim('all')}
              className={`px-5 py-2.5 rounded-full text-sm font-black transition-all ${selectedAnim === 'all' ? 'bg-black text-white shadow-lg' : 'bg-gray-100 hover:bg-gray-200 text-gray-500'}`}
            >
              전체
            </button>
            {animations.map(anim => (
              <button 
                key={anim.id}
                onClick={() => setSelectedAnim(anim.id)}
                className={`px-5 py-2.5 rounded-full text-sm font-black transition-all whitespace-nowrap ${selectedAnim === anim.id ? 'bg-black text-white shadow-lg' : 'bg-gray-100 hover:bg-gray-200 text-gray-500'}`}
              >
                {anim.title}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8">
        <div className="flex items-baseline gap-4 mb-10">
          <h2 className="text-4xl font-black tracking-tight">실시간 글로벌 매물</h2>
          <p className="text-gray-400 font-bold">전 세계 8개국 실시간 추적 중</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="aspect-[3/4] bg-gray-50 animate-pulse rounded-[2rem]" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {goods.map(item => (
              <a key={item.id} href={item.source_url} target="_blank" rel="noopener noreferrer" 
                 className="group bg-white border border-gray-100 rounded-[2rem] overflow-hidden hover:border-indigo-500 hover:shadow-2xl hover:shadow-indigo-100 transition-all duration-300 relative flex flex-col">
                
                {/* 국가 마크 표시 (중요) */}
                <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl text-xs font-black shadow-sm border border-gray-100">
                  <span className="text-base leading-none">{getCountryFlag(item.country_code)}</span>
                  <span className="text-[10px] text-gray-600 uppercase tracking-tighter">{item.source_platform}</span>
                </div>

                <div className="aspect-square bg-gray-50 overflow-hidden">
                  <img src={item.image_url} alt={item.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                </div>
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-bold line-clamp-2 h-10 mb-3 leading-snug group-hover:text-indigo-600 transition-colors">{item.title}</h3>
                  </div>
                  <div className="flex justify-between items-end mt-auto">
                    <p className="font-black text-lg text-indigo-600">{item.price?.toLocaleString()}원</p>
                    <span className="text-[10px] font-black text-gray-300 uppercase">View →</span>
                  </div>
                </div>
              </a>
            ))}

            {/* 결과가 없을 때 표시되는 섹션 */}
            {goods.length === 0 && (
              <div className="col-span-full py-40 text-center bg-gray-50 rounded-[3rem] border-2 border-dashed border-gray-100">
                <div className="text-6xl mb-6">🔍</div>
                <p className="text-gray-400 text-2xl font-black mb-4">"{searchTerm || '아이템'}"을(를) 찾을 수 없습니다.</p>
                <p className="text-gray-400 font-bold mb-8">전 세계 마켓을 AI가 정밀 분석하도록 요청하시겠습니까?</p>
                <button 
                  onClick={triggerAIRequest}
                  className="px-10 py-5 bg-black text-white rounded-3xl font-black text-xl hover:scale-105 transition-all shadow-2xl flex items-center gap-3 mx-auto"
                >
                  🤖 AI에게 전 세계 뒤지라고 하기
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="p-20 text-center">
        <div className="inline-block p-4 px-8 bg-gray-100 rounded-full text-gray-400 font-black text-sm">
          © 2024 DUCKTEM GLOBAL ENGINE 🌍
        </div>
      </footer>
    </div>
  );
}
