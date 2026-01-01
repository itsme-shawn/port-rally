package api.enums.ocr;

/**
 * OCR 결과 상태
 */
public enum OcrStatus {
    PENDING,   // 인식 대기
    VERIFIED,  // 사용자 확인 완료
    REJECTED,  // 사용자 거부
    FAILED     // 인식 실패
}
