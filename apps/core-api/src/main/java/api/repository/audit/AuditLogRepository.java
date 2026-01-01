package api.repository.audit;

import api.domain.audit.AuditLog;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.UUID;

@Repository
public interface AuditLogRepository extends ReactiveCrudRepository<AuditLog, UUID> {

    Flux<AuditLog> findAllByUserIdOrderByCreatedAtDesc(UUID userId);

    Flux<AuditLog> findAllByEventType(String eventType);

    @Query("SELECT * FROM audit_logs WHERE user_id = :userId ORDER BY created_at DESC LIMIT :limit")
    Flux<AuditLog> findLatestByUserId(UUID userId, int limit);

    @Query("SELECT * FROM audit_logs WHERE created_at >= :since ORDER BY created_at DESC")
    Flux<AuditLog> findAllSince(Instant since);

    @Query("SELECT * FROM audit_logs WHERE user_id = :userId AND event_type = :eventType ORDER BY created_at DESC")
    Flux<AuditLog> findByUserIdAndEventType(UUID userId, String eventType);
}
