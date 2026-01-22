"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { TrendingUp, Menu, X, ArrowRight, Search, User, PieChart, Monitor, HelpCircle, FileText, LogOut } from "lucide-react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/lib/store";
import { useDebounce } from "@/lib/hooks";
import { searchAssets } from "@/lib/api/asset";
import type { AssetSearchResponse } from "@/types/asset";

export function GlobalNavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const isLanding = pathname === "/";
  const isDashboard = pathname === "/dashboard";
  
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  
  // Asset Search State
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<AssetSearchResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  const { isLoggedIn, user, logout, checkAuth } = useAuthStore();

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Close menu on route change
  useEffect(() => {
    setIsMenuOpen(false);
  }, [pathname]);

  // Handle search term changes
  useEffect(() => {
    if (debouncedSearchTerm) {
      setIsLoading(true);
      searchAssets(debouncedSearchTerm)
        .then(results => {
          setSearchResults(results);
        })
        .catch(error => {
          console.error("Search failed:", error);
          setSearchResults([]);
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setSearchResults([]);
    }
  }, [debouncedSearchTerm]);

  // Reset search when closing
  useEffect(() => {
    if (!isSearchOpen) {
      setSearchTerm("");
      setSearchResults([]);
    }
  }, [isSearchOpen]);

  const handleResultClick = (assetId: number) => {
    setIsSearchOpen(false);
    router.push(`/assets/${assetId}`);
  };

  const userDisplayName = user ? (user.displayName || user.email) : "로그인이 필요합니다";

  return (
    <>
      <nav className={cn(
        "fixed top-0 left-0 right-0 z-50",
        "bg-white/80 backdrop-blur-xl"
      )}>
        <div className="container-custom h-[72px] flex items-center justify-between">
          
          {/* Left Side: Logo + Links */}
          <div className="flex items-center gap-16">
             {/* Logo */}
             <Link href="/" className="flex items-center gap-2.5 group z-50 relative hover:scale-[1.02] transition-transform">
               <TrendingUp size={28} className="text-[var(--color-primary)] stroke-[3px]" />
               <span className="font-[900] text-2xl tracking-tighter text-slate-900 leading-none">
                 PortRally
               </span>
             </Link>

              {/* Links (Desktop) - Refined Typography */}
              {!isDashboard && (
                <div className="hidden md:flex items-center gap-10">
                  <Link href="/features" className="text-[15px] font-[800] text-slate-500 hover:text-black tracking-tight transition-all relative group/link">
                    기능 소개
                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[var(--color-primary)] transition-all duration-300 group-hover/link:w-full" />
                  </Link>
                  <Link href="/pricing" className="text-[15px] font-[800] text-slate-500 hover:text-black tracking-tight transition-all relative group/link">
                    가격 정책
                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[var(--color-primary)] transition-all duration-300 group-hover/link:w-full" />
                  </Link>
                </div>
              )}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4 flex-1 justify-end">
            {isDashboard && (
              <div className="relative">
                <button
                  onClick={() => setIsSearchOpen(!isSearchOpen)}
                  className="flex items-center gap-2.5 px-5 h-11 bg-slate-50 border border-slate-100 rounded-full text-slate-400 hover:bg-slate-100 transition-all w-full max-w-[160px] sm:max-w-[200px]"
                  aria-label="Search assets"
                >
                  <Search size={18} strokeWidth={2.5} />
                  <span className="text-[13px] font-[700]">종목 AI분석</span>
                </button>

                {/* Autocomplete Dropdown */}
                <AnimatePresence>
                  {isSearchOpen && (
                    <>
                      {/* Backdrop */}
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsSearchOpen(false)}
                      />
                      <motion.div
                        initial={{ opacity: 0, y: -8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -8, scale: 0.96 }}
                        transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
                        className="absolute top-[calc(100%+8px)] right-0 w-[280px] sm:w-[320px] bg-white rounded-2xl border border-slate-100 shadow-[0_20px_40px_-12px_rgba(0,0,0,0.15)] z-50 overflow-hidden"
                        style={{ height: 'auto', maxHeight: '70vh' }}
                      >
                        {/* Search Input */}
                        <div className="p-3 border-b border-slate-50">
                          <div className="flex items-center gap-2.5 px-3 h-10 bg-slate-50 rounded-xl">
                            <Search size={16} strokeWidth={2.5} className="text-slate-300" />
                            <input
                              type="text"
                              placeholder="종목명 또는 티커 검색..."
                              className="flex-1 bg-transparent text-[13px] font-[700] text-slate-900 placeholder:text-slate-300 outline-none"
                              autoFocus
                              value={searchTerm}
                              onChange={(e) => setSearchTerm(e.target.value)}
                            />
                          </div>
                        </div>

                        {/* Autocomplete Results */}
                        <div className="p-2 space-y-0.5 overflow-y-auto">
                          {isLoading ? (
                            <div className="text-center p-4 text-xs text-slate-400 font-semibold">로딩 중...</div>
                          ) : searchResults.length > 0 ? (
                            searchResults.map(asset => (
                              <div
                                key={asset.assetId}
                                onClick={() => handleResultClick(asset.assetId)}
                                className="px-3 py-2.5 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors flex items-center justify-between group"
                              >
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-[11px] font-[900] text-slate-400">
                                    {asset.symbol.charAt(0)}
                                  </div>
                                  <div>
                                    <div className="text-[13px] font-[800] text-slate-900">{asset.name}</div>
                                    <div className="text-[11px] font-[700] text-slate-400">{asset.symbol} · {asset.market}</div>
                                  </div>
                                </div>
                                <ArrowRight size={14} className="text-slate-200 group-hover:text-slate-400 transition-colors" />
                              </div>
                            ))
                          ) : searchTerm && !isLoading ? (
                            <div className="text-center p-4 text-xs text-slate-400 font-semibold">검색 결과가 없습니다.</div>
                          ) : null}
                        </div>
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>
              </div>
            )}
            
            {isDashboard ? (
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => setIsMenuOpen(true)}
                  className="p-2.5 text-slate-500 hover:text-slate-900 hover:bg-slate-50 rounded-full transition-all"
                >
                  <Menu size={24} />
                </button>
              </div>
            ) : (
              <>
                <Link href="/login" className="block">
                  <Button size="sm" className="rounded-full px-6 sm:px-8 font-[800] bg-black text-white hover:bg-slate-800 shadow-[0_12px_24px_-8px_rgba(0,0,0,0.2)] hover:shadow-[0_16px_32px_-8px_rgba(0,0,0,0.3)] hover:-translate-y-0.5 transition-all h-10 sm:h-11 text-[13px] sm:text-sm">
                    시작하기
                  </Button>
                </Link>

                <button 
                  onClick={() => setIsMenuOpen(true)}
                  className="p-2 -mr-2 text-slate-400 hover:text-slate-900 rounded-full transition-colors ml-1 md:hidden active:scale-90"
                >
                   <Menu size={26} />
                </button>
                
                {!isLanding && (
                   <button 
                     onClick={() => setIsMenuOpen(true)}
                     className="hidden md:block p-2.5 -mr-2 text-slate-500 hover:text-slate-900 hover:bg-slate-50 rounded-full transition-all ml-2"
                   >
                      <Menu size={24} />
                   </button>
                )}
              </>
            )}
          </div>
        </div>
      </nav>
      {/* Spacer to prevent layout shift - Not shown on Landing */}
      {!isLanding && <div className="h-[72px] shrink-0" />}

      {/* Sidebar Overlay */}
      <AnimatePresence>
        {isMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMenuOpen(false)}
              className="fixed inset-0 z-[60] bg-black/30 backdrop-blur-md transition-all"
            />
            
            {/* Drawer */}
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 250 }}
              className="fixed top-0 right-0 bottom-0 w-full sm:w-[320px] bg-white z-[70] shadow-[-40px_0_100px_rgba(0,0,0,0.1)] flex flex-col pt-safe overflow-hidden"
            >
               {/* Drawer Header - Refined */}
               <div className="h-[72px] flex items-center justify-between px-10">
                  <div className="flex items-center gap-2.5">
                    <TrendingUp size={22} className="text-[var(--color-primary)] stroke-[3px]" />
                    <span className="font-[900] text-xl tracking-tighter text-slate-900 leading-none">
                      PortRally
                    </span>
                  </div>
                  <button 
                    onClick={() => setIsMenuOpen(false)}
                    className="w-12 h-12 flex items-center justify-center -mr-3 text-slate-300 hover:text-slate-900 transition-all active:scale-90"
                  >
                    <X size={28} strokeWidth={1.5} />
                  </button>
               </div>

               {/* Drawer Content */}
               <div className="flex-1 flex flex-col overflow-y-auto no-scrollbar px-10 py-6">
                  {isLanding ? (
                    /* Case A: Landing Page Menu - Ultra Minimal */
                    <div className="flex flex-col gap-12 flex-1 pt-8">
                      <div className="space-y-10">
                        <Link 
                          href="/features" 
                          onClick={() => setIsMenuOpen(false)} 
                          className="group flex flex-col gap-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-3xl font-[900] tracking-tighter text-slate-900 group-hover:text-[var(--color-primary)] transition-colors">
                              기능 소개
                            </span>
                            <ArrowRight size={24} className="text-slate-200 group-hover:text-[var(--color-primary)] group-hover:translate-x-1 transition-all" />
                          </div>
                          <span className="text-xs font-bold text-slate-400">당신을 위한 스마트한 투자 분석</span>
                        </Link>
                        
                        <Link 
                          href="/pricing" 
                          onClick={() => setIsMenuOpen(false)} 
                          className="group flex flex-col gap-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-3xl font-[900] tracking-tighter text-slate-900 group-hover:text-[var(--color-primary)] transition-colors">
                              가격 정책
                            </span>
                            <ArrowRight size={24} className="text-slate-200 group-hover:text-[var(--color-primary)] group-hover:translate-x-1 transition-all" />
                          </div>
                          <span className="text-xs font-bold text-slate-400">합리적인 플랜으로 시작하세요</span>
                        </Link>
                      </div>

                      <div className="mt-auto pb-16">
                        <Link href="/login" onClick={() => setIsMenuOpen(false)} className="block">
                          <Button className="w-full h-16 rounded-[24px] bg-black text-white font-[900] text-lg shadow-[0_20px_40px_-12px_rgba(0,0,0,0.3)] hover:bg-slate-800 active:scale-[0.98] transition-all duration-300">
                            지금 시작하기
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ) : (
                    /* Case B: App Internal Menu - Streamlined */
                    <div className="space-y-6 pt-4">
                      <div className="text-[11px] font-[900] text-slate-300 uppercase tracking-[0.2em] mb-8">설정 및 관리</div>
                      
                      <button className="w-full text-left group">
                           <div className="flex items-center gap-3 mb-1 text-slate-900 group-hover:text-[var(--color-primary)] transition-colors">
                             <User size={20} className="text-slate-400 group-hover:text-[var(--color-primary)]" />
                             <span className="text-lg font-[900] tracking-tight">계정 관리</span>
                           </div>
                           <span className="text-[11px] font-[700] text-slate-400 pl-8">{isLoggedIn ? userDisplayName : "로그인이 필요합니다"}</span>
                        </button>

                        <button className="w-full text-left group">
                           <div className="flex items-center gap-3 mb-1 text-slate-900 group-hover:text-[var(--color-primary)] transition-colors">
                             <PieChart size={20} className="text-slate-400 group-hover:text-[var(--color-primary)]" />
                             <span className="text-lg font-[900] tracking-tight">투자 성향 관리</span>
                           </div>
                           <span className="text-[11px] font-[700] text-slate-400 pl-8">성장 지향적 투자자</span>
                        </button>

                        <button className="w-full text-left group">
                           <div className="flex items-center gap-3 mb-1 text-slate-900 group-hover:text-[var(--color-primary)] transition-colors">
                             <Monitor size={20} className="text-slate-400 group-hover:text-[var(--color-primary)]" />
                             <span className="text-lg font-[900] tracking-tight">표시 설정</span>
                           </div>
                           <span className="text-[11px] font-[700] text-slate-400 pl-8">통화, 언어, 테마</span>
                        </button>

                      {/* Footer Menu */}
                      <div className="pt-8 border-t border-slate-50 space-y-4">
                        <button className="w-full text-left flex items-center gap-3 text-slate-500 hover:text-slate-900 transition-colors">
                          <HelpCircle size={18} />
                          <span className="text-[13px] font-[800]">고객 문의</span>
                        </button>

                        <button className="w-full text-left flex items-center gap-3 text-slate-500 hover:text-slate-900 transition-colors">
                          <FileText size={18} />
                          <span className="text-[13px] font-[800]">약관 및 정책</span>
                        </button>

                        {isLoggedIn && (
                          <button 
                            onClick={() => logout()}
                            className="w-full text-left flex items-center gap-3 text-red-400 hover:text-red-500 transition-colors pt-4"
                          >
                            <LogOut size={18} />
                            <span className="text-[13px] font-[800]">로그아웃</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}
               </div>

               {/* Drawer Footer - Modernized */}
               <div className="p-10 bg-slate-50/50 backdrop-blur-sm space-y-4 border-t border-slate-100/50">
                  {!isLanding && (
                    <div className="flex gap-6 text-[11px] font-[900] text-slate-400 tracking-wider uppercase">
                      <Link href="#" className="hover:text-slate-900 transition-colors">Support</Link>
                      <Link href="#" className="hover:text-slate-900 transition-colors">Legal</Link>
                    </div>
                  )}
                  <div className="text-[10px] font-bold text-slate-300 tracking-tight">
                    © 2026 PortRally.
                  </div>
               </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
