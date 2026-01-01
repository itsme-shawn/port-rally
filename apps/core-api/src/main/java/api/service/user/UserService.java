package api.service.user;

import api.domain.user.User;
import api.dto.user.CreateUserRequest;
import api.enums.user.UserStatus;
import api.repository.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    @Transactional
    public Mono<User> createUser(CreateUserRequest request) {
        log.info("Creating user with email: {}", request.getEmail());

        return userRepository.existsByPrimaryEmail(request.getEmail())
                .flatMap(exists -> {
                    if (exists) {
                        return Mono.error(new IllegalArgumentException("Email already exists: " + request.getEmail()));
                    }

                    User user = User.builder()
                            .displayName(request.getDisplayName())
                            .primaryEmail(request.getEmail())
                            .status(UserStatus.PENDING)
                            .build();

                    log.debug("Saving user: displayName={}, email={}, status={}",
                            user.getDisplayName(), user.getPrimaryEmail(), user.getStatus());

                    return userRepository.save(user);
                })
                .doOnSuccess(user -> log.info("User created successfully: userId={}", user.getUserId()))
                .doOnError(e -> {
                    Throwable rootCause = e;
                    while (rootCause.getCause() != null) {
                        rootCause = rootCause.getCause();
                    }
                    log.error("Create user failed. rootCause={}, rootCauseClass={}",
                            rootCause.getMessage(), rootCause.getClass().getSimpleName(), e);
                });
    }

    public Mono<User> getUserById(UUID userId) {
        return userRepository.findByUserIdAndDeletedAtIsNull(userId);
    }

    public Flux<User> getAllUsers() {
        return userRepository.findAllByDeletedAtIsNull();
    }

    @Transactional
    public Mono<Void> deleteUser(UUID userId) {
        return userRepository.findById(userId)
                .flatMap(user -> {
                    user.softDelete();
                    return userRepository.save(user);
                })
                .then();
    }
}
