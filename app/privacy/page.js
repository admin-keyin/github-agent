import Link from 'next/link';

export const metadata = {
  title: "개인정보처리방침 (Privacy Policy) - keyin",
  description: "keyin 서비스의 개인정보처리방침입니다.",
};

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto bg-white p-8 sm:p-12 rounded-2xl shadow-sm border border-gray-200">
        <div className="border-b pb-6 mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">개인정보처리방침 (Privacy Policy)</h1>
            <p className="text-sm text-gray-500 mt-1">애플리케이션 이름: <strong className="text-gray-800">keyin</strong> | 최종 수정일: 2026년 9월 7일</p>
          </div>
          <Link href="/" className="text-sm font-semibold text-blue-600 hover:underline">
            ← 홈으로 돌아가기
          </Link>
        </div>

        <div className="space-y-8 text-sm leading-relaxed text-gray-700">
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">1. 개요</h2>
            <p>
              본 개인정보처리방침은 <strong>keyin</strong>(이하 "서비스")이 사용자의 개인정보 및 관련 데이터를 수집, 이용, 보관, 파기하는 방식과 관련 정책을 명시합니다.
              본 서비스는 이용자의 개인정보를 중요시하며, "개인정보 보호법" 및 Google API 서비스 사용자 데이터 정책(Google API Services User Data Policy)을 준수합니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">2. 수집하는 개인정보 및 데이터 항목</h2>
            <p className="mb-2">서비스는 이용자가 동의한 경우에 한하여 다음과 같은 최소한의 데이터를 수집 및 처리합니다:</p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li><strong>Google 계정 인증 정보</strong>: OAuth 2.0 인증을 위한 기본 프로필 정보 및 Access/Refresh Token</li>
              <li><strong>YouTube 관련 데이터</strong>: 사용자가 승인한 경우 YouTube 동영상 업로드 및 채널 관리에 필요한 최소한의 식별자</li>
              <li><strong>서비스 이용 기록</strong>: 자동화 작업 로그, 요청 일시, 오류 기록</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">3. 데이터의 이용 목적</h2>
            <p className="mb-2">수집된 데이터는 오직 다음의 목적을 위해서만 사용됩니다:</p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>사용자가 요청한 콘텐츠(음악 비디오, 굿즈/이벤트 데이터 등)의 자동 생성 및 YouTube 업로드 자동화 수행</li>
              <li>OAuth 토큰의 유효성 검증 및 API 호출 인증</li>
              <li>서비스 안정성 확보, 오류 분석 및 개선</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">4. Google API 사용자 데이터 정책 준수 (Google API Services User Data Policy)</h2>
            <p className="mb-2">
              <strong>keyin</strong>의 Google API 사용 및 수집된 정보의 타 앱으로의 전송은 Google의 제한적 사용 요구사항(Limited Use Requirements)을 포함한{' '}
              <a 
                href="https://developers.google.com/terms/api-services-user-data-policy" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-blue-600 underline"
              >
                Google API 서비스 사용자 데이터 정책
              </a>
              을 철저히 준수합니다:
            </p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>Google 사용자 데이터는 사용자에게 직접적인 서비스 기능을 제공하는 용도 외에 제3자에게 판매하거나 광고 타깃팅 용도로 사용되지 않습니다.</li>
              <li>사용자 데이터를 인간이 직접 열람하지 않으며, AI 모델의 일반적인 학습 목적으로 사용하지 않습니다.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">5. 데이터의 제3자 제공 및 위탁</h2>
            <p>
              서비스는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. 단, 이용자가 사전에 동의한 경우 또는 법령의 규정에 의거하거나 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우는 예외로 합니다.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">6. 데이터 보관 기간 및 파기 절차</h2>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>이용자의 인증 토큰 및 관련 정보는 이용 목적이 달성되거나 사용자가 연동 해제(권한 철회)를 요청할 때 즉시 안전하게 파기됩니다.</li>
              <li>사용자는 언제든지 <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Google 계정 보안 설정</a>에서 앱 접근 권한을 직접 취소할 수 있습니다.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-2">7. 개인정보 보호책임자 및 문의</h2>
            <p className="mb-1">서비스의 개인정보 처리에 관한 문의 사항은 아래로 연락해 주시기 바랍니다:</p>
            <div className="bg-gray-100 p-4 rounded-xl mt-2">
              <p><strong>애플리케이션:</strong> keyin</p>
              <p><strong>서비스 웹사이트:</strong> https://github-agent-one.vercel.app</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
