"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type QueryRow = {
  query_text?: string;
  answer_text?: string;
  created_at?: string;
};

export function QueryHistoryPanel({ tenantId, tenantKey }: { tenantId: string; tenantKey: string }) {
  const [rows, setRows] = useState<QueryRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const headers: Record<string, string> = {};
        if (tenantKey.trim()) headers["X-Tenant-Key"] = tenantKey.trim();
        const response = await fetch(
          `${API_BASE}/api/v1/query/history?tenant_id=${encodeURIComponent(tenantId)}&limit=20`,
          { headers },
        );
        if (!response.ok) {
          setError("Query history unavailable (database may be skipped in dev).");
          return;
        }
        const payload = await response.json();
        setRows(payload.queries ?? []);
      } catch (err) {
        setError(String(err));
      }
    }
    void load();
  }, [tenantId, tenantKey]);

  return (
    <aside style={{ minWidth: 260, borderLeft: "1px solid #ddd", paddingLeft: 16 }}>
      <h3>Query History</h3>
      <p style={{ fontSize: 12, color: "#666" }}>Live API history when PostgreSQL is enabled.</p>
      {error ? <p>{error}</p> : null}
      <ul style={{ paddingLeft: 16 }}>
        {rows.map((row, index) => (
          <li key={`${row.created_at}-${index}`} style={{ marginBottom: 8 }}>
            <strong>{row.query_text}</strong>
            <div style={{ fontSize: 12 }}>{row.answer_text?.slice(0, 120)}</div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
