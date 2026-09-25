# Failure handling

HTTP, parsing, extraction, and database errors are attached to monitoring checks. Celery retries transient task failures with exponential backoff and a finite retry count. A failed competitor check marks only that competitor offline and does not stop the scheduler.
