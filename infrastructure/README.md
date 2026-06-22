# Infrastructure

Deployment and observability configuration for local development.

- `prometheus/prometheus.yml` — Prometheus scrape config mounted by Docker Compose.
  See also `monitoring/prometheus.yml` for the expanded monitoring definition.
- Docker Compose service definitions live at the project root in `docker-compose.yml`.
- Application Dockerfiles live in `docker/`.
