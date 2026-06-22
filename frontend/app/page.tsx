export default function HomePage() {
  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Self-Optimizing RAG Platform</h1>
      <p>Next.js UI for chat, document upload, experiments, monitoring, and admin.</p>
      <ul>
        <li><a href="/chat">Chat</a></li>
        <li><a href="/documents">Documents</a></li>
        <li><a href="/experiments">Experiments</a></li>
        <li><a href="/dashboard">Dashboard</a></li>
        <li><a href="/admin">Admin</a></li>
      </ul>
    </main>
  );
}
