import { getAssetDetails } from "@/lib/api/asset";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/Badge";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { BackButton } from "@/components/ui/BackButton";
import { RealtimeQuoteCard } from "@/components/asset/RealtimeQuoteCard";

type Props = {
    params: Promise<{ identifier: string }>;
};

export default async function AssetDetailPage({ params }: Props) {
    const { identifier } = await params;

    if (!identifier) {
        notFound();
    }

    try {
        // The identifier from the URL is already decoded by Next.js
        const asset = await getAssetDetails(identifier);

        return (
            <div className="container-custom py-10">
                <header className="mb-8">
                    <div className="mb-4">
                        <BackButton />
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-2xl font-black text-slate-400">
                            {asset.symbol.charAt(0)}
                        </div>
                        <div>
                            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">{asset.nameKo || asset.nameEn}</h1>
                            <p className="text-slate-500 font-semibold">{asset.symbol} · {asset.market} ({asset.national})</p>
                        </div>
                    </div>
                </header>

                <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* 실시간 시세 카드 */}
                    <div className="lg:col-span-3">
                        <RealtimeQuoteCard
                            identifier={identifier}
                            initialSymbol={asset.symbol}
                        />
                    </div>

                    <div className="lg:col-span-2 bg-white p-8 rounded-2xl border border-slate-100">
                        <h2 className="text-xl font-bold mb-6">자산 정보</h2>
                        <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
                            <div>
                                <p className="text-slate-400 font-medium">종목 코드 (Symbol)</p>
                                <p className="font-bold text-slate-700">{asset.symbol}</p>
                            </div>
                            <div>
                                <p className="text-slate-400 font-medium">시장 / 국가</p>
                                <p className="font-bold text-slate-700">{asset.market} / {asset.national}</p>
                            </div>
                            <div>
                                <p className="text-slate-400 font-medium">ISIN</p>
                                <p className="font-bold text-slate-700">{asset.isin || "N/A"}</p>
                            </div>
                            <div>
                                <p className="text-slate-400 font-medium">자산 유형</p>
                                <p className="font-bold text-slate-700">{asset.assetType || "N/A"}</p>
                            </div>
                            <div>
                                <p className="text-slate-400 font-medium">기준 통화</p>
                                <p className="font-bold text-slate-700">{asset.currency}</p>
                            </div>
                        </div>
                    </div>

                    <aside className="bg-white p-8 rounded-2xl border border-slate-100">
                        <h2 className="text-xl font-bold mb-6">분류</h2>
                        <div>
                            <p className="text-slate-400 font-medium mb-1">섹터 분류</p>
                            <p className="font-bold text-slate-700 mb-4">{asset.sectorScheme || "N/A"}</p>
                        </div>
                        <div>
                            <p className="text-slate-400 font-medium mb-2">섹터 태그</p>
                            <div className="flex flex-wrap gap-2">
                                {asset.sectorTags && asset.sectorTags.length > 0 ? (
                                    asset.sectorTags.map(tag => <Badge key={tag}>{tag}</Badge>)
                                ) : (
                                    <p className="text-sm text-slate-500">태그 정보가 없습니다.</p>
                                )}
                            </div>
                        </div>
                    </aside>
                </main>
            </div>
        );

    } catch (error) {
        console.error("Failed to fetch asset details:", error);
        notFound();
    }
}
