"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter, usePathname } from "next/navigation";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-white flex justify-center">
      <div className="w-full max-w-7xl px-4 md:px-6 min-h-screen relative">
        {/* Back Button */}
        {pathname !== "/onboarding/add/photo" && (
          <button
            onClick={() => {
              router.back();
            }}
            className="absolute top-4 left-4 md:left-6 z-50 p-2 text-slate-800 hover:bg-slate-100 rounded-full transition-colors"
            aria-label="Go back"
          >
            <ArrowLeft size={24} />
          </button>
        )}

        {/* Content */}
        {children}
      </div>
    </div>
  );
}
