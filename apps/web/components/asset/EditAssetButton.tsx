"use client";

import { usePortfolioStore } from "@/lib/store";
import Link from "next/link";
import { Edit2 } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface EditAssetButtonProps {
  identifier: string;  // national:exchange:symbol
}

export function EditAssetButton({ identifier }: EditAssetButtonProps) {
  const assets = usePortfolioStore((state) => state.assets);

  // identifier로부터 종목 정보 추출
  const [national, exchange, symbol] = identifier.split(":");

  // Store에서 해당 자산 찾기 (ticker로 매칭)
  const asset = assets.find(
    (a) => a.ticker === symbol && a.national === national && a.market === exchange
  );

  // 포트폴리오에 없으면 버튼 숨김
  if (!asset) {
    return null;
  }

  return (
    <Link href={`/assets/edit?positionId=${asset.positionId}`}>
      <Button variant="outline" size="sm">
        <Edit2 size={16} className="mr-2" />
        수정
      </Button>
    </Link>
  );
}
