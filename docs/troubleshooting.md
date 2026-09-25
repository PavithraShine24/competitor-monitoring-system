# Troubleshooting

Check `docker compose logs backend worker scheduler` for structured service errors. If the dashboard says API unavailable, verify port 8000 and that migrations have run. If a target cannot be added, its URL may resolve to a private or loopback address, which is rejected to prevent SSRF.
