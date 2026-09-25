from app.services.strategies import RSSDetector

def test_rss_detector_has_common_strategy_name():
    assert RSSDetector.name == "rss"
