# Kubernetes Manifests

Scaffold manifests for deploying the RAG platform to Kubernetes. These files
have not been validated against a live cluster in this repository.

## Apply order

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/chromadb-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/api-deployment.yaml
kubectl apply -f infrastructure/kubernetes/worker-deployment.yaml
kubectl apply -f infrastructure/kubernetes/prometheus-deployment.yaml
kubectl apply -f infrastructure/kubernetes/grafana-deployment.yaml
kubectl apply -f infrastructure/kubernetes/hpa.yaml
```

Create a `rag-platform-env` secret with database, Redis, and API settings before
deploying API/worker pods.

## Scaling strategy

- **API (`rag-api-hpa`)** — scales on CPU utilization (2–10 replicas). Add custom
  metrics (request latency, queue depth) once Prometheus adapter is configured.
- **Worker (`rag-worker-hpa`)** — scales on CPU (1–8 replicas). The worker
  consumes Redis-backed ingest/evaluation tasks via `scripts/run_worker.py`;
  prefer queue-depth metrics when a Prometheus adapter is available.
- **Stateful services** — Postgres and ChromaDB use PVCs; scale vertically or
  adopt operator-managed HA patterns before multi-replica stateful scaling.

## Notes

- Images default to locally built tags (`rag-platform-api:latest`).
- Prometheus expects a `prometheus-config` ConfigMap (create from `monitoring/prometheus.yml`).
- This is a deployment scaffold, not a complete production rollout.
