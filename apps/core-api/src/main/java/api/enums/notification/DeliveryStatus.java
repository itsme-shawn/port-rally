package api.enums.notification;

/**
 * 알림 발송 상태
 */
public enum DeliveryStatus {
    PENDING,  // 발송 대기
    SENT,     // 발송 완료
    FAILED,   // 발송 실패
    READ      // 읽음
}
