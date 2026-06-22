"use client";

import { useState } from "react";
import { CitationPanel } from "./CitationPanel";
import { QueryHistoryPanel } from "./QueryHistoryPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function ChatInterface() {
  const [query, setQuery] = useState("");
  const [tenantId, setTenantId] = useState("demo-tenant");
  const [tenantKey, setTenantKey] = useState("");
  const [tokens, setTokens] = useState<string[]>([]);
  const [citations, setCitations] = useState<Array<Record<string, unknown>>>([]);
  const [streaming, setStreaming] = useState(false);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [lowConfidence, setLowConfidence] = useState(false);

  async function handleStream() {
    setTokens([]);
    setCitations([]);
    setConfidence(null);
    setLowConfidence(false);
    setStreaming(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (tenantKey.trim()) headers["X-Tenant-Key"] = tenantKey.trim();
      const response = await fetch(`${API_BASE}/api/v1/query/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ tenant_id: tenantId, query, top_k: 5, use_cache: true }),
      });
      if (!response.ok) {
        setTokens([`Error ${response.status}: ${await response.text()}`]);
        return;
      }
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const payload = JSON.parse(part.slice(6));
          if (payload.done) {
            setCitations(payload.citations ?? []);
            if (typeof payload.confidence_score === "number") setConfidence(payload.confidence_score);
            setLowConfidence(Boolean(payload.low_confidence));
          } else if (payload.token) {
            setTokens((prev) => [...prev, payload.token]);
          }
        }
      }
    } catch {
      setTokens(["Streaming unavailable. Start the API locally on port 8000."]);
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
      <section style={{ flex: 1 }}>
        <label>
          Tenant ID
          <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} style={{ marginLeft: 8 }} />
        </label>
        <label style={{ display: "block", marginTop: 8 }}>
          X-Tenant-Key (optional)
          <input value={tenantKey} onChange={(e) => setTenantKey(e.target.value)} style={{ marginLeft: 8, width: 320 }} />
        </label>
        <div style={{ marginTop: 12 }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
            style={{ width: "100%", maxWidth: 720 }}
            placeholder="Ask a question..."
          />
        </div>
        <button onClick={handleStream} disabled={streaming || !query.trim()} style={{ marginTop: 8 }}>
          {streaming ? "Streaming..." : "Stream Query"}
        </button>
        {confidence !== null ? (
          <p style={{ marginTop: 8 }}>
            Confidence: {confidence.toFixed(2)} {lowConfidence ? "(low confidence)" : ""}
          </p>
        ) : null}
        <div style={{ marginTop: 16, whiteSpace: "pre-wrap", minHeight: 80, border: "1px solid #eee", padding: 12 }}>
          {tokens.join(" ")}
        </div>
        <CitationPanel citations={citations} />
      </section>
      <QueryHistoryPanel tenantId={tenantId} tenantKey={tenantKey} />
    </div>
  );
}
