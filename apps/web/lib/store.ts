import { create } from 'zustand';
import { getCurrentUser, UserProfile } from './api/auth';

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
