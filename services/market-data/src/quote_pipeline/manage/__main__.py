"""Quote Pipeline 운영 관리 도구.

Usage:
    python -m quote_pipeline.manage
    python -m quote_pipeline.manage --redis-url redis://localhost:6379

    # 기존 CLI 명령어도 지원
    python -m quote_pipeline.manage symbols list kis
    python -m quote_pipeline.manage quotes get NVDA
"""

import sys
import asyncio


def main() -> None:
    # 서브커맨드 없이 실행하면 대화형 모드
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help")):
        run_interactive()
        return

    # --redis-url 만 있는 경우도 대화형 모드
    if len(sys.argv) == 3 and sys.argv[1] == "--redis-url":
        run_interactive()
        return

    # 서브커맨드가 있으면 기존 CLI 방식
    command = sys.argv[1]

    if command == "symbols":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from quote_pipeline.manage import symbols
        asyncio.run(symbols.main())

    elif command == "quotes":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from quote_pipeline.manage import quotes
        asyncio.run(quotes.main())

    else:
        # 알 수 없는 명령어면 대화형 모드로 폴백
        run_interactive()


def run_interactive() -> None:
    """대화형 모드 실행."""
    import argparse
    from quote_pipeline.manage.interactive import main as interactive_main, DEFAULT_REDIS_URL

    parser = argparse.ArgumentParser(description="Quote Pipeline 운영 관리 도구")
    parser.add_argument(
        "--redis-url",
        default=DEFAULT_REDIS_URL,
        help=f"Redis URL (default: {DEFAULT_REDIS_URL})",
    )
    args, _ = parser.parse_known_args()

    asyncio.run(interactive_main(args.redis_url))


if __name__ == "__main__":
    main()
