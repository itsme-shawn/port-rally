"use client";

import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function ErrorContent() {
  const searchParams = useSearchParams();
  // 에러 메시지 매핑이나 디코딩이 필요할 수 있음
  const error = searchParams.get("error") || "로그인 처리 중 문제가 발생했습니다.";

  return (
    <div className="w-full max-w-[400px] px-6 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="w-20 h-20 bg-red-50 rounded-[28px] flex items-center justify-center mx-auto mb-8 shadow-sm">
        <AlertCircle size={40} className="text-red-500" />
      </div>
      
      <h1 className="text-3xl font-[900] text-slate-900 mb-4 tracking-tighter">
        로그인 실패
      </h1>
      
      <p className="text-slate-500 mb-10 font-bold text-lg leading-relaxed break-keep">
        {error}
        <br />
        잠시 후 다시 시도해 주세요.
      </p>

      <Link 
        href="/login" 
        className="block w-full h-16 bg-slate-900 text-white rounded-[24px] font-[800] text-lg flex items-center justify-center hover:bg-slate-800 transition-all hover:scale-[1.02] active:scale-[0.98]"
      >
        다시 로그인하기
      </Link>
    </div>
  );
}

export default function AuthErrorPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white relative overflow-hidden font-[family-name:var(--font-inter)]">
      {/* 배경 장식 */}
      <div className="absolute top-0 inset-x-0 h-[600px] bg-gradient-to-b from-red-50/50 to-white pointer-events-none opacity-60" />
      
      <Suspense fallback={<div className="text-slate-400 font-bold">로딩 중...</div>}>
        <ErrorContent />
      </Suspense>
    </div>
  );
}
