"use client";

import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { GlobalNavBar } from "@/components/GlobalNavBar";
import { Button } from "@/components/ui/Button";
import { PhoneMockup } from "@/components/landing/PhoneMockup";
import { FeatureCardChart, FeatureCardAI, FeatureCardSecurity, CompactFeatureCards } from "@/components/landing/FeatureCards";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8 } }
};

const stagger = {
  visible: { transition: { staggerChildren: 0.2 } }
};

export default function LandingPage() {

  return (
    <div className="flex flex-col min-h-screen bg-white font-[family-name:var(--font-inter)] overflow-x-hidden">
      <GlobalNavBar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative min-h-[85vh] flex items-start md:items-center px-6 overflow-hidden pt-20 md:pt-40 pb-20 md:pb-40">
           {/* Background Gradients */}
           <div className="absolute top-0 inset-x-0 h-[600px] bg-gradient-to-b from-[#E0FFF0] to-white pointer-events-none opacity-50" />
           <div className="absolute top-20 right-0 w-[600px] h-[600px] bg-blue-50/40 rounded-full blur-[80px] pointer-events-none translate-x-1/3" />
           
           {/* Mobile: 3-section Layout */}
           <div className="container-custom md:hidden relative z-10">
             <div className="flex flex-col gap-8">
               {/* 최상단 영역: Hero 제목 + 슬로건 */}
               <motion.div 
                 variants={stagger}
                 initial="hidden"
                 animate="visible"
                 className="text-center mt-8 px-4"
               >
                 {/* 작은 뱃지 */}
             <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-[var(--color-primary)]/10 to-blue-500/10 border border-[var(--color-primary)]/20 mb-8 w-fit">
               <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse" />
               <span className="text-[11px] font-bold text-slate-700 tracking-wide">
                 지금 <span className="text-[var(--color-primary)]">1,247개</span>의 포트폴리오가 함께하는 중
               </span>
             </motion.div>
                 
                 <motion.h1 variants={fadeInUp} className="text-4xl font-[800] tracking-tighter leading-[1.1] mb-4">
                   <span className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 bg-clip-text text-transparent">
                     AI 로 관리하는
                   </span>
                   <br />
                   <span className="bg-gradient-to-r from-[var(--color-primary)] to-blue-600 bg-clip-text text-transparent">
                     투자 포트폴리오
                   </span>
                 </motion.h1>
                 
                 <motion.p variants={fadeInUp} className="text-sm text-slate-600 leading-relaxed max-w-xs mx-auto">
                   감이 아닌 <span className="font-bold text-slate-800">데이터</span>로,<br />
                   더 스마트한 투자 결정을 내리세요
                 </motion.p>
               </motion.div>

               {/* 중앙 영역: 수직 배치 (CTA + 컴팩트 기능 설명) */}
               <div className="flex flex-col items-center gap-10">
                 {/* CTA 버튼 */}
                 <motion.div 
                   variants={fadeInUp}
                   initial="hidden"
                   animate="visible"
                   className="w-full flex justify-center px-4"
                 >
                   <Link href="/login" className="w-full max-w-xs">
                     <Button size="lg" className="w-full rounded-full h-14 text-sm font-[800] bg-black text-white hover:bg-gray-800 shadow-xl hover:scale-[1.02] active:scale-95 transition-all duration-300">
                       지금 무료로 시작하기
                     </Button>
                   </Link>
                 </motion.div>

                 {/* 컴팩트 기능 설명 */}
                 <motion.div
                   variants={fadeInUp}
                   initial="hidden"
                   animate="visible"
                   className="w-full transform scale-110"
                 >
                   <CompactFeatureCards />
                 </motion.div>
               </div>
             </div>
           </div>

           {/* Desktop: 2-column Layout */}
           <div className="container-custom hidden md:grid md:grid-cols-2 gap-6 lg:gap-20 items-center relative z-10">
             {/* Left Column: Text */}
             <motion.div 
               variants={stagger}
               initial="hidden"
               animate="visible"
               className="text-left max-w-2xl flex flex-col justify-center"
             >
             <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-[var(--color-primary)]/10 to-blue-500/10 border border-[var(--color-primary)]/20 mb-8 w-fit">
               <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse" />
               <span className="text-[11px] font-bold text-slate-700 tracking-wide">
                 지금 <span className="text-[var(--color-primary)]">1,247개</span>의 포트폴리오가 함께하는 중
               </span>
             </motion.div>
               
             <motion.h1 variants={fadeInUp} className="text-5xl lg:text-6xl font-[800] tracking-tighter leading-[1.05] mb-8 font-sans">
               <span className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 bg-clip-text text-transparent">
                 AI 로 관리하는
               </span>
               <br />
               <span className="bg-gradient-to-r from-[var(--color-primary)] to-blue-500 bg-clip-text text-transparent">
                 투자 포트폴리오
               </span>
             </motion.h1>
             
             <motion.p variants={fadeInUp} className="text-xl text-slate-600 mb-10 leading-relaxed tracking-tight max-w-lg">
               감이 아닌 <span className="font-bold text-slate-800">데이터</span>로, 더 스마트한 투자 결정을 내리세요.<br />
             </motion.p>
               
               <motion.div variants={fadeInUp} className="flex items-center justify-start gap-4">
                 <Link href="/login">
                   <Button size="lg" className="rounded-full px-8 h-12 text-base font-bold bg-black text-white hover:bg-gray-800 shadow-lg hover:scale-105 transition-all duration-300">
                     지금 무료로 시작하기
                   </Button>
                 </Link>
               </motion.div>
             </motion.div>

             {/* Right Column: Phone Mockup */}
             <motion.div 
               initial={{ x: 100, opacity: 0, rotate: 0 }}
               animate={{ x: 0, opacity: 1, rotate: -12, rotateY: 10 }}
               transition={{ duration: 1.2, delay: 0.2, type: "spring" }}
               className="relative z-10 perspective-1000"
               style={{ transformStyle: "preserve-3d" }}
             >
               <div className="relative transform md:scale-[0.65] lg:scale-[0.85] hover:scale-[0.7] lg:hover:scale-[0.9] transition-transform duration-500 ease-out origin-center">
                 <PhoneMockup />
               </div>
             </motion.div>
           </div>
        </section>

        {/* Features Grid */}
        <section className="pt-4 md:pt-40 pb-32 bg-white relative overflow-hidden">
           {/* 배경 장식 */}
           <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none">
             <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-50/50 rounded-full blur-[120px]" />
             <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-[var(--color-primary)]/5 rounded-full blur-[120px]" />
           </div>

           <div className="container-custom relative z-10">
              <div className="text-center mb-24">
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 mb-6"
                  >
                    <span className="text-[10px] font-black tracking-[0.2em] text-slate-500 uppercase">Core Features</span>
                  </motion.div>
                  
                  <motion.h2 
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.1 }}
                    className="text-4xl md:text-5xl font-[900] mb-8 tracking-tighter leading-tight text-slate-900"
                  >
                    복잡한 투자의 끝, <br className="md:hidden" />
                    해답은 결국 <span className="text-[var(--color-primary)]">PortRally</span>
                  </motion.h2>
                  <motion.p 
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="text-sm md:text-lg text-slate-500 font-bold max-w-2xl mx-auto leading-relaxed md:leading-relaxed"
                  >
                    당신이 놓치고 있던 리스크와 수익의 기회를 <br className="md:hidden" />
                    PortRally AI가 찾아냅니다. <br />
                    <span className="md:hidden"><br /></span>
                    이제 개인 투자자의 한계를 넘어 <br className="md:hidden" />
                    전문가급 인사이트를 경험하세요.
                  </motion.p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-8 lg:gap-12 text-left">
                 {[
                   {
                     component: <FeatureCardChart />,
                     title: "압도적인 가시성",
                     desc: "모든 자산을 단 한 곳에서 완벽하게 통합 관리합니다.",
                     tag: "Connectivity"
                   },
                   {
                     component: <FeatureCardAI />,
                     title: "심도 있는 AI 분석",
                     desc: "AI가 매일 리스크와 성장 기회를 정교하게 분석합니다.",
                     tag: "Intelligence"
                   },
                   {
                     component: <FeatureCardSecurity />,
                     title: "강력한 보안",
                     desc: "금융권 수준의 보안으로 정보를 안전하게 보호합니다.",
                     tag: "Security"
                   }
                 ].map((feature, i) => (
                   <motion.div 
                     key={i} 
                     initial={{ opacity: 0, y: 30 }}
                     whileInView={{ opacity: 1, y: 0 }}
                     viewport={{ once: true }}
                     transition={{ delay: i * 0.1 + 0.3 }}
                     className="group relative h-full"
                   >
                     <div className="relative h-full bg-white rounded-[24px] md:rounded-[40px] overflow-hidden border border-slate-200/60 shadow-sm transition-all duration-500 group-hover:border-[var(--color-primary)]/40 group-hover:shadow-2xl group-hover:shadow-[var(--color-primary)]/10 group-hover:-translate-y-2 flex flex-row md:flex-col items-center md:items-stretch">
                        <div className="w-[110px] md:w-full h-32 md:h-72 bg-gradient-to-b from-slate-50/50 to-white relative overflow-hidden flex items-center justify-center p-2 md:p-8 transition-colors shrink-0">
                           <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-50/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                           <div className="transform transition-transform duration-1000 group-hover:scale-[0.63] md:group-hover:scale-110 scale-[0.55] md:scale-100 origin-center">
                             {feature.component}
                           </div>
                        </div>
                        <div className="p-4 md:p-10 flex-1 flex flex-col justify-center min-w-0">
                          <span className="text-[8px] md:text-[10px] font-black tracking-widest text-[var(--color-primary)] uppercase mb-1 md:mb-4 opacity-60">
                            {feature.tag}
                          </span>
                          <h3 className="text-base md:text-2xl font-[900] mb-0.5 md:mb-4 tracking-tighter text-slate-900 group-hover:text-[var(--color-primary)] transition-colors truncate md:whitespace-normal">
                            {feature.title}
                          </h3>
                          <p className="text-slate-500 leading-snug md:leading-relaxed font-bold text-[11px] md:text-sm tracking-tight break-keep">
                            {feature.desc}
                          </p>
                        </div>
                     </div>
                   </motion.div>
                 ))}
              </div>
           </div>
        </section>
      </main>

      <footer className="bg-white border-t border-slate-100 py-12">
        <div className="container-custom">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            {/* Logo & Copyright */}
            <div className="flex flex-col items-center md:items-start gap-3">
              <Link href="/" className="flex items-center gap-2 group">
                <TrendingUp size={20} className="text-[var(--color-primary)] stroke-[3px]" />
                <span className="font-[900] text-lg tracking-tighter text-slate-900 leading-none">
                  PortRally
                </span>
              </Link>
              <div className="text-slate-400 text-[12px] font-bold tracking-tight">
                © 2026 PortRally. All rights reserved.
              </div>
            </div>

            {/* Quick Links */}
            <div className="flex items-center gap-8">
              <Link href="#" className="text-[13px] font-bold text-slate-500 hover:text-black transition-colors">
                고객문의
              </Link>
              <Link href="#" className="text-[13px] font-bold text-slate-500 hover:text-black transition-colors">
                이용약관
              </Link>
              <Link href="#" className="text-[13px] font-bold text-slate-500 hover:text-black transition-colors">
                개인정보처리방침
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
