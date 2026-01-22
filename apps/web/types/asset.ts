export interface AssetSearchResponse {
    assetId: number;
    symbol: string;
    name: string;
    market: string;
    national: string;
}

export interface AssetDetailResponse {
    assetId: number;
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
}
