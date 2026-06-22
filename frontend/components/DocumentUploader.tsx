"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type DocumentRow = {
  id: string;
  title?: string;
  document_type?: string;
  chunk_count?: number;
};

export function DocumentUploader() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState("demo-tenant");
  const [tenantKey, setTenantKey] = useState("");
  const [title, setTitle] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);

  async function loadDocuments() {
    const headers: Record<string, string> = {};
    if (tenantKey.trim()) headers["X-Tenant-Key"] = tenantKey.trim();
    const response = await fetch(`${API_BASE}/api/v1/documents?tenant_id=${encodeURIComponent(tenantId)}`, {
      headers,
    });
    if (!response.ok) return;
    const payload = await response.json();
    setDocuments(payload.documents ?? []);
  }

  useEffect(() => {
    void loadDocuments();
  }, [tenantId, tenantKey]);

  const filtered = useMemo(
    () => documents.filter((doc) => (doc.title ?? doc.id).toLowerCase().includes(search.toLowerCase())),
    [documents, search],
  );

  async function handleUpload(file: File, asyncMode = false) {
    setUploading(true);
    setStatus(null);
    try {
      const form = new FormData();
      form.append("tenant_id", tenantId);
      form.append("title", title || file.name);
      const lower = file.name.toLowerCase();
      const docType = lower.endsWith(".pdf")
        ? "pdf"
        : lower.endsWith(".md")
          ? "markdown"
          : lower.endsWith(".html")
            ? "html"
            : "txt";
      form.append("document_type", docType);
      form.append("source", "frontend-upload");
      form.append("file", file);
      const headers: Record<string, string> = {};
      if (tenantKey.trim()) headers["X-Tenant-Key"] = tenantKey.trim();
      const endpoint = asyncMode ? "/api/v1/documents/upload/async" : "/api/v1/documents/upload";
      const response = await fetch(`${API_BASE}${endpoint}`, { method: "POST", headers, body: form });
      const payload = await response.json();
      if (!response.ok) {
        setStatus(`Upload failed: ${payload.detail ?? response.statusText}`);
        return;
      }
      setStatus(
        asyncMode
          ? `Queued async ingest task ${payload.queued?.task_id ?? "unknown"}`
          : `Indexed ${payload.indexed_count} chunks for ${payload.document_id}`,
      );
      await loadDocuments();
    } catch (error) {
      setStatus(`Upload error: ${String(error)}`);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(documentId: string) {
    const headers: Record<string, string> = {};
    if (tenantKey.trim()) headers["X-Tenant-Key"] = tenantKey.trim();
    const response = await fetch(
      `${API_BASE}/api/v1/documents/${encodeURIComponent(documentId)}?tenant_id=${encodeURIComponent(tenantId)}`,
      { method: "DELETE", headers },
    );
    const payload = await response.json();
    setStatus(response.ok ? `Deleted ${documentId}` : `Delete failed: ${payload.detail ?? response.statusText}`);
    await loadDocuments();
  }

  return (
    <section>
      <label>
        Tenant ID
        <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} style={{ marginLeft: 8 }} />
      </label>
      <label style={{ display: "block", marginTop: 8 }}>
        X-Tenant-Key
        <input value={tenantKey} onChange={(e) => setTenantKey(e.target.value)} style={{ marginLeft: 8, width: 320 }} />
      </label>
      <label style={{ display: "block", marginTop: 8 }}>
        Title
        <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ marginLeft: 8, width: 320 }} />
      </label>
      <label style={{ display: "block", marginTop: 8 }}>
        Search documents
        <input value={search} onChange={(e) => setSearch(e.target.value)} style={{ marginLeft: 8, width: 320 }} />
      </label>
      <div style={{ marginTop: 12 }}>
        <input
          type="file"
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            setFileName(file?.name ?? null);
            if (file) void handleUpload(file, false);
          }}
        />
        <button
          type="button"
          disabled={uploading || !fileName}
          style={{ marginLeft: 8 }}
          onClick={() => {
            const input = document.querySelector<HTMLInputElement>('input[type="file"]');
            const file = input?.files?.[0];
            if (file) void handleUpload(file, true);
          }}
        >
          Upload Async
        </button>
      </div>
      {fileName ? <p>Selected: {fileName}</p> : null}
      {status ? <p>{status}</p> : null}
      <table style={{ marginTop: 16, borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th align="left">Title</th>
            <th align="left">Type</th>
            <th align="left">Chunks</th>
            <th align="left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.title ?? doc.id}</td>
              <td>{doc.document_type ?? "—"}</td>
              <td>{doc.chunk_count ?? "—"}</td>
              <td>
                <button type="button" onClick={() => void handleDelete(doc.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!filtered.length ? <p style={{ marginTop: 8 }}>No documents loaded (PostgreSQL may be skipped).</p> : null}
    </section>
  );
}
