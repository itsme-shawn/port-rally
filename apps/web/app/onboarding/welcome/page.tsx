"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function WelcomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col items-center justify-center text-center">
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-8 text-6xl"
      >
        🎉
      </motion.div>
      
      <h1 className="text-3xl font-bold mb-4">가입을 축하해요!</h1>
      <p className="text-[var(--color-text-secondary)] mb-12">
        이제 포트폴리오를 만들고<br/>
        맞춤형 분석을 받아보세요.
      </p>
      
      <div className="w-full max-w-md space-y-3">
        <Button 
          className="w-full text-lg h-14 rounded-2xl" 
          onClick={() => router.push("/onboarding/check")}
        >
          포트폴리오 생성하기
        </Button>
        <Button 
          variant="ghost" 
          className="w-full text-lg h-14 rounded-2xl"
          onClick={() => router.push("/dashboard")}
        >
          일단 둘러보기
        </Button>
      </div>
    </div>
  );
}
