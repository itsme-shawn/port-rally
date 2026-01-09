"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AgreePage() {
  const router = useRouter();
  const [agreed, setAgreed] = useState(false);

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col">
      <div className="flex-1 max-w-md mx-auto w-full pt-10">
        <h1 className="text-2xl font-bold mb-8">서비스 이용을 위해<br/>약관에 동의해주세요</h1>
        
        <div className="space-y-6">
          <div 
            onClick={() => setAgreed(!agreed)}
            className="flex items-center gap-4 p-4 rounded-2xl cursor-pointer hover:bg-gray-50 transition-colors"
          >
             <div className={cn(
               "w-6 h-6 rounded-full border flex items-center justify-center transition-colors",
               agreed ? "bg-[var(--color-primary)] border-transparent text-white" : "border-gray-300"
             )}>
                {agreed && <Check size={14} />}
             </div>
             <span className="font-bold text-lg">전체 동의하기</span>
          </div>

          <div className="space-y-4 pl-2">
             <div className="flex items-center gap-3 text-sm text-[var(--color-text-secondary)]">
                <Check size={16} className={agreed ? "text-[var(--color-primary)]" : "text-gray-300"} />
                <span>[필수] 서비스 이용약관</span>
             </div>
             <div className="flex items-center gap-3 text-sm text-[var(--color-text-secondary)]">
                <Check size={16} className={agreed ? "text-[var(--color-primary)]" : "text-gray-300"} />
                <span>[필수] 개인정보 수집 및 이용</span>
             </div>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto w-full pb-8">
        <Button 
          className="w-full text-lg h-14 rounded-2xl" 
          disabled={!agreed}
          onClick={() => router.push("/onboarding/welcome")}
        >
          동의하고 시작하기
        </Button>
      </div>
    </div>
  );
}
