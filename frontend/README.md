# Frontend (Next.js)

TypeScript Next.js UI for the Self-Optimizing RAG Platform, wired to the live
FastAPI backend.

## Pages

- `/` — landing links
- `/chat` — SSE streaming chat (calls `/api/v1/query/stream`, optional `X-Tenant-Key`)
- `/documents` — document upload (`POST /api/v1/documents/upload`)
- `/experiments` — run and list experiments (`/api/v1/experiments/*`)
- `/dashboard` — readiness, backend details, and cache statistics
- `/admin` — platform status, configuration, and tenant listing

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE=http://localhost:8000` to point the UI at the API.

The chat page uses Server-Sent Events from the backend streaming endpoint. If the
API is not running, the UI shows an error message.
