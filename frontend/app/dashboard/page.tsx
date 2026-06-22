"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type HealthDetails = {
  retrieval_backend: string;
  vector_store_class: string;
  embedding_backend: string;
  auth_required: boolean;
};

type Readiness = {
  status: string;
  checks: Record<string, { status: string }>;
};

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthDetails | null>(null);
  const [ready, setReady] = useState<Readiness | null>(null);
  const [cacheStats, setCacheStats] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    async function load() {
      const [detailsRes, readyRes, cacheRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/rag/health/details`),
        fetch(`${API_BASE}/health/ready`),
        fetch(`${API_BASE}/api/v1/query/cache/stats`),
      ]);
      if (detailsRes.ok) setHealth(await detailsRes.json());
      if (readyRes.ok) setReady(await readyRes.json());
      if (cacheRes.ok) setCacheStats(await cacheRes.json());
    }
    void load();
  }, []);

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Dashboard</h1>
      <section style={{ marginTop: 16 }}>
        <h2>Platform Health</h2>
        <p>Readiness: {ready?.status ?? "unknown"}</p>
        <ul>
          {ready
            ? Object.entries(ready.checks).map(([name, check]) => (
                <li key={name}>
                  {name}: {check.status}
                </li>
              ))
            : null}
        </ul>
      </section>
      <section style={{ marginTop: 16 }}>
        <h2>Backends</h2>
        {health ? (
          <ul>
            <li>Retrieval backend: {health.retrieval_backend}</li>
            <li>Vector store: {health.vector_store_class}</li>
            <li>Embedding: {health.embedding_backend}</li>
            <li>Auth required: {String(health.auth_required)}</li>
          </ul>
        ) : (
          <p>Health details unavailable.</p>
        )}
      </section>
      <section style={{ marginTop: 16 }}>
        <h2>Cache</h2>
        {cacheStats ? (
          <ul>
            <li>Hits: {cacheStats.hits}</li>
            <li>Misses: {cacheStats.misses}</li>
            <li>Hit rate: {cacheStats.hit_rate}</li>
          </ul>
        ) : (
          <p>Cache stats unavailable.</p>
        )}
      </section>
    </main>
  );
}
