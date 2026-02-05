import { apiClient } from "@/lib/api-client";
import { AssetSearchResponse, AssetDetailResponse } from "@/types/asset";

/**
 * 자산 검색 API
 * @param keyword 검색어
 * @param limit 최대 결과 수
 */
export const searchAssets = async (keyword: string, limit: number = 10): Promise<AssetSearchResponse[]> => {
    if (!keyword.trim()) {
        return [];
    }
    const endpoint = `/api/v1/assets/search?keyword=${encodeURIComponent(keyword)}&limit=${limit}`;
    return apiClient<AssetSearchResponse[]>(endpoint);
};

/**
 * 자산 상세 조회 API
 * @param identifier "national:market:symbol" 형식의 자산 식별자
 * @param includePrice 현재가 정보 포함 여부 (기본값: true)
 */
export const getAssetDetails = async (
    identifier: string,
    includePrice: boolean = true
): Promise<AssetDetailResponse> => {
    const endpoint = `/api/v1/assets/by-symbol/${identifier}${includePrice ? '?includePrice=true' : ''}`;
    return apiClient<AssetDetailResponse>(endpoint);
};
