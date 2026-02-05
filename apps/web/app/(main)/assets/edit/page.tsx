"use client";

import { usePortfolioStore } from "@/lib/store";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { BackButton } from "@/components/ui/BackButton";
import { cn } from "@/lib/utils";
import { ArrowLeft, Save } from "lucide-react";

export default function AssetEditPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const positionId = searchParams.get("positionId");

  const assets = usePortfolioStore((state) => state.assets);
  const updateAsset = usePortfolioStore((state) => state.updateAsset);

  const asset = assets.find((a) => a.positionId === positionId);

  const [quantity, setQuantity] = useState<string>("");
  const [avgPrice, setAvgPrice] = useState<string>("");
  const [currency, setCurrency] = useState<"KRW" | "USD">("KRW");

  useEffect(() => {
    if (asset) {
      setQuantity(asset.quantity.toString());
      setAvgPrice(asset.avgPrice.toString());
      setCurrency(asset.currency);
    }
  }, [asset]);

  if (!positionId || !asset) {
    return (
      <div className="container-custom py-10">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">자산을 찾을 수 없습니다</h1>
          <p className="text-slate-500 mb-6">요청하신 자산이 존재하지 않습니다.</p>
          <Button onClick={() => router.push("/dashboard")}>대시보드로 돌아가기</Button>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    const parsedQuantity = parseFloat(quantity);
    const parsedAvgPrice = parseFloat(avgPrice);

    if (isNaN(parsedQuantity) || parsedQuantity <= 0) {
      alert("유효한 수량을 입력해주세요.");
      return;
    }

    if (isNaN(parsedAvgPrice) || parsedAvgPrice <= 0) {
      alert("유효한 평단가를 입력해주세요.");
      return;
    }

    updateAsset(positionId, {
      quantity: parsedQuantity,
      avgPrice: parsedAvgPrice,
      currency,
    });

    router.push("/dashboard");
  };

  const handleCancel = () => {
    router.back();
  };

  const formatNumber = (val: string) => {
    if (!val) return "";
    const num = val.replace(/[^0-9.]/g, "");
    return num;
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="container-custom py-10">
        <header className="mb-8">
          <div className="mb-4">
            <BackButton />
          </div>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-2xl font-black text-slate-400">
              {asset.ticker.charAt(0)}
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                {asset.name}
              </h1>
              <p className="text-slate-500 font-semibold">
                {asset.ticker} · {asset.market} ({asset.national})
              </p>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto">
          <div className="bg-white p-8 rounded-2xl border border-slate-100">
            <h2 className="text-xl font-bold mb-6">보유 정보 수정</h2>

            <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              {/* 수량 */}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  보유 수량
                </label>
                <Input
                  type="text"
                  value={quantity}
                  onChange={(e) => setQuantity(formatNumber(e.target.value))}
                  placeholder="예: 100"
                />
                <p className="text-xs text-slate-400 mt-1">소수점 가능</p>
              </div>

              {/* 평단가 */}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  평균 매입가
                </label>
                <Input
                  type="text"
                  value={avgPrice}
                  onChange={(e) => setAvgPrice(formatNumber(e.target.value))}
                  placeholder="예: 169100"
                />
                <p className="text-xs text-slate-400 mt-1">매입 평균 가격</p>
              </div>
            </div>

            {/* 통화 */}
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">
                기준 통화
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setCurrency("KRW")}
                  className={cn(
                    "flex-1 px-4 py-2.5 rounded-xl border-2 font-bold transition-all text-sm",
                    currency === "KRW"
                      ? "border-[var(--color-primary)] bg-[var(--color-secondary)] text-[var(--color-primary)]"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  )}
                >
                  ₩ 원화 (KRW)
                </button>
                <button
                  type="button"
                  onClick={() => setCurrency("USD")}
                  className={cn(
                    "flex-1 px-4 py-2.5 rounded-xl border-2 font-bold transition-all text-sm",
                    currency === "USD"
                      ? "border-[var(--color-primary)] bg-[var(--color-secondary)] text-[var(--color-primary)]"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  )}
                >
                  $ 달러 (USD)
                </button>
              </div>
            </div>

            {/* 미리보기 */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <h3 className="text-sm font-bold text-slate-600 mb-2">미리보기</h3>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">보유 수량</span>
                  <span className="font-bold text-slate-900">
                    {quantity || "0"}주
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">평단가</span>
                  <span className="font-bold text-slate-900">
                    {currency === "USD" ? "$" : "₩"}
                    {parseFloat(avgPrice || "0").toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between pt-1.5 border-t border-slate-200">
                  <span className="text-slate-700 font-bold">총 투자금액</span>
                  <span className="font-bold text-[var(--color-primary)]">
                    {currency === "USD" ? "$" : "₩"}
                    {(
                      parseFloat(quantity || "0") * parseFloat(avgPrice || "0")
                    ).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* 버튼 */}
            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                onClick={handleCancel}
                className="flex-1"
              >
                취소
              </Button>
              <Button onClick={handleSave} className="flex-1">
                <Save size={16} className="mr-2" />
                저장
              </Button>
            </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
