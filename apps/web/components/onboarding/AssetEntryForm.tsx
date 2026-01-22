"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, useCallback } from "react";
import { usePortfolioStore } from "@/lib/store";
import { Plus, Trash2, Calendar, Building2, ChevronDown, CheckCircle2, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export type AssetRow = {
  id: string;
  ticker: string;
  name: string;
  price: string;
  qty: string;
  totalValue: string;
  currency: "KRW" | "USD";
  purchaseDate?: string;
  broker?: string;
  accountName?: string;
};

// 숫자 포맷팅 유틸리티
const formatNumber = (val: string | number) => {
  if (!val && val !== 0) return "";
  const num = typeof val === "string" ? val.replace(/[^0-9.]/g, "") : val.toString();
  if (isNaN(Number(num))) return "";
  const parts = num.split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return parts.join(".");
};

const parseNumber = (val: string) => {
  return val.replace(/,/g, "");
};

const isOverseas = (ticker: string) => {
  return /[a-zA-Z]/.test(ticker);
};

export function AssetEntryForm({ title, subtitle, badgeText, backHref, nextPath }: { title: string; subtitle: string; badgeText?: string; backHref: string; nextPath?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromDashboard = searchParams.get("from") === "dashboard";
  
  const assets = usePortfolioStore((state) => state.assets);
  const addAsset = usePortfolioStore((state) => state.addAsset);
  const reset = usePortfolioStore((state) => state.reset);

  const [rows, setRows] = useState<AssetRow[]>([]);

  useEffect(() => {
    if (assets.length > 0) {
      const initialRows = assets.map(asset => {
        const p = asset.avgPrice || 0;
        const q = asset.quantity || 0;
        return {
          id: asset.id,
          ticker: asset.ticker,
          name: asset.name,
          price: p.toString(),
          qty: q.toString(),
          totalValue: (p * q).toString(),
          currency: asset.currency,
        };
      });
      setRows(initialRows);
    } else {
      setRows([{ id: "1", ticker: "", name: "", price: "", qty: "", totalValue: "", currency: "KRW" }]);
    }
  }, [assets]);

  const [expandedOptional, setExpandedOptional] = useState<Record<string, boolean>>({});

  const handleAddRow = () => {
    setRows([...rows, { id: Date.now().toString(), ticker: "", name: "", price: "", qty: "", totalValue: "", currency: "KRW" }]);
  };

  const handleRemoveRow = (id: string) => {
    if (rows.length === 1) {
      setRows([{ id: Date.now().toString(), ticker: "", name: "", price: "", qty: "", totalValue: "", currency: "KRW" }]);
      return;
    }
    setRows(rows.filter(r => r.id !== id));
  };

  const updateRow = useCallback((id: string, field: keyof AssetRow, value: string) => {
    setRows(prevRows => prevRows.map(r => {
      if (r.id !== id) return r;
      const isSearchField = field === "ticker" || field === "name";
      const cleanValue = isSearchField ? value : parseNumber(value);
      const updatedRow = { ...r, [field]: cleanValue };

      if (field === "price" || field === "qty") {
        const p = field === "price" ? Number(cleanValue) : Number(r.price);
        const q = field === "qty" ? Number(cleanValue) : Number(r.qty);
        if (!isNaN(p) && !isNaN(q)) updatedRow.totalValue = (p * q).toString();
      } else if (field === "totalValue") {
        const tv = Number(cleanValue);
        const q = Number(r.qty);
        const p = Number(r.price);
        if (!isNaN(tv)) {
          if (q > 0) updatedRow.price = (tv / q).toFixed(2).replace(/\.00$/, "");
          else if (p > 0) updatedRow.qty = (tv / p).toFixed(4).replace(/\.00$/, "");
        }
      }
      return updatedRow;
    }));
  }, []);

  const toggleOptional = (id: string) => setExpandedOptional(prev => ({ ...prev, [id]: !prev[id] }));

  const handleSubmit = () => {
    reset();
    rows.forEach(r => {
      if (r.ticker && r.qty) {
        addAsset({ id: r.id, ticker: r.ticker.toUpperCase(), name: r.name || r.ticker, avgPrice: Number(r.price) || 0, quantity: Number(r.qty) || 0, currency: r.currency });
      }
    });
    router.push(nextPath || (fromDashboard ? "/dashboard" : "/onboarding/ai/decision"));
  };

  const isValidRow = (row: AssetRow) => row.ticker && row.qty && row.price;
  const canSubmit = rows.some(isValidRow);

  return (
    <div className="flex-1 bg-white flex flex-col overflow-hidden">
      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="w-full max-w-md mx-auto">
          <div className="mb-6 w-full">
            {badgeText && <div className="flex items-center gap-2 mb-2"><div className="px-2 py-0.5 rounded bg-[var(--color-secondary)] text-[var(--color-primary)] text-[10px] font-bold uppercase tracking-wider">{badgeText}</div></div>}
            <h1 className="text-2xl font-bold mb-2 text-slate-900">{title}</h1>
            <p className="text-[14px] font-[600] text-slate-400">{subtitle}</p>
          </div>
          <div className="space-y-3 w-full">
          {rows.map((row, index) => (
            <motion.div key={row.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-slate-100 p-4 relative hover:border-[var(--color-primary)]/30 transition-all shadow-sm">
              <button onClick={() => handleRemoveRow(row.id)} className="absolute top-4 right-4 w-7 h-7 rounded-full bg-slate-50 hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all flex items-center justify-center cursor-pointer"><Trash2 size={14} strokeWidth={2.5} /></button>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 flex-1 mr-4 overflow-hidden">
                  <div className="w-6 h-6 rounded-lg bg-[var(--color-primary)] text-white flex items-center justify-center shrink-0"><span className="text-[12px] font-[900]">{index + 1}</span></div>
                  {row.name ? <div className="flex items-center gap-2 truncate"><span className="text-[14px] font-[800] text-slate-900 truncate">{row.name}</span><span className="text-[12px] font-[600] text-slate-400 shrink-0">{row.ticker}</span></div> : <div className="relative flex-1"><Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400" /><input type="text" placeholder="종목명 또는 티커 검색" value={row.ticker} onChange={(e) => updateRow(row.id, "ticker", e.target.value)} className="w-full bg-transparent border-none focus:outline-none text-[14px] font-[800] text-slate-900 pl-7 placeholder:text-slate-300 placeholder:font-bold" /></div>}
                  {isValidRow(row) && <CheckCircle2 size={14} className="text-[var(--color-primary)] shrink-0" />}
                </div>
                <div className="shrink-0 mr-8">
                  {isOverseas(row.ticker) ? <div className="flex bg-slate-100 p-0.5 rounded-lg"><button onClick={() => updateRow(row.id, "currency", "KRW")} className={cn("px-2 py-1 text-[10px] font-bold rounded-md transition-all cursor-pointer", row.currency === "KRW" ? "bg-white text-slate-900 shadow-sm" : "text-slate-400")}>₩</button><button onClick={() => updateRow(row.id, "currency", "USD")} className={cn("px-2 py-1 text-[10px] font-bold rounded-md transition-all cursor-pointer", row.currency === "USD" ? "bg-white text-slate-900 shadow-sm" : "text-slate-400")}>$</button></div> : <div className="px-2 py-1 bg-slate-50 text-slate-400 text-[10px] font-extrabold rounded-md border border-slate-100">₩</div>}
                </div>
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-12 gap-2">
                  <div className="col-span-4"><label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider block mb-1 ml-1">평단가</label><Input placeholder="0" value={formatNumber(row.price)} onChange={(e) => updateRow(row.id, "price", e.target.value)} className="bg-slate-50 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[700] h-10 rounded-xl px-3" /></div>
                  <div className="col-span-3"><label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider block mb-1 ml-1">수량</label><Input placeholder="0" value={formatNumber(row.qty)} onChange={(e) => updateRow(row.id, "qty", e.target.value)} className="bg-slate-50 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[700] h-10 rounded-xl px-3" /></div>
                  <div className="col-span-5"><label className="text-[10px] font-[800] text-[var(--color-primary)] uppercase tracking-wider block mb-1 ml-1 font-bold">평가 금액</label><Input placeholder="0" value={formatNumber(row.totalValue)} onChange={(e) => updateRow(row.id, "totalValue", e.target.value)} className="bg-[var(--color-secondary)]/30 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[800] h-10 rounded-xl px-3 text-[var(--color-primary)]" /></div>
                </div>
              </div>
              <button onClick={() => toggleOptional(row.id)} className="w-full mt-3 pt-3 border-t border-slate-50 flex items-center justify-between text-[11px] font-[800] text-slate-400 hover:text-[var(--color-primary)] transition-colors cursor-pointer"><span>상세 정보 (매수일, 증권사)</span><ChevronDown size={14} strokeWidth={3} className={cn("transition-transform", expandedOptional[row.id] && "rotate-180")} /></button>
              <AnimatePresence>{expandedOptional[row.id] && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden"><div className="grid grid-cols-2 gap-2 mt-3"><div><label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider flex items-center gap-1 mb-1 ml-1"><Calendar size={10} /> 매수일</label><Input type="date" value={row.purchaseDate || ""} onChange={(e) => updateRow(row.id, "purchaseDate", e.target.value)} className="bg-slate-50 border-transparent text-[12px] font-[700] h-9 rounded-xl px-2" /></div><div><label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider flex items-center gap-1 mb-1 ml-1"><Building2 size={10} /> 증권사</label><Input placeholder="토스증권" value={row.broker || ""} onChange={(e) => updateRow(row.id, "broker", e.target.value)} className="bg-slate-50 border-transparent text-[12px] font-[700] h-9 rounded-xl px-2" /></div></div></motion.div>}</AnimatePresence>
            </motion.div>
          ))}
          </div>
          <button onClick={handleAddRow} className="mt-4 w-full py-3 rounded-2xl bg-white border-2 border-[var(--color-primary)]/20 border-dashed flex items-center justify-center gap-2 text-[var(--color-primary)] hover:bg-[var(--color-secondary)]/30 transition-all font-[800] text-[13px] group cursor-pointer"><Plus size={16} strokeWidth={3} className="group-hover:rotate-90 transition-transform duration-300" />종목 추가하기</button>
        </div>
      </div>

      {/* Fixed Button Area */}
      <div className="flex-shrink-0 border-t border-gray-100 bg-white">
        <div className="w-full max-w-md mx-auto p-6">
          <Button size="lg" className={cn("w-full h-14 text-[16px] font-[900] rounded-2xl transition-all shadow-lg cursor-pointer", canSubmit ? "bg-[var(--color-primary)] hover:bg-[#00B34E] text-white shadow-[var(--color-primary)]/20" : "bg-slate-100 text-slate-400 cursor-not-allowed")} onClick={handleSubmit} disabled={!canSubmit}>{canSubmit ? "완료하고 분석하기" : "종목 정보를 입력해주세요"}</Button>
        </div>
      </div>
    </div>
  );
}
