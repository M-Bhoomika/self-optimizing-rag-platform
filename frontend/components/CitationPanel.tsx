type Citation = Record<string, unknown>;

export function CitationPanel({ citations }: { citations: Citation[] }) {
  if (!citations.length) {
    return <p style={{ marginTop: 16, color: "#666" }}>No citations yet.</p>;
  }
  return (
    <aside style={{ marginTop: 16 }}>
      <h3>Citations</h3>
      <ul>
        {citations.map((c, i) => (
          <li key={i}>
            chunk={String(c.chunk_id ?? "n/a")} doc={String(c.document_id ?? "n/a")} score=
            {String(c.score ?? "n/a")}
          </li>
        ))}
      </ul>
    </aside>
  );
}
