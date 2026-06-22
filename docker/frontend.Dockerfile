# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder — install deps and compile the Next.js App Router bundle
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Runtime — serve prebuilt pages (/, /admin, /chat, etc.)
# ---------------------------------------------------------------------------
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
