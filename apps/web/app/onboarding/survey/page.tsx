"use client";

import { Button } from "@/components/ui/Button";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const QUESTIONS = [
  {
    id: 1,
    question: "가장 관심 있는 투자 섹터는?",
    options: ["IT / AI / 반도체", "금융 / 보험", "헬스케어 / 바이오", "소비재 / 플랫폼", "에너지 / 인프라", "잘 모르겠음"]
  },
  {
    id: 2,
    question: "투자에서 가장 중요한 목표는?",
    options: ["원금 보존이 최우선", "안정적인 배당/이자", "장기 자산 성장", "높은 수익률(한방)"]
  },
  {
    id: 3,
    question: "단기간에 -20%가 된다면?",
    options: ["즉시 매도한다", "일부 매도한다", "존버(유지)한다", "오히려 좋아(추매)"]
  },
  {
    id: 4,
    question: "평균적인 투자 기간은?",
    options: ["6개월 이내", "6개월 ~ 1년", "1년 ~ 3년", "3년 이상"]
  }
];

function SurveyContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Get step from URL, default to 0
  const step = parseInt(searchParams.get("step") || "0", 10);
  
  const [answers, setAnswers] = useState<Record<number, string>>({});

  const currentQ = QUESTIONS[step] || QUESTIONS[0];
  const progress = ((step + 1) / QUESTIONS.length) * 100;

  const handleSelect = (option: string) => {
    setAnswers({ ...answers, [currentQ.id]: option });
    if (step < QUESTIONS.length - 1) {
      setTimeout(() => {
        router.push(`/onboarding/survey?step=${step + 1}`);
      }, 200);
    } else {
      // Finish
      setTimeout(() => router.push("/dashboard"), 300);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="p-6 max-w-md mx-auto w-full flex-1 flex flex-col pt-20">
         <AnimatePresence mode="wait">
            <motion.div
               key={step}
               initial={{ opacity: 0, x: 20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: -20 }}
               className="flex-1"
            >
               {/* Segmented Progress Bar */}
               <div className="flex gap-1.5 mb-6">
                 {QUESTIONS.map((q, i) => (
                   <div 
                     key={q.id} 
                     className={cn(
                       "h-1.5 rounded-full flex-1 transition-all duration-500",
                       i <= step ? "bg-[var(--color-primary)]" : "bg-gray-100"
                     )} 
                   />
                 ))}
               </div>

               <h2 className="text-[var(--color-primary)] font-bold text-sm mb-2 uppercase tracking-wider">
                 질문 {step + 1} / {QUESTIONS.length}
               </h2>
               <h1 className="text-2xl font-bold mb-10 leading-relaxed">
                 {currentQ.question}
               </h1>

               <div className="space-y-3">
                 {currentQ.options.map((option) => (
                   <button
                     key={option}
                     onClick={() => handleSelect(option)}
                     className={cn(
                       "w-full p-5 text-left rounded-2xl transition-all flex items-center justify-between",
                       answers[currentQ.id] === option 
                         ? "bg-[var(--color-secondary)]/40 text-[var(--color-primary)] font-bold ring-2 ring-[var(--color-primary)]/50" 
                         : "bg-slate-50 hover:bg-slate-100 text-[var(--color-text-primary)]"
                     )}
                   >
                     {option}
                     {answers[currentQ.id] === option && <ChevronRight size={20} />}
                   </button>
                 ))}
               </div>
            </motion.div>
         </AnimatePresence>
      </div>
    </div>
  );
}

export default function SurveyPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <SurveyContent />
    </Suspense>
  );
}
