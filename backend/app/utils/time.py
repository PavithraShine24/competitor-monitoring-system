from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def detection_delay_seconds(published_at: datetime | None, detected_at: datetime) -> float | None:
    if published_at is None:
        return None
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=timezone.utc)
    return max(0.0, (detected_at - published_at).total_seconds())

def format_delay(seconds: float | None) -> str:
    if seconds is None:
        return "Unavailable"
    total = int(seconds)
    if total < 60:
        return f"{total} seconds"
    if total < 3600:
        return f"{total // 60}m {total % 60:02d}s"
    return f"{total // 3600}h {(total % 3600) // 60:02d}m"
