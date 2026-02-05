"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, useCallback } from "react";
import { usePortfolioStore } from "@/lib/store";
import { Plus, Trash2, ChevronDown, CheckCircle2, Search, XCircle, Edit2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { searchAssets, getAssetDetails } from "@/lib/api/asset";
import type { AssetSearchResponse } from "@/types/asset";

export type AssetRow = {
  id: string;
  ticker: string;
  name: string;
  price: string;
  qty: string;
  totalValue: string;
  currency: "KRW" | "USD";
  national: string;
  market: string;
  purchaseDate?: string;
  broker?: string;
  accountName?: string;
  isMapped?: boolean;        // OCR/DB 매핑 여부
  matchConfidence?: number;  // OCR 매칭 신뢰도 (0-1)
  ocrRawText?: string;        // OCR 원본 텍스트
};

type OcrSummary = {
  total: number;
  mapped: number;
  unmapped: number;
  deduped: number;
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

const normalizeName = (value: string) => value.trim().toLowerCase().replace(/\s+/g, "");

const normalizeNumeric = (value: string) => {
  const num = Number(parseNumber(value));
  return Number.isFinite(num) && num > 0 ? num : null;
};

const countMatchingFields = (a: AssetRow, b: AssetRow) => {
  let matches = 0;

  const nameA = normalizeName(a.name || "");
  const nameB = normalizeName(b.name || "");
  if (nameA && nameB && nameA === nameB) matches += 1;

  const priceA = normalizeNumeric(a.price || "");
  const priceB = normalizeNumeric(b.price || "");
  if (priceA !== null && priceB !== null && Math.abs(priceA - priceB) < 0.000001) matches += 1;

  const qtyA = normalizeNumeric(a.qty || "");
  const qtyB = normalizeNumeric(b.qty || "");
  if (qtyA !== null && qtyB !== null && Math.abs(qtyA - qtyB) < 0.000001) matches += 1;

  return matches;
};

const scoreRow = (row: AssetRow) => {
  let score = 0;
  if (row.isMapped) score += 3;
  if (normalizeName(row.name || "")) score += 1;
  if (normalizeNumeric(row.price || "") !== null) score += 1;
  if (normalizeNumeric(row.qty || "") !== null) score += 1;
  if (row.matchConfidence !== undefined) score += row.matchConfidence;
  return score;
};

const dedupeRows = (rows: AssetRow[]) => {
  const result: AssetRow[] = [];
  rows.forEach((row) => {
    const dupIndex = result.findIndex((existing) => countMatchingFields(existing, row) >= 2);
    if (dupIndex === -1) {
      result.push(row);
      return;
    }
    const existing = result[dupIndex];
    if (scoreRow(row) > scoreRow(existing)) {
      result[dupIndex] = row;
    }
  });
  return result;
};

const isRowMapped = (row: AssetRow) => {
  if (row.isMapped !== undefined) return row.isMapped;
  return Boolean(row.national && row.market && row.market !== "UNKNOWN");
};

const hasRowContent = (row: AssetRow) => Boolean(row.name || row.ticker || row.ocrRawText || row.price || row.qty);

const createEmptyRow = (): AssetRow => ({
  id: Date.now().toString(),
  ticker: "",
  name: "",
  price: "",
  qty: "",
  totalValue: "",
  currency: "KRW",
  national: "",
  market: "",
  isMapped: false,
});

export function AssetEntryForm({ title, subtitle, badgeText, nextPath }: { title: string; subtitle: string; badgeText?: string; nextPath?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromDashboard = searchParams.get("from") === "dashboard";
  const shouldShowOcrSummary = searchParams.get("ocr") === "1";
  
  const assets = usePortfolioStore((state) => state.assets);
  const addAsset = usePortfolioStore((state) => state.addAsset);
  const reset = usePortfolioStore((state) => state.reset);

  const [rows, setRows] = useState<AssetRow[]>([]);
  const [editingRows, setEditingRows] = useState<Record<string, boolean>>({});
  const [collapsedRows, setCollapsedRows] = useState<Record<string, boolean>>({});
  const [searchTerms, setSearchTerms] = useState<Record<string, string>>({});
  const [debouncedSearchTerms, setDebouncedSearchTerms] = useState<Record<string, string>>({});
  const [searchResults, setSearchResults] = useState<Record<string, AssetSearchResponse[]>>({});
  const [isSearching, setIsSearching] = useState<Record<string, boolean>>({});
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);
  const [ocrSummary, setOcrSummary] = useState<OcrSummary | null>(null);
  const [showOcrSummary, setShowOcrSummary] = useState(false);

  useEffect(() => {
    if (assets.length > 0) {
      const initialRows = assets.map(asset => {
        const p = asset.avgPrice || 0;
        const q = asset.quantity || 0;
        const mapped = asset.isMapped ?? Boolean(asset.national && asset.market && asset.market !== "UNKNOWN");
        return {
          id: asset.positionId,
          ticker: asset.ticker,
          name: asset.name,
          price: p.toString(),
          qty: q.toString(),
          totalValue: (p * q).toString(),
          currency: asset.currency,
          national: asset.national,
          market: asset.market,
          isMapped: mapped,
          matchConfidence: asset.matchConfidence,
          ocrRawText: asset.ocrRawText,
        };
      });
      const dedupedRows = dedupeRows(initialRows);
      setRows(dedupedRows);
      const total = initialRows.length;
      const mappedCount = initialRows.filter(row => isRowMapped(row)).length;
      const dedupedCount = Math.max(0, total - dedupedRows.length);
      setOcrSummary({
        total,
        mapped: mappedCount,
        unmapped: total - mappedCount,
        deduped: dedupedCount,
      });
    } else {
      setRows([createEmptyRow()]);
      setOcrSummary(null);
    }
    setEditingRows({});
    setCollapsedRows({});
    setSearchTerms({});
    setSearchResults({});
    setActiveSearchId(null);
  }, [assets]);

  useEffect(() => {
    if (shouldShowOcrSummary && assets.length > 0) {
      setShowOcrSummary(true);
    }
  }, [shouldShowOcrSummary, assets.length]);


  // Debounce search terms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerms(searchTerms);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerms]);

  // Perform search when debounced terms change
  useEffect(() => {
    Object.entries(debouncedSearchTerms).forEach(async ([rowId, term]) => {
      if (!term.trim()) {
        setSearchResults(prev => ({ ...prev, [rowId]: [] }));
        return;
      }

      setIsSearching(prev => ({ ...prev, [rowId]: true }));
      try {
        const results = await searchAssets(term, 10);
        setSearchResults(prev => ({ ...prev, [rowId]: results }));
      } catch (error) {
        console.error("Search failed:", error);
        setSearchResults(prev => ({ ...prev, [rowId]: [] }));
      } finally {
        setIsSearching(prev => ({ ...prev, [rowId]: false }));
      }
    });
  }, [debouncedSearchTerms]);

  // Asset search handler
  const handleSearchChange = (rowId: string, term: string) => {
    setSearchTerms(prev => ({ ...prev, [rowId]: term }));
  };

  const startEditingRow = useCallback((rowId: string, seed?: string) => {
    setEditingRows(prev => ({ ...prev, [rowId]: true }));
    setCollapsedRows(prev => ({ ...prev, [rowId]: false }));
    if (seed !== undefined) {
      setSearchTerms(prev => ({ ...prev, [rowId]: seed }));
    }
    setActiveSearchId(rowId);
  }, []);

  const cancelEditingRow = useCallback((rowId: string) => {
    // 편집 모드 종료
    setEditingRows(prev => ({ ...prev, [rowId]: false }));
    // 검색 관련 상태 초기화
    setSearchTerms(prev => ({ ...prev, [rowId]: "" }));
    setSearchResults(prev => ({ ...prev, [rowId]: [] }));
    setActiveSearchId(null);
  }, []);

  const toggleRowCollapse = useCallback((rowId: string) => {
    setCollapsedRows(prev => ({ ...prev, [rowId]: !prev[rowId] }));
  }, []);

  const setAllCollapsed = useCallback((collapsed: boolean) => {
    setCollapsedRows(() => {
      const next: Record<string, boolean> = {};
      rows.forEach(row => {
        next[row.id] = collapsed;
      });
      return next;
    });
  }, [rows]);

  const removeAllUnmappedRows = useCallback(() => {
    const removedIds = rows
      .filter(row => hasRowContent(row) && !isRowMapped(row))
      .map(row => row.id);

    if (removedIds.length === 0) return;

    const remainingRows = rows.filter(row => !removedIds.includes(row.id));
    setRows(remainingRows.length > 0 ? remainingRows : [createEmptyRow()]);

    setSearchTerms(prev => {
      const next = { ...prev };
      removedIds.forEach(id => delete next[id]);
      return next;
    });
    setSearchResults(prev => {
      const next = { ...prev };
      removedIds.forEach(id => delete next[id]);
      return next;
    });
    setEditingRows(prev => {
      const next = { ...prev };
      removedIds.forEach(id => delete next[id]);
      return next;
    });
    setCollapsedRows(prev => {
      const next = { ...prev };
      removedIds.forEach(id => delete next[id]);
      return next;
    });
  }, [rows]);

  const closeOcrSummary = useCallback(() => {
    setShowOcrSummary(false);
    if (shouldShowOcrSummary) {
      const params = new URLSearchParams(searchParams.toString());
      params.delete("ocr");
      const nextQuery = params.toString();
      const nextPath = nextQuery ? `/onboarding/ai/check?${nextQuery}` : "/onboarding/ai/check";
      router.replace(nextPath);
    }
  }, [router, searchParams, shouldShowOcrSummary]);

  // Handle asset selection from search results
  const handleAssetSelect = async (rowId: string, asset: AssetSearchResponse) => {
    try {
      // Fetch asset details with current price
      const details = await getAssetDetails(asset.identifier, true);
      const currentPrice = details.price?.price || 0;

      // Determine currency based on national
      const currency: "KRW" | "USD" = asset.national === "KR" ? "KRW" : "USD";

      // Update row with asset data and defaults
      setRows(prevRows => prevRows.map(r => {
        if (r.id !== rowId) return r;
        const price = currentPrice.toString();
        const qty = "1";
        const totalValue = (currentPrice * 1).toString();

        return {
          ...r,
          ticker: asset.symbol,
          name: asset.name,
          price,
          qty,
          totalValue,
          currency,
          national: asset.national,
          market: asset.market,
          isMapped: true,
          matchConfidence: undefined,
          ocrRawText: undefined,
        };
      }));

      // Clear search state
      setSearchTerms(prev => ({ ...prev, [rowId]: "" }));
      setSearchResults(prev => ({ ...prev, [rowId]: [] }));
      setActiveSearchId(null);
      setEditingRows(prev => ({ ...prev, [rowId]: false }));
    } catch (error) {
      console.error("Failed to fetch asset details:", error);
    }
  };

  const handleAddRow = () => {
    setRows([...rows, createEmptyRow()]);
  };

  const handleRemoveRow = useCallback((id: string) => {
    console.log('handleRemoveRow called for id:', id);
    console.log('Current rows:', rows);

    if (rows.length === 1) {
      console.log('Only one row, creating empty row');
      setRows([createEmptyRow()]);
      // Clear search state for this row
      setSearchTerms(prev => ({ ...prev, [id]: "" }));
      setSearchResults(prev => ({ ...prev, [id]: [] }));
      setEditingRows(prev => ({ ...prev, [id]: false }));
      setCollapsedRows(prev => ({ ...prev, [id]: false }));
      return;
    }

    console.log('Removing row:', id);
    setRows(prevRows => {
      const newRows = prevRows.filter(r => r.id !== id);
      console.log('New rows after filter:', newRows);
      return newRows;
    });

    // Clean up search state
    setSearchTerms(prev => {
      const newState = { ...prev };
      delete newState[id];
      return newState;
    });
    setSearchResults(prev => {
      const newState = { ...prev };
      delete newState[id];
      return newState;
    });
    setEditingRows(prev => {
      const newState = { ...prev };
      delete newState[id];
      return newState;
    });
    setCollapsedRows(prev => {
      const newState = { ...prev };
      delete newState[id];
      return newState;
    });
  }, [rows]);

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


  const handleSubmit = () => {
    const hasUnmappedRows = rows.some(row => {
      return hasRowContent(row) && !isRowMapped(row);
    });
    if (hasUnmappedRows) {
      alert("매핑되지 않은 종목이 있습니다. 삭제하거나 수정해 주세요.");
      return;
    }

    reset();

    const validRows = rows.filter(r => {
      const mapped = isRowMapped(r);
      if (!r.ticker || !r.qty || !r.national || !r.market || !mapped) return false;
      return true;
    });

    validRows.forEach(r => {
      addAsset({
        positionId: r.id,
        ticker: r.ticker.toUpperCase(),
        name: r.name || r.ticker,
        avgPrice: Number(r.price) || 0,
        quantity: Number(r.qty) || 0,
        currency: r.currency,
        national: r.national,
        market: r.market,
        isMapped: true,
        matchConfidence: r.matchConfidence,
        ocrRawText: r.ocrRawText,
      });
    });

    const skippedCount = rows.length - validRows.length;
    if (skippedCount > 0) {
      alert(`매핑되지 않은 ${skippedCount}개 종목은 제외되었습니다.`);
    }

    router.push(nextPath || (fromDashboard ? "/dashboard" : "/onboarding/ai/decision"));
  };

  const isValidRow = (row: AssetRow) => row.ticker && row.qty && row.price && row.national && row.market && isRowMapped(row);
  const hasUnmappedRows = rows.some(row => hasRowContent(row) && !isRowMapped(row));
  const canSubmit = rows.some(isValidRow) && !hasUnmappedRows;
  const allCollapsed = rows.length > 0 && rows.every(row => Boolean(collapsedRows[row.id]));
  const allExpanded = rows.length > 0 && rows.every(row => !collapsedRows[row.id]);
  const submitLabel = hasUnmappedRows
    ? "매핑되지 않은 종목을 수정/삭제해주세요"
    : canSubmit
      ? "완료하고 분석하기"
      : "종목 정보를 입력해주세요";

  return (
    <div className="flex-1 bg-white flex flex-col overflow-hidden">
      <AnimatePresence>
        {showOcrSummary && ocrSummary && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-[60] backdrop-blur-sm"
              onClick={closeOcrSummary}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="fixed inset-0 z-[70] flex items-center justify-center p-6"
            >
              <div className="bg-white rounded-3xl p-6 shadow-2xl max-w-sm w-full border border-slate-100">
                <div className="text-[11px] font-[800] text-slate-400 uppercase tracking-wider mb-2">OCR 결과 요약</div>
                <h2 className="text-[20px] font-[900] text-slate-900 mb-4">인식 결과를 확인해 주세요</h2>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-2xl bg-slate-50 p-3 flex flex-col items-center justify-center gap-1 min-h-[76px]">
                    <div className="text-[11px] font-[800] text-slate-400 leading-tight">인식</div>
                    <div className="text-[18px] font-[900] text-slate-900 tabular-nums">{ocrSummary.total}</div>
                  </div>
                  <div className="rounded-2xl bg-emerald-50 p-3 flex flex-col items-center justify-center gap-1 min-h-[76px]">
                    <div className="text-[11px] font-[800] text-emerald-700 leading-tight">종목 매핑 성공</div>
                    <div className="text-[18px] font-[900] text-emerald-700 tabular-nums">{ocrSummary.mapped}</div>
                  </div>
                  <div className="rounded-2xl bg-red-50 p-3 flex flex-col items-center justify-center gap-1 min-h-[76px]">
                    <div className="text-[11px] font-[800] text-red-700 leading-tight">종목 매핑 오류</div>
                    <div className="text-[18px] font-[900] text-red-700 tabular-nums">{ocrSummary.unmapped}</div>
                  </div>
                </div>
                {ocrSummary.deduped > 0 && (
                  <div className="mt-3 text-[12px] font-[800] text-slate-600 bg-slate-50 rounded-xl px-3 py-2">
                    중복 항목 {ocrSummary.deduped}개가 자동으로 제거되었습니다.
                  </div>
                )}
                {ocrSummary.unmapped > 0 && (
                  <div className="mt-2 text-[12px] font-[800] text-red-600">
                    미매핑 종목은 수정/삭제 후에만 다음 단계로 진행할 수 있어요.
                  </div>
                )}
                <Button
                  size="lg"
                  className="w-full mt-4 h-11 text-[14px] font-[900] rounded-2xl bg-[var(--color-primary)] hover:bg-[#00B34E] text-white"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeOcrSummary();
                  }}
                >
                  확인
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="w-full max-w-md mx-auto">
          <div className="mb-4 w-full">
            {badgeText && <div className="flex items-center gap-2 mb-2"><div className="px-2 py-0.5 rounded bg-[var(--color-secondary)] text-[var(--color-primary)] text-[10px] font-bold uppercase tracking-wider">{badgeText}</div></div>}
            <h1 className="text-2xl font-bold mb-2 text-slate-900">{title}</h1>
            <p className="text-[14px] font-[600] text-slate-400">{subtitle}</p>
          </div>
          <div className="mb-5 w-full flex items-center gap-2 justify-end">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                removeAllUnmappedRows();
              }}
              disabled={!hasUnmappedRows}
              className={cn(
                "px-3.5 py-2 rounded-xl text-[11px] font-[800] border transition-all whitespace-nowrap",
                hasUnmappedRows
                  ? "border-red-200 text-red-700 bg-red-50 hover:bg-red-100"
                  : "border-slate-100 text-slate-300 bg-slate-50 cursor-not-allowed"
              )}
            >
              매핑 실패 전체 삭제
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setAllCollapsed(true);
              }}
              disabled={allCollapsed}
              className={cn(
                "px-3.5 py-2 rounded-xl text-[11px] font-[800] border transition-all whitespace-nowrap",
                allCollapsed
                  ? "border-slate-100 text-slate-300 bg-slate-50 cursor-not-allowed"
                  : "border-slate-200 text-slate-600 bg-white hover:bg-slate-50"
              )}
            >
              전체 접기
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setAllCollapsed(false);
              }}
              disabled={allExpanded}
              className={cn(
                "px-3.5 py-2 rounded-xl text-[11px] font-[800] border transition-all whitespace-nowrap",
                allExpanded
                  ? "border-slate-100 text-slate-300 bg-slate-50 cursor-not-allowed"
                  : "border-slate-200 text-slate-600 bg-white hover:bg-slate-50"
              )}
            >
              전체 펼치기
            </button>
          </div>
          <div className="space-y-3 w-full">
          {rows.map((row, index) => {
            const mapped = isRowMapped(row);
            const isEditing = Boolean(editingRows[row.id]);
            const isCollapsed = Boolean(collapsedRows[row.id]);
            const hasNoMapping = hasRowContent(row) && !mapped;
            const showSearch = (!row.name || isEditing) && !isCollapsed;

            return (
            <motion.div key={row.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={cn(
              "bg-white rounded-2xl border p-4 relative hover:border-[var(--color-primary)]/30 transition-all shadow-sm",
              hasNoMapping ? "border-red-200 bg-red-50/20" : "border-slate-100"
            )}>

              {/* OCR 매핑 경고 */}
              {hasNoMapping && !isCollapsed && (
                <div className={cn(
                  "mb-3 rounded-xl p-3 border",
                  "bg-red-50 border-red-200"
                )}>
                  <div className="flex items-start gap-2">
                    <XCircle size={16} className="text-red-600 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className={cn(
                        "text-[12px] font-[800] mb-1",
                        "text-red-800"
                      )}>
                        ❌ 매핑 실패 - 종목을 찾을 수 없습니다
                      </div>
                      {row.ocrRawText && (
                        <div className={cn(
                          "text-[11px] font-[700] mb-2 truncate",
                          "text-red-700"
                        )}>
                          OCR 인식: "{row.ocrRawText}" → 매핑: "{row.name || '없음'}"
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditingRow(row.id, row.name || row.ocrRawText || row.ticker);
                        }}
                        className={cn(
                          "text-[11px] font-[800] underline",
                          "text-red-700 hover:text-red-900"
                        )}
                      >
                        종목 검색하기
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className={cn("flex items-center justify-between", isCollapsed ? "mb-0" : "mb-4")}>
                {/* 왼쪽 영역: 번호/아이콘/종목명/티커 */}
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {/* 번호 */}
                  <div className="w-6 h-6 rounded-lg bg-[var(--color-primary)] text-white flex items-center justify-center shrink-0">
                    <span className="text-[12px] font-[900]">{index + 1}</span>
                  </div>

                  {!showSearch ? (
                    <>
                      {/* 매핑 상태 아이콘 */}
                      {mapped ? (
                        <CheckCircle2 size={16} className="text-green-500 shrink-0" />
                      ) : (
                        <XCircle size={16} className="text-red-500 shrink-0" />
                      )}

                      {/* 종목명과 티커를 한 컨테이너로 묶어서 붙임 */}
                      <div className="flex items-center gap-1 min-w-0">
                        <span className="text-[14px] font-[800] text-slate-900 truncate max-w-[180px]">
                          {row.name || row.ticker || "종목 미지정"}
                        </span>
                        <span className="text-[12px] font-[600] text-slate-400 shrink-0">
                          {row.ticker}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="relative flex-1 min-w-0">
                      <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 z-10 pointer-events-none" />
                      <input
                        type="text"
                        placeholder="종목명 또는 티커 검색"
                        value={searchTerms[row.id] ?? ""}
                        onChange={(e) => handleSearchChange(row.id, e.target.value)}
                        onFocus={() => setActiveSearchId(row.id)}
                        onBlur={(e) => {
                          // 드롭다운 내부 클릭은 무시 (약간의 지연으로 클릭 이벤트 처리 시간 확보)
                          setTimeout(() => {
                            if (activeSearchId === row.id) {
                              cancelEditingRow(row.id);
                            }
                          }, 200);
                        }}
                        onKeyDown={(e) => {
                          // ESC 키로 검색 취소
                          if (e.key === 'Escape') {
                            cancelEditingRow(row.id);
                          }
                        }}
                        className="w-full bg-transparent border-none focus:outline-none text-[14px] font-[800] text-slate-900 pl-7 placeholder:text-slate-300 placeholder:font-bold"
                      />

                      {/* Search Results Dropdown - 검색 입력창 바로 아래 */}
                      {showSearch && activeSearchId === row.id && searchTerms[row.id] && (
                        <>
                          <div
                            className="fixed inset-0 z-[100]"
                            onClick={() => setActiveSearchId(null)}
                          />
                          <motion.div
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl border border-slate-100 shadow-xl z-[110] overflow-hidden max-h-60"
                          >
                            <div className="p-2 space-y-0.5 overflow-y-auto max-h-56">
                              {isSearching[row.id] ? (
                                <div className="text-center p-3 text-xs text-slate-400 font-semibold">검색 중...</div>
                              ) : searchResults[row.id] && searchResults[row.id].length > 0 ? (
                                searchResults[row.id].map(asset => (
                                  <div
                                    key={asset.identifier}
                                    onMouseDown={(e) => {
                                      // onBlur 방지
                                      e.preventDefault();
                                    }}
                                    onClick={() => handleAssetSelect(row.id, asset)}
                                    className="px-3 py-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors flex items-center justify-between group"
                                  >
                                    <div className="flex items-center gap-2">
                                      <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-[10px] font-[900] text-slate-400">
                                        {asset.symbol.charAt(0)}
                                      </div>
                                      <div>
                                        <div className="text-[12px] font-[800] text-slate-900">{asset.name}</div>
                                        <div className="text-[10px] font-[700] text-slate-400">{asset.symbol} · {asset.market}</div>
                                      </div>
                                    </div>
                                  </div>
                                ))
                              ) : (
                                <div className="text-center p-3 text-xs text-slate-400 font-semibold">검색 결과가 없습니다.</div>
                              )}
                            </div>
                          </motion.div>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* 오른쪽 영역: [화폐토글][변경][삭제] */}
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  {/* 화폐 토글 (외국 주식만) */}
                  {!isCollapsed && isOverseas(row.ticker) && (
                    <div className="flex items-center bg-slate-50 rounded-lg p-0.5">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          updateRow(row.id, "currency", "KRW");
                        }}
                        className={cn(
                          "px-2 py-1 text-[11px] font-[900] rounded transition-all",
                          row.currency === "KRW"
                            ? "bg-white text-slate-900 shadow-sm"
                            : "text-slate-400 hover:text-slate-600"
                        )}
                      >
                        ₩
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          updateRow(row.id, "currency", "USD");
                        }}
                        className={cn(
                          "px-2 py-1 text-[11px] font-[900] rounded transition-all",
                          row.currency === "USD"
                            ? "bg-white text-slate-900 shadow-sm"
                            : "text-slate-400 hover:text-slate-600"
                        )}
                      >
                        $
                      </button>
                    </div>
                  )}

                  {/* 변경 버튼 (연필만) */}
                  {!isCollapsed && !showSearch && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        startEditingRow(row.id, row.name || row.ticker);
                      }}
                      className="w-7 h-7 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-all flex items-center justify-center"
                    >
                      <Edit2 size={14} strokeWidth={2.5} />
                    </button>
                  )}

                  {/* 버리기 버튼 */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      console.log('Delete button clicked for row:', row.id);
                      handleRemoveRow(row.id);
                    }}
                    className="w-7 h-7 rounded-full bg-slate-50 hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all flex items-center justify-center"
                  >
                    <Trash2 size={14} strokeWidth={2.5} />
                  </button>

                  {/* 펼치기 버튼 (접혔을 때만 표시) */}
                  {isCollapsed && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        toggleRowCollapse(row.id);
                      }}
                      className="px-2 py-1 rounded-lg text-[10px] font-[800] text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 transition-all flex items-center gap-1"
                    >
                      펼치기
                      <ChevronDown size={12} />
                    </button>
                  )}
                </div>
              </div>

              {/* Content area when expanded */}
              {!isCollapsed && (
                <>
                  <div className="space-y-3">
                    <div className="grid grid-cols-12 gap-2">
                      <div className="col-span-4">
                        <label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider block mb-1 ml-1">
                          평단가
                        </label>
                        <Input
                          placeholder="0"
                          value={formatNumber(row.price)}
                          onChange={(e) => updateRow(row.id, "price", e.target.value)}
                          className="bg-slate-50 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[700] h-10 rounded-xl px-3"
                        />
                      </div>
                      <div className="col-span-3">
                        <label className="text-[10px] font-[800] text-slate-400 uppercase tracking-wider block mb-1 ml-1">
                          수량
                        </label>
                        <Input
                          placeholder="0"
                          value={formatNumber(row.qty)}
                          onChange={(e) => updateRow(row.id, "qty", e.target.value)}
                          className="bg-slate-50 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[700] h-10 rounded-xl px-3"
                        />
                      </div>
                      <div className="col-span-5">
                        <label className="text-[10px] font-[800] text-[var(--color-primary)] uppercase tracking-wider block mb-1 ml-1 font-bold">
                          평가 금액
                        </label>
                        <Input
                          placeholder="0"
                          value={formatNumber(row.totalValue)}
                          onChange={(e) => updateRow(row.id, "totalValue", e.target.value)}
                          className="bg-[var(--color-secondary)]/30 border-transparent focus:bg-white focus:border-[var(--color-primary)] text-[13px] font-[800] h-10 rounded-xl px-3 text-[var(--color-primary)]"
                        />
                      </div>
                    </div>
                  </div>

                  {/* 접기/펼치기 버튼 - 우측 하단 */}
                  <div className="flex justify-end mt-3 pt-3 border-t border-slate-50">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        toggleRowCollapse(row.id);
                      }}
                      className="px-2 py-1 rounded-lg text-[10px] font-[800] text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 transition-all flex items-center gap-1"
                    >
                      접기
                      <ChevronDown size={12} className="rotate-180" />
                    </button>
                  </div>
                </>
              )}
            </motion.div>
          );
          })}
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleAddRow();
            }}
            className="mt-4 w-full py-3 rounded-2xl bg-white border-2 border-[var(--color-primary)]/20 border-dashed flex items-center justify-center gap-2 text-[var(--color-primary)] hover:bg-[var(--color-secondary)]/30 transition-all font-[800] text-[13px] group cursor-pointer"
          >
            <Plus size={16} strokeWidth={3} className="group-hover:rotate-90 transition-transform duration-300" />
            종목 추가하기
          </button>
        </div>
      </div>

      {/* Fixed Button Area */}
      <div className="flex-shrink-0 border-t border-gray-100 bg-white">
        <div className="w-full max-w-md mx-auto p-6">
          {hasUnmappedRows && (
            <div className="mb-2 text-center text-[12px] font-[800] text-red-600">
              매핑되지 않은 종목이 있어 다음 단계로 진행할 수 없습니다.
            </div>
          )}
          <Button
            size="lg"
            className={cn(
              "w-full h-14 text-[16px] font-[900] rounded-2xl transition-all shadow-lg cursor-pointer",
              canSubmit ? "bg-[var(--color-primary)] hover:bg-[#00B34E] text-white shadow-[var(--color-primary)]/20" : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
            onClick={(e) => {
              e.stopPropagation();
              handleSubmit();
            }}
            disabled={!canSubmit}
          >
            {submitLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
