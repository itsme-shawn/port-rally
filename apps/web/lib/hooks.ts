"use client";

import { useState, useEffect } from 'react';

/**
 * 디바운스된 값을 반환하는 커스텀 훅
 * @param value 디바운스할 값
 * @param delay 디바운스 지연 시간 (ms)
 */
export function useDebounce<T>(value: T, delay: number): T {
  // 디바운스된 값을 저장할 상태
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // value가 변경된 후 delay 시간이 지나면 debouncedValue를 업데이트
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // cleanup 함수: 다음 effect가 실행되기 전이나 언마운트 시 타이머를 제거
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]); // value나 delay가 변경될 때만 effect를 다시 실행

  return debouncedValue;
}

export { useRealtimeQuote } from './hooks/useRealtimeQuote';
