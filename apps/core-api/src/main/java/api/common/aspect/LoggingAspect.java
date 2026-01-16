package api.common.aspect;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.stream.Collectors;

@Aspect
@Component
@Slf4j
public class LoggingAspect {

    @Around("execution(* api.controller..*(..)) || execution(* api.service..*(..))")
    public Object logAround(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        String className = signature.getDeclaringType().getSimpleName();
        String methodName = signature.getName();

        // 입력 인자 로깅 (시각적 구분 기호 추가)
        String args = Arrays.stream(joinPoint.getArgs())
                .map(arg -> {
                    if (arg == null) return "null";
                    String str = arg.toString();
                    return str.length() > 500 ? str.substring(0, 500) + "..." : str;
                })
                .collect(Collectors.joining(", "));
        
        log.info("▶▶▶ [START] {}.{} | Args: [{}]", className, methodName, args);

        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();

        // 리턴값 로깅 (Reactive 타입 대응)
        if (result instanceof Mono) {
            return ((Mono<?>) result)
                    .doOnSuccess(data -> {
                        long time = System.currentTimeMillis() - start;
                        log.info("◀◀◀ [ END ] {}.{} | Time: {}ms | Result: {}", className, methodName, time, data);
                    })
                    .doOnError(err -> {
                        long time = System.currentTimeMillis() - start;
                        log.error("✘✘✘ [ERROR] {}.{} | Time: {}ms | Reason: {}", className, methodName, time, err.getMessage());
                    });
        } else if (result instanceof Flux) {
            return ((Flux<?>) result)
                    .doOnComplete(() -> {
                         long time = System.currentTimeMillis() - start;
                         log.info("◀◀◀ [DONE ] {}.{} | Time: {}ms | Result: [Flux Completed]", className, methodName, time);
                    })
                    .doOnError(err -> {
                         long time = System.currentTimeMillis() - start;
                         log.error("✘✘✘ [ERROR] {}.{} | Time: {}ms | Reason: {}", className, methodName, time, err.getMessage());
                    });
        } else {
            long time = System.currentTimeMillis() - start;
            log.info("◀◀◀ [SUCCESS] {}.{} | Time: {}ms | Result: {}", className, methodName, time, result);
            return result;
        }
    }
}
