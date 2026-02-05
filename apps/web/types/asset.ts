export interface AssetSearchResponse {
    identifier: string;
    symbol: string;
    name: string;
    market: string;
    national: string;
}

export interface AssetPriceResponse {
    symbol: string;
    national: string;
    exchange: string;
    price: number;
    change: number;
    change_rate: number;
    volume: number;
    high: number;
    low: number;
    open: number;
    raw_output?: Record<string, unknown>;
}

export interface AssetDetailResponse {
    identifier: string;
    national: string;
    market: string;
    symbol: string;
    isin: string;
    nameKo: string;
    nameEn: string;
    assetType: string;
    currency: string;
    sectorScheme: string;
    sectorTags: string[];
    createdAt: string; // ISO 8601 string
    updatedAt: string; // ISO 8601 string
    price?: AssetPriceResponse; // includePrice=true일 때 포함
}
