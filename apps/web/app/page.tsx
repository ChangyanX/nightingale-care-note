export default function HomePage() {
  return (
    <main className="shell">
      <p className="eyebrow">Nightingale 72-hour build</p>
      <h1>One patient story, traced from source to action.</h1>
      <p className="lede">
        The Phase 1 foundation is ready for authenticated, clinic-scoped Care Notes with
        server-enforced permissions and exact provenance.
      </p>
      <section className="status" aria-labelledby="foundation-status">
        <h2 id="foundation-status">Foundation status</h2>
        <dl>
          <div><dt>Frontend</dt><dd>Next.js + TypeScript</dd></div>
          <div><dt>API</dt><dd>FastAPI</dd></div>
          <div><dt>Data</dt><dd>Supabase PostgreSQL + RLS</dd></div>
        </dl>
      </section>
    </main>
  );
}
