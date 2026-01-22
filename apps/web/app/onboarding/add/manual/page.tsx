"use client";

import { Suspense } from "react";
import { AssetEntryForm } from "@/components/onboarding/AssetEntryForm";

function ManualAddContent() {
  return (
    <AssetEntryForm 
      title="자산 직접 입력"
      subtitle="보유하신 자산 정보를 꼼꼼하게 입력해주세요."
      backHref="/onboarding/add"
    />
  );
}

export default function ManualAddPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ManualAddContent />
    </Suspense>
  );
}
