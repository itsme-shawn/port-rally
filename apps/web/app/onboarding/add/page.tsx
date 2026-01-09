"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { Camera, Edit3, ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";

export default function AddPortfolioPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col">
      <div className="w-full max-w-2xl mx-auto pt-10 flex-1 flex flex-col">

        <motion.div
           initial={{ opacity: 0, x: 20 }}
           animate={{ opacity: 1, x: 0 }}
        >
          <h1 className="text-2xl font-bold mb-3">어떻게 자산을 입력할까요?</h1>
          <p className="text-[var(--color-text-secondary)] mb-12">
             증권사 앱 캡처 한 장이면<br/>
             AI가 자동으로 종목을 정리해드려요.
          </p>

          <div className="space-y-4">
             <button 
               onClick={() => router.push("/onboarding/add/photo")}
               className="w-full p-6 text-left rounded-[28px] bg-[var(--color-primary)] text-white hover:bg-[#00B34E] transition-all shadow-lg flex items-center justify-between group"
             >
                <div>
                   <div className="font-bold text-lg mb-1">스크린샷으로 자동 입력</div>
                   <div className="text-white/80 text-sm">가장 빠르고 간편해요</div>
                </div>
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                   <Camera size={24} />
                </div>
             </button>

             <button 
               onClick={() => router.push("/onboarding/add/manual")}
               className="w-full p-6 text-left rounded-[28px] bg-[var(--color-background-subtle)] hover:bg-gray-100 transition-all flex items-center justify-between"
             >
                <div>
                   <div className="font-bold text-lg mb-1 text-[var(--color-text-primary)]">직접 검색해서 입력</div>
                   <div className="text-[var(--color-text-tertiary)] text-sm">하나씩 꼼꼼하게</div>
                </div>
                <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-gray-400">
                   <Edit3 size={24} />
                </div>
             </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
