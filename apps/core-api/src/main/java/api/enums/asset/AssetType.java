package api.enums.asset;

/**
 * 자산 유형
 *
 * Note: DB에서는 TEXT 타입으로 저장되며, 이 enum은 타입 안정성을 위한 참조용입니다.
 */
public enum AssetType {
    STOCK,    // 주식
    ETF,      // 상장지수펀드
    ETN,      // 상장지수채권
    INDEX,    // 지수
    WARRANT,  // 워런트
    CRYPTO,   // 암호화폐
    BOND,     // 채권
    CASH,     // 현금성 자산
    OTHER;    // 기타

    /**
     * 문자열을 AssetType enum으로 변환
     * @param value DB에서 조회한 문자열
     * @return AssetType enum, 없으면 OTHER
     */
    public static AssetType fromString(String value) {
        if (value == null) {
            return OTHER;
        }
        try {
            return AssetType.valueOf(value.toUpperCase());
        } catch (IllegalArgumentException e) {
            return OTHER;
        }
    }
}
