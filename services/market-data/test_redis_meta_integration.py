#!/usr/bin/env python3
"""Redis metadata integration test - 키 생성 검증."""

import sys
sys.path.insert(0, 'src')

from quote_pipeline.redis_meta import meta


def test_quote_key():
    """Quote 키 생성 테스트."""
    print("Testing quote key...")
    quote_key = meta.quote(national="KR", exchange="KOSPI", symbol="005930")
    result = quote_key.build()
    expected = "quote:KR:KOSPI:005930"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ Quote key: {result}")
    print(f"  ✓ TTL: {quote_key.get_ttl_seconds()}s")
    print(f"  ✓ Type: {quote_key.get_type()}")


def test_active_symbols_key():
    """Active symbols 키 생성 테스트."""
    print("\nTesting active_symbols key...")

    # Test with valid provider
    for provider in ["kis", "upbit", "binance"]:
        key = meta.active_symbols(provider=provider)
        result = key.build()
        expected = f"active_symbols:{provider}"

        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"  ✓ Active symbols key ({provider}): {result}")

    # Test enum validation
    try:
        bad_key = meta.active_symbols(provider="invalid")
        bad_key.build()
        assert False, "Should have raised ValueError for invalid provider"
    except ValueError as e:
        print(f"  ✓ Enum validation works: {e}")


def test_symbol_metadata_key():
    """Symbol metadata 키 생성 테스트."""
    print("\nTesting symbol_metadata key...")
    key = meta.symbol_metadata(symbol="005930")
    result = key.build()
    expected = "symbol_metadata:005930"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ Symbol metadata key: {result}")
    print(f"  ✓ TTL: {key.get_ttl_seconds()}s")


def test_symbol_map_key():
    """Symbol map 키 생성 테스트."""
    print("\nTesting symbol_map key...")
    key = meta.symbol_map(symbol="TSLA")
    result = key.build()
    expected = "symbol_map:TSLA"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ Symbol map key: {result}")


def test_symbol_detail_key():
    """Symbol detail 키 생성 테스트."""
    print("\nTesting symbol_detail key...")
    key = meta.symbol_detail(
        national="US",
        market="NAS",
        symbol="TSLA"
    )
    result = key.build()
    expected = "symbol_detail:US:NAS:TSLA"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ Symbol detail key: {result}")
    print(f"  ✓ Fields: {key.get_fields()}")


def test_refresh_token_key():
    """Refresh token 키 생성 테스트 (core-api용)."""
    print("\nTesting refresh_token key...")
    token = "eyJhbGciOiJIUzI1NiIs.test.signature"
    key = meta.refresh_token(token=token)
    result = key.build()
    expected = f"refresh_token:{token}"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ Refresh token key: {result}")
    print(f"  ✓ TTL: {key.get_ttl_seconds()}s")


def test_user_refresh_key():
    """User refresh 키 생성 테스트 (core-api용)."""
    print("\nTesting user_refresh key...")
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    key = meta.user_refresh(userId=user_id)
    result = key.build()
    expected = f"user_refresh:{user_id}"

    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  ✓ User refresh key: {result}")


def test_environment_prefix():
    """환경별 prefix 테스트."""
    print("\nTesting environment prefixes...")

    quote_key = meta.quote(national="KR", exchange="KOSPI", symbol="005930")

    # Dev environment (no prefix)
    dev_key = quote_key.build(env="dev")
    assert dev_key == "quote:KR:KOSPI:005930"
    print(f"  ✓ Dev key: {dev_key}")

    # Prod environment (with prefix)
    prod_key = quote_key.build(env="prod")
    assert prod_key == "prod:quote:KR:KOSPI:005930"
    print(f"  ✓ Prod key: {prod_key}")

    # Test environment
    test_key = quote_key.build(env="test")
    assert test_key == "test:quote:KR:KOSPI:005930"
    print(f"  ✓ Test key: {test_key}")


def test_validation():
    """파라미터 검증 테스트."""
    print("\nTesting parameter validation...")

    # Valid pattern
    try:
        key = meta.quote(national="KR", exchange="KOSPI", symbol="005930")
        key.build()
        print("  ✓ Valid pattern accepted")
    except ValueError:
        assert False, "Valid pattern should not raise error"

    # Invalid national (not 2 uppercase letters)
    try:
        key = meta.quote(national="KOR", exchange="KOSPI", symbol="005930")
        key.build()
        assert False, "Should have raised ValueError for invalid national"
    except ValueError as e:
        print(f"  ✓ Invalid national rejected: {e}")

    # Invalid symbol (contains special characters)
    try:
        key = meta.quote(national="KR", exchange="KOSPI", symbol="@#$")
        key.build()
        assert False, "Should have raised ValueError for invalid symbol"
    except ValueError as e:
        print(f"  ✓ Invalid symbol rejected: {e}")


def main():
    """모든 테스트 실행."""
    print("=" * 60)
    print("Redis Meta Integration Test")
    print("=" * 60)

    try:
        test_quote_key()
        test_active_symbols_key()
        test_symbol_metadata_key()
        test_symbol_map_key()
        test_symbol_detail_key()
        test_refresh_token_key()
        test_user_refresh_key()
        test_environment_prefix()
        test_validation()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
