import asyncio
from decimal import Decimal
from types import SimpleNamespace

import pytest

from quote_pipeline.ingestors.kis import KisIngestor


class CollectSink:
    """테스트용 Sink: publish 호출 시 payload를 쌓는다."""

    def __init__(self) -> None:
        self.payloads = []

    async def publish(self, payload):
        self.payloads.append(payload)


@pytest.mark.asyncio
async def test_kis_ingestor_publishes_when_market_open(monkeypatch):
    """시장 오픈 시 단일 심볼 구독 후 sink.publish가 호출되는지 검증."""

    class FakeTicket:
        def unsubscribe(self):
            pass

    class FakeStock:
        def on(self, event_name, callback):
            # PyKis가 콜백을 등록하는 대신 즉시 한 건 발행
            e = SimpleNamespace(
                response=SimpleNamespace(
                    symbol="NVDA",
                    price=Decimal("10.0"),
                    time="2025-01-01T00:00:00Z",
                    model_dump=lambda: {"symbol": "NVDA", "price": Decimal("10.0"), "time": "2025-01-01T00:00:00Z"},
                )
            )
            callback(None, e)
            return FakeTicket()

    class FakeWebsocket:
        def __init__(self):
            self.subscriptions = {"HDFSCNT0.DNASNVDA"}

    class FakePyKis:
        def __init__(self, *args, **kwargs):
            self.websocket = FakeWebsocket()

        def trading_hours(self, market):
            # 항상 장 오픈으로 판정되는 시간
            return SimpleNamespace(open_kst="00:00:00", close_kst="23:59:59")

        def stock(self, sym):
            return FakeStock()

    # PyKis, sleep 패치
    monkeypatch.setattr("quote_pipeline.ingestors.kis.PyKis", FakePyKis)

    sink = CollectSink()
    ingestor = KisIngestor(
        symbols=["NVDA"],
        sink=sink,
        user_id="id",
        account="acct",
        appkey="app",
        secretkey="secret",
    )

    task = asyncio.create_task(ingestor.run_forever())
    # 이벤트 루프가 콜백을 처리할 시간 부여
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert sink.payloads, "sink.publish가 호출되지 않았습니다."
    assert sink.payloads[0]["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_kis_ingestor_skips_when_market_closed(monkeypatch):
    """시장 닫힘으로 판단되면 구독하지 않고 sink 호출도 없어야 한다."""

    class FakePyKis:
        def __init__(self, *args, **kwargs):
            self.websocket = SimpleNamespace(subscriptions=set())

        def trading_hours(self, market):
            return SimpleNamespace(open_kst="10:00:00", close_kst="10:00:00")  # 닫힘 처리되도록 반환

        def stock(self, sym):
            raise AssertionError("market closed 상태에서 stock.on 이 호출되면 안 됨")

    monkeypatch.setattr("quote_pipeline.ingestors.kis.PyKis", FakePyKis)
    monkeypatch.setattr("quote_pipeline.ingestors.kis.is_market_open", lambda fetch: False)

    async def fake_sleep(_sec):
        raise asyncio.CancelledError

    import quote_pipeline.ingestors.kis as kis_mod

    monkeypatch.setattr(kis_mod.asyncio, "sleep", fake_sleep)

    sink = CollectSink()
    ingestor = KisIngestor(
        symbols=["NVDA"],
        sink=sink,
        user_id="id",
        account="acct",
        appkey="app",
        secretkey="secret",
    )

    with pytest.raises(asyncio.CancelledError):
        await ingestor.run_forever()

    assert not sink.payloads, "시장 닫힘 상태에서 publish가 호출되면 안 됩니다."
