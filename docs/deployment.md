# Deployment

Use a managed PostgreSQL and Redis instance in production, inject secrets through the platform secret store, terminate TLS at the ingress, and run backend, worker, and scheduler as separate replicas. Keep `JWT_SECRET`, database credentials, and SMTP credentials out of source control.
