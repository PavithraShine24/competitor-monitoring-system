# Database

PostgreSQL stores users, competitors, monitoring configurations, every monitoring check, articles, images, detection events, notifications, and system settings. `backend/alembic/versions/0001_initial.py` creates the schema. Apply it with `alembic upgrade head` after the database is available.

All application timestamps are timezone-aware UTC values. Article identity is protected by a unique `(competitor_id, normalized_url)` constraint.
