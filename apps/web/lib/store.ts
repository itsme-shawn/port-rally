import { create } from 'zustand';

export interface Asset {
  id: string;
  ticker: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currency: 'KRW' | 'USD';
  currentPrice?: number;
}

interface PortfolioState {
  hasInvestment: boolean | null;
  assets: Asset[];
  setHasInvestment: (has: boolean) => void;
  addAsset: (asset: Asset) => void;
  removeAsset: (id: string) => void;
  reset: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  hasInvestment: null,
  assets: [],
  setHasInvestment: (has) => set({ hasInvestment: has }),
  addAsset: (asset) => set((state) => {
    // Prevent duplicate IDs
    if (state.assets.some((a) => a.id === asset.id)) {
      return state;
    }
    return { assets: [...state.assets, asset] };
  }),
  removeAsset: (id) => set((state) => ({ assets: state.assets.filter((a) => a.id !== id) })),
  reset: () => set({ hasInvestment: null, assets: [] }),
}));
