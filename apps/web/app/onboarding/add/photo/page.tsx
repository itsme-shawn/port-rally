"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { usePortfolioStore } from "@/lib/store";

export default function PhotoUploadPage() {
  const router = useRouter();
  const addAsset = usePortfolioStore((state) => state.addAsset);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    // Simulate upload flow
    const timer = setTimeout(() => {
       setAnalyzing(true);
       
       // Simulate AI processing time
       setTimeout(() => {
          // Add mock data with unique IDs
          const timestamp = Date.now();
          addAsset({ id: `mock-${timestamp}-1`, ticker: "TSLA", name: "테슬라", avgPrice: 240, quantity: 15, currency: "USD" });
          addAsset({ id: `mock-${timestamp}-2`, ticker: "NVDA", name: "엔비디아", avgPrice: 130, quantity: 50, currency: "USD" });
          addAsset({ id: `mock-${timestamp}-3`, ticker: "005930", name: "삼성전자", avgPrice: 72000, quantity: 100, currency: "KRW" });
          
          router.replace("/onboarding/add/manual"); // Redirect to manual for verification
       }, 2000);

    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center text-slate-900 p-6 text-center">
       {!analyzing ? (
         <div className="animate-pulse">
           <h2 className="text-xl font-bold mb-2">이미지 업로드 중...</h2>
           <p className="text-slate-500">잠시만 기다려주세요</p>
         </div>
       ) : (
         <div>
           <Loader2 className="animate-spin w-12 h-12 text-[var(--color-primary)] mx-auto mb-6" />
           <h2 className="text-2xl font-bold mb-2">AI가 자산을<br/>분석하고 있어요</h2>
           <p className="text-slate-500">약 5초 정도 소요됩니다</p>
         </div>
       )}
    </div>
  );
}
