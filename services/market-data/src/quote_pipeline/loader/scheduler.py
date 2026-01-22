import asyncio
import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from quote_pipeline.loader.master_loader import MasterLoader

logger = logging.getLogger(__name__)

# 매일 고정 시각(24h) 실행 시간: 오전 7시, 오후 10시 (KST 기준)
SCHEDULE_HOURS = (7, 22)
# 스케줄 기준 타임존 (서버가 UTC여도 KST 시각으로 계산)
SCHEDULE_TZ = ZoneInfo("Asia/Seoul")

# 재시도 정책: 최대 시도 횟수 및 지수 백오프 지연(초)
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 5.0
RETRY_MAX_DELAY_S = 60.0

# 동일 프로세스 내에서 master_loader가 동시에 두 번 실행되지 않도록 하는 락
# (startup 실행과 scheduled 실행이 겹치거나, 예외로 인해 중복 호출되는 상황 방지)
_master_loader_lock = asyncio.Lock()


def _next_run_time(now: datetime) -> datetime:
    # 오늘 남은 스케줄 중 가장 가까운 시간을 찾는다
    for hour in SCHEDULE_HOURS:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate > now:
            return candidate

    # 오늘 남은 시간이 없으면 다음날 첫 번째 스케줄(오전 7시)로 예약
    next_day = now + timedelta(days=1)
    return next_day.replace(
        hour=SCHEDULE_HOURS[0],
        minute=0,
        second=0,
        microsecond=0,
    )


async def _run_master_loader_once(trigger: str) -> bool:
    # 이미 실행 중이면 중복 실행을 막고 스킵한다 (스케줄 밀림 방지)
    if _master_loader_lock.locked():
        logger.warning(
            "[MasterLoaderScheduler] Skip trigger=%s (previous run still in progress)",
            trigger,
        )
        return True

    # 락을 획득한 동안만 실행하여 동시 실행을 방지
    async with _master_loader_lock:
        loader = MasterLoader()
        started_at = time.monotonic()
        try:
            # DB 연결 실패 시 재시도 대상이 되도록 False 반환
            if not await loader.check_connection():
                logger.error("[MasterLoaderScheduler] DB connection failed")
                return False

            # 실제 마스터 로딩 수행
            result = await loader.load_all()
            elapsed = time.monotonic() - started_at
            logger.info(
                "[MasterLoaderScheduler] Completed trigger=%s result=%s elapsed=%.2fs",
                trigger,
                result,
                elapsed,
            )
            return True
        except Exception:
            # 예외 상세는 logger.exception으로 스택트레이스까지 기록
            logger.exception("[MasterLoaderScheduler] Failed trigger=%s", trigger)
            return False
        finally:
            # 항상 커넥션 풀 종료
            await loader.close()


async def run_master_loader_with_retry(trigger: str) -> None:
    # 실패 시 최대 RETRY_MAX_ATTEMPTS까지 재시도
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        ok = await _run_master_loader_once(trigger)
        if ok:
            return

        # 마지막 시도 전까지는 지수 백오프로 대기 후 재시도
        if attempt < RETRY_MAX_ATTEMPTS:
            delay = min(RETRY_BASE_DELAY_S * (2 ** (attempt - 1)), RETRY_MAX_DELAY_S)
            logger.warning(
                "[MasterLoaderScheduler] Retry trigger=%s attempt=%d/%d in %.1fs",
                trigger,
                attempt + 1,
                RETRY_MAX_ATTEMPTS,
                delay,
            )
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                raise

    # 모든 재시도 실패 시 오류 로그로 기록
    logger.error(
        "[MasterLoaderScheduler] Exhausted retries trigger=%s attempts=%d",
        trigger,
        RETRY_MAX_ATTEMPTS,
    )


async def master_loader_scheduler() -> None:
    # 프로세스 시작 시 1회 즉시 실행
    await run_master_loader_with_retry("startup")

    while True:
        # 다음 스케줄 시간을 계산하고 그때까지 대기
        now = datetime.now(SCHEDULE_TZ)
        next_run = _next_run_time(now)
        delay = max(0.0, (next_run - now).total_seconds())
        logger.info(
            "[MasterLoaderScheduler] Next run at %s (in %.1fs)",
            next_run.isoformat(),
            delay,
        )
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logger.info("[MasterLoaderScheduler] Scheduler cancelled")
            raise

        # 예약 시각 도래 후 실행
        await run_master_loader_with_retry("scheduled")
