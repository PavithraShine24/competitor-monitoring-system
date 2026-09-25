# Detection delay

Delay is `detected_at - published_at` in seconds. Unknown publication time remains NULL and is rendered as `Unavailable`. The UI separately counts values at or below 300 seconds and values above 300 seconds; it never caps or drops late values.
