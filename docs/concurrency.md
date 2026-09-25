# Concurrency

Celery worker concurrency is configured with `WORKER_CONCURRENCY`. HTTP clients have timeouts and follow redirects. The load harness uses 100 concurrent HTTP endpoints and writes an evidence report; deploy per-domain semaphores when operating at larger scale.
