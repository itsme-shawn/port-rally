"use client";

import { motion } from "framer-motion";
import { TrendingUp, ArrowUpRight, Wallet, PieChart } from "lucide-react";
export function PhoneMockup() {
  return (
    <div className="relative mx-auto w-[280px] h-[580px] bg-gray-900 rounded-[3rem] ring-8 ring-gray-900 shadow-2xl overflow-hidden border-[6px] border-gray-800 z-10">
      {/* Notch */}
      <div className="absolute top-0 inset-x-0 h-6 bg-gray-900 z-20 rounded-b-xl w-32 mx-auto" />
      
      {/* Screen Content (Light Mode) */}
      <div className="w-full h-full bg-white flex flex-col pt-10 px-4 pb-4 overflow-hidden relative">
        {/* Status Bar Mock */}
        <div className="flex justify-between items-center text-[10px] font-bold text-gray-400 mb-4 px-2">
          <span>9:41</span>
          <div className="flex gap-1">
             <div className="h-2 w-2 rounded-full bg-black/20" />
             <div className="h-2 w-2 rounded-full bg-black/20" />
             <div className="h-2 w-4 rounded-full bg-black" />
          </div>
        </div>

        {/* App Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-1.5">
             <div className="w-6 h-6 bg-black rounded-full flex items-center justify-center text-white">
                <TrendingUp size={14} />
             </div>
             <span className="font-bold text-sm tracking-tight text-black">PortRally</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-gray-100" />
        </div>

        {/* Total Balance Card */}
        <div className="bg-black text-white rounded-3xl p-5 mb-4 shadow-lg relative overflow-hidden">
           <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--color-primary)] opacity-20 blur-2xl rounded-full translate-x-10 -translate-y-10" />
           <div className="relative z-10">
             <div className="text-xs text-gray-400 font-medium mb-1">총 자산</div>
             <div className="text-2xl font-[800] tracking-tight mb-2">₩124,500,000</div>
             <div className="flex items-center gap-1 text-[var(--color-primary)] text-xs font-bold bg-white/10 w-fit px-2 py-1 rounded-lg">
               <ArrowUpRight size={12} />
                <span>+12.5% (오늘)</span>
             </div>
           </div>
        </div>

        {/* Chart Area */}
        <div className="flex-1 bg-gray-50 rounded-3xl p-4 border border-gray-100 flex flex-col mb-4">
           <div className="flex justify-between items-center mb-4">
               <span className="text-xs font-bold text-gray-500">내 포트폴리오</span>
              <div className="flex gap-1">
                 {['1D', '1W', '1M'].map(t => (
                    <span key={t} className={`text-[10px] px-2 py-0.5 rounded-full ${t === '1W' ? 'bg-black text-white' : 'text-gray-400'}`}>{t}</span>
                 ))}
              </div>
           </div>
           
           {/* CSS Chart Line */}
           <div className="flex-1 w-full relative flex items-end px-2 pb-2">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 100 50" preserveAspectRatio="none">
                 <motion.path 
                   initial={{ pathLength: 0 }}
                   animate={{ pathLength: 1 }}
                   transition={{ duration: 2, ease: "easeInOut" }}
                   d="M0,50 C20,45 30,30 40,35 C50,40 60,20 80,15 C90,10 100,0 100,0"
                   fill="none"
                   stroke="var(--color-primary)"
                   strokeWidth="3"
                   strokeLinecap="round"
                 />
                 <path 
                   d="M0,50 C20,45 30,30 40,35 C50,40 60,20 80,15 C90,10 100,0 100,0 V50 H0 Z"
                   fill="url(#gradient)"
                   opacity="0.2"
                 />
                 <defs>
                   <linearGradient id="gradient" x1="0" x2="0" y1="0" y2="1">
                     <stop stopColor="var(--color-primary)" stopOpacity="1"/>
                     <stop stopColor="white" stopOpacity="0"/>
                   </linearGradient>
                 </defs>
              </svg>
           </div>
        </div>

        {/* Bottom Nav Mock */}
        <div className="h-14 bg-white border-t border-gray-100 flex items-center justify-around text-gray-300">
           <div className="text-black"><Wallet size={20} /></div>
           <div><PieChart size={20} /></div>
           <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
        </div>

      </div>
    </div>
  );
}
