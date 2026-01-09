"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { usePortfolioStore } from "@/lib/store";
import { ArrowLeft, Search, PlusCircle, Trash2 } from "lucide-react";
import { motion } from "framer-motion";

export default function ManualAddPage() {
  const router = useRouter();
  const addAsset = usePortfolioStore((state) => state.addAsset);
  
  // Local state for form
  const [rows, setRows] = useState([
    { id: "1", ticker: "", name: "", price: "", qty: "" }
  ]);

  const handleAddRow = () => {
    setRows([...rows, { id: Date.now().toString(), ticker: "", name: "", price: "", qty: "" }]);
  };

  const handleRemoveRow = (id: string) => {
    if (rows.length === 1) return;
    setRows(rows.filter(r => r.id !== id));
  };

  const updateRow = (id: string, field: string, value: string) => {
    setRows(rows.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const handleSubmit = () => {
    // Save to store
    rows.forEach(r => {
      if (r.ticker && r.qty) {
        addAsset({
          id: r.id,
          ticker: r.ticker.toUpperCase(),
          name: r.name || r.ticker, // Fallback name
          avgPrice: Number(r.price) || 0,
          quantity: Number(r.qty) || 0,
          currency: "KRW" // Default for prototype
        });
      }
    });
    router.push("/onboarding/survey");
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="max-w-4xl w-full mx-auto flex-1 flex flex-col">
        <div className="p-4 pt-20 flex items-center justify-center gap-4">
          <span className="font-bold text-lg">자산 직접 입력</span>
        </div>

      <div className="flex-1 p-4 overflow-y-auto pb-24">
        <div className="space-y-6">
           {rows.map((row, index) => (
             <motion.div 
               key={row.id} 
               initial={{ opacity: 0, y: 10 }} 
               animate={{ opacity: 1, y: 0 }}
               className="p-5 rounded-2xl bg-[var(--color-background-subtle)] space-y-4 relative"
             >
                <div className="absolute top-4 right-4">
                  {rows.length > 1 && (
                    <button onClick={() => handleRemoveRow(row.id)} className="text-gray-400 hover:text-red-500">
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>

                <div>
                   <label className="text-xs font-bold text-gray-500 block mb-1">종목명/티커</label>
                   <Input 
                     placeholder="예: 삼성전자, aapl" 
                     value={row.ticker}
                     onChange={(e) => updateRow(row.id, "ticker", e.target.value)}
                     className="bg-white"
                   />
                </div>
                
                <div className="flex gap-4">
                   <div className="flex-1">
                      <label className="text-xs font-bold text-gray-500 block mb-1">매수 수량</label>
                      <Input 
                        type="number" 
                        placeholder="0" 
                        value={row.qty}
                        onChange={(e) => updateRow(row.id, "qty", e.target.value)}
                        className="bg-white"
                      />
                   </div>
                   <div className="flex-1">
                      <label className="text-xs font-bold text-gray-500 block mb-1">평균 단가 (KRW)</label>
                      <Input 
                        type="number" 
                        placeholder="0" 
                        value={row.price}
                        onChange={(e) => updateRow(row.id, "price", e.target.value)}
                        className="bg-white"
                      />
                   </div>
                </div>
             </motion.div>
           ))}
        </div>

        <button 
          onClick={handleAddRow}
          className="mt-6 w-full py-4 flex items-center justify-center gap-2 text-[var(--color-primary)] font-bold rounded-2xl hover:bg-[var(--color-secondary)]/20 transition-colors"
        >
           <PlusCircle /> 종목 추가하기
        </button>
      </div>

      <div className="p-4 bg-white fixed bottom-0 left-0 right-0">
         <Button 
           size="lg" 
           className="w-full h-14 text-lg rounded-2xl"
           onClick={handleSubmit}
         >
           입력 완료
         </Button>
      </div>
      </div>
    </div>
  );
}
