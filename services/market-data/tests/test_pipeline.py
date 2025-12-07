from quote_pipeline.config import Provider, Settings, KisConfig
from quote_pipeline.ingestors.binance import BinanceIngestor
from quote_pipeline.ingestors.kis import KisIngestor
from quote_pipeline.ingestors.upbit import UpbitIngestor
from quote_pipeline.pipeline import build_ingestor, build_sink
from quote_pipeline.sinks import StdoutSink


def test_build_sink_defaults_to_stdout():
    # Redis URL이 없으면 stdout sink 선택
    settings = Settings()
    sink = build_sink(settings)
    assert isinstance(sink, StdoutSink)


def test_build_ingestor_upbit():
    # provider가 upbit면 UpbitIngestor 생성
    settings = Settings(provider=Provider.upbit, symbols=["KRW-BTC"])
    ing = build_ingestor(settings, build_sink(settings))
    assert isinstance(ing, UpbitIngestor)


def test_build_ingestor_binance():
    # provider가 binance면 BinanceIngestor 생성
    settings = Settings(provider=Provider.binance, symbols=["BTCUSDT"])
    ing = build_ingestor(settings, build_sink(settings))
    assert isinstance(ing, BinanceIngestor)


def test_build_ingestor_kis_requires_creds():
    # provider가 kis면 KIS 자격을 채워야 ingestor 생성 가능
    settings = Settings(
        provider=Provider.kis,
        symbols=["NVDA"],
        kis=KisConfig(id="id", account="acct", appkey="app", secretkey="secret"),
    )
    ing = build_ingestor(settings, build_sink(settings))
    assert isinstance(ing, KisIngestor)
