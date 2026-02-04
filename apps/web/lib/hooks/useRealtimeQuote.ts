"use client";

import { useEffect, useRef, useState } from "react";
import type {
  ConnectionStatus,
  QuoteStreamDto,
  UseRealtimeQuoteReturn,
} from "@/types/quote";
import { getQuoteStreamUrl } from "@/lib/api/quote";

interface UseRealtimeQuoteOptions {
  enabled?: boolean;
  maxRetries?: number;
  baseRetryDelay?: number;
}

const DEFAULT_OPTIONS: Required<UseRealtimeQuoteOptions> = {
  enabled: true,
  maxRetries: 10,
  baseRetryDelay: 1000,
};

const MAX_RETRY_DELAY = 30000; // 30초

/**
 * 실시간 시세 구독 Hook
 *
 * EventSource를 사용하여 SSE 연결을 관리하고,
 * 자동 재연결 및 에러 처리를 수행합니다.
 *
 * @param identifier - 종목 식별자 (예: "KR:KOSPI:005930")
 * @param options - 옵션
 * @returns 시세 데이터, 연결 상태, 에러, 재연결 함수
 */
export function useRealtimeQuote(
  identifier: string | null,
  options?: UseRealtimeQuoteOptions
): UseRealtimeQuoteReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  const [quote, setQuote] = useState<QuoteStreamDto | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualCloseRef = useRef(false);

  const connect = () => {
    if (!identifier || !opts.enabled) {
      setStatus("idle");
      return;
    }

    // 기존 연결 정리
    if (eventSourceRef.current) {
      isManualCloseRef.current = true;
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // 재시도 타이머 정리
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }

    setStatus("connecting");
    setError(null);

    try {
      const url = getQuoteStreamUrl(identifier);
      const eventSource = new EventSource(url);

      eventSource.onopen = () => {
        setStatus("connected");
        setError(null);
        retryCountRef.current = 0; // 연결 성공 시 재시도 카운트 리셋
        isManualCloseRef.current = false;
      };

      eventSource.addEventListener("quote-update", (event) => {
        try {
          const data = JSON.parse(event.data) as QuoteStreamDto;
          setQuote(data);
        } catch (err) {
          console.error("Failed to parse quote data:", err);
        }
      });

      eventSource.onerror = () => {
        // 수동으로 닫은 경우 재연결하지 않음
        if (isManualCloseRef.current) {
          return;
        }

        eventSource.close();
        eventSourceRef.current = null;

        // 최대 재시도 횟수 초과
        if (retryCountRef.current >= opts.maxRetries) {
          setStatus("error");
          setError("연결 실패: 최대 재시도 횟수를 초과했습니다.");
          return;
        }

        // Exponential backoff 계산
        const delay = Math.min(
          opts.baseRetryDelay * Math.pow(2, retryCountRef.current),
          MAX_RETRY_DELAY
        );

        setStatus("disconnected");
        setError(`연결 끊김. ${Math.ceil(delay / 1000)}초 후 재시도...`);

        retryCountRef.current++;

        retryTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      eventSourceRef.current = eventSource;
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "알 수 없는 오류");
    }
  };

  const reconnect = () => {
    retryCountRef.current = 0;
    setError(null);
    connect();
  };

  useEffect(() => {
    connect();

    return () => {
      isManualCloseRef.current = true;

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [identifier, opts.enabled]);

  return {
    quote,
    status,
    error,
    reconnect,
  };
}
