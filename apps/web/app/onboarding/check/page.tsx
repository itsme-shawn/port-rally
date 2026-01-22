"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { usePortfolioStore } from "@/lib/store";
import { TrendingUp, Wallet } from "lucide-react";
import { motion } from "framer-motion";

export default function InvestmentCheckPage() {
  const router = useRouter();
  const setHasInvestment = usePortfolioStore((state) => state.setHasInvestment);
  const reset = usePortfolioStore((state) => state.reset);

  const handleSelection = (hasInvestment: boolean) => {
    reset(); // Clear any existing mock/stale data
    setHasInvestment(hasInvestment);
    if (hasInvestment) {
      router.push("/onboarding/add");
    } else {
      router.push("/onboarding/survey");
    }
  };

  return (
    <div className="flex-1 bg-white px-6 pb-6 flex flex-col items-center justify-center overflow-hidden">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md text-center"
      >
        <h1 className="text-2xl font-bold mb-4">현재 투자를 하고 계신가요?</h1>
        <p className="text-[var(--color-text-secondary)] mb-12">
          투자 여부에 따라 맞춤형 시작 화면을<br/>
          제공해 드릴게요.
        </p>

        <div className="grid grid-cols-1 gap-4">
          <Button
            onClick={() => handleSelection(true)}
            className="flex flex-col items-center justify-center gap-4 p-8 rounded-[32px] h-auto"
          >
             <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-white shadow-sm">
                <TrendingUp size={32} strokeWidth={2.5} />
             </div>
             <div className="font-bold text-lg">네, 투자를 하고 있어요</div>
          </Button>

          <Button
            variant="ghost"
            onClick={() => handleSelection(false)}
            className="flex flex-col items-center justify-center gap-4 p-8 rounded-[32px] h-auto bg-slate-50 hover:bg-slate-100  border-slate-100 hover:border-slate-200"
          >
             <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center text-slate-400 shadow-sm">
                <Wallet size={32} />
             </div>
             <div className="font-bold text-lg">아니요, 아직 안 해요</div>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
