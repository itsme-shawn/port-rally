package api.controller;

import api.dto.user.CreateUserRequest;
import api.dto.user.UserResponse;
import api.service.user.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<UserResponse> createUser(@Valid @RequestBody CreateUserRequest request) {
        log.info("POST /api/v1/users - Creating user: {}", request.getEmail());
        return userService.createUser(request)
                .map(UserResponse::from);
    }

    @GetMapping("/{userId}")
    public Mono<UserResponse> getUser(@PathVariable UUID userId) {
        log.info("GET /api/v1/users/{}", userId);
        return userService.getUserById(userId)
                .map(UserResponse::from)
                .switchIfEmpty(Mono.error(new IllegalArgumentException("User not found: " + userId)));
    }

    @GetMapping
    public Flux<UserResponse> getAllUsers() {
        log.info("GET /api/v1/users - Fetching all users");
        return userService.getAllUsers()
                .map(UserResponse::from);
    }

    @DeleteMapping("/{userId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public Mono<Void> deleteUser(@PathVariable UUID userId) {
        log.info("DELETE /api/v1/users/{}", userId);
        return userService.deleteUser(userId);
    }
}
