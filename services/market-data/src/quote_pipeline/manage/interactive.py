#!/usr/bin/env python
"""Quote Pipeline 운영 관리 대화형 CLI.

Usage:
    python -m quote_pipeline.manage
    python -m quote_pipeline.manage --redis-url redis://localhost:6379
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    print("Error: redis package required. Install with: pip install redis")
    sys.exit(1)


DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PROVIDERS = ["kis", "upbit", "binance"]


class QuotePipelineManager:
    """Quote Pipeline 대화형 관리 도구."""

    def __init__(self, redis_url: str = DEFAULT_REDIS_URL):
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None
        self.running = True

    async def connect(self) -> bool:
        """Redis 연결."""
        try:
            self.client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            return False

    async def close(self) -> None:
        """연결 종료."""
        if self.client:
            await self.client.aclose()

    def print_banner(self) -> None:
        """배너 출력."""
        print("\n" + "=" * 60)
        print("  Quote Pipeline 운영 관리 도구")
        print(f"  Redis: {self.redis_url}")
        print("=" * 60)

    def print_main_menu(self) -> None:
        """메인 메뉴 출력."""
        print("\n[메인 메뉴]")
        print("  0. 시스템 상태 조회")
        print("  1. Active Symbols 관리")
        print("  2. Quote 조회")
        print("  3. 실시간 시세 구독")
        print("  q. 종료")
        print()

    def print_symbols_menu(self) -> None:
        """Active Symbols 메뉴 출력."""
        print("\n[Active Symbols 관리]")
        print("  1. 전체 조회 (list)")
        print("  2. Provider별 조회")
        print("  3. 심볼 추가 (add)")
        print("  4. 심볼 삭제 (remove)")
        print("  5. 전체 초기화 (clear)")
        print("  b. 뒤로가기")
        print()

    def print_quotes_menu(self) -> None:
        """Quote 조회 메뉴 출력."""
        print("\n[Quote 조회]")
        print("  1. 심볼로 조회 (get)")
        print("  2. 전체 목록 (list)")
        print("  3. 전체 현재가 테이블 (all)")
        print("  4. 패턴별 조회")
        print("  b. 뒤로가기")
        print()

    # =========================================================================
    # 시스템 상태 조회
    # =========================================================================

    async def show_system_status(self) -> None:
        """시스템 상태 조회."""
        print("\n" + "=" * 60)
        print("  시스템 상태")
        print("=" * 60)

        # 1. 환경변수에서 설정된 providers 조회
        env_providers = os.getenv("PROVIDERS", "")
        print(f"\n[환경변수 설정]")
        print(f"  PROVIDERS: {env_providers if env_providers else '(미설정)'}")
        print(f"  REDIS_URL: {os.getenv('REDIS_URL', '(미설정)')}")
        print(f"  DYNAMIC_ENABLED: {os.getenv('DYNAMIC_ENABLED', 'false')}")

        # 2. 현재 구동 중인 provider 추정 (active_symbols 기반)
        print(f"\n[구동 중인 Provider 추정]")
        configured_providers = [p.strip() for p in env_providers.split(",") if p.strip()]

        if configured_providers:
            print(f"  설정된 providers: {', '.join(configured_providers)}")
        else:
            print("  ⚠️  PROVIDERS 환경변수가 설정되지 않음")

        # 3. Provider별 상태 (active_symbols 개수)
        print(f"\n[Provider별 Active Symbols]")
        for provider in PROVIDERS:
            key = f"active_symbols:{provider}"
            symbols = await self.client.smembers(key)
            count = len(symbols) if symbols else 0

            # 구동 중인지 표시
            is_running = provider in configured_providers if configured_providers else False
            status = "🟢 구동중" if is_running else "⚪ 미구동"

            print(f"  {provider:<10} {status}  ({count} symbols)")

        # 4. Quote 현황
        quote_keys = await self.client.keys("quote:*")
        print(f"\n[Quote 현황]")
        print(f"  총 Quote 수: {len(quote_keys)}개")

        # provider별 quote 수
        quote_by_provider = {"kis": 0, "upbit": 0, "binance": 0, "other": 0}
        for key in quote_keys:
            if ":US:" in key or ":KR:KOSPI:" in key or ":KR:KOSDAQ:" in key:
                quote_by_provider["kis"] += 1
            elif ":UPBIT:" in key:
                quote_by_provider["upbit"] += 1
            elif ":BINANCE:" in key or ":CRYPTO:" in key:
                quote_by_provider["binance"] += 1
            else:
                quote_by_provider["other"] += 1

        for provider, count in quote_by_provider.items():
            if count > 0:
                print(f"    {provider}: {count}개")

        # 5. Redis 연결 상태
        print(f"\n[Redis 연결]")
        print(f"  URL: {self.redis_url}")
        try:
            info = await self.client.info("server")
            print(f"  버전: {info.get('redis_version', 'unknown')}")
            print(f"  상태: 🟢 연결됨")
        except Exception as e:
            print(f"  상태: 🔴 오류 ({e})")

        print()

    # =========================================================================
    # Active Symbols 관리
    # =========================================================================

    async def symbols_list_all(self) -> None:
        """전체 active_symbols 조회."""
        print("\n[Active Symbols - 전체 조회]")
        for provider in PROVIDERS:
            key = f"active_symbols:{provider}"
            symbols = await self.client.smembers(key)
            count = len(symbols) if symbols else 0
            print(f"\n  [{provider}] ({count} symbols)")
            if symbols:
                for sym in sorted(symbols):
                    print(f"    - {sym}")
            else:
                print("    (비어있음)")

    async def symbols_list_provider(self) -> None:
        """Provider별 조회."""
        provider = await self._select_provider()
        if not provider:
            return

        key = f"active_symbols:{provider}"
        symbols = await self.client.smembers(key)
        count = len(symbols) if symbols else 0

        print(f"\n[{provider}] Active Symbols ({count}개)")
        if symbols:
            for sym in sorted(symbols):
                print(f"  - {sym}")
        else:
            print("  (비어있음)")

    async def symbols_add(self) -> None:
        """심볼 추가."""
        provider = await self._select_provider()
        if not provider:
            return

        print(f"\n추가할 심볼을 입력하세요 (공백 또는 콤마로 구분)")
        print(f"예: NVDA AAPL TSLA 또는 KRW-BTC,KRW-ETH")
        symbols_input = input("> ").strip()

        if not symbols_input:
            print("취소되었습니다.")
            return

        # 공백 또는 콤마로 분리
        symbols = [s.strip() for s in symbols_input.replace(",", " ").split() if s.strip()]

        if not symbols:
            print("유효한 심볼이 없습니다.")
            return

        key = f"active_symbols:{provider}"
        added = await self.client.sadd(key, *symbols)
        print(f"\n✅ [{provider}] {added}개 심볼 추가됨: {', '.join(symbols)}")

        current = await self.client.smembers(key)
        print(f"   현재 총 {len(current)}개")

    async def symbols_remove(self) -> None:
        """심볼 삭제."""
        provider = await self._select_provider()
        if not provider:
            return

        # 현재 심볼 표시
        key = f"active_symbols:{provider}"
        current = await self.client.smembers(key)

        if not current:
            print(f"\n[{provider}] 등록된 심볼이 없습니다.")
            return

        print(f"\n[{provider}] 현재 심볼: {', '.join(sorted(current))}")
        print(f"\n삭제할 심볼을 입력하세요 (공백 또는 콤마로 구분)")
        symbols_input = input("> ").strip()

        if not symbols_input:
            print("취소되었습니다.")
            return

        symbols = [s.strip() for s in symbols_input.replace(",", " ").split() if s.strip()]

        if not symbols:
            print("유효한 심볼이 없습니다.")
            return

        removed = await self.client.srem(key, *symbols)
        print(f"\n✅ [{provider}] {removed}개 심볼 삭제됨: {', '.join(symbols)}")

        remaining = await self.client.smembers(key)
        print(f"   현재 총 {len(remaining)}개")

    async def symbols_clear(self) -> None:
        """전체 초기화."""
        print("\n[초기화 대상 선택]")
        print("  1. 특정 Provider만")
        print("  2. 전체 Provider")
        print("  b. 취소")

        choice = input("> ").strip().lower()

        if choice == "1":
            provider = await self._select_provider()
            if not provider:
                return

            confirm = input(f"\n정말 [{provider}] active_symbols를 초기화할까요? (y/N) > ").strip().lower()
            if confirm != "y":
                print("취소되었습니다.")
                return

            key = f"active_symbols:{provider}"
            deleted = await self.client.delete(key)
            if deleted:
                print(f"\n✅ [{provider}] active_symbols 초기화 완료")
            else:
                print(f"\n[{provider}] 이미 비어있습니다.")

        elif choice == "2":
            confirm = input(f"\n정말 전체 active_symbols를 초기화할까요? (y/N) > ").strip().lower()
            if confirm != "y":
                print("취소되었습니다.")
                return

            for provider in PROVIDERS:
                key = f"active_symbols:{provider}"
                deleted = await self.client.delete(key)
                status = "✅ 초기화됨" if deleted else "이미 비어있음"
                print(f"  [{provider}] {status}")

    async def _select_provider(self) -> Optional[str]:
        """Provider 선택."""
        print("\n[Provider 선택]")
        for i, p in enumerate(PROVIDERS, 1):
            print(f"  {i}. {p}")
        print("  b. 취소")

        choice = input("> ").strip().lower()

        if choice == "b":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(PROVIDERS):
                return PROVIDERS[idx]
        except ValueError:
            # 직접 입력한 경우
            if choice in PROVIDERS:
                return choice

        print("잘못된 선택입니다.")
        return None

    # =========================================================================
    # Quote 조회
    # =========================================================================

    async def quotes_get(self) -> None:
        """심볼로 현재가 조회."""
        print("\n조회할 심볼을 입력하세요")
        print("예: NVDA, KRW-BTC, KOSPI:005930")
        symbol = input("> ").strip()

        if not symbol:
            print("취소되었습니다.")
            return

        candidates = self._guess_quote_key(symbol)

        for key in candidates:
            data = await self.client.hgetall(key)
            if data:
                print(f"\n[{key}]")
                print("-" * 50)
                self._print_quote_data(data)
                return

        print(f"\n❌ Quote를 찾을 수 없습니다: {symbol}")
        print(f"   시도한 키: {', '.join(candidates)}")

    async def quotes_list(self) -> None:
        """전체 quote 목록."""
        keys = await self.client.keys("quote:*")

        if not keys:
            print("\n등록된 Quote가 없습니다.")
            return

        print(f"\n[Quote 목록] ({len(keys)}개)")
        for key in sorted(keys):
            display = key[6:]  # "quote:" 제거
            print(f"  {display}")

    async def quotes_all(self) -> None:
        """전체 현재가 테이블."""
        keys = await self.client.keys("quote:*")

        if not keys:
            print("\n등록된 Quote가 없습니다.")
            return

        print(f"\n{'Symbol':<25} {'Price':>15} {'Change':>10} {'Volume':>12} {'Updated':<20}")
        print("-" * 85)

        for key in sorted(keys):
            data = await self.client.hgetall(key)
            if not data:
                continue

            # 키 형식: quote:{market}:{symbol}
            parts = key.split(":")
            symbol = parts[-1] if len(parts) >= 3 else key

            price = self._format_price(data.get("price"))
            change_str = self._format_change(data.get("change_rate"))
            volume = self._format_volume(data.get("volume"))
            updated = self._format_timestamp(data.get("updated_at"))

            print(f"{symbol:<25} {price:>15} {change_str:>10} {volume:>12} {updated:<20}")

        print(f"\n총 {len(keys)}개")

    async def quotes_by_pattern(self) -> None:
        """패턴별 조회."""
        print("\n[패턴 선택]")
        print("  1. NAS:*    (미국 나스닥)")
        print("  2. NYS:*    (미국 뉴욕)")
        print("  3. KOSPI:*  (한국 코스피)")
        print("  4. KOSDAQ:* (한국 코스닥)")
        print("  5. UPBIT:*  (업비트)")
        print("  6. 직접 입력")
        print("  b. 취소")

        choice = input("> ").strip().lower()

        patterns = {
            "1": "NAS:*",
            "2": "NYS:*",
            "3": "KOSPI:*",
            "4": "KOSDAQ:*",
            "5": "UPBIT:*",
        }

        if choice == "b":
            return
        elif choice == "6":
            pattern = input("패턴 입력 (예: NAS:*) > ").strip()
            if not pattern:
                return
        elif choice in patterns:
            pattern = patterns[choice]
        else:
            print("잘못된 선택입니다.")
            return

        keys = await self.client.keys(f"quote:{pattern}")

        if not keys:
            print(f"\n패턴 '{pattern}'에 해당하는 Quote가 없습니다.")
            return

        print(f"\n[패턴: {pattern}] ({len(keys)}개)")
        print(f"{'Symbol':<25} {'Price':>15} {'Change':>10}")
        print("-" * 55)

        for key in sorted(keys):
            data = await self.client.hgetall(key)
            if not data:
                continue

            # 키 형식: quote:{market}:{symbol}
            parts = key.split(":")
            symbol = parts[-1] if len(parts) >= 3 else key
            price = self._format_price(data.get("price"))
            change_str = self._format_change(data.get("change_rate"))

            print(f"{symbol:<25} {price:>15} {change_str:>10}")

    # =========================================================================
    # 실시간 구독
    # =========================================================================

    async def subscribe_quotes(self) -> None:
        """실시간 시세 구독."""
        channel = "quotes"

        # 출력 모드 선택
        print("\n[출력 모드 선택]")
        print("  1. 요약 (테이블 형식)")
        print("  2. Raw (전체 JSON payload)")
        print("  b. 취소")

        choice = input("> ").strip().lower()
        if choice == "b":
            return

        raw_mode = choice == "2"

        print(f"\n[실시간 시세 구독] 채널: {channel}")
        print("Ctrl+C를 눌러 중지하세요.\n")

        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)

        if raw_mode:
            print("=== Raw payload mode ===\n")
        else:
            print(f"{'Time':<12} {'Provider':<8} {'Symbol':<20} {'Price':>15} {'Change':>10}")
            print("-" * 70)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data = json.loads(message["data"])

                    if raw_mode:
                        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{now}]")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        print()
                    else:
                        provider = data.get("provider", "?")
                        symbol = data.get("symbol", "?")
                        price = self._format_price(str(data.get("price", "")))
                        change_str = self._format_change(data.get("change_rate"))
                        now = datetime.now().strftime("%H:%M:%S")

                        print(f"{now:<12} {provider:<8} {symbol:<20} {price:>15} {change_str:>10}")

                except json.JSONDecodeError:
                    pass

        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            print("\n구독 종료됨.")

    # =========================================================================
    # 유틸리티
    # =========================================================================

    def _guess_quote_key(self, symbol: str) -> list[str]:
        """심볼로 quote 키 추측.

        키 형식: quote:{market}:{symbol}
        """
        symbol_upper = symbol.upper()
        symbol_lower = symbol.lower()
        prefix = "quote"

        # 이미 전체 키 형식인 경우 (market:symbol)
        if symbol.count(":") >= 1:
            return [f"{prefix}:{symbol}"]

        candidates = []
        if symbol_upper.startswith("KRW-"):
            candidates.append(f"{prefix}:UPBIT:{symbol_upper}")
        elif symbol_lower.endswith("usdt") or symbol_lower.endswith("btc"):
            candidates.append(f"{prefix}:BINANCE:{symbol_upper}")
        else:
            candidates.extend([
                f"{prefix}:NAS:{symbol_upper}",
                f"{prefix}:NYS:{symbol_upper}",
                f"{prefix}:KOSPI:{symbol_upper}",
                f"{prefix}:KOSDAQ:{symbol_upper}",
            ])

        return candidates

    def _print_quote_data(self, data: dict) -> None:
        """Quote 데이터 출력."""
        priority = ["provider", "price", "volume", "timestamp", "updated_at", "change", "change_rate"]

        for field in priority:
            if field in data:
                value = data[field]
                if field in ("price", "open", "high", "low", "change"):
                    value = self._format_price(value)
                elif field in ("timestamp", "updated_at"):
                    value = self._format_timestamp(value)
                elif field == "change_rate" and value:
                    value = self._format_change(value)
                print(f"  {field}: {value}")

        others = [f for f in data.keys() if f not in priority]
        if others:
            print()
            for field in sorted(others):
                value = data[field]
                if field in ("open", "high", "low"):
                    value = self._format_price(value)
                print(f"  {field}: {value}")

    def _format_price(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        try:
            num = float(value)
            if num >= 1000:
                return f"{num:,.2f}"
            elif num >= 1:
                return f"{num:.4f}"
            else:
                return f"{num:.8f}"
        except ValueError:
            return value

    def _format_change(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        try:
            cr = float(value)
            return f"{cr:+.2f}%"
        except (ValueError, TypeError):
            return "-"

    def _format_volume(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        try:
            vol = float(value)
            if vol >= 1_000_000:
                return f"{vol/1_000_000:.2f}M"
            elif vol >= 1_000:
                return f"{vol/1_000:.2f}K"
            return f"{vol:.0f}"
        except ValueError:
            return value

    def _format_timestamp(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return value[:19] if len(value) > 19 else value

    # =========================================================================
    # 메인 루프
    # =========================================================================

    async def run_symbols_menu(self) -> None:
        """Active Symbols 메뉴 루프."""
        while True:
            self.print_symbols_menu()
            choice = input("> ").strip().lower()

            if choice == "b":
                break
            elif choice == "1":
                await self.symbols_list_all()
            elif choice == "2":
                await self.symbols_list_provider()
            elif choice == "3":
                await self.symbols_add()
            elif choice == "4":
                await self.symbols_remove()
            elif choice == "5":
                await self.symbols_clear()
            else:
                print("잘못된 선택입니다.")

    async def run_quotes_menu(self) -> None:
        """Quote 조회 메뉴 루프."""
        while True:
            self.print_quotes_menu()
            choice = input("> ").strip().lower()

            if choice == "b":
                break
            elif choice == "1":
                await self.quotes_get()
            elif choice == "2":
                await self.quotes_list()
            elif choice == "3":
                await self.quotes_all()
            elif choice == "4":
                await self.quotes_by_pattern()
            else:
                print("잘못된 선택입니다.")

    async def run(self) -> None:
        """메인 실행 루프."""
        self.print_banner()

        if not await self.connect():
            return

        print("✅ Redis 연결 성공")

        try:
            while self.running:
                self.print_main_menu()
                choice = input("> ").strip().lower()

                if choice in ("q", "quit", "exit"):
                    print("\n종료합니다.")
                    break
                elif choice == "0":
                    await self.show_system_status()
                elif choice == "1":
                    await self.run_symbols_menu()
                elif choice == "2":
                    await self.run_quotes_menu()
                elif choice == "3":
                    await self.subscribe_quotes()
                else:
                    print("잘못된 선택입니다.")

        except KeyboardInterrupt:
            print("\n\n종료합니다.")
        finally:
            await self.close()


async def main(redis_url: str = DEFAULT_REDIS_URL) -> None:
    manager = QuotePipelineManager(redis_url)
    await manager.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quote Pipeline 운영 관리 도구")
    parser.add_argument(
        "--redis-url",
        default=DEFAULT_REDIS_URL,
        help=f"Redis URL (default: {DEFAULT_REDIS_URL})",
    )
    args = parser.parse_args()

    asyncio.run(main(args.redis_url))
