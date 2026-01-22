"use client";

import { useRouter } from "next/navigation";
import { Button } from "./Button";
import { ArrowLeft } from "lucide-react";

export function BackButton() {
    const router = useRouter();

    return (
        <Button
            variant="ghost"
            onClick={() => router.back()}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-900 px-0 hover:bg-transparent"
        >
            <ArrowLeft size={16} />
            <span className="font-bold text-sm">뒤로가기</span>
        </Button>
    );
}