"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";
import { BackButton } from "@/components/ui/BackButton";

export default function AiDecisionPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col items-center">
      <div className="w-full max-w-md flex-1 flex flex-col pt-2 items-start">
        <BackButton className="-ml-8 mb-6" href="/onboarding/add" />

        <div className="flex-1 w-full flex flex-col justify-center pb-20">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-20 h-20 rounded-3xl bg-[var(--color-secondary)] flex items-center justify-center text-[var(--color-primary)] mb-8 mx-auto shadow-sm"
          >
            <Sparkles size={40} />
          </motion.div>

          <div className="text-center mb-12">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-4 leading-tight">
              투자성향 분석을 <br /> 시작할까요?
            </h1>
            <p className="text-[var(--color-text-secondary)] leading-relaxed px-4">
              사용자의 투자 성향을 분석하고 <br />
              현재 보유 자산과의 조화도를 체크해드려요.
            </p>
          </div>

          <div className="space-y-3 w-full">
            <Button
              className="w-full h-16 rounded-[24px] text-[17px] font-bold shadow-lg shadow-emerald-100 cursor-pointer"
              onClick={() => router.push("/onboarding/survey/intro")}
            >
              네, 정밀 분석 받을게요
              <ArrowRight size={20} className="ml-2" />
            </Button>
            <Button
              variant="ghost"
              className="w-full h-16 rounded-[24px] text-[16px] font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
              onClick={() => router.push("/dashboard")}
            >
              나중에 할게요
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
