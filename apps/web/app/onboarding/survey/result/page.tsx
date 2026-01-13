"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, TrendingUp, BarChart3, ShieldCheck } from "lucide-react";

export default function SurveyResultPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col items-center">
      <div className="w-full max-w-md flex-1 flex flex-col pt-12 items-center justify-center text-center">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", damping: 15 }}
          className="w-24 h-24 bg-[var(--color-primary)] text-white rounded-full flex items-center justify-center mb-10 shadow-lg shadow-emerald-100"
        >
          <CheckCircle2 size={48} strokeWidth={2.5} />
        </motion.div>

        <div className="mb-12">
          <h2 className="text-[var(--color-primary)] font-black text-[12px] uppercase tracking-[0.2em] mb-4">
            Analysis Complete
          </h2>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-6 leading-tight">
            성장 지향적 투자자 <br /> 타입이시네요!
          </h1>
          <p className="text-[var(--color-text-secondary)] leading-relaxed px-4 break-keep">
            시장 평균보다 높은 수익을 위해 리스크를 <br className="hidden md:block" />
            감수할 준비가 된 전략가 스타일입니다.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 w-full mb-12">
          {[
            { icon: <TrendingUp size={20} />, label: "공격적" },
            { icon: <BarChart3 size={20} />, label: "전략적" },
            { icon: <ShieldCheck size={20} />, label: "균형" },
          ].map((item, i) => (
            <div key={i} className="flex flex-col items-center gap-2 p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="text-slate-400">{item.icon}</div>
              <span className="text-[11px] font-bold text-slate-500">{item.label}</span>
            </div>
          ))}
        </div>

        <Button
          className="w-full h-16 rounded-[24px] text-[17px] font-bold shadow-xl shadow-emerald-100 cursor-pointer"
          onClick={() => router.push("/dashboard")}
        >
          내 포트폴리오 분석 보기
        </Button>
      </div>
    </div>
  );
}
