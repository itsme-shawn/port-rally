"use client";

import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { getActiveTerms } from "@/lib/api/terms";
import { completeSignup } from "@/lib/api/auth";
import { useQuery, useMutation } from "@tanstack/react-query";

export default function AgreePage() {
  const router = useRouter();
  const [agreedTerms, setAgreedTerms] = useState<Set<number>>(new Set());

  // 1. 서버 상태 관리 (데이터 조회)
  const { data: terms = [], isLoading } = useQuery({
    queryKey: ["terms"],
    queryFn: getActiveTerms,
  });

  // 2. 서버 상태 관리 (데이터 변경)
  const { mutate: submitSignup, isPending: isSubmitting } = useMutation({
    mutationFn: completeSignup,
    onSuccess: () => {
      router.push("/onboarding/welcome");
    },
    onError: (error) => {
      console.error("Failed to complete signup:", error);
      // 추후 Toast 등으로 에러 표시
    },
  });

  const handleToggleTerm = (termId: number) => {
    const newAgreed = new Set(agreedTerms);
    if (newAgreed.has(termId)) {
      newAgreed.delete(termId);
    } else {
      newAgreed.add(termId);
    }
    setAgreedTerms(newAgreed);
  };

  const handleToggleAll = () => {
    if (agreedTerms.size === terms.length) {
      setAgreedTerms(new Set());
    } else {
      setAgreedTerms(new Set(terms.map((t) => t.termsId)));
    }
  };

  const handleSubmit = () => {
    submitSignup({
      agreements: terms.map((t) => ({
        termsId: t.termsId,
        agreed: agreedTerms.has(t.termsId),
      })),
    });
  };

  const allRequiredAgreed = terms.length > 0 && terms
    .filter((t) => t.isRequired)
    .every((t) => agreedTerms.has(t.termsId));
    
  const isAllAgreed = terms.length > 0 && agreedTerms.size === terms.length;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="animate-spin text-[var(--color-primary)]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col">
      <div className="flex-1 max-w-md mx-auto w-full pt-10">
        <h1 className="text-2xl font-bold mb-8">서비스 이용을 위해<br/>약관에 동의해주세요</h1>
        
        <div className="space-y-6">
          <div 
            onClick={handleToggleAll}
            className="flex items-center gap-4 p-5 rounded-2xl cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors border border-transparent"
          >
             <div className={cn(
               "w-6 h-6 rounded-full border flex items-center justify-center transition-colors",
               isAllAgreed ? "bg-[var(--color-primary)] border-transparent text-white" : "border-gray-300 bg-white"
             )}>
                <Check size={14} strokeWidth={3} className={cn(!isAllAgreed && "opacity-0")} />
             </div>
             <span className="font-bold text-lg">전체 동의하기</span>
          </div>

          <div className="space-y-6 px-2">
             {terms.map((term) => (
               <div key={term.termsId} className="space-y-3">
                 <div 
                   className="flex items-center gap-3 cursor-pointer group"
                   onClick={() => handleToggleTerm(term.termsId)}
                 >
                    <div className={cn(
                      "w-5 h-5 rounded-full border flex items-center justify-center transition-colors",
                      agreedTerms.has(term.termsId) ? "bg-[var(--color-primary)] border-transparent text-white" : "border-gray-300 group-hover:border-gray-400"
                    )}>
                      <Check size={12} strokeWidth={3} className={cn(!agreedTerms.has(term.termsId) && "opacity-0")} />
                    </div>
                    <span className={cn(
                      "text-sm font-medium transition-colors",
                      agreedTerms.has(term.termsId) ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)]"
                    )}>
                      {term.isRequired ? "[필수]" : "[선택]"} {term.title}
                    </span>
                 </div>
                 {term.content && (
                   <div className="ml-8 p-4 bg-[var(--color-background-subtle)] rounded-xl text-xs text-[var(--color-text-secondary)] max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed border border-[var(--color-border)]">
                      {term.content}
                   </div>
                 )}
               </div>
             ))}
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto w-full pb-8">
        <Button 
          className="w-full text-lg h-14 rounded-2xl" 
          disabled={!allRequiredAgreed || isSubmitting}
          onClick={handleSubmit}
        >
          {isSubmitting ? (
            <Loader2 className="animate-spin mr-2" /> 
          ) : null}
          동의하고 시작하기
        </Button>
      </div>
    </div>
  );
}
