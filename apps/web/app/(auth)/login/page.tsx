"use client";

import { motion } from "framer-motion";
import { TrendingUp, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_SERVER_DOMAIN } from "@/lib/constants";

export default function LoginPage() {
  const router = useRouter();

  const handleSocialLogin = (platform: string) => {
    if (platform === "google") {
      window.location.href = `${API_SERVER_DOMAIN}/oauth2/authorization/google`;
      return;
    }
    // 임시로 바로 약관 동의 페이지로 이동
    console.log(`${platform} login attempt`);
    router.push("/onboarding/agree");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white relative overflow-hidden font-[family-name:var(--font-inter)]">
      {/* 배경 장식 (Financial Zen 스타일) */}
      <div className="absolute top-0 inset-x-0 h-[600px] bg-gradient-to-b from-[#E0FFF0] to-white pointer-events-none opacity-40" />
      <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-blue-50/40 rounded-full blur-[100px] pointer-events-none translate-x-1/4 translate-y-1/4" />
      <div className="absolute top-20 left-0 w-[400px] h-[400px] bg-emerald-50/30 rounded-full blur-[80px] pointer-events-none -translate-x-1/2" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-[440px] px-6 relative z-10"
      >
        <div className="text-center mb-12">
          <Link href="/" className="inline-flex items-center gap-2 group mb-8">
            <TrendingUp size={32} className="text-[var(--color-primary)] stroke-[3px] transition-transform group-hover:scale-110" />
            <span className="font-[900] text-3xl tracking-tighter text-slate-900 leading-none">
              PortRally
            </span>
          </Link>
          
          <h1 className="text-4xl font-[900] tracking-tighter text-slate-900 mb-4 leading-tight">
            가장 스마트한 <br />
            투자의 시작
          </h1>
          <p className="text-slate-500 font-bold text-lg tracking-tight">
            AI 로 관리하는 투자 포트폴리오
          </p>
        </div>

        <div className="space-y-4">
          {/* Google Login */}
          <button 
            onClick={() => handleSocialLogin("google")}
            className="group w-full h-16 bg-white border border-slate-200 rounded-[24px] flex items-center px-8 gap-4 hover:border-[var(--color-primary)]/40 hover:shadow-xl hover:shadow-[var(--color-primary)]/5 transition-all duration-300 relative overflow-hidden"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="w-5 h-5">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            </div>
            <span className="text-slate-900 font-[800] text-base flex-1 text-center">Google로 시작하기</span>
            <ArrowRight size={18} className="text-slate-300 group-hover:text-[var(--color-primary)] group-hover:translate-x-1 transition-all" />
          </button>
          
          {/* Apple Login */}
          <button 
            onClick={() => handleSocialLogin("apple")}
            className="group w-full h-16 bg-black text-white rounded-[24px] flex items-center px-8 gap-4 hover:bg-slate-900 transition-all duration-300 relative overflow-hidden"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
                <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.06.75.79-.02 2.05-.8 3.53-.69 1.57.11 2.8.72 3.58 1.83-3.15 1.87-2.64 6 0 7.35-1.12 2.83-2.17 3.73-3.17 3.73zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
              </svg>
            </div>
            <span className="font-[800] text-base flex-1 text-center">Apple로 시작하기</span>
            <ArrowRight size={18} className="text-slate-500 group-hover:translate-x-1 transition-all" />
          </button>
        </div>
        
        <div className="mt-12 text-center space-y-4">
          <p className="text-[11px] text-slate-400 font-bold leading-relaxed">
            회원가입 시 PortRally의 <Link href="#" className="text-slate-900 underline underline-offset-4">이용약관</Link> 및 <br />
            <Link href="#" className="text-slate-900 underline underline-offset-4">개인정보처리방침</Link>에 동의하게 됩니다.
          </p>
          

        </div>
      </motion.div>
    </div>
  );
}
