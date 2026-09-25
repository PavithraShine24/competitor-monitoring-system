from datetime import datetime, timezone
from app.utils.time import detection_delay_seconds, format_delay
from app.utils.urls import normalize_url

def test_normalize_url_removes_tracking_and_fragment():
    assert normalize_url("HTTP://Example.com/article/?utm_source=x#comments") == "https://example.com/article"

def test_delay_is_exact_and_unavailable_is_none():
    published = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
    detected = datetime(2026, 9, 25, 10, 8, 17, tzinfo=timezone.utc)
    assert detection_delay_seconds(published, detected) == 497
    assert detection_delay_seconds(None, detected) is None

def test_delay_format_keeps_late_value():
    assert format_delay(2220) == "37m 00s"
    assert format_delay(None) == "Unavailable"
