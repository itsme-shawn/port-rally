export interface QuoteStreamDto {
  symbol: string;
  national: string;
  exchange: string;
  provider?: string;
  price: string;          // BigDecimal → string
  change: string;
  changeRate: string;
  volume: number;
  open: string;
  high: string;
  low: string;
  timestamp: string;
  updatedAt: number;
}

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseRealtimeQuoteReturn {
  quote: QuoteStreamDto | null;
  status: ConnectionStatus;
  error: string | null;
  reconnect: () => void;
}
