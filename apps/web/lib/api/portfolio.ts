import { apiClient } from '@/lib/api-client';

export interface InitialPosition {
  assetId: number;
  symbol: string;
  name: string;
  market: string;
  quantity: number;
  averageCost: number;
  positionValue: number;
  currency: string;
  purchaseDate?: string;
  broker?: string;
  accountAlias?: string;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  investmentType?: string;
  isPrimary?: boolean;
  initialPositions: InitialPosition[];
}

export interface PortfolioResponse {
  portfolioId: string;
  userId: string;
  name: string;
  description?: string;
  investmentType?: string;
  isPrimary: boolean;
  baseCurrency: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 포트폴리오 생성
 */
export async function createPortfolio(
  request: CreatePortfolioRequest
): Promise<PortfolioResponse> {
  return apiClient<PortfolioResponse>('/api/v1/portfolio', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * 포트폴리오 존재 여부 확인
 */
export async function checkPortfolio(): Promise<{ hasPortfolio: boolean }> {
  return apiClient<{ hasPortfolio: boolean }>('/api/v1/portfolio/check');
}

/**
 * 포트폴리오 목록 조회
 */
export async function getPortfolios(): Promise<PortfolioResponse[]> {
  return apiClient<PortfolioResponse[]>('/api/v1/portfolio');
}

/**
 * 포트폴리오 상세 조회
 */
export async function getPortfolio(portfolioId: string): Promise<PortfolioResponse> {
  return apiClient<PortfolioResponse>(`/api/v1/portfolio/${portfolioId}`);
}

// === AI Insights ===

export interface AiInsight {
  type: 'warning' | 'positive' | 'neutral';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
}

export interface AiRecommendation {
  action: 'rebalance' | 'add' | 'reduce' | 'hold';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

export interface SectorDistribution {
  name: string;
  percentage: number;
  color: string;
}

export interface RiskMetrics {
  level: string;
  volatility: number;
  sharpeRatio: number;
  beta: number;
  maxDrawdown: number;
}

export interface PortfolioAiInsightResponse {
  portfolioInsightId: string;
  portfolioId: string;
  insightType: string;
  analysisDate: string;
  title: string;
  executiveSummary: string;
  fullReport: string;
  healthScore: number;
  riskScore: number;
  diversificationScore: number;
  performanceScore: number;
  insightsData: AiInsight[];
  recommendationsData: AiRecommendation[];
  sectorsData: SectorDistribution[];
  riskMetrics: RiskMetrics;
  generatedBy: string;
  generatedAt: string;
}

/**
 * 최신 AI 분석 결과 조회
 */
export async function getLatestAiInsight(portfolioId: string): Promise<PortfolioAiInsightResponse | null> {
  try {
    return await apiClient<PortfolioAiInsightResponse>(`/api/v1/portfolio/${portfolioId}/ai/latest`);
  } catch (error) {
    console.error('Failed to fetch latest AI insight:', error);
    return null;
  }
}

/**
 * AI 분석 실행 요청
 */
export async function analyzePortfolio(portfolioId: string): Promise<{ job_id: string; status: string }> {
  return apiClient<{ job_id: string; status: string }>(`/api/v1/portfolio/${portfolioId}/ai/analyze`, {
    method: 'POST',
  });
}
