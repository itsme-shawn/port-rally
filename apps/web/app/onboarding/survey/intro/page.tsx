"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ClipboardCheck, Target, Zap } from "lucide-react";
import { BackButton } from "@/components/ui/BackButton";

export default function SurveyIntroPage() {
  const router = useRouter();

  const benefits = [
    { icon: <Target size={18} />, text: "개인화된 리스크 진단" },
    { icon: <Zap size={18} />, text: "맞춤형 종목 추천" },
    { icon: <ClipboardCheck size={18} />, text: "투자 성향별 포트폴리오 제안" },
  ];

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col items-center">
      <div className="w-full max-w-md flex-1 flex flex-col pt-2 items-start">
        <BackButton className="-ml-8 mb-6" href="/onboarding/ai/decision" />

        <div className="flex-1 w-full flex flex-col justify-center pb-20">
          <div className="text-center mb-12">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-6 leading-tight">
              더 정교한 분석을 위해 <br /> 몇 가지만 여쭤볼게요
            </h1>
            <div className="space-y-3 inline-block text-left">
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
                  <span className="text-[15px]">{b.text}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <Button
            className="w-full h-16 rounded-[24px] text-[17px] font-bold bg-slate-900 hover:bg-slate-800 text-white transition-all active:scale-[0.98] cursor-pointer"
            onClick={() => router.push("/onboarding/survey")}
          >
            성향 분석 시작하기
          </Button>
          <p className="text-center text-[12px] text-slate-400 mt-6 font-medium">
            약 1분 정도 소요됩니다
          </p>
        </div>
      </div>
    </div>
  );
}