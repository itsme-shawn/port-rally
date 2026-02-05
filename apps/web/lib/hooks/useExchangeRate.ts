import { useState, useEffect } from 'react';

const EXCHANGE_RATE_API = 'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json';
const CACHE_KEY = 'exchange_rate_usd_krw';
const CACHE_DURATION = 3600000; // 1시간

interface ExchangeRateCache {
  rate: number;
  timestamp: number;
}

/**
 * USD to KRW 환율을 가져오는 Hook
 * - 1시간마다 자동 갱신
 * - localStorage에 캐싱
 * - 네트워크 오류시 기본값(1380) 사용
 */
export function useExchangeRate() {
  const [rate, setRate] = useState<number>(1380); // 기본값
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchExchangeRate = async () => {
      try {
        // 1. 캐시 확인
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const cachedData: ExchangeRateCache = JSON.parse(cached);
          const now = Date.now();

          // 캐시가 유효하면 사용
          if (now - cachedData.timestamp < CACHE_DURATION) {
            setRate(cachedData.rate);
            setIsLoading(false);
            return;
          }
        }

        // 2. API 호출
        const response = await fetch(EXCHANGE_RATE_API);
        if (!response.ok) {
          throw new Error(`Failed to fetch exchange rate: ${response.status}`);
        }

        const data = await response.json();
        const newRate = data.usd?.krw;

        if (!newRate || typeof newRate !== 'number') {
          throw new Error('Invalid exchange rate data');
        }

        // 3. 상태 업데이트 및 캐싱
        setRate(newRate);
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          rate: newRate,
          timestamp: Date.now()
        }));
        setError(null);
      } catch (err) {
        console.error('Exchange rate fetch error:', err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
        // 에러 발생시 캐시된 값이나 기본값 사용
      } finally {
        setIsLoading(false);
      }
    };

    // 초기 로드
    fetchExchangeRate();

    // 1시간마다 갱신
    const interval = setInterval(fetchExchangeRate, CACHE_DURATION);

    return () => clearInterval(interval);
  }, []);

  return { rate, isLoading, error };
}
