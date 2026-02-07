"use client";

import { usePortfolioStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, PieChart, Brain, ArrowUpRight, Plus, RefreshCw, ChevronRight, Shield, Target, AlertTriangle, Zap, Sparkles, BarChart3, ArrowRight, Wallet, Globe, Calendar, Trophy, Clock, DollarSign, Percent, Loader2, X, ClipboardList } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { getAssetDetails } from "@/lib/api/asset";
import { useExchangeRate } from "@/lib/hooks/useExchangeRate";
import { toKRW } from "@/lib/utils/currency";

// Mock AI Data
const AI_ANALYSIS = {
   // 포트폴리오 건강도
   health: {
      score: 78,
      grade: "B+",
      trend: "up", // up, down, stable
      previousScore: 72,
      summary: "지난 달 대비 6점 상승했어요"
   },

   // 핵심 인사이트
   insights: [
      {
         type: "warning",
         title: "섹터 집중도 높음",
         description: "기술주 비중이 68%로 높아요. 섹터 분산을 고려해보세요.",
         impact: "high"
      },
      {
         type: "positive",
         title: "수익률 양호",
         description: "최근 3개월 수익률이 시장 평균(+4.2%) 대비 우수해요.",
         impact: "medium"
      },
      {
         type: "neutral",
         title: "환율 노출",
         description: "달러 자산 비중 45%. 환율 변동에 따른 영향을 받을 수 있어요.",
         impact: "medium"
      }
   ],

   // 리스크 분석
   risk: {
      level: "중간-높음",
      volatility: 24.5, // 변동성 (%)
      sharpeRatio: 1.42,
      maxDrawdown: -12.3,
      beta: 1.15
   },

   // 섹터 분포
   sectors: [
      { name: "기술", percentage: 68, color: "#3B82F6" },
      { name: "금융", percentage: 15, color: "#10B981" },
      { name: "헬스케어", percentage: 10, color: "#8B5CF6" },
      { name: "기타", percentage: 7, color: "#94A3B8" }
   ],

   // AI 추천
   recommendations: [
      {
         action: "rebalance",
         title: "리밸런싱 제안",
         description: "기술주 비중을 50%로 줄이고, 채권 ETF 추가를 권장해요.",
         priority: "high"
      },
      {
         action: "add",
         title: "분산 투자",
         description: "방어주(유틸리티, 필수소비재) 편입으로 안정성을 높여보세요.",
         priority: "medium"
      },
      {
         action: "hold",
         title: "현 포지션 유지",
         description: "삼성전자, Apple은 장기 보유 관점에서 유지하세요.",
         priority: "low"
      }
   ],

   // 시장 컨텍스트
   marketContext: {
      sentiment: "neutral",
      keyFactors: ["금리 동결 예상", "AI 섹터 강세 지속", "달러 약세 전환 가능성"]
   },

   // 분석 리포트
   executiveSummary: "본 포트폴리오는 기술주 중심의 고성장 전략을 취하고 있으나, 최근 섹터 쏠림 현상으로 인한 변동성 확대가 우려됩니다. 현금 비중 확대를 통한 리스크 관리와 함께, 배당주 편입을 통한 'Barbell 전략'으로 포트폴리오 안정성을 강화할 시점입니다.",
   fullReport: `# 2026년 하반기 포트폴리오 정밀 진단

## 1. 시장 현황 및 포트폴리오 포지셔닝
현재 글로벌 증시는 인플레이션 둔화와 경기 침체 우려가 공존하는 국면입니다. 귀하의 포트폴리오는 **기술주(68%)**에 과도하게 편중되어 있어, 시장 변동성에 매우 민감한 구조를 보이고 있습니다. 이는 상승장에서 강력한 초과 수익을 기대할 수 있으나, 하락장에서는 벤치마크 대비 더 큰 손실 위험에 노출됨을 의미합니다.

## 2. 핵심 종목 심층 분석
- **NVIDIA & Apple**: 포트폴리오의 코어 자산으로서 훌륭한 성장성을 보유하고 있으나, 두 종목 합산 비중이 30%를 상회하는 것은 개별 기업 리스크를 제어하기 어려운 수준입니다.
- **금융 섹터**: 금리 인하 사이클 진입 시 순이자마진(NIM) 축소 우려가 있으나, 현재의 밸류에이션은 매력적인 수준입니다.

## 3. 리스크 요인 점검 (Risk Factor)
현재 포트폴리오의 연환산 변동성은 **24.5%**로, S&P 500 평균(약 15%)을 크게 상회합니다. 또한 최대 낙폭(MDD)이 -12.3%로 나타나, 하락장에서의 방어력이 다소 부족한 것으로 판단됩니다.

## 4. 향후 대응 전략 (Action Plan)
1. **현금 비중 확대**: 단기적으로 현금 비중을 10%까지 확대하여 시장 조정 시 저가 매수 기회를 확보하세요.
2. **배당 성장주 편입**: 리츠(REITs) 또는 배당 귀족주(Dividend Aristocrats) ETF를 15% 수준으로 편입하여 포트폴리오의 하단을 방어하는 전략을 권장합니다.`
}

// Mock 통계 데이터 - 현재 포트폴리오 기반
const STATS_DATA = {
   // 섹터별 분포
   sectors: [
      { name: "정보기술", value: 42, color: "#3B82F6", stocks: ["삼성전자", "Apple", "NVIDIA"] },
      { name: "금융", value: 18, color: "#10B981", stocks: ["KB금융", "JPMorgan"] },
      { name: "헬스케어", value: 15, color: "#8B5CF6", stocks: ["삼성바이오", "Pfizer"] },
      { name: "경기소비재", value: 12, color: "#F59E0B", stocks: ["Tesla", "현대차"] },
      { name: "커뮤니케이션", value: 8, color: "#EF4444", stocks: ["카카오", "Meta"] },
      { name: "기타", value: 5, color: "#94A3B8", stocks: [] }
   ],

   // 종목별 히트맵 데이터 (수익률 기반)
   heatmap: [
      { ticker: "AAPL", name: "Apple", weight: 18, return: 24.5 },
      { ticker: "005930", name: "삼성전자", weight: 15, return: 8.2 },
      { ticker: "NVDA", name: "NVIDIA", weight: 12, return: 48.3 },
      { ticker: "TSLA", name: "Tesla", weight: 10, return: -5.2 },
      { ticker: "035720", name: "카카오", weight: 8, return: -12.4 },
      { ticker: "105560", name: "KB금융", weight: 7, return: 15.6 },
      { ticker: "207940", name: "삼성바이오", weight: 6, return: 3.8 },
      { ticker: "META", name: "Meta", weight: 5, return: 32.1 },
      { ticker: "JPM", name: "JPMorgan", weight: 5, return: 18.9 },
      { ticker: "PFE", name: "Pfizer", weight: 4, return: -8.7 },
      { ticker: "005380", name: "현대차", weight: 5, return: 11.2 },
      { ticker: "CASH", name: "현금", weight: 5, return: 0 }
   ],

   // 시가총액별 분포
   marketCap: [
      { name: "대형주", range: ">100조", value: 55, color: "#3B82F6" },
      { name: "중형주", range: "10-100조", value: 30, color: "#10B981" },
      { name: "소형주", range: "<10조", value: 15, color: "#F59E0B" }
   ],

   // 통화별 분포
   currencies: [
      { name: "KRW", label: "원화", value: 55, color: "#3B82F6" },
      { name: "USD", label: "달러", value: 45, color: "#10B981" }
   ],

   // 국가별 분포
   countries: [
      { name: "한국", flag: "🇰🇷", value: 55 },
      { name: "미국", flag: "🇺🇸", value: 45 }
   ],

   // 포트폴리오 집중도
   concentration: {
      top1: 18,  // 상위 1개 종목 비중
      top3: 45,  // 상위 3개 종목 비중
      top5: 63,  // 상위 5개 종목 비중
      hhi: 1250  // 허핀달-허쉬만 지수
   },

   // 배당 정보
   dividends: {
      yieldRate: 1.8,
      expectedAnnual: 480000,
      payingStocks: 6,
      totalStocks: 11
   },

   // 밸류에이션 지표
   valuation: {
      avgPER: 22.4,
      avgPBR: 3.2,
      avgDividendYield: 1.8
   }
};

import { GlobalNavBar } from "@/components/GlobalNavBar";
import { Treemap, ResponsiveContainer } from "recharts";
import { HoldingsSection } from "@/components/dashboard/HoldingsSection";

export default function DashboardPage() {
   const { assets } = usePortfolioStore();
   const [activeTab, setActiveTab] = useState<"assets" | "ai" | "stats">("assets");
   const [isTreemapLoading, setIsTreemapLoading] = useState(true);
   const [currentPrices, setCurrentPrices] = useState<Record<string, number>>({});
   const [dailyChanges, setDailyChanges] = useState<Record<string, number>>({});
   const { rate: exchangeRate } = useExchangeRate();
   const [isReportOpen, setIsReportOpen] = useState(false);

   // 통계 탭으로 전환될 때 트리맵 로딩 시뮬레이션
   useEffect(() => {
      if (activeTab === "stats") {
         setIsTreemapLoading(true);
         const timer = setTimeout(() => {
            setIsTreemapLoading(false);
         }, 1200); // 1.2초 로딩
         return () => clearTimeout(timer);
      }
   }, [activeTab]);

   // 현재가 및 변동률 조회
   useEffect(() => {
      const fetchPrices = async () => {
         const pricePromises = assets.map(async (asset) => {
            try {
               const identifier = `${asset.national}:${asset.market}:${asset.ticker}`;
               const data = await getAssetDetails(identifier, true);

               if (data.price) {
                  return {
                     positionId: asset.positionId,
                     currentPrice: data.price.price,
                     dailyChange: data.price.change_rate
                  };
               }
            } catch (error) {
               console.error(`Failed to fetch price for ${asset.ticker}:`, error);
            }
            return null;
         });

         const results = await Promise.all(pricePromises);
         const newPrices: Record<string, number> = {};
         const newChanges: Record<string, number> = {};

         results.forEach((result) => {
            if (result) {
               newPrices[result.positionId] = result.currentPrice;
               newChanges[result.positionId] = result.dailyChange;
            }
         });

         setCurrentPrices(newPrices);
         setDailyChanges(newChanges);
      };

      if (assets.length > 0) {
         fetchPrices();
      }
   }, [assets]);

   // 실제 평가금액 계산 (현재가 기준, KRW로 통일, 1원 미만 절사)
   const totalValue = Math.floor(assets.reduce((acc, a) => {
      const currentPrice = currentPrices[a.positionId] ?? a.currentPrice ?? a.avgPrice;
      const valueInOriginalCurrency = currentPrice * a.quantity;
      const valueInKRW = toKRW(valueInOriginalCurrency, a.currency, exchangeRate);
      return acc + valueInKRW;
   }, 0));

   // 실제 매입금액 계산 (KRW로 통일, 1원 미만 절사)
   const totalInvested = Math.floor(assets.reduce((acc, a) => {
      const investedInOriginalCurrency = a.avgPrice * a.quantity;
      const investedInKRW = toKRW(investedInOriginalCurrency, a.currency, exchangeRate);
      return acc + investedInKRW;
   }, 0));

   // 실제 수익/손실 계산 (총 평가금액 - 투자원금)
   const totalGain = totalValue - totalInvested;

   // Mock 요약 통계
   const portfolioStats = {
      dailyChange: totalValue * 0.012,
      dailyChangeRate: 1.2,
      weeklyChangeRate: 3.8,
      monthlyChangeRate: 5.2,
      profitableCount: Math.max(1, Math.floor(assets.length * 0.7)),
      losingCount: Math.max(0, assets.length - Math.floor(assets.length * 0.7)),
      bestPerformer: assets.length > 0 ? { name: assets[0]?.name || "삼성전자", rate: 24.5 } : null,
      worstPerformer: assets.length > 1 ? { name: assets[1]?.name || "카카오", rate: -8.2 } : null
   };

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
                        className="space-y-6"
                     >
                        {/* 총자산 히어로 카드 */}
                        <section className="bg-slate-900 rounded-[24px] p-6 sm:p-8 text-white relative overflow-hidden">
                           <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 to-transparent" />
                           <div className="absolute bottom-0 right-0 w-80 h-80 bg-gradient-to-tl from-emerald-500/5 to-transparent rounded-full blur-3xl" />

                           <div className="relative z-10">
                              <div className="flex items-center gap-2 mb-6">
                                 <TrendingUp size={16} className="text-emerald-400" />
                                 <span className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider">내 포트폴리오</span>
                              </div>

                              {/* 총자산 금액 */}
                              <div className="mb-6">
                                 <div className="text-slate-400 text-[12px] font-[700] mb-1">총 평가금액</div>
                                 <div className="flex items-baseline gap-2">
                                    <span className="text-[40px] sm:text-[48px] font-[900] tracking-tighter leading-none">
                                       {totalValue.toLocaleString()}
                                    </span>
                                    <span className="text-[18px] font-[800] text-slate-500">원</span>
                                 </div>
                              </div>

                              {/* 수익 정보 */}
                              <div className="flex flex-wrap items-center gap-x-6 gap-y-3 mb-6">
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">총 수익</div>
                                    <div className={cn(
                                       "text-[20px] font-[900]",
                                       totalGain >= 0 ? "text-red-400" : "text-blue-400"
                                    )}>
                                       {totalGain >= 0 ? "+" : ""}{totalGain.toLocaleString()}원
                                    </div>
                                 </div>
                                 <div className="w-px h-8 bg-slate-700" />
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">수익률</div>
                                    <div className={cn(
                                       "text-[20px] font-[900]",
                                       totalGain >= 0 ? "text-red-400" : "text-blue-400"
                                    )}>
                                       {totalGain >= 0 ? "+" : ""}{totalInvested > 0 ? ((totalGain / totalInvested) * 100).toFixed(2) : "0.00"}%
                                    </div>
                                 </div>
                                 <div className="w-px h-8 bg-slate-700" />
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">투자원금</div>
                                    <div className="text-[20px] font-[900] text-white">
                                       {totalInvested.toLocaleString()}원
                                    </div>
                                 </div>
                              </div>

                              {/* 기간별 변화 */}
                              {/* <div className="flex gap-3">
                         <div className="px-3 py-2 bg-white/5 rounded-xl border border-white/10">
                            <div className="text-[10px] font-[700] text-slate-500 mb-0.5">오늘</div>
                            <div className={cn(
                               "text-[13px] font-[900]",
                               portfolioStats.dailyChangeRate >= 0 ? "text-red-400" : "text-blue-400"
                            )}>
                               {portfolioStats.dailyChangeRate >= 0 ? "+" : ""}{portfolioStats.dailyChangeRate}%
                            </div>
                         </div>
                         <div className="px-3 py-2 bg-white/5 rounded-xl border border-white/10">
                            <div className="text-[10px] font-[700] text-slate-500 mb-0.5">1주일</div>
                            <div className={cn(
                               "text-[13px] font-[900]",
                               portfolioStats.weeklyChangeRate >= 0 ? "text-red-400" : "text-blue-400"
                            )}>
                               {portfolioStats.weeklyChangeRate >= 0 ? "+" : ""}{portfolioStats.weeklyChangeRate}%
                            </div>
                         </div>
                         <div className="px-3 py-2 bg-white/5 rounded-xl border border-white/10">
                            <div className="text-[10px] font-[700] text-slate-500 mb-0.5">1개월</div>
                            <div className={cn(
                               "text-[13px] font-[900]",
                               portfolioStats.monthlyChangeRate >= 0 ? "text-red-400" : "text-blue-400"
                            )}>
                               {portfolioStats.monthlyChangeRate >= 0 ? "+" : ""}{portfolioStats.monthlyChangeRate}%
                            </div>
                         </div>
                      </div> */}
                           </div>
                        </section>

                        {/* 빠른 통계 카드 */}
                        {assets.length > 0 && (
                           <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                              <div className="bg-slate-50/50 rounded-2xl border border-slate-100 p-4">
                                 <div className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider mb-1">보유 종목</div>
                                 <div className="text-[24px] font-[900] text-slate-900">{assets.length}<span className="text-[14px] text-slate-400 ml-0.5">개</span></div>
                              </div>
                              <div className="bg-emerald-50/50 rounded-2xl border border-emerald-100 p-4">
                                 <div className="text-[10px] font-[800] text-emerald-600 uppercase tracking-wider mb-1">수익 종목</div>
                                 <div className="text-[24px] font-[900] text-emerald-600">{portfolioStats.profitableCount}<span className="text-[14px] text-emerald-400 ml-0.5">개</span></div>
                              </div>
                              <div className="bg-red-50/50 rounded-2xl border border-red-100 p-4">
                                 <div className="text-[10px] font-[800] text-red-500 uppercase tracking-wider mb-1">손실 종목</div>
                                 <div className="text-[24px] font-[900] text-red-500">{portfolioStats.losingCount}<span className="text-[14px] text-red-300 ml-0.5">개</span></div>
                              </div>
                              <div className="bg-blue-50/50 rounded-2xl border border-blue-100 p-4">
                                 <div className="text-[10px] font-[800] text-blue-600 uppercase tracking-wider mb-1">최고 수익</div>
                                 <div className="text-[24px] font-[900] text-blue-600">+{portfolioStats.bestPerformer?.rate || 0}<span className="text-[14px] text-blue-400 ml-0.5">%</span></div>
                              </div>
                           </div>
                        )}

                        {/* 보유 종목 섹션 */}
                        <HoldingsSection
                           assets={assets.map(a => ({
                              ...a,
                              currentPrice: currentPrices[a.positionId] ?? a.currentPrice ?? a.avgPrice
                           }))}
                           dailyChanges={dailyChanges}
                           exchangeRate={exchangeRate}
                        />
                     </motion.div>
                  )}

                  {activeTab === "ai" && (
                     <motion.div
                        key="ai"
                        initial={{ opacity: 0, scale: 0.98, y: 8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98, y: -8 }}
                        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                        className="space-y-6"
                     >
                        {/* 포트폴리오 건강도 점수 */}
                        <section className="bg-slate-900 rounded-[24px] p-6 sm:p-8 text-white relative overflow-hidden">
                           <div className="absolute inset-0 bg-gradient-to-br from-slate-800/50 to-transparent" />
                           <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-emerald-500/10 to-transparent rounded-full blur-3xl" />

                           <div className="relative z-10">
                              <div className="flex items-center gap-2 mb-6">
                                 <Sparkles size={16} className="text-emerald-400" />
                                 <span className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider">AI 포트폴리오 분석</span>
                              </div>

                              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
                                 <div>
                                    <div className="text-slate-400 text-[12px] font-[700] mb-2">포트폴리오 건강도</div>
                                    <div className="flex items-baseline gap-3">
                                       <span className="text-[56px] sm:text-[64px] font-[900] tracking-tighter leading-none">{AI_ANALYSIS.health.score}</span>
                                       <div className="flex flex-col gap-1">
                                          <span className="text-[24px] font-[900] text-emerald-400">{AI_ANALYSIS.health.grade}</span>
                                          <div className="flex items-center gap-1.5 text-emerald-400">
                                             <TrendingUp size={14} strokeWidth={3} />
                                             <span className="text-[12px] font-[800]">+{AI_ANALYSIS.health.score - AI_ANALYSIS.health.previousScore}점</span>
                                          </div>
                                       </div>
                                    </div>
                                    <div className="text-slate-500 text-[13px] font-[700] mt-3">{AI_ANALYSIS.health.summary}</div>
                                 </div>

                                 <div className="flex gap-4 sm:gap-6">
                                    {(AI_ANALYSIS.risk.volatility > 0) && (
                                       <div className="text-center">
                                          <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">변동성</div>
                                          <div className="text-[18px] font-[900] text-white">{AI_ANALYSIS.risk.volatility}%</div>
                                       </div>
                                    )}
                                    {(AI_ANALYSIS.risk.volatility > 0 && AI_ANALYSIS.risk.sharpeRatio > 0) && <div className="w-px h-10 bg-slate-700" />}
                                    {(AI_ANALYSIS.risk.sharpeRatio > 0) && (
                                       <div className="text-center">
                                          <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">샤프 비율</div>
                                          <div className="text-[18px] font-[900] text-white">{AI_ANALYSIS.risk.sharpeRatio}</div>
                                       </div>
                                    )}
                                    {(AI_ANALYSIS.risk.sharpeRatio > 0 && AI_ANALYSIS.risk.beta > 0) && <div className="w-px h-10 bg-slate-700" />}
                                    {(AI_ANALYSIS.risk.beta > 0) && (
                                       <div className="text-center">
                                          <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">베타</div>
                                          <div className="text-[18px] font-[900] text-white">{AI_ANALYSIS.risk.beta}</div>
                                       </div>
                                    )}
                                 </div>
                              </div>
                           </div>
                        </section>

                        {/* AI 투자 리포트 (New Section) */}
                        <section className="bg-white rounded-[24px] border border-slate-100 p-6 sm:p-8 shadow-sm">
                           <div className="flex items-center gap-2 mb-6">
                              <div className="bg-slate-900 w-8 h-8 rounded-lg flex items-center justify-center">
                                 <ClipboardList size={18} className="text-white" />
                              </div>
                              <div>
                                 <h3 className="text-[16px] font-[900] text-slate-900">AI 투자 리포트</h3>
                                 <p className="text-[12px] font-medium text-slate-500">Wall Street Senior Analyst Persona</p>
                              </div>
                           </div>

                           <div className="relative">
                              <div className="pl-4 border-l-2 border-slate-200 mb-6">
                                 <h4 className="text-[14px] font-[800] text-slate-800 mb-2">Executive Summary</h4>
                                 <p className="text-[14px] leading-relaxed text-slate-600 font-medium line-clamp-2">
                                    {AI_ANALYSIS.executiveSummary}
                                 </p>
                              </div>

                              <Button
                                 onClick={() => setIsReportOpen(true)}
                                 className="w-full sm:w-auto bg-slate-50 hover:bg-slate-100 text-slate-900 border border-slate-200 font-[800] text-[13px] h-10 px-5 rounded-xl transition-all"
                              >
                                 전문 보기
                                 <ChevronRight size={14} className="ml-1" />
                              </Button>
                           </div>
                        </section>

                        {/* 핵심 인사이트 */}
                        <section>
                           <div className="flex items-center gap-2 mb-4 px-1">
                              <Zap size={16} className="text-amber-500" />
                              <span className="text-[13px] font-[900] text-slate-900">핵심 인사이트</span>
                           </div>
                           <div className="space-y-3">
                              {AI_ANALYSIS.insights.map((insight, idx) => (
                                 <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className={cn(
                                       "p-4 rounded-2xl border transition-all hover:shadow-sm cursor-pointer group",
                                       insight.type === "warning" && "bg-amber-50/50 border-amber-100 hover:border-amber-200",
                                       insight.type === "positive" && "bg-emerald-50/50 border-emerald-100 hover:border-emerald-200",
                                       insight.type === "neutral" && "bg-slate-50/50 border-slate-100 hover:border-slate-200"
                                    )}
                                 >
                                    <div className="flex items-start gap-3">
                                       <div className={cn(
                                          "w-8 h-8 rounded-xl flex items-center justify-center shrink-0",
                                          insight.type === "warning" && "bg-amber-100 text-amber-600",
                                          insight.type === "positive" && "bg-emerald-100 text-emerald-600",
                                          insight.type === "neutral" && "bg-slate-100 text-slate-500"
                                       )}>
                                          {insight.type === "warning" && <AlertTriangle size={16} strokeWidth={2.5} />}
                                          {insight.type === "positive" && <TrendingUp size={16} strokeWidth={2.5} />}
                                          {insight.type === "neutral" && <BarChart3 size={16} strokeWidth={2.5} />}
                                       </div>
                                       <div className="flex-1 min-w-0">
                                          <div className="flex items-center justify-between gap-2">
                                             <span className="text-[14px] font-[900] text-slate-900">{insight.title}</span>
                                             <span className={cn(
                                                "text-[10px] font-[800] uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0",
                                                insight.impact === "high" && "bg-red-100 text-red-600",
                                                insight.impact === "medium" && "bg-amber-100 text-amber-600",
                                                insight.impact === "low" && "bg-slate-100 text-slate-500"
                                             )}>
                                                {insight.impact === "high" ? "중요" : insight.impact === "medium" ? "참고" : "정보"}
                                             </span>
                                          </div>
                                          <p className="text-[13px] font-[600] text-slate-500 mt-1 leading-relaxed">{insight.description}</p>
                                       </div>
                                    </div>
                                 </motion.div>
                              ))}
                           </div>
                        </section>

                        {/* 섹터 분포 & 리스크 */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                           {/* 섹터 분포 */}
                           <section className="bg-slate-50/50 rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <PieChart size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">섹터 분포</span>
                              </div>

                              {/* 프로그레스 바 */}
                              <div className="h-3 rounded-full overflow-hidden flex mb-4">
                                 {AI_ANALYSIS.sectors.map((sector, idx) => (
                                    <div
                                       key={idx}
                                       className="h-full first:rounded-l-full last:rounded-r-full"
                                       style={{ width: `${sector.percentage}%`, backgroundColor: sector.color }}
                                    />
                                 ))}
                              </div>

                              <div className="space-y-2">
                                 {AI_ANALYSIS.sectors.map((sector, idx) => (
                                    <div key={idx} className="flex items-center justify-between">
                                       <div className="flex items-center gap-2">
                                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: sector.color }} />
                                          <span className="text-[12px] font-[700] text-slate-600">{sector.name}</span>
                                       </div>
                                       <span className="text-[12px] font-[900] text-slate-900">{sector.percentage}%</span>
                                    </div>
                                 ))}
                              </div>
                           </section>

                           {/* 리스크 지표 */}
                           <section className="bg-slate-50/50 rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <Shield size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">리스크 분석</span>
                              </div>

                              <div className="space-y-4">
                                 <div>
                                    <div className="flex items-center justify-between mb-1.5">
                                       <span className="text-[11px] font-[700] text-slate-500">리스크 레벨</span>
                                       <span className="text-[12px] font-[900] text-amber-600">{AI_ANALYSIS.risk.level}</span>
                                    </div>
                                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                       <div className="h-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-400 rounded-full" style={{ width: '65%' }} />
                                    </div>
                                 </div>

                                 <div className="grid grid-cols-2 gap-3 pt-2">
                                    <div className="bg-white rounded-xl p-3 border border-slate-100">
                                       <div className="text-[10px] font-[700] text-slate-400 mb-0.5">최대 낙폭</div>
                                       <div className="text-[15px] font-[900] text-red-500">{AI_ANALYSIS.risk.maxDrawdown}%</div>
                                    </div>
                                    <div className="bg-white rounded-xl p-3 border border-slate-100">
                                       <div className="text-[10px] font-[700] text-slate-400 mb-0.5">시장 민감도</div>
                                       <div className="text-[15px] font-[900] text-slate-900">β {AI_ANALYSIS.risk.beta}</div>
                                    </div>
                                 </div>
                              </div>
                           </section>
                        </div>

                        {/* AI 추천 액션 */}
                        <section>
                           <div className="flex items-center gap-2 mb-4 px-1">
                              <Target size={16} className="text-blue-500" />
                              <span className="text-[13px] font-[900] text-slate-900">AI 추천</span>
                           </div>
                           <div className="space-y-3">
                              {AI_ANALYSIS.recommendations.map((rec, idx) => (
                                 <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.2 + idx * 0.1 }}
                                    className="bg-white rounded-2xl border border-slate-100 p-4 hover:border-slate-200 hover:shadow-sm transition-all cursor-pointer group"
                                 >
                                    <div className="flex items-start justify-between gap-4">
                                       <div className="flex items-start gap-3">
                                          <div className={cn(
                                             "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
                                             rec.priority === "high" && "bg-blue-100 text-blue-600",
                                             rec.priority === "medium" && "bg-slate-100 text-slate-600",
                                             rec.priority === "low" && "bg-slate-50 text-slate-400"
                                          )}>
                                             {rec.action === "rebalance" && <RefreshCw size={18} strokeWidth={2.5} />}
                                             {rec.action === "add" && <Plus size={18} strokeWidth={2.5} />}
                                             {rec.action === "hold" && <Shield size={18} strokeWidth={2.5} />}
                                          </div>
                                          <div>
                                             <div className="text-[14px] font-[900] text-slate-900 mb-0.5">{rec.title}</div>
                                             <p className="text-[13px] font-[600] text-slate-500 leading-relaxed">{rec.description}</p>
                                          </div>
                                       </div>
                                       <ArrowRight size={16} className="text-slate-300 group-hover:text-slate-500 group-hover:translate-x-0.5 transition-all shrink-0 mt-1" />
                                    </div>
                                 </motion.div>
                              ))}
                           </div>
                        </section>

                        {/* 시장 컨텍스트 */}
                        <section className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-[20px] border border-slate-100 p-5">
                           <div className="flex items-center gap-2 mb-4">
                              <Brain size={14} className="text-slate-400" />
                              <span className="text-[12px] font-[900] text-slate-900">시장 환경</span>
                              <span className={cn(
                                 "text-[10px] font-[800] uppercase tracking-wider px-2 py-0.5 rounded-full ml-auto",
                                 AI_ANALYSIS.marketContext.sentiment === "positive" && "bg-emerald-100 text-emerald-600",
                                 AI_ANALYSIS.marketContext.sentiment === "neutral" && "bg-slate-200 text-slate-600",
                                 AI_ANALYSIS.marketContext.sentiment === "negative" && "bg-red-100 text-red-600"
                              )}>
                                 {AI_ANALYSIS.marketContext.sentiment === "positive" ? "긍정적" : AI_ANALYSIS.marketContext.sentiment === "neutral" ? "중립" : "부정적"}
                              </span>
                           </div>
                           <div className="flex flex-wrap gap-2">
                              {AI_ANALYSIS.marketContext.keyFactors.map((factor, idx) => (
                                 <span key={idx} className="px-3 py-1.5 bg-white rounded-full text-[12px] font-[700] text-slate-600 border border-slate-100">
                                    {factor}
                                 </span>
                              ))}
                           </div>
                        </section>

                     </motion.div>
                  )}

                  <AnimatePresence>
                     {isReportOpen && (
                        <ReportModal
                           isOpen={isReportOpen}
                           onClose={() => setIsReportOpen(false)}
                           title="AI Investment Research Report"
                           content={AI_ANALYSIS.fullReport}
                        />
                     )}
                  </AnimatePresence>

                  {activeTab === "stats" && (
                     <motion.div
                        key="stats"
                        initial={{ opacity: 0, scale: 0.98, y: 8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98, y: -8 }}
                        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                        className="space-y-6"
                     >
                        {/* 포트폴리오 요약 히어로 */}
                        <section className="bg-slate-900 rounded-[24px] p-6 sm:p-8 text-white relative overflow-hidden">
                           <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 to-transparent" />
                           <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-blue-500/10 to-transparent rounded-full blur-3xl" />

                           <div className="relative z-10">
                              <div className="flex items-center gap-2 mb-6">
                                 <BarChart3 size={16} className="text-violet-400" />
                                 <span className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider">포트폴리오 구성</span>
                              </div>

                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">보유 종목</div>
                                    <div className="text-[28px] sm:text-[32px] font-[900] text-white tracking-tight">
                                       {STATS_DATA.heatmap.length}<span className="text-[16px] text-slate-500 ml-0.5">개</span>
                                    </div>
                                 </div>
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">섹터 분산</div>
                                    <div className="text-[28px] sm:text-[32px] font-[900] text-white tracking-tight">
                                       {STATS_DATA.sectors.length}<span className="text-[16px] text-slate-500 ml-0.5">개</span>
                                    </div>
                                 </div>
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">평균 PER</div>
                                    <div className="text-[28px] sm:text-[32px] font-[900] text-violet-400 tracking-tight">
                                       {STATS_DATA.valuation.avgPER}
                                    </div>
                                 </div>
                                 <div>
                                    <div className="text-[10px] font-[800] text-slate-500 uppercase tracking-wider mb-1">배당 수익률</div>
                                    <div className="text-[28px] sm:text-[32px] font-[900] text-emerald-400 tracking-tight">
                                       {STATS_DATA.dividends.yieldRate}%
                                    </div>
                                 </div>
                              </div>
                           </div>
                        </section>

                        {/* 종목 트리맵 */}
                        <section className="bg-white rounded-[20px] border border-slate-100 p-5">
                           <div className="flex items-center justify-between mb-5">
                              <div className="flex items-center gap-2">
                                 <PieChart size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">종목 트리맵</span>
                                 <span className="text-[10px] font-[600] text-slate-400">(평가금액 비례)</span>
                              </div>
                              <div className="flex items-center gap-3 text-[10px] font-[700]">
                                 <div className="flex items-center gap-1">
                                    <div className="w-3 h-3 rounded bg-blue-500" />
                                    <span className="text-slate-400">손실</span>
                                 </div>
                                 <div className="flex items-center gap-1">
                                    <div className="w-3 h-3 rounded bg-slate-200" />
                                    <span className="text-slate-400">보합</span>
                                 </div>
                                 <div className="flex items-center gap-1">
                                    <div className="w-3 h-3 rounded bg-red-500" />
                                    <span className="text-slate-400">수익</span>
                                 </div>
                              </div>
                           </div>

                           <div className="w-full h-[400px] relative">
                              <AnimatePresence mode="wait">
                                 {isTreemapLoading ? (
                                    <motion.div
                                       key="loading"
                                       initial={{ opacity: 0 }}
                                       animate={{ opacity: 1 }}
                                       exit={{ opacity: 0, scale: 0.95 }}
                                       transition={{ duration: 0.3 }}
                                       className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50/50 rounded-2xl"
                                    >
                                       <Loader2 size={32} className="text-slate-400 animate-spin mb-3" />
                                       <span className="text-[13px] font-[700] text-slate-400">데이터 분석 중...</span>
                                    </motion.div>
                                 ) : (
                                    <motion.div
                                       key="treemap"
                                       initial={{ opacity: 0, scale: 0.95 }}
                                       animate={{ opacity: 1, scale: 1 }}
                                       transition={{
                                          duration: 0.5,
                                          ease: [0.16, 1, 0.3, 1]
                                       }}
                                       className="w-full h-full"
                                    >
                                       <ResponsiveContainer width="100%" height="100%">
                                          <Treemap
                                             data={STATS_DATA.heatmap.map((stock) => ({
                                                name: stock.name,
                                                ticker: stock.ticker,
                                                size: stock.weight,
                                                return: stock.return
                                             }))}
                                             dataKey="size"
                                             stroke="#fff"
                                             isAnimationActive={true}
                                             animationDuration={600}
                                             animationBegin={0}
                                             content={({ x, y, width, height, name, ticker, return: ret }: any) => {
                                                // 수익률에 따른 색상 계산
                                                const getColor = (ret: number) => {
                                                   if (ret > 30) return "#dc2626"; // red-600
                                                   if (ret > 15) return "#ef4444"; // red-500
                                                   if (ret > 5) return "#f87171"; // red-400
                                                   if (ret > 0) return "#fecaca"; // red-200
                                                   if (ret === 0) return "#f1f5f9"; // slate-100
                                                   if (ret > -5) return "#bfdbfe"; // blue-200
                                                   if (ret > -15) return "#60a5fa"; // blue-400
                                                   return "#2563eb"; // blue-600
                                                };

                                                // 텍스트 색상 (배경에 따라)
                                                const getTextColor = (ret: number) => {
                                                   if (ret > 0 && ret <= 5) return "#991b1b"; // red-800
                                                   if (ret === 0) return "#475569"; // slate-600
                                                   if (ret > -5 && ret < 0) return "#1e3a8a"; // blue-900
                                                   return "#ffffff";
                                                };

                                                const bgColor = getColor(ret);
                                                const textColor = getTextColor(ret);
                                                const fontSize = Math.min(width, height) / 8;
                                                const shouldShowTicker = width < 80 || name.length > 5;
                                                const displayName = shouldShowTicker ? ticker : name;

                                                return (
                                                   <g>
                                                      <rect
                                                         x={x}
                                                         y={y}
                                                         width={width}
                                                         height={height}
                                                         fill={bgColor}
                                                         className="cursor-pointer hover:opacity-90 transition-opacity"
                                                         rx={8}
                                                      />
                                                      {width > 40 && height > 40 && (
                                                         <>
                                                            <text
                                                               x={x + width / 2}
                                                               y={y + height / 2 - fontSize / 3}
                                                               textAnchor="middle"
                                                               fill={textColor}
                                                               fontSize={Math.max(fontSize, 10)}
                                                               fontWeight="900"
                                                            >
                                                               {displayName}
                                                            </text>
                                                            <text
                                                               x={x + width / 2}
                                                               y={y + height / 2 + fontSize}
                                                               textAnchor="middle"
                                                               fill={textColor}
                                                               fontSize={Math.max(fontSize * 0.8, 9)}
                                                               fontWeight="800"
                                                               opacity="0.8"
                                                            >
                                                               {ret > 0 ? "+" : ""}{ret}%
                                                            </text>
                                                         </>
                                                      )}
                                                   </g>
                                                );
                                             }}
                                          />
                                       </ResponsiveContainer>
                                    </motion.div>
                                 )}
                              </AnimatePresence>
                           </div>
                        </section>

                        {/* 섹터별 비중 */}
                        <section className="bg-slate-50/50 rounded-[20px] border border-slate-100 p-5">
                           <div className="flex items-center gap-2 mb-4">
                              <Target size={14} className="text-slate-400" />
                              <span className="text-[12px] font-[900] text-slate-900">섹터별 비중</span>
                           </div>

                           <div className="h-4 rounded-full overflow-hidden flex mb-5">
                              {STATS_DATA.sectors.map((sector, idx) => (
                                 <motion.div
                                    key={idx}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${sector.value}%` }}
                                    transition={{ delay: idx * 0.1, duration: 0.5 }}
                                    className="h-full first:rounded-l-full last:rounded-r-full"
                                    style={{ backgroundColor: sector.color }}
                                 />
                              ))}
                           </div>

                           <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                              {STATS_DATA.sectors.map((sector, idx) => (
                                 <div key={idx} className="bg-white rounded-xl p-3 border border-slate-100">
                                    <div className="flex items-center justify-between mb-2">
                                       <div className="flex items-center gap-2">
                                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: sector.color }} />
                                          <span className="text-[12px] font-[800] text-slate-900">{sector.name}</span>
                                       </div>
                                       <span className="text-[13px] font-[900]" style={{ color: sector.color }}>{sector.value}%</span>
                                    </div>
                                    {sector.stocks.length > 0 && (
                                       <div className="text-[10px] font-[600] text-slate-400 truncate">
                                          {sector.stocks.join(", ")}
                                       </div>
                                    )}
                                 </div>
                              ))}
                           </div>
                        </section>

                        {/* 시가총액 & 국가별 */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                           {/* 시가총액별 */}
                           <section className="bg-white rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <BarChart3 size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">시가총액 분포</span>
                              </div>

                              <div className="space-y-3">
                                 {STATS_DATA.marketCap.map((cap, idx) => (
                                    <div key={idx}>
                                       <div className="flex items-center justify-between mb-1.5">
                                          <div className="flex items-center gap-2">
                                             <span className="text-[12px] font-[800] text-slate-900">{cap.name}</span>
                                             <span className="text-[10px] font-[600] text-slate-400">{cap.range}</span>
                                          </div>
                                          <span className="text-[12px] font-[900]" style={{ color: cap.color }}>{cap.value}%</span>
                                       </div>
                                       <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                                          <motion.div
                                             initial={{ width: 0 }}
                                             animate={{ width: `${cap.value}%` }}
                                             transition={{ delay: idx * 0.15, duration: 0.5 }}
                                             className="h-full rounded-full"
                                             style={{ backgroundColor: cap.color }}
                                          />
                                       </div>
                                    </div>
                                 ))}
                              </div>
                           </section>

                           {/* 국가별 */}
                           <section className="bg-white rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <Globe size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">국가별 분포</span>
                              </div>

                              <div className="space-y-3">
                                 {STATS_DATA.countries.map((country, idx) => (
                                    <div key={idx}>
                                       <div className="flex items-center justify-between mb-1.5">
                                          <div className="flex items-center gap-2">
                                             <span className="text-lg">{country.flag}</span>
                                             <span className="text-[12px] font-[800] text-slate-900">{country.name}</span>
                                          </div>
                                          <span className="text-[12px] font-[900] text-slate-900">{country.value}%</span>
                                       </div>
                                       <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                                          <motion.div
                                             initial={{ width: 0 }}
                                             animate={{ width: `${country.value}%` }}
                                             transition={{ delay: idx * 0.15, duration: 0.5 }}
                                             className="h-full bg-slate-900 rounded-full"
                                          />
                                       </div>
                                    </div>
                                 ))}
                              </div>
                           </section>
                        </div>

                        {/* 포트폴리오 집중도 */}
                        <section className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-[20px] border border-amber-100 p-5">
                           <div className="flex items-center gap-2 mb-4">
                              <AlertTriangle size={14} className="text-amber-600" />
                              <span className="text-[12px] font-[900] text-amber-900">포트폴리오 집중도</span>
                           </div>

                           <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <div>
                                 <div className="text-[10px] font-[700] text-amber-700 mb-1">상위 1종목</div>
                                 <div className="text-[20px] font-[900] text-amber-900">{STATS_DATA.concentration.top1}%</div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-amber-700 mb-1">상위 3종목</div>
                                 <div className="text-[20px] font-[900] text-amber-900">{STATS_DATA.concentration.top3}%</div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-amber-700 mb-1">상위 5종목</div>
                                 <div className="text-[20px] font-[900] text-amber-900">{STATS_DATA.concentration.top5}%</div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-amber-700 mb-1">HHI 지수</div>
                                 <div className="flex items-baseline gap-1">
                                    <span className="text-[20px] font-[900] text-amber-900">{STATS_DATA.concentration.hhi}</span>
                                    <span className="text-[10px] font-[700] text-amber-600">중간</span>
                                 </div>
                              </div>
                           </div>

                           <div className="mt-4 pt-3 border-t border-amber-200/50">
                              <p className="text-[11px] font-[600] text-amber-700">
                                 상위 5개 종목이 전체의 {STATS_DATA.concentration.top5}%를 차지해요. 분산 투자를 위해 비중 조절을 고려해보세요.
                              </p>
                           </div>
                        </section>

                        {/* 통화별 & 밸류에이션 */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                           {/* 통화별 분포 */}
                           <section className="bg-white rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <DollarSign size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">통화별 분포</span>
                              </div>

                              <div className="space-y-3">
                                 {STATS_DATA.currencies.map((currency, idx) => (
                                    <div key={idx} className="flex items-center gap-3">
                                       <div className="w-12 h-12 rounded-xl flex items-center justify-center font-[900] text-[14px]"
                                          style={{ backgroundColor: `${currency.color}15`, color: currency.color }}>
                                          {currency.name}
                                       </div>
                                       <div className="flex-1">
                                          <div className="flex items-center justify-between mb-1">
                                             <span className="text-[12px] font-[700] text-slate-600">{currency.label}</span>
                                             <span className="text-[13px] font-[900]" style={{ color: currency.color }}>{currency.value}%</span>
                                          </div>
                                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                             <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${currency.value}%` }}
                                                transition={{ delay: idx * 0.1, duration: 0.5 }}
                                                className="h-full rounded-full"
                                                style={{ backgroundColor: currency.color }}
                                             />
                                          </div>
                                       </div>
                                    </div>
                                 ))}
                              </div>
                           </section>

                           {/* 밸류에이션 */}
                           <section className="bg-white rounded-[20px] border border-slate-100 p-5">
                              <div className="flex items-center gap-2 mb-4">
                                 <Percent size={14} className="text-slate-400" />
                                 <span className="text-[12px] font-[900] text-slate-900">밸류에이션 지표</span>
                              </div>

                              <div className="space-y-4">
                                 <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                                    <div>
                                       <div className="text-[10px] font-[700] text-slate-500">평균 PER</div>
                                       <div className="text-[11px] font-[600] text-slate-400">주가수익비율</div>
                                    </div>
                                    <div className="text-[22px] font-[900] text-slate-900">{STATS_DATA.valuation.avgPER}</div>
                                 </div>
                                 <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                                    <div>
                                       <div className="text-[10px] font-[700] text-slate-500">평균 PBR</div>
                                       <div className="text-[11px] font-[600] text-slate-400">주가순자산비율</div>
                                    </div>
                                    <div className="text-[22px] font-[900] text-slate-900">{STATS_DATA.valuation.avgPBR}</div>
                                 </div>
                                 <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl">
                                    <div>
                                       <div className="text-[10px] font-[700] text-emerald-600">배당 수익률</div>
                                       <div className="text-[11px] font-[600] text-emerald-500">Dividend Yield</div>
                                    </div>
                                    <div className="text-[22px] font-[900] text-emerald-600">{STATS_DATA.valuation.avgDividendYield}%</div>
                                 </div>
                              </div>
                           </section>
                        </div>

                        {/* 배당 정보 */}
                        <section className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 rounded-[20px] border border-emerald-100 p-5">
                           <div className="flex items-center gap-2 mb-4">
                              <Wallet size={14} className="text-emerald-600" />
                              <span className="text-[12px] font-[900] text-emerald-900">배당 현황</span>
                           </div>

                           <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <div>
                                 <div className="text-[10px] font-[700] text-emerald-600 mb-1">예상 연간 배당</div>
                                 <div className="text-[18px] font-[900] text-emerald-900">{STATS_DATA.dividends.expectedAnnual.toLocaleString()}원</div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-emerald-600 mb-1">포트폴리오 배당률</div>
                                 <div className="text-[18px] font-[900] text-emerald-900">{STATS_DATA.dividends.yieldRate}%</div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-emerald-600 mb-1">배당주 비중</div>
                                 <div className="text-[18px] font-[900] text-emerald-900">
                                    {STATS_DATA.dividends.payingStocks}/{STATS_DATA.dividends.totalStocks}
                                    <span className="text-[12px] text-emerald-600 ml-1">종목</span>
                                 </div>
                              </div>
                              <div>
                                 <div className="text-[10px] font-[700] text-emerald-600 mb-1">월 환산 배당</div>
                                 <div className="text-[18px] font-[900] text-emerald-900">{Math.round(STATS_DATA.dividends.expectedAnnual / 12).toLocaleString()}원</div>
                              </div>
                           </div>
                        </section>

                        {/* 데이터 기준일 */}
                        <div className="text-center py-4">
                           <span className="text-[11px] font-[700] text-slate-300">현재 포트폴리오 기준 · 실시간 반영</span>
                        </div>
                     </motion.div>
                  )}
               </AnimatePresence>
            </main>
         </div>
      </div>
   );
}
