#!/usr/bin/env python
"""Quote Pipeline 운영 관리 통합 CLI.

Usage:
    python -m quote_pipeline.manage [symbols|quotes] [command] [args...]

Examples:
    # Active Symbols 관리
    python -m quote_pipeline.manage symbols list kis
    python -m quote_pipeline.manage symbols add kis NVDA AAPL
    python -m quote_pipeline.manage symbols remove kis NVDA
    python -m quote_pipeline.manage symbols clear kis

    # Quote 조회
    python -m quote_pipeline.manage quotes get NVDA
    python -m quote_pipeline.manage quotes list
    python -m quote_pipeline.manage quotes all
    python -m quote_pipeline.manage quotes subscribe
"""

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command in ("-h", "--help", "help"):
        print_help()
        return

    if command == "symbols":
        # symbols 서브커맨드 실행
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from quote_pipeline.manage import symbols
        import asyncio
        asyncio.run(symbols.main())

    elif command == "quotes":
        # quotes 서브커맨드 실행
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from quote_pipeline.manage import quotes
        import asyncio
        asyncio.run(quotes.main())

    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


def print_help() -> None:
    print("""
Quote Pipeline 운영 관리 CLI

Usage:
    python -m quote_pipeline.manage <command> [args...]

Commands:
    symbols     Active Symbols CRUD (조회/추가/삭제)
    quotes      Quote 조회 (현재가/목록/구독)

Examples:
    # Active Symbols 관리
    python -m quote_pipeline.manage symbols list kis
    python -m quote_pipeline.manage symbols add kis NVDA AAPL
    python -m quote_pipeline.manage symbols remove kis NVDA
    python -m quote_pipeline.manage symbols clear --all

    # Quote 조회
    python -m quote_pipeline.manage quotes get NVDA
    python -m quote_pipeline.manage quotes list --pattern "US:*"
    python -m quote_pipeline.manage quotes all
    python -m quote_pipeline.manage quotes subscribe

Run 'python -m quote_pipeline.manage <command> --help' for more info.
""")


if __name__ == "__main__":
    main()
