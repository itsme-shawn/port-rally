"use client";

import { Suspense } from "react";
import { AssetEntryForm } from "@/components/onboarding/AssetEntryForm";

function AiCheckContent() {
  return (
    <AssetEntryForm 
      title="내역이 맞는지 확인해주세요"
      subtitle="AI가 분석한 정보가 정확한지 확인하고 수정할 수 있어요."
      badgeText="OCR 분석 완료"
      backHref="/onboarding/add/photo"
    />
  );
}

export default function AiCheckPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <AiCheckContent />
    </Suspense>
  );
}