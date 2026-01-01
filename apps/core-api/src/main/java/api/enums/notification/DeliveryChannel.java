package api.enums.notification;

/**
 * 알림 발송 채널
 */
public enum DeliveryChannel {
    PUSH,   // 푸시 알림
    EMAIL,  // 이메일
    SMS,    // 문자메시지
    IN_APP  // 인앱 알림
}
