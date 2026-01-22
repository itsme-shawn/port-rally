"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, ClipboardCheck, Target, Zap } from "lucide-react";

export default function AiDecisionPage() {
  const router = useRouter();

  const benefits = [
    { icon: <Target size={16} />, text: "개인화된 리스크 진단" },
    { icon: <Zap size={16} />, text: "맞춤형 종목 추천" },
    { icon: <ClipboardCheck size={16} />, text: "투자 성향별 포트폴리오 제안" },
  ];

  return (
    <div className="flex-1 bg-white flex flex-col overflow-hidden">
      {/* Content Area */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pb-6">
        <div className="w-full max-w-md">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-20 h-20 rounded-3xl bg-[var(--color-secondary)] flex items-center justify-center text-[var(--color-primary)] mb-8 mx-auto shadow-sm"
          >
            <Sparkles size={40} />
          </motion.div>

          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-4 leading-tight">
              투자성향 분석을 <br /> 시작할까요?
            </h1>
            <p className="text-[var(--color-text-secondary)] leading-relaxed px-4 mb-8">
              사용자의 투자 성향을 바탕으로 <br />
              포트폴리오를 제안해드릴게요
            </p>

            {/* Benefits */}
            <div className="space-y-2.5 inline-block text-left">
              {benefits.map((b, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 + 0.3 }}
                  className="flex items-center gap-3 text-slate-600 font-medium"
                >
                  <div className="text-[var(--color-primary)] bg-[var(--color-secondary)]/50 p-1.5 rounded-lg">
                    {b.icon}
                  </div>
                  <span className="text-[14px]">{b.text}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Button Area */}
      <div className="flex-shrink-0 border-t border-gray-100 bg-white">
        <div className="max-w-md mx-auto p-6 space-y-3">
          <Button
            className="w-full h-16 rounded-[24px] text-[17px] font-bold shadow-lg shadow-emerald-100 cursor-pointer"
            onClick={() => router.push("/onboarding/survey")}
          >
            분석 시작
          </Button>
          <Button
            variant="ghost"
            className="w-full h-16 rounded-[24px] text-[16px] font-bold cursor-pointer bg-slate-100 hover:bg-slate-200"
            onClick={() => router.push("/dashboard")}
          >
            나중에 할게요
          </Button>
        </div>
      </div>
    </div>
  );
}
