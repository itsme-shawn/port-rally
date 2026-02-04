interface PriceChangeIndicatorProps {
  change: string;
  changeRate: string;
  className?: string;
}

/**
 * 가격 변동 표시 컴포넌트
 *
 * 상승/하락/보합에 따라 색상과 아이콘을 표시합니다.
 */
export function PriceChangeIndicator({
  change,
  changeRate,
  className = "",
}: PriceChangeIndicatorProps) {
  const changeNum = parseFloat(change);

  if (changeNum > 0) {
    return (
      <span className={`text-red-600 font-semibold ${className}`}>
        ▲ {change} ({changeRate}%)
      </span>
    );
  }

  if (changeNum < 0) {
    return (
      <span className={`text-blue-600 font-semibold ${className}`}>
        ▼ {Math.abs(changeNum).toFixed(2)} ({Math.abs(parseFloat(changeRate)).toFixed(2)}%)
      </span>
    );
  }

  return (
    <span className={`text-gray-600 font-semibold ${className}`}>
      - {change} ({changeRate}%)
    </span>
  );
}
