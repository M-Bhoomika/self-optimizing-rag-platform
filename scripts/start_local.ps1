# Start local development environment for the Self-Optimizing RAG Platform.
#
# Usage:
#   .\scripts\start_local.ps1              # infrastructure + instructions
#   .\scripts\start_local.ps1 infra        # docker compose up only
#   .\scripts\start_local.ps1 api          # run FastAPI (requires deps installed)
#   .\scripts\start_local.ps1 test         # run pytest
#   .\scripts\start_local.ps1 seed         # generate in-memory demo data

param(
    [ValidateSet("all", "infra", "api", "test", "seed")]
    [string]$Command = "all"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Start-Infra {
    Write-Host "Starting infrastructure (Postgres, Redis, ChromaDB, MLflow, Prometheus, Grafana, Jaeger)..."
    docker compose up -d
    Write-Host ""
    Write-Host "Services:"
    Write-Host "  Postgres:    localhost:5432"
    Write-Host "  Redis:       localhost:6379"
    Write-Host "  ChromaDB:    localhost:8001"
    Write-Host "  MLflow:      localhost:5000"
    Write-Host "  Prometheus:  localhost:9090"
    Write-Host "  Grafana:     localhost:3001  (admin / admin)"
    Write-Host "  Jaeger UI:   localhost:16686"
}

function Start-Api {
    Write-Host "Starting API on http://127.0.0.1:8000 ..."
    python -m uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000
}

function Start-Tests {
    Write-Host "Running test suite..."
    python -m pytest tests/ -q
}

function Start-Seed {
    Write-Host "Generating in-memory demo data..."
    python scripts/seed_demo_data.py
}

switch ($Command) {
    "infra" { Start-Infra }
    "api"   { Start-Api }
    "test"  { Start-Tests }
    "seed"  { Start-Seed }
    "all" {
        Start-Infra
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "  1. Copy .env.example to .env if you have not already."
        Write-Host "  2. Install Python deps:  pip install -r requirements.txt"
        Write-Host "  3. Initialize DB:        python -m api.db.init_db"
        Write-Host "  4. Start API:            .\scripts\start_local.ps1 api"
        Write-Host "  5. Run tests:            .\scripts\start_local.ps1 test"
        Write-Host "  6. Seed demo data:       .\scripts\start_local.ps1 seed"
    }
}
