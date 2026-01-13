"use client";

import { useRouter } from "next/navigation";
import { useState, useRef, useCallback, useEffect } from "react";
import { Loader2, Upload, X, Plus } from "lucide-react";
import { usePortfolioStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { motion, AnimatePresence } from "framer-motion";
import { BackButton } from "@/components/ui/BackButton";

interface DetectedPosition {
  detectedPositionId: string;
  symbol: string;
  name: string;
  market: string;
  quantity: number;
  averageCost: number;
  currency: string;
  purchaseDate: string;
  broker: string;
  accountAlias: string;
  assetId: number;
  matchConfidence: number;
}

interface ImageUploadResponse {
  imageId: string;
  ocrResultId: string;
  detectedPositions: DetectedPosition[];
}

export default function PhotoUploadPage() {
  const router = useRouter();
  const addAsset = usePortfolioStore((state) => state.addAsset);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // Auto hide toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Clean up previews on unmount
  useEffect(() => {
    return () => {
      previews.forEach(url => URL.revokeObjectURL(url));
    };
  }, []);

  const handleFileSelect = useCallback((selectedFiles: File[]) => {
    const validFiles = selectedFiles.filter(file => file.type.startsWith("image/"));
    if (validFiles.length === 0) return;

    // 중복 체크
    const nonDuplicates = validFiles.filter(newFile => 
      !files.some(existingFile => 
        existingFile.name === newFile.name && existingFile.size === newFile.size
      )
    );

    if (nonDuplicates.length < validFiles.length) {
      setToast("이미 추가된 사진입니다.");
    }

    if (nonDuplicates.length === 0) return;

    setFiles(prev => [...prev, ...nonDuplicates]);
    const newPreviews = nonDuplicates.map(file => URL.createObjectURL(file));
    setPreviews(prev => [...prev, ...newPreviews]);
  }, [files]);

  const removeFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => {
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(Array.from(e.dataTransfer.files));
    }
  }, [handleFileSelect]);

  const handleUpload = async () => {
    if (files.length === 0) return;

    setAnalyzing(true);

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch("/api/v1/portfolio/setup/upload-images", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          alert("로그인이 필요합니다.");
          router.push("/login");
          return;
        }
        throw new Error(`분석 실패 (Status: ${response.status})`);
      }

      const data: ImageUploadResponse[] = await response.json();
      
      // Process detected positions
      data.forEach((imgResult) => {
        imgResult.detectedPositions.forEach((pos) => {
          addAsset({
            id: pos.detectedPositionId || `detected-${Date.now()}-${Math.random()}`,
            ticker: pos.symbol,
            name: pos.name,
            avgPrice: pos.averageCost,
            quantity: pos.quantity,
            currency: pos.currency as "USD" | "KRW",
          });
        });
      });

      router.replace("/onboarding/ai/check");
    } catch (error) {
      console.error("Upload failed:", error);
      alert("이미지 분석 중 오류가 발생했습니다. 다시 시도해 주세요.");
      setAnalyzing(false);
    }
  };

  if (analyzing) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center text-slate-900 p-6 text-center">
        <div>
          <Loader2 className="animate-spin w-12 h-12 text-[var(--color-primary)] mx-auto mb-6" />
          <h2 className="text-2xl font-bold mb-2">AI가 자산을<br />분석하고 있어요</h2>
          <p className="text-slate-500">잠시만 기다려주세요</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-6 flex flex-col">
      <div className="w-full max-w-md mx-auto pt-2 flex-1 flex flex-col items-start">
        <BackButton className="-ml-8 mb-6" href="/onboarding/add" />
        
        <h1 className="text-2xl font-bold mb-3">스크린샷 업로드</h1>
        <p className="text-[var(--color-text-secondary)] mb-8">
          보유 자산 화면을 캡쳐해서 올려주세요.<br />
          여러 장을 한 번에 올릴 수 있어요.
        </p>

        {/* Dropzone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={`
            relative w-full aspect-[2/1] rounded-2xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center gap-3 mb-8
            ${isDragging 
              ? "border-[var(--color-primary)] bg-[var(--color-secondary)]" 
              : "border-gray-200 hover:border-[var(--color-primary)] hover:bg-gray-50"
            }
          `}
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            multiple
            accept="image/*"
            onChange={(e) => {
              if (e.target.files) {
                handleFileSelect(Array.from(e.target.files));
                // 중요: 동일한 파일 재선택 시에도 이벤트를 발생시키기 위해 value 초기화
                e.target.value = "";
              }
            }}
          />
          <div className={`p-4 rounded-full ${isDragging ? "bg-white" : "bg-gray-100"}`}>
            <Upload className={`w-6 h-6 ${isDragging ? "text-[var(--color-primary)]" : "text-gray-400"}`} />
          </div>
          <div className="text-center">
            <p className="font-medium text-[var(--color-text-primary)]">
              {isDragging ? "여기에 놓아주세요" : "사진을 드래그하거나 클릭해서 업로드"}
            </p>
            <p className="text-sm text-[var(--color-text-tertiary)] mt-1">JPG, PNG</p>
          </div>
        </div>

        {/* Preview Grid */}
        <div className="flex-1 overflow-y-auto mb-20 no-scrollbar">
          {files.length > 0 && (
            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              <AnimatePresence>
                {previews.map((src, index) => (
                  <motion.div
                    key={src}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="relative aspect-square rounded-xl overflow-hidden shadow-sm border border-gray-100"
                  >
                    <img src={src} alt="preview" className="w-full h-full object-cover" />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(index);
                      }}
                      className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/60 text-white flex items-center justify-center transition-colors hover:bg-red-500 backdrop-blur-sm"
                    >
                      <X size={14} />
                    </button>
                  </motion.div>
                ))}
                
                <motion.button
                   layout
                   onClick={() => fileInputRef.current?.click()}
                   className="aspect-square rounded-xl border border-gray-200 flex flex-col items-center justify-center gap-1 text-gray-400 hover:bg-gray-50 hover:border-gray-300 transition-all"
                >
                   <Plus size={20} />
                   <span className="text-[11px] font-bold">추가</span>
                </motion.button>
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

            <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white to-transparent">

              <div className="max-w-md mx-auto">

                <Button 

                  className="w-full h-14 text-lg rounded-[28px] shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"

                  disabled={files.length === 0}

                  onClick={handleUpload}

                >

                  {files.length > 0 ? `${files.length}장 분석하기` : "사진을 선택해주세요"}

                </Button>

              </div>

            </div>

      

            {/* Toast Notification */}

            <AnimatePresence>

              {toast && (

                <motion.div

                  initial={{ opacity: 0, y: 50 }}

                  animate={{ opacity: 1, y: 0 }}

                  exit={{ opacity: 0, y: 20 }}

                  className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 px-6 py-3 bg-slate-800 text-white text-sm font-bold rounded-full shadow-xl whitespace-nowrap"

                >

                  {toast}

                </motion.div>

              )}

            </AnimatePresence>

          </div>

        );

      }

      