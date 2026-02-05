"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, Plus, ChevronDown, ArrowUpDown, Edit2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { toKRW, convertCurrency, formatCurrency, type Currency } from "@/lib/utils/currency";

interface Asset {
  positionId: string;
  name: string;
  ticker: string;
  quantity: number;
  avgPrice: number;
  currency: string;
  national: string;
  market: string;
  currentPrice?: number;
}

interface HoldingsSectionProps {
  assets: Asset[];
  dailyChanges: Record<string, number>;
  exchangeRate: number;
}

export function HoldingsSection({ assets, dailyChanges, exchangeRate }: HoldingsSectionProps) {
  const router = useRouter();
  const [displayCurrency, setDisplayCurrency] = useState<Currency>("KRW"); // 표시 화폐
  const [displayMode, setDisplayMode] = useState<"current" | "valuation">("current"); // 현재가 vs 평가금
  const [sortBy, setSortBy] = useState<"value" | "rate">("value"); // 금액순 vs 수익률순
  const [sortMenuOpen, setSortMenuOpen] = useState(false);

  // 총 평가금액 계산 (현재가 기준, KRW로 통일)
  const totalValue = assets.reduce((acc, a) => {
    const currentPrice = a.currentPrice ?? a.avgPrice;
    const valueInOriginalCurrency = currentPrice * a.quantity;
    const valueInKRW = toKRW(valueInOriginalCurrency, a.currency, exchangeRate);
    return acc + valueInKRW;
  }, 0);

  // 정렬된 자산 목록
  const sortedAssets = [...assets].sort((a, b) => {
    if (sortBy === "value") {
      return (b.avgPrice * b.quantity) - (a.avgPrice * a.quantity);
    } else {
      const getRate = (asset: typeof a) => mockAssetReturns[asset.positionId]?.rate ?? 12.4;
      return getRate(b) - getRate(a);
    }
  });

  // 종목 클릭 핸들러
  const handleAssetClick = (asset: Asset) => {
    // Check if required fields are present
    if (!asset.national || !asset.market) {
      console.warn("Asset missing national or market data:", asset);
      return;
    }
    const national = asset.national;
    const exchange = asset.market;
    const symbol = asset.ticker;
    router.push(`/assets?national=${encodeURIComponent(national)}&exchange=${encodeURIComponent(exchange)}&symbol=${encodeURIComponent(symbol)}`);
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-4 px-1">
        {/* 왼쪽: 제목 + 정렬 */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-slate-400" />
            <span className="text-[13px] font-[900] text-slate-900">보유 종목</span>
            {assets.length > 0 && (
              <span className="text-[12px] font-[800] text-slate-400">{assets.length}개</span>
            )}
          </div>

          {/* 정렬 드롭다운 */}
          {assets.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setSortMenuOpen(!sortMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-100 transition-all"
              >
                <ArrowUpDown size={12} className="text-slate-400" />
                <span className="text-[11px] font-[900] text-slate-600">
                  {sortBy === "value" ? "금액순" : "수익률순"}
                </span>
                <ChevronDown size={12} className={cn(
                  "text-slate-400 transition-transform",
                  sortMenuOpen && "rotate-180"
                )} />
              </button>

              {/* 드롭다운 메뉴 */}
              {sortMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setSortMenuOpen(false)}
                  />
                  <div className="absolute top-full left-0 mt-1 w-32 bg-white rounded-xl border border-slate-100 shadow-lg z-20 overflow-hidden">
                    <button
                      onClick={() => {
                        setSortBy("value");
                        setSortMenuOpen(false);
                      }}
                      className={cn(
                        "w-full px-3 py-2 text-left text-[12px] font-[800] transition-colors",
                        sortBy === "value"
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      금액순
                    </button>
                    <button
                      onClick={() => {
                        setSortBy("rate");
                        setSortMenuOpen(false);
                      }}
                      className={cn(
                        "w-full px-3 py-2 text-left text-[12px] font-[800] transition-colors",
                        sortBy === "rate"
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      수익률순
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* 오른쪽: 화폐 토글 + 현재가/평가금 토글 */}
        {assets.length > 0 && (
          <div className="flex items-center gap-2">
            {/* 화폐 토글 */}
            <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-100/50">
              <button
                onClick={() => setDisplayCurrency("KRW")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-[900] rounded-lg transition-all",
                  displayCurrency === "KRW"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                )}
              >
                ₩
              </button>
              <button
                onClick={() => setDisplayCurrency("USD")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-[900] rounded-lg transition-all",
                  displayCurrency === "USD"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                )}
              >
                $
              </button>
            </div>

            {/* 현재가/평가금 토글 */}
            <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-100/50">
              <button
                onClick={() => setDisplayMode("current")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-[900] rounded-lg transition-all",
                  displayMode === "current"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                )}
              >
                현재가
              </button>
              <button
                onClick={() => setDisplayMode("valuation")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-[900] rounded-lg transition-all",
                  displayMode === "valuation"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                )}
              >
                평가금
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 종목 리스트 */}
      {assets.length === 0 ? (
        <div className="text-center py-20 px-6 bg-slate-50/30 rounded-2xl border border-slate-100 border-dashed">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <BarChart3 size={28} strokeWidth={1.5} className="text-slate-300" />
          </div>
          <div className="text-slate-400 font-[900] text-[15px] mb-1">보유한 자산이 없어요</div>
          <div className="text-slate-400 text-[13px] font-[600] mb-6">지금 바로 첫 자산을 추가해보세요</div>
          <Link href="/onboarding/add/manual?from=dashboard">
            <button className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-xl text-[13px] font-[800] hover:bg-slate-800 transition-all">
              <Plus size={16} strokeWidth={3} />
              종목 추가하기
            </button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedAssets.map((asset, idx) => {
            // 현재가는 이미 asset에 포함되어 전달됨
            const currentPrice = asset.currentPrice ?? asset.avgPrice;
            const assetValue = currentPrice * asset.quantity; // 평가금 (원화폐)
            const purchaseValue = asset.avgPrice * asset.quantity; // 매입금 (원화폐)
            const profit = assetValue - purchaseValue; // 수익 (원화폐)
            const profitRate = ((profit / purchaseValue) * 100) || 0;

            // 표시할 통화 결정: 국내자산(KRW)은 항상 원화로 표시, 해외자산(USD)만 변환
            const effectiveDisplayCurrency = asset.currency === 'KRW' ? 'KRW' : displayCurrency;

            // KRW로 변환하여 비중 계산
            const assetValueInKRW = toKRW(assetValue, asset.currency, exchangeRate);
            const dailyChange = dailyChanges[asset.positionId] ?? 0;
            const weight = totalValue > 0 ? (assetValueInKRW / totalValue * 100) : 0;

            return (
              <motion.div
                key={asset.positionId}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => handleAssetClick(asset)}
                className="bg-white rounded-2xl border border-slate-100 p-4 hover:border-slate-200 hover:shadow-sm transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between gap-4">
                  {/* 왼쪽: 종목 정보 */}
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-100 to-slate-50 flex items-center justify-center font-[900] text-slate-400 text-sm border border-slate-100 group-hover:scale-105 transition-transform duration-300 shrink-0">
                      {asset.ticker.slice(0, 2)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-[900] text-[15px] text-slate-900 tracking-tight truncate">
                          {asset.name}
                        </span>
                        <span className="text-[10px] font-[800] text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded shrink-0">
                          {asset.ticker}
                        </span>
                        {/* 수정 버튼 (hover시 표시) */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/assets/edit?positionId=${asset.positionId}`);
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity w-6 h-6 rounded-md hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
                          title="수정"
                        >
                          <Edit2 size={14} />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[12px] font-[700] text-slate-400">
                          {asset.quantity.toLocaleString()}주
                        </span>
                        <span className="text-slate-200">·</span>
                        <span className="text-[12px] font-[700] text-slate-400">
                          평단 {formatCurrency(
                            convertCurrency(asset.avgPrice, asset.currency, effectiveDisplayCurrency, exchangeRate),
                            effectiveDisplayCurrency
                          )}
                        </span>
                        <span className="text-slate-200">·</span>
                        <span className="text-[12px] font-[700] text-slate-300">
                          비중 {weight.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 오른쪽: 가격 표시 (현재가 or 평가금) */}
                  <div className="text-right shrink-0">
                    {displayMode === "current" ? (
                      <>
                        {/* 현재가 표시 */}
                        <div className="font-[900] text-[16px] text-slate-900 tracking-tight">
                          {formatCurrency(
                            convertCurrency(currentPrice, asset.currency, effectiveDisplayCurrency, exchangeRate),
                            effectiveDisplayCurrency
                          )}
                        </div>
                        <div className="text-[11px] font-[700] text-slate-400 mt-0.5">
                          현재가
                        </div>
                      </>
                    ) : (
                      <>
                        {/* 평가금 표시 */}
                        <div className="font-[900] text-[16px] text-slate-900 tracking-tight">
                          {formatCurrency(
                            convertCurrency(assetValue, asset.currency, effectiveDisplayCurrency, exchangeRate),
                            effectiveDisplayCurrency
                          )}
                        </div>
                        <div className="flex items-center justify-end gap-1.5 mt-0.5">
                          <span className={cn(
                            "text-[13px] font-[900]",
                            profitRate >= 0 ? "text-red-500" : "text-blue-500"
                          )}>
                            {profitRate >= 0 ? "+" : ""}{profitRate.toFixed(2)}%
                          </span>
                          <span className={cn(
                            "text-[11px] font-[700]",
                            profitRate >= 0 ? "text-red-400" : "text-blue-400"
                          )}>
                            ({profitRate >= 0 ? "+" : ""}{formatCurrency(
                              convertCurrency(profit, asset.currency, effectiveDisplayCurrency, exchangeRate),
                              effectiveDisplayCurrency
                            )})
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* 일간 변화 태그 */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-50">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-[700] text-slate-400">오늘</span>
                    <span className={cn(
                      "text-[11px] font-[800] px-1.5 py-0.5 rounded",
                      dailyChange >= 0
                        ? "bg-red-50 text-red-500"
                        : "bg-blue-50 text-blue-500"
                    )}>
                      {dailyChange >= 0 ? "+" : ""}{dailyChange.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-[10px] font-[700] text-slate-300 group-hover:text-slate-500 transition-colors">
                    상세보기 →
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 종목 추가 CTA */}
      {assets.length > 0 && (
        <Link href="/onboarding/add/manual?from=dashboard" className="block mt-6">
          <div className="w-full py-4 rounded-2xl bg-slate-50 border border-slate-100 border-dashed flex items-center justify-center gap-2 hover:bg-slate-100 hover:border-slate-200 transition-all text-slate-400 font-[800] text-[13px] group">
            <Plus size={16} strokeWidth={3} className="group-hover:rotate-90 transition-transform duration-300" />
            <span>종목 추가하기</span>
          </div>
        </Link>
      )}
    </section>
  );
}
