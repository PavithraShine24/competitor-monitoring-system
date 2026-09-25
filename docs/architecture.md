# Architecture

FastAPI owns authenticated management and read APIs. PostgreSQL is the source of truth. Redis carries Celery jobs; workers run network-bound monitoring and extraction outside request handlers. A periodic scheduler enqueues one isolated check per enabled competitor.

Detection uses a common strategy contract: RSS/Atom first, sitemap second, and direct-page discovery as a fallback. Every check and detection event is persisted. Article uniqueness is enforced on competitor plus normalized canonical URL.
