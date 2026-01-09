"use client";

import { PieChart, Zap, ShieldCheck, TrendingUp, Search, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export function FeatureCardChart() {
  return (
    <div className="relative w-full h-full p-6 flex flex-col justify-center">
       <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 w-full max-w-[240px] mx-auto transform rotate-[-2deg] hover:rotate-0 transition-transform duration-300">
          <div className="flex justify-between items-center mb-4">
             <div className="w-8 h-8 bg-green-50 rounded-full flex items-center justify-center text-[var(--color-primary)]">
                <PieChart size={16} />
             </div>
             <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">+24%</span>
          </div>
          <div className="space-y-2">
             <div className="h-2 bg-gray-100 rounded-full w-3/4" />
             <div className="h-2 bg-gray-50 rounded-full w-1/2" />
          </div>
          <div className="mt-4 flex gap-1 h-12 items-end justify-between px-1">
             <div className="w-2 bg-[var(--color-primary)] h-[40%] rounded-t-sm" />
             <div className="w-2 bg-[var(--color-primary)] opacity-40 h-[70%] rounded-t-sm" />
             <div className="w-2 bg-[var(--color-primary)] opacity-60 h-[50%] rounded-t-sm" />
             <div className="w-2 bg-[var(--color-primary)] h-[100%] rounded-t-sm" />
             <div className="w-2 bg-[var(--color-primary)] opacity-30 h-[60%] rounded-t-sm" />
          </div>
       </div>
    </div>
  );
}

export function FeatureCardAI() {
  return (
    <div className="relative w-full h-full p-2 flex flex-col justify-center items-center">
       <div className="relative">
          {/* AI Glowing Effect */}
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full animate-pulse" />
          
          <div className="relative bg-white rounded-3xl shadow-lg border border-blue-100 p-4 w-32 h-32 flex flex-col items-center justify-center gap-3 transform -rotate-3 hover:rotate-0 transition-transform duration-500">
             <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
                <Sparkles size={24} fill="white" className="animate-pulse" />
             </div>
             <div className="w-full space-y-1.5">
                <div className="h-1.5 bg-blue-50 rounded-full w-full" />
                <div className="h-1.5 bg-blue-50 rounded-full w-3/4 mx-auto" />
             </div>
             <div className="absolute -top-2 -right-2 bg-blue-600 text-white text-[8px] font-black px-2 py-1 rounded-lg shadow-md uppercase tracking-tighter">
                AI
             </div>
          </div>
       </div>
    </div>
  );
}

export function FeatureCardSecurity() {
  return (
    <div className="relative w-full h-full p-6 flex flex-col justify-center items-center">
       <div className="w-24 h-24 bg-gradient-to-br from-gray-50 to-white rounded-[2rem] shadow-inner border border-gray-100 flex items-center justify-center mb-4 relative overflow-hidden group">
          <div className="absolute inset-0 bg-green-500/5 group-hover:bg-green-500/10 transition-colors" />
          <ShieldCheck size={40} className="text-gray-900 drop-shadow-sm" />
          <div className="absolute top-2 right-3 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
       </div>
       <div className="flex gap-2">
          <div className="w-2 h-2 rounded-full bg-gray-200" />
          <div className="w-2 h-2 rounded-full bg-gray-200" />
          <div className="w-2 h-2 rounded-full bg-gray-200" />
          <div className="w-2 h-2 rounded-full bg-gray-200" />
       </div>
    </div>
  );
}

export function CompactFeatureCards() {
  const features = [
    { icon: <PieChart size={14} />, title: "통합 관리", color: "bg-green-500" },
    { icon: <Zap size={14} />, title: "AI 진단", color: "bg-blue-600" },
    { icon: <ShieldCheck size={14} />, title: "강력 보안", color: "bg-slate-800" }
  ];

  return (
    <div className="flex justify-center gap-3 w-full px-4 mt-4">
      {features.map((f, i) => (
        <div key={i} className="flex flex-col items-center gap-2 flex-1 max-w-[100px] p-3 rounded-2xl bg-white/50 backdrop-blur-sm border border-slate-200/50 shadow-sm">
          <div className={`${f.color} w-8 h-8 rounded-full flex items-center justify-center text-white shadow-sm`}>
            {f.icon}
          </div>
          <span className="text-[10px] font-[800] text-slate-700 whitespace-nowrap">{f.title}</span>
        </div>
      ))}
    </div>
  );
}
