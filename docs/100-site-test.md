# 100-site test

Start 100 controlled endpoints in the load-test environment, then run `python scripts/load_test.py`. The script makes 100 concurrent HTTP probes with distinct behavior slots and records success, failure, timeout, latency, and total duration in `load-test-report.json`. It does not insert database rows or fabricate detection results.
