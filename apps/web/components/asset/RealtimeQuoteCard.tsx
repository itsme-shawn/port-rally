"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { useRealtimeQuote } from "@/lib/hooks";
import { PriceChangeIndicator } from "./PriceChangeIndicator";

interface RealtimeQuoteCardProps {
  identifier: string;
  initialSymbol: string;
}

/**
 * 실시간 시세 카드 컴포넌트
 *
 * SSE를 통해 실시간 시세를 수신하여 표시합니다.
 */
export function RealtimeQuoteCard({
  identifier,
  initialSymbol,
}: RealtimeQuoteCardProps) {
  const { quote, status, error, reconnect } = useRealtimeQuote(identifier);
  const [previousPrice, setPreviousPrice] = useState<string | null>(null);
  const [priceDirection, setPriceDirection] = useState<"up" | "down" | null>(
    null
  );

  // 가격 변동 감지 및 애니메이션
  useEffect(() => {
    if (quote?.price && previousPrice && quote.price !== previousPrice) {
      const prevNum = parseFloat(previousPrice);
      const currNum = parseFloat(quote.price);

      if (currNum > prevNum) {
        setPriceDirection("up");
      } else if (currNum < prevNum) {
        setPriceDirection("down");
      }

      // 500ms 후 애니메이션 제거
      const timer = setTimeout(() => {
        setPriceDirection(null);
      }, 500);

      return () => clearTimeout(timer);
    }

    if (quote?.price) {
      setPreviousPrice(quote.price);
    }
  }, [quote?.price]);

  // 연결 상태 표시
  const renderConnectionStatus = () => {
    switch (status) {
      case "connecting":
        return (
          <span className="text-sm text-gray-500">
            연결 중<span className="animate-pulse">...</span>
          </span>
        );
      case "connected":
        return (
          <span className="flex items-center gap-1 text-sm text-green-600">
            <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></span>
            실시간
          </span>
        );
      case "disconnected":
        return (
          <span className="text-sm text-yellow-600">재연결 시도 중...</span>
        );
      case "error":
        return (
          <div className="flex items-center gap-2">
            <span className="text-sm text-red-600">연결 실패</span>
            <button
              onClick={reconnect}
              className="text-sm text-blue-600 hover:underline"
            >
              다시 시도
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  // 가격 포맷팅
  const formatPrice = (price: string) => {
    return parseFloat(price).toLocaleString("ko-KR");
  };

  // 거래량 포맷팅
  const formatVolume = (volume: number) => {
    return volume.toLocaleString("ko-KR");
  };

  return (
    <Card
      className={`transition-colors duration-300 ${
        priceDirection === "up"
          ? "bg-red-50"
          : priceDirection === "down"
            ? "bg-blue-50"
            : ""
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {quote?.symbol || initialSymbol}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {quote?.exchange} · {quote?.national}
            {quote?.provider && ` · ${quote.provider}`}
          </p>
        </div>
        <div>{renderConnectionStatus()}</div>
      </div>

      {error && status !== "connected" && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">{error}</p>
        </div>
      )}

      {quote ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 현재가 및 변동 */}
          <div>
            <div className="text-4xl font-bold text-gray-900 mb-2">
              {formatPrice(quote.price)}
              <span className="text-lg text-gray-500 ml-2">KRW</span>
            </div>
            <PriceChangeIndicator
              change={quote.change}
              changeRate={quote.changeRate}
              className="text-lg"
            />
          </div>

          {/* 거래 정보 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500 mb-1">시가</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatPrice(quote.open)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">고가</p>
              <p className="text-lg font-semibold text-red-600">
                {formatPrice(quote.high)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">저가</p>
              <p className="text-lg font-semibold text-blue-600">
                {formatPrice(quote.low)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">거래량</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatVolume(quote.volume)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          {status === "connecting" ? (
            <p>시세 정보를 불러오는 중...</p>
          ) : status === "error" ? (
            <p>시세 정보를 불러올 수 없습니다.</p>
          ) : (
            <p>시세 정보가 없습니다.</p>
          )}
        </div>
      )}

      {quote?.updatedAt && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-400 text-right">
            마지막 업데이트:{" "}
            {new Date(quote.updatedAt).toLocaleString("ko-KR")}
          </p>
        </div>
      )}
    </Card>
  );
}
