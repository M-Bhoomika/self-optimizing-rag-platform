"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type RunRow = {
  run_id: string;
  experiment_name: string;
  metrics: Record<string, number>;
  created_at: string;
};

export function ExperimentTable() {
  const [rows, setRows] = useState<RunRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const response = await fetch(`${API_BASE}/api/v1/experiments/runs`);
        if (!response.ok) {
          setError(`Failed to load runs (${response.status})`);
          return;
        }
        setRows(await response.json());
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function runExperiment() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/experiments/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment_name: "frontend-eval",
          tenant_id: "eval-tenant",
          use_mlflow: false,
        }),
      });
      if (!response.ok) {
        setError(`Run failed (${response.status})`);
        return;
      }
      const reload = await fetch(`${API_BASE}/api/v1/experiments/runs`);
      setRows(await reload.json());
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <p>Loading experiments...</p>;
  if (error) return <p>{error}</p>;

  return (
    <section>
      <button onClick={() => void runExperiment()} style={{ marginBottom: 12 }}>
        Run Evaluation
      </button>
      <table style={{ width: "100%", borderCollapse: "collapse", maxWidth: 900 }}>
        <thead>
          <tr>
            <th align="left">Run ID</th>
            <th align="left">Experiment</th>
            <th align="left">Faithfulness</th>
            <th align="left">Latency (ms)</th>
            <th align="left">Created</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5}>No runs yet. Click Run Evaluation.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.run_id}>
                <td>{row.run_id.slice(0, 8)}</td>
                <td>{row.experiment_name}</td>
                <td>{row.metrics.faithfulness_score_mean?.toFixed(3) ?? "—"}</td>
                <td>{row.metrics.mean_retrieval_latency_ms?.toFixed(1) ?? "—"}</td>
                <td>{new Date(row.created_at).toLocaleString()}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
