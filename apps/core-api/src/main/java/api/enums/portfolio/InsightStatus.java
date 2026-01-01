package api.enums.portfolio;

/**
 * AI 인사이트 상태
 */
public enum InsightStatus {
    ACTIVE,      // 활성 (최신)
    SUPERSEDED,  // 대체됨 (새 버전 생성됨)
    ARCHIVED     // 보관됨
}
