"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type PlatformStatus = {
  service: string;
  auth_required: boolean;
  retrieval_backend: string;
  vector_store_class: string;
  embedding_provider: string;
  cache_backend: string;
  worker_queue_backend: string;
  worker_queue_depth: number;
  skip_db: boolean;
};

type TenantRow = {
  id: string;
  name: string;
  document_quota?: number | null;
  query_quota_per_day?: number | null;
};

export default function AdminPage() {
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tenantKeyInput, setTenantKeyInput] = useState("");
  const [newTenantName, setNewTenantName] = useState("");
  const [documentQuota, setDocumentQuota] = useState("100");
  const [queryQuota, setQueryQuota] = useState("1000");
  const [adminMessage, setAdminMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [statusRes, configRes, tenantsRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/admin/status`),
          fetch(`${API_BASE}/api/v1/admin/config`),
          fetch(`${API_BASE}/api/v1/admin/tenants`),
        ]);
        if (statusRes.ok) setStatus(await statusRes.json());
        if (configRes.ok) setConfig(await configRes.json());
        if (tenantsRes.ok) {
          const body = await tenantsRes.json();
          setTenants(body.tenants ?? []);
        }
      } catch (err) {
        setError(String(err));
      }
    }
    void load();
  }, []);

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Admin</h1>
      <p style={{ fontSize: 13, color: "#666" }}>
        Demo-safe admin UI. Tenant creation/API key provisioning requires PostgreSQL and is shown as guidance when unavailable.
      </p>
      {error ? <p style={{ color: "crimson" }}>{error}</p> : null}

      <section style={{ marginTop: 16 }}>
        <h2>Platform Status</h2>
        {status ? (
          <ul>
            <li>Service: {status.service}</li>
            <li>Auth required: {String(status.auth_required)}</li>
            <li>Retrieval backend: {status.retrieval_backend}</li>
            <li>Vector store: {status.vector_store_class}</li>
            <li>Embedding provider: {status.embedding_provider}</li>
            <li>Cache backend: {status.cache_backend}</li>
            <li>Worker queue: {status.worker_queue_backend} (depth {status.worker_queue_depth})</li>
            <li>Skip DB: {String(status.skip_db)}</li>
          </ul>
        ) : (
          <p>Loading status...</p>
        )}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Tenant Management (demo form)</h2>
        <label style={{ display: "block" }}>
          Tenant name
          <input value={newTenantName} onChange={(e) => setNewTenantName(e.target.value)} style={{ marginLeft: 8 }} />
        </label>
        <label style={{ display: "block", marginTop: 8 }}>
          Document quota
          <input value={documentQuota} onChange={(e) => setDocumentQuota(e.target.value)} style={{ marginLeft: 8, width: 100 }} />
        </label>
        <label style={{ display: "block", marginTop: 8 }}>
          Query quota/day
          <input value={queryQuota} onChange={(e) => setQueryQuota(e.target.value)} style={{ marginLeft: 8, width: 100 }} />
        </label>
        <label style={{ display: "block", marginTop: 8 }}>
          API key (for X-Tenant-Key testing)
          <input value={tenantKeyInput} onChange={(e) => setTenantKeyInput(e.target.value)} style={{ marginLeft: 8, width: 320 }} />
        </label>
        <button
          type="button"
          style={{ marginTop: 8 }}
          onClick={() =>
            setAdminMessage(
              "Tenant provisioning via UI is demo-only. Use DB seed scripts or register_test_tenant() in development.",
            )
          }
        >
          Save Tenant (demo)
        </button>
        {adminMessage ? <p>{adminMessage}</p> : null}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Configuration</h2>
        {config ? (
          <pre style={{ background: "#f5f5f5", padding: 12, overflow: "auto" }}>
            {JSON.stringify(config, null, 2)}
          </pre>
        ) : (
          <p>Loading configuration...</p>
        )}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Tenants</h2>
        {tenants.length ? (
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th align="left">ID</th>
                <th align="left">Name</th>
                <th align="left">Document quota</th>
                <th align="left">Query quota/day</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr key={tenant.id}>
                  <td>{tenant.id}</td>
                  <td>{tenant.name}</td>
                  <td>{tenant.document_quota ?? "—"}</td>
                  <td>{tenant.query_quota_per_day ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No tenants loaded (database may be skipped in dev).</p>
        )}
      </section>
    </main>
  );
}
