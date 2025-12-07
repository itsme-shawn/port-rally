import json

from quote_pipeline.sinks.stdout import StdoutSink


def test_stdout_sink_prints_json(capsys):
    # StdoutSink가 JSON 문자열을 출력하는지 검증
    sink = StdoutSink()
    payload = {"provider": "test", "symbol": "ABC", "price": 1.23}
    # StdoutSink.publish is async; call via loop.run_until_complete not needed if we use asyncio.run
    import asyncio

    asyncio.run(sink.publish(payload))

    captured = capsys.readouterr().out.strip()
    loaded = json.loads(captured)
    assert loaded["provider"] == "test"
    assert loaded["symbol"] == "ABC"
    assert loaded["price"] == 1.23
