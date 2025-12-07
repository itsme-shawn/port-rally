import logging

from quote_pipeline.logging_config import configure_logging


def test_configure_logging_sets_level():
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG
