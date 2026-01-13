"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

interface BackButtonProps {
  className?: string;
  onClick?: () => void;
  iconSize?: number;
  href?: string;
}

export function BackButton({ className, onClick, iconSize = 24, href }: BackButtonProps) {
  const router = useRouter();

  const handleBack = () => {
    if (href) {
      router.push(href);
    } else if (onClick) {
      onClick();
    } else {
      router.back();
    }
  };

  return (
    <button 
      onClick={handleBack}
      className={cn("inline-flex items-center justify-center p-2 hover:bg-slate-50 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 cursor-pointer", className)}
      aria-label="Go back"
    >
      <ArrowLeft size={iconSize} className="text-slate-900" />
    </button>
  );
}
