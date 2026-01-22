"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white flex justify-center">
      {/* Mobile-First Container */}
      <div className="w-full max-w-md flex flex-col">
        {/* Header - 뒤로가기 버튼 영역 */}
        <header className="flex-shrink-0 px-4 py-6">
          <button
            onClick={() => router.back()}
            className="p-2 text-slate-800 hover:bg-slate-100 rounded-full transition-colors"
            aria-label="Go back"
          >
            <ArrowLeft size={24} />
          </button>
        </header>

        {/* Content */}
        <div className="flex-1 flex flex-col">
          {children}
        </div>
      </div>
    </div>
  );
}
