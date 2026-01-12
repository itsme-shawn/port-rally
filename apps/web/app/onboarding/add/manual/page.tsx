"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { usePortfolioStore } from "@/lib/store";
import { ArrowLeft, Plus, Trash2, TrendingUp, Calendar, Building2, Wallet, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

type AssetRow = {
  id: string;
  ticker: string;
  name: string;
  price: string;
  qty: string;
  currency: "KRW" | "USD";
  purchaseDate?: string;
  broker?: string;
  accountName?: string;
};

export default function ManualAddPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromDashboard = searchParams.get("from") === "dashboard";
  const addAsset = usePortfolioStore((state) => state.addAsset);

  // Local state for form
  const [rows, setRows] = useState<AssetRow[]>([
    { id: "1", ticker: "", name: "", price: "", qty: "", currency: "KRW" }
  ]);

  const [expandedOptional, setExpandedOptional] = useState<Record<string, boolean>>({});

  const handleAddRow = () => {
    setRows([...rows, {
      id: Date.now().toString(),
      ticker: "",
      name: "",
      price: "",
      qty: "",
      currency: "KRW"
    }]);
  };

  const handleRemoveRow = (id: string) => {
    if (rows.length === 1) return;
    setRows(rows.filter(r => r.id !== id));
    const newExpanded = { ...expandedOptional };
    delete newExpanded[id];
    setExpandedOptional(newExpanded);
  };

  const updateRow = (id: string, field: keyof AssetRow, value: string) => {
    setRows(rows.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const toggleOptional = (id: string) => {
    setExpandedOptional(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSubmit = () => {
    // Save to store
    rows.forEach(r => {
      if (r.ticker && r.qty) {
        addAsset({
          id: r.id,
          ticker: r.ticker.toUpperCase(),
          name: r.name || r.ticker, // Fallback name
          avgPrice: Number(r.price) || 0,
          quantity: Number(r.qty) || 0,
          currency: r.currency
        });
      }
    });
    // dashboard에서 왔으면 survey 건너뛰고 바로 dashboard로
    router.push(fromDashboard ? "/dashboard" : "/onboarding/survey");
  };

  const isValidRow = (row: AssetRow) => {
    return row.ticker && row.qty && row.price;
  };

  const canSubmit = rows.some(isValidRow);

  return (
    <div className="min-h-screen bg-white">
      {/* 헤더 */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="container-custom">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft size={20} strokeWidth={2.5} />
              <span className="text-[14px] font-[800]">뒤로</span>
            </button>
            <h1 className="text-[16px] font-[900] text-slate-900">자산 입력</h1>
            <div className="w-16" />
          </div>
        </div>
      </header>

      {/* 히어로 섹션 */}
      <section className="bg-slate-900 text-white py-8 px-4">
        <div className="container-custom">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-emerald-400" />
            <span className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider">포트폴리오 구성</span>
          </div>
          <h2 className="text-[28px] font-[900] tracking-tight mb-2">보유 자산을 입력해주세요</h2>
          <p className="text-[14px] font-[600] text-slate-400">종목별로 정보를 입력하면 포트폴리오 분석을 시작할 수 있어요</p>
        </div>
      </section>

      {/* 메인 콘텐츠 */}
      <main className="container-custom py-6 pb-32">
        <div className="space-y-4">
          {rows.map((row, index) => (
            <motion.div
              key={row.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-[20px] border border-slate-100 p-5 relative hover:border-slate-200 transition-all"
            >
              {/* 삭제 버튼 */}
              {rows.length > 1 && (
                <button
                  onClick={() => handleRemoveRow(row.id)}
                  className="absolute top-4 right-4 w-8 h-8 rounded-full bg-slate-50 hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all flex items-center justify-center"
                >
                  <Trash2 size={16} strokeWidth={2.5} />
                </button>
              )}

              {/* 종목 번호 */}
              <div className="flex items-center gap-2 mb-5">
                <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center">
                  <span className="text-[13px] font-[900]">{index + 1}</span>
                </div>
                <span className="text-[13px] font-[800] text-slate-400">종목</span>
              </div>

              {/* 필수 입력 필드 */}
              <div className="space-y-4">
                {/* 종목명/티커 */}
                <div>
                  <label className="text-[11px] font-[800] text-slate-500 uppercase tracking-wider block mb-2">
                    종목명 / 티커 *
                  </label>
                  <Input
                    placeholder="예: 삼성전자, AAPL"
                    value={row.ticker}
                    onChange={(e) => updateRow(row.id, "ticker", e.target.value)}
                    className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[15px] font-[700] h-12 rounded-xl"
                  />
                </div>

                {/* 평단가 & 수량 */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-[800] text-slate-500 uppercase tracking-wider block mb-2">
                      평단가 *
                    </label>
                    <Input
                      type="number"
                      placeholder="0"
                      value={row.price}
                      onChange={(e) => updateRow(row.id, "price", e.target.value)}
                      className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[15px] font-[700] h-12 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-[800] text-slate-500 uppercase tracking-wider block mb-2">
                      보유 수량 *
                    </label>
                    <Input
                      type="number"
                      placeholder="0"
                      value={row.qty}
                      onChange={(e) => updateRow(row.id, "qty", e.target.value)}
                      className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[15px] font-[700] h-12 rounded-xl"
                    />
                  </div>
                </div>

                {/* 통화 선택 */}
                <div>
                  <label className="text-[11px] font-[800] text-slate-500 uppercase tracking-wider block mb-2">
                    통화 *
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => updateRow(row.id, "currency", "KRW")}
                      className={cn(
                        "flex-1 h-12 rounded-xl text-[14px] font-[900] transition-all border-2",
                        row.currency === "KRW"
                          ? "bg-slate-900 text-white border-slate-900"
                          : "bg-white text-slate-400 border-slate-100 hover:border-slate-300"
                      )}
                    >
                      원화 (₩)
                    </button>
                    <button
                      onClick={() => updateRow(row.id, "currency", "USD")}
                      className={cn(
                        "flex-1 h-12 rounded-xl text-[14px] font-[900] transition-all border-2",
                        row.currency === "USD"
                          ? "bg-slate-900 text-white border-slate-900"
                          : "bg-white text-slate-400 border-slate-100 hover:border-slate-300"
                      )}
                    >
                      달러 ($)
                    </button>
                  </div>
                </div>
              </div>

              {/* 선택 입력 토글 */}
              <button
                onClick={() => toggleOptional(row.id)}
                className="w-full mt-5 pt-5 border-t border-slate-100 flex items-center justify-between text-[13px] font-[800] text-slate-600 hover:text-slate-900 transition-colors"
              >
                <span>추가 정보 입력 (선택)</span>
                <ChevronDown
                  size={16}
                  strokeWidth={3}
                  className={cn(
                    "transition-transform",
                    expandedOptional[row.id] && "rotate-180"
                  )}
                />
              </button>

              {/* 선택 입력 필드 */}
              <AnimatePresence>
                {expandedOptional[row.id] && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-4 mt-4">
                      {/* 매수일 */}
                      <div>
                        <label className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                          <Calendar size={12} />
                          매수일
                        </label>
                        <Input
                          type="date"
                          value={row.purchaseDate || ""}
                          onChange={(e) => updateRow(row.id, "purchaseDate", e.target.value)}
                          className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[14px] font-[700] h-11 rounded-xl"
                        />
                      </div>

                      {/* 증권사 */}
                      <div>
                        <label className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                          <Building2 size={12} />
                          증권사
                        </label>
                        <Input
                          placeholder="예: 키움증권, 미래에셋"
                          value={row.broker || ""}
                          onChange={(e) => updateRow(row.id, "broker", e.target.value)}
                          className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[14px] font-[700] h-11 rounded-xl"
                        />
                      </div>

                      {/* 계좌별명 */}
                      <div>
                        <label className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                          <Wallet size={12} />
                          계좌별명
                        </label>
                        <Input
                          placeholder="예: 연금계좌, 주계좌"
                          value={row.accountName || ""}
                          onChange={(e) => updateRow(row.id, "accountName", e.target.value)}
                          className="bg-slate-50 border-slate-100 focus:border-slate-900 focus:ring-slate-900 text-[14px] font-[700] h-11 rounded-xl"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* 종목 추가 버튼 */}
        <button
          onClick={handleAddRow}
          className="mt-4 w-full py-4 rounded-2xl bg-slate-50 border-2 border-slate-100 border-dashed flex items-center justify-center gap-2 text-slate-600 hover:bg-slate-100 hover:border-slate-200 transition-all font-[800] text-[14px] group"
        >
          <Plus size={18} strokeWidth={3} className="group-hover:rotate-90 transition-transform duration-300" />
          종목 추가하기
        </button>
      </main>

      {/* 하단 고정 버튼 */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-slate-100">
        <div className="container-custom">
          <Button
            size="lg"
            className={cn(
              "w-full h-14 text-[15px] font-[900] rounded-2xl transition-all",
              canSubmit
                ? "bg-slate-900 hover:bg-slate-800 text-white"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
            onClick={handleSubmit}
            disabled={!canSubmit}
          >
            {canSubmit ? "입력 완료" : "필수 항목을 입력해주세요"}
          </Button>
        </div>
      </div>
    </div>
  );
}
