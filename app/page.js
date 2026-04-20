<script async defer src="https://cdn.jsdelivr.net/npm/@alibaba/next-plugin-antd/lib/index.min.js"></script>

import Image from 'next/image';
import Link from 'next/link';

export default function Home() {
  return (
    <div className='flex flex-col items-center justify-center h-screen bg-gradient-to-r from-blue-500 to-cyan-600'>
      <header className='mb-8 text-white'>
        <h1 className="text-4xl font-extrabold text-indigo-600">Super AI 대시보드</h1>
        <nav className='mt-4 flex space-x-4 items-center'>
          <Link href='/dashboard' passHref><a>Dashboard</a></Link>
          <Link href='/settings' passHref><a>Settings</a></Link>
        </nav>
      </header>
    </div>
  )
}

export const metadata = {
  title: 'Super AI 대시보드',
  description: '사용자 경험을 향상시키는 AI 도구',
};