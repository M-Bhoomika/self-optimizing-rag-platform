# RAG Platform Helm Scaffold

This chart is a **deployable scaffold** only. Values and probes have not been
validated against a live cluster in this repository.

## Install

```bash
helm install rag-platform ./infrastructure/helm/rag-platform \
  --namespace rag-platform --create-namespace
```

## Notes

- Images default to locally built tags (`rag-platform-api:latest`, `rag-platform-worker:latest`).
- Set `global.databaseUrl`, `global.redisUrl`, and secrets before production use.
- See `values.yaml` for service ports and replica counts.
