import { useEffect, useState } from "react";
import { Card, ErrorNote, Loading, PageHeader } from "../ui";

interface AdminStatus {
  release: { release_id: string; version: string; source: string | null; approved: boolean };
  ingestion: { public_upload_enabled: boolean; write_operations: string; pipeline: string };
  counts: { concepts: number; flashcards: number; families: number };
}

export function Admin() {
  const [status, setStatus] = useState<AdminStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/admin/status");
        if (!r.ok) throw new Error(String(r.status));
        setStatus((await r.json()) as AdminStatus);
      } catch {
        setError("Could not reach the backend. Start it with `grove-serve` (port 8001 — temporary).");
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Admin"
        sub="Operator view. Ingestion runs through the private grove-ingest CLI — not through this surface."
      />
      {error ? <ErrorNote>{error}</ErrorNote> : null}
      {!status ? (
        <Loading />
      ) : (
        <>
          <Card className="px-5 py-4">
            <h2 className="text-sm font-semibold text-forest-900">Current release</h2>
            <dl className="mt-3 space-y-1.5 text-sm">
              <Row k="Release" v={`${status.release.release_id} v${status.release.version}`} />
              <Row k="Source" v={status.release.source ?? "—"} />
              <Row k="Approved" v={status.release.approved ? "yes" : "no"} />
              <Row
                k="Contents"
                v={`${status.counts.concepts} concepts · ${status.counts.flashcards} flashcards · ${status.counts.families} question families`}
              />
            </dl>
          </Card>

          <Card className="mt-4 px-5 py-4">
            <h2 className="text-sm font-semibold text-forest-900">Ingestion boundary</h2>
            <dl className="mt-3 space-y-1.5 text-sm">
              <Row k="Public upload" v={status.ingestion.public_upload_enabled ? "enabled" : "disabled"} />
              <Row k="Write operations" v={status.ingestion.write_operations} />
              <Row k="Pipeline" v={status.ingestion.pipeline} />
            </dl>
            <p className="mt-3 text-xs leading-relaxed text-forest-900/50">
              Pipeline flow: extract (python-pptx) → classify → validate → human review → approved
              release → import. Generated content is never published automatically.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-forest-900/60">{k}</dt>
      <dd className="text-right text-forest-900">{v}</dd>
    </div>
  );
}
