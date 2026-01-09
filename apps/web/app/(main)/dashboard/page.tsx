"use client";

import { usePortfolioStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { TrendingUp, PieChart, Brain, ArrowUpRight, Plus, RefreshCw, ChevronRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// Mock AI Data
const AI_SUMMARY = {
  score: 78,
  summary: "포트폴리오가 기술주에 집중되어 있어요. 변동성이 높지만, 현재 상승장에서 유리한 구조입니다.",
  risk: "High",
  rebalancing: "현금 비중을 10% 늘리는 것을 추천해요."
};

import { GlobalNavBar } from "@/components/GlobalNavBar";

// ... (keep existing imports)

export default function DashboardPage() {
  const { assets } = usePortfolioStore();
  const [activeTab, setActiveTab] = useState<"assets" | "ai" | "stats">("assets");
  const [sortBy, setSortBy] = useState<"value" | "rate">("value");

  // Mock Calculation
  const totalValue = assets.reduce((acc, a) => acc + (a.avgPrice * a.quantity), 0);
  const totalGain = totalValue * 0.05; // Mock 5% gain

  return (
    <div className="min-h-screen bg-white">
      <GlobalNavBar />

      <div className="container-custom mt-2">
        {/* Tabs - Refined Premium Zen Style */}
        <div className="mb-8">
          <div className="flex gap-4 w-fit">
             {["assets", "ai", "stats"].map((tab) => (
               <button
                 key={tab}
                 onClick={() => setActiveTab(tab as any)}
                 className={cn(
                   "px-6 py-2.5 rounded-full font-[900] text-[16px] transition-all duration-300 tracking-tight border",
                   activeTab === tab 
                     ? "bg-slate-900 text-white border-slate-900 shadow-[0_8px_16px_-4px_rgba(0,0,0,0.1)]" 
                     : "bg-white text-slate-400 border-slate-100 hover:border-slate-300 hover:text-slate-600"
                 )}
               >
                 {tab === "assets" && "자산 현황"}
                 {tab === "ai" && "AI 분석"}
                 {tab === "stats" && "통계"}
               </button>
             ))}
          </div>
        </div>

      <main className="space-y-12 mt-6">
        {/* Tab Content */}
        <AnimatePresence mode="wait">
            {activeTab === "assets" && (
              <motion.div 
                key="assets"
                initial={{ opacity: 0, scale: 0.98, y: 8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.98, y: -8 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="space-y-12"
              >
                {/* Total Asset Summary - Horizontal & Softer (Non-Toss) */}
                <section className="bg-slate-50/50 rounded-[24px] border border-slate-100 py-4 px-6 group transition-all duration-500 hover:bg-white hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.05)] w-full">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-6">
                       {/* Left Side: Total Amount */}
                       <div className="flex flex-col gap-0.5">
                          <div className="text-slate-400 text-[10px] sm:text-[11px] font-[800] uppercase tracking-wider">내 자산 총액</div>
                          <div className="flex items-baseline gap-1.5">
                             <span className="text-[24px] sm:text-[28px] font-[900] tracking-tight text-slate-900">
                                {totalValue.toLocaleString()}
                             </span>
                             <span className="text-[14px] sm:text-[16px] font-[800] text-slate-300">원</span>
                          </div>
                       </div>
 
                       {/* Right Side: Quick Stats - Combined on Mobile line, Split on PC */}
                       <div className="flex flex-row items-center sm:items-center gap-0 sm:gap-8 bg-transparent">
                          <div className="flex flex-row items-baseline sm:flex-col sm:gap-0.5 sm:items-end text-right">
                             <span className="text-[10px] font-[800] text-slate-300 uppercase tracking-tight hidden sm:block">누적 수익</span>
                             <span className={cn(
                                "text-[14px] sm:text-[16px] font-[900]",
                                totalGain >= 0 ? "text-red-500" : "text-blue-500"
                             )}>
                                {totalGain >= 0 ? "+" : ""}{totalGain.toLocaleString()}원
                             </span>
                          </div>
                          
                          {/* Separator: Split Line on PC, Colored Parentheses on Mobile */}
                          <div className="flex items-center">
                            <div className="w-[1px] h-6 bg-slate-100 mx-4 hidden sm:block" />
                          </div>

                          <div className="flex flex-row items-baseline sm:flex-col sm:gap-0.5 sm:items-end text-right">
                             <span className="text-[10px] font-[800] text-slate-300 uppercase tracking-tight hidden sm:block">수익률</span>
                             <span className={cn(
                                "text-[14px] sm:text-[16px] font-[900]",
                                totalGain >= 0 ? "text-red-500" : "text-blue-500"
                             )}>
                                <span className="sm:hidden">(</span>
                                {totalGain >= 0 ? "+" : ""}{((totalGain/totalValue)*100).toFixed(1)}%
                                <span className="sm:hidden">)</span>
                             </span>
                          </div>
                       </div>
                    </div>
                </section>
 
                 <div className="space-y-6">
                    {/* Control Bar: Sort & Add Stock */}
                    {assets.length > 0 && (
                      <div className="flex items-center justify-between px-2 pt-2">
                         <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-100/50">
                            <button 
                              onClick={() => setSortBy("value")}
                              className={cn(
                                "px-3 py-1.5 text-[12px] font-[900] rounded-lg transition-all",
                                sortBy === "value" ? "bg-white text-slate-900 shadow-sm" : "text-slate-400 hover:text-slate-600"
                              )}
                            >
                               평가금액 순
                            </button>
                            <button 
                              onClick={() => setSortBy("rate")}
                              className={cn(
                                "px-3 py-1.5 text-[12px] font-[900] rounded-lg transition-all",
                                sortBy === "rate" ? "bg-white text-slate-900 shadow-sm" : "text-slate-400 hover:text-slate-600"
                              )}
                            >
                               등락률 순
                            </button>
                         </div>
 
                         <Link href="/onboarding/add/manual">
                            <button className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-[900] text-[var(--color-primary)] hover:bg-slate-50 rounded-xl transition-all group">
                               <Plus size={16} strokeWidth={3} className="group-hover:rotate-90 transition-transform" />
                               <span>종목 추가</span>
                            </button>
                         </Link>
                      </div>
                    )}
 
                    <div className="space-y-0 -mx-6">
                      {assets.length === 0 ? (
                        <div className="text-center py-24 px-6">
                           <div className="text-slate-200 mb-4 flex justify-center">
                              <TrendingUp size={48} strokeWidth={1} />
                           </div>
                           <div className="text-slate-300 font-[900] text-lg">보유한 자산이 없어요</div>
                           <div className="text-slate-400 text-sm font-bold mt-1">지금 바로 첫 자산을 추가해보세요</div>
                        </div>
                      ) : (
                        [...assets].sort((a, b) => {
                          if (sortBy === "value") {
                            return (b.avgPrice * b.quantity) - (a.avgPrice * a.quantity);
                          } else {
                            // Mocking rate sort (using +12.4% mock for now, but in reality we'd use currentPrice)
                            const getRate = (asset: any) => 12.4; // Mock
                            return getRate(b) - getRate(a);
                          }
                        }).map((asset) => (
                          <div key={asset.id} className="px-6 py-7 hover:bg-slate-50/50 transition-all flex items-center justify-between group cursor-pointer border-b border-slate-50/50 last:border-0">
                             <div className="flex items-center gap-5">
                                <div className="w-14 h-14 rounded-2xl bg-slate-50 flex items-center justify-center font-[900] text-slate-300 text-base border border-slate-100/50 group-hover:scale-105 transition-transform duration-300">
                                   {asset.ticker.slice(0,1)}
                                </div>
                                <div className="flex flex-col gap-0.5">
                                   <div className="font-[900] text-[18px] text-slate-900 tracking-tight">{asset.name}</div>
                                   <div className="text-[13px] font-[700] text-slate-400">
                                      {asset.quantity}주 · {asset.currency === 'USD' ? '$' : '₩'}{asset.avgPrice.toLocaleString()}
                                   </div>
                                </div>
                             </div>
                             <div className="text-right flex flex-col gap-0.5">
                                <div className="font-[900] text-[18px] text-slate-900 tracking-tight">
                                   {asset.currency === 'USD' ? '$' : '₩'}{(asset.avgPrice * asset.quantity).toLocaleString()}
                                </div>
                                <div className={cn(
                                   "text-[14px] font-[900]",
                                   12 >= 0 ? "text-red-500" : "text-blue-500"
                                )}>
                                   +12.4%
                                </div>
                             </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                 {/* Add Asset Button - Premium Zen Style */}
                 <Link href="/onboarding/add/manual" className="block pt-7">
                     <div className="w-full py-4 sm:py-5 rounded-[20px] sm:rounded-[24px] bg-slate-50 border border-slate-100 flex items-center justify-center gap-2.5 hover:bg-slate-100 transition-all text-slate-500 font-[900] text-[14px] sm:text-[15px] group">
                        <Plus size={18} strokeWidth={3} className="sm:size-5 group-hover:rotate-90 transition-transform duration-500" />
                        <span>종목 추가하기</span>
                     </div>
                  </Link>
              </motion.div>
            )}

           {activeTab === "ai" && (
             <motion.div 
               key="ai"
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: -10 }}
               className="space-y-4"
             >
                <div className="bg-gradient-to-br from-[var(--color-primary)] to-green-600 rounded-[32px] p-8 text-white relative overflow-hidden">
                   <div className="relative z-10">
                      <div className="text-white/80 mb-2 font-medium">포트폴리오 건강도</div>
                      <div className="text-6xl font-bold mb-4">{AI_SUMMARY.score}점</div>
                      <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-xl text-sm font-medium w-fit">
                         {AI_SUMMARY.score > 70 ? "아주 튼튼해요 🚀" : "개선이 필요해요 🤔"}
                      </div>
                   </div>
                   <Brain className="absolute right-[-20px] bottom-[-20px] w-40 h-40 text-white/10" />
                </div>

                <div className="bg-white p-6 rounded-[32px] border border-[var(--color-border)]">
                   <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                     <Brain size={20} className="text-[var(--color-primary)]" />
                     AI 분석 리포트
                   </h3>
                   <p className="text-[var(--color-text-secondary)] leading-relaxed mb-6">
                      {AI_SUMMARY.summary}
                   </p>
                   
                   <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                         <span className="text-gray-500">위험도</span>
                         <span className="font-bold text-red-500">{AI_SUMMARY.risk}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                         <span className="text-gray-500">리밸런싱 제안</span>
                         <span className="font-bold text-blue-500">{AI_SUMMARY.rebalancing}</span>
                      </div>
                   </div>
                </div>
             </motion.div>
           )}

           {activeTab === "stats" && (
             <motion.div 
               key="stats"
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: -10 }}
               className="space-y-4"
             >
                <div className="bg-white p-6 rounded-[32px] border border-[var(--color-border)] h-64 flex items-center justify-center text-gray-400">
                   <div className="text-center">
                     <PieChart size={40} className="mx-auto mb-2 opacity-50" />
                     <p>자산 비중 차트 준비중</p>
                   </div>
                </div>
             </motion.div>
           )}
        </AnimatePresence>
      </main>
      </div>
    </div>
  );
}
