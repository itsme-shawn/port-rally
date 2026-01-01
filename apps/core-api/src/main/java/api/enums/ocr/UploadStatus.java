package api.enums.ocr;

/**
 * 이미지 업로드 상태
 */
public enum UploadStatus {
    PENDING,     // 대기중
    PROCESSING,  // 처리중
    COMPLETED,   // 완료
    FAILED       // 실패
}
