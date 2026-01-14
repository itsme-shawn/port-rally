"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function WelcomePage() {
  const router = useRouter();

  return (
    <div className="flex-1 bg-white flex flex-col overflow-hidden">
      {/* Content Area */}
      <div className="flex-1 flex flex-col items-center justify-center text-center px-6 pb-6">
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
          이제 포트폴리오를 만들고<br />
          맞춤형 분석을 받아보세요.
        </p>
      </div>

      {/* Fixed Button Area */}
      <div className="flex-shrink-0 border-t border-gray-100 bg-white">
        <div className="max-w-md mx-auto p-6 space-y-3">
          <Button
            className="w-full text-lg h-14 rounded-2xl"
            onClick={() => router.push("/onboarding/check")}
          >
            포트폴리오 생성하기
          </Button>
          <Button
            variant="ghost"
            className="w-full text-lg h-14 rounded-2xl font-bold cursor-pointer bg-slate-100 hover:bg-slate-200"
            onClick={() => router.push("/dashboard")}
          >
            일단 둘러보기
          </Button>
        </div>
      </div>
    </div>
  );
}
