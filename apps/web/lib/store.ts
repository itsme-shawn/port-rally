import { create } from 'zustand';
import { getCurrentUser, UserProfile } from './api/auth';

export interface Asset {
  positionId: string;  // UUID from positions table (renamed from 'id')
  assetId?: number;    // BIGINT from assets_master table (FK)
  ticker: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currency: 'KRW' | 'USD';
  national: string;
  market: string;
  currentPrice?: number;
  isMapped?: boolean; // OCR 매핑 여부
  matchConfidence?: number;  // OCR 매칭 신뢰도 (0-1)
  ocrRawText?: string;        // OCR 원본 텍스트
}

interface PortfolioState {
  hasInvestment: boolean | null;
  assets: Asset[];
  setHasInvestment: (has: boolean) => void;
  addAsset: (asset: Asset) => void;
  updateAsset: (positionId: string, updates: Partial<Asset>) => void;
  removeAsset: (positionId: string) => void;
  reset: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  hasInvestment: null,
  assets: [],
  setHasInvestment: (has) => set({ hasInvestment: has }),
  addAsset: (asset) => set((state) => {
    // Prevent duplicate position IDs
    if (state.assets.some((a) => a.positionId === asset.positionId)) {
      return state;
    }
    return { assets: [...state.assets, asset] };
  }),
  updateAsset: (positionId, updates) => set((state) => ({
    assets: state.assets.map((a) => a.positionId === positionId ? { ...a, ...updates } : a)
  })),
  removeAsset: (positionId) => set((state) => ({ assets: state.assets.filter((a) => a.positionId !== positionId) })),
  reset: () => set({ hasInvestment: null, assets: [] }),
}));

interface AuthState {
  isLoggedIn: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  checkAuth: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isLoggedIn: false,
  isLoading: true,
  user: null,
  checkAuth: async () => {
    try {
      set({ isLoading: true });
      const user = await getCurrentUser();
      set({ isLoggedIn: true, user, isLoading: false });
    } catch (error) {
      set({ isLoggedIn: false, user: null, isLoading: false });
    }
  },
  logout: () => {
    // In a real app, you might also want to call a logout API endpoint here
    set({ isLoggedIn: false, user: null });
    // Force reload or redirect might be needed depending on auth strategy (cookies)
    window.location.href = "/"; 
  },
}));
