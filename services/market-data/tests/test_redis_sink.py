import pytest

from quote_pipeline.sinks.redis_sink import RedisSink


class FakeRedis:
    def __init__(self):
        self.published = []

    async def publish(self, channel, payload):
        self.published.append((channel, payload))


def test_redis_sink_publish(monkeypatch):
    fake = FakeRedis()

    class FakeRedisModule:
        @staticmethod
        def from_url(url, decode_responses=True):
            return fake

    import sys
    # redis.asyncio 모듈을 패치해서 RedisSink 내부 import를 대체
    monkeypatch.setitem(sys.modules, "redis.asyncio", FakeRedisModule)

    sink = RedisSink(url="redis://localhost:6379/0", channel="test-channel")
    import asyncio

    asyncio.run(sink.publish({"foo": "bar"}))

    assert fake.published
    channel, payload = fake.published[0]
    assert channel == "test-channel"
    assert '"foo": "bar"' in payload
