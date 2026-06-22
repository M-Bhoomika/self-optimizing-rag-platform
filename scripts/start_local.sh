#!/usr/bin/env bash
# Start local development environment for the Self-Optimizing RAG Platform.
#
# Usage:
#   ./scripts/start_local.sh              # infrastructure + instructions
#   ./scripts/start_local.sh infra        # docker compose up only
#   ./scripts/start_local.sh api          # run FastAPI (requires deps installed)
#   ./scripts/start_local.sh test         # run pytest
#   ./scripts/start_local.sh seed         # generate in-memory demo data
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

run_infra() {
  echo "Starting infrastructure (Postgres, Redis, ChromaDB, MLflow, Prometheus, Grafana, Jaeger)..."
  docker compose up -d
  echo ""
  echo "Services:"
  echo "  Postgres:    localhost:5432"
  echo "  Redis:       localhost:6379"
  echo "  ChromaDB:    localhost:8001"
  echo "  MLflow:      localhost:5000"
  echo "  Prometheus:  localhost:9090"
  echo "  Grafana:     localhost:3001  (admin / admin)"
  echo "  Jaeger UI:   localhost:16686"
}

run_api() {
  echo "Starting API on http://127.0.0.1:8000 ..."
  python -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000
}

run_tests() {
  echo "Running test suite..."
  python -m pytest tests/ -q
}

run_seed() {
  echo "Generating in-memory demo data..."
  python scripts/seed_demo_data.py
}

case "${1:-all}" in
  infra)
    run_infra
    ;;
  api)
    run_api
    ;;
  test)
    run_tests
    ;;
  seed)
    run_seed
    ;;
  all)
    run_infra
    echo ""
    echo "Next steps:"
    echo "  1. Copy .env.example to .env if you have not already."
    echo "  2. Install Python deps:  pip install -r requirements.txt"
    echo "  3. Initialize DB:        python -m api.db.init_db"
    echo "  4. Start API:            ./scripts/start_local.sh api"
    echo "  5. Run tests:            ./scripts/start_local.sh test"
    echo "  6. Seed demo data:       ./scripts/start_local.sh seed"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Usage: $0 [infra|api|test|seed|all]"
    exit 1
    ;;
esac
