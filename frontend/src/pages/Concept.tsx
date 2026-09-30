import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Check, ChevronRight, Copy, FolderOpen,
} from "lucide-react";
import {
  api, sourceCaption,
  type Concept, type ConceptExample, type ConceptMedia, type Taxonomy,
} from "../api";
import { Card, ErrorNote, Loading, PageHeader } from "../ui";

function CodeBlock({ block, onOpen }: { block: Concept["code_blocks"][number]; onOpen?: (deckId?: string) => void }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(block.code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable */
    }
  }
  const caption = sourceCaption(block.source);
  return (
    <li className="px-4 py-3">
      <div className="flex items-center justify-between border border-paper-300 border-b-0 bg-paper-100 px-3 py-1.5">
        <span className="font-mono text-[10px] uppercase tracking-wide text-forest-900/50">
          {block.language}
        </span>
        <button
          onClick={() => void copy()}
          className="flex items-center gap-1 text-xs text-forest-700 hover:text-forest-600"
          aria-label="Copy code"
        >
          {copied ? <Check size={12} aria-hidden /> : <Copy size={12} aria-hidden />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto border border-paper-300 bg-forest-900 px-3 py-2.5 text-xs leading-relaxed text-paper-50">
        <code>{block.code}</code>
      </pre>
      {caption ? (
        <SourceCaptionRow caption={caption} onOpen={onOpen} deckId={block.source?.deck_id} />
      ) : null}
    </li>
  );
}

function SourceCaptionRow({ caption, onOpen, deckId }: { caption: string; onOpen?: (deckId?: string) => void; deckId?: string }) {
  return (
    <div className="mt-1.5 flex items-center gap-2 text-[11px] text-forest-900/45">
      <span className="truncate" title={caption}>{caption}</span>
      {onOpen && deckId ? (
        <button
          onClick={() => onOpen(deckId)}
          className="inline-flex shrink-0 items-center gap-1 text-forest-900/40 hover:text-forest-700"
          title="Open this deck's folder in File Explorer"
          aria-label={`Open source deck for ${caption}`}
        >
          <FolderOpen size={11} aria-hidden /> open
        </button>
      ) : null}
    </div>
  );
}

function ExampleBlock({ ex, onOpen }: { ex: ConceptExample; onOpen?: (deckId?: string) => void }) {
  return (
    <li className="px-4 py-3">
      <p className="text-sm leading-relaxed text-forest-900">{ex.prompt}</p>
      {Object.keys(ex.options).length > 0 ? (
        <ul className="mt-2 space-y-1">
          {Object.entries(ex.options).map(([id, text]) => {
            const isAnswer = ex.answer !== null && ex.answer.toLowerCase() === id.toLowerCase();
            return (
              <li
                key={id}
                className={`flex items-start gap-2 px-2 py-1 text-sm ${
                  isAnswer ? "border-l-2 border-forest-500 bg-forest-50 text-forest-900" : "text-forest-900/80"
                }`}
              >
                <span className="font-medium text-forest-900/60">{id.toUpperCase()}</span>
                <span>{text}</span>
                {isAnswer ? (
                  <span className="ml-auto text-xs font-medium text-forest-600">answer</span>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
      {ex.explanation ? (
        <div className="mt-2 border-l-2 border-forest-500 pl-3 text-xs leading-relaxed text-forest-900/70">
          {ex.explanation}
        </div>
      ) : null}
      {ex.source?.deck_id ? (
        <SourceCaptionRow
          caption={sourceCaption(ex.source) ?? ex.source.deck_id}
          onOpen={onOpen}
          deckId={ex.source.deck_id}
        />
      ) : null}
    </li>
  );
}

function MediaBlock({ m, onOpen }: { m: ConceptMedia; onOpen?: (deckId?: string) => void }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .media(m.image_id)
      .then((url) => {
        if (alive) setSrc(url);
      })
      .catch(() => {
        if (alive) setFailed(true);
      });
    return () => {
      alive = false;
    };
  }, [m.image_id]);

  if (failed) return null;
  return (
    <li className="px-4 py-3">
      {src ? (
        <img src={src} alt="Teaching slide from source deck" className="max-h-64 border border-paper-200" />
      ) : (
        <div className="h-40 animate-pulse bg-paper-100" />
      )}
      {m.source?.deck_id ? (
        <SourceCaptionRow
          caption={sourceCaption(m.source) ?? m.source.deck_id}
          onOpen={onOpen}
          deckId={m.source.deck_id}
        />
      ) : null}
    </li>
  );
}

export function ConceptPage() {
  const { conceptId } = useParams<{ conceptId: string }>();
  const [concept, setConcept] = useState<Concept | null>(null);
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [allConcepts, setAllConcepts] = useState<Concept[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openFailed, setOpenFailed] = useState(false);

  useEffect(() => {
    if (!conceptId) return;
    (async () => {
      try {
        const c = await api.concept(conceptId);
        setConcept(c);
        void api.recordConceptView(c.id, c.title).catch(() => undefined);
      } catch {
        setError("Could not load this concept.");
      }
    })();
  }, [conceptId]);

  useEffect(() => {
    (async () => {
      try {
        const [t, cs] = await Promise.all([api.taxonomy(), api.concepts()]);
        setTaxonomy(t);
        setAllConcepts(cs);
      } catch {
        /* nav context is optional */
      }
    })();
  }, []);

  // navigation context: bucket > topic > siblings
  const nav = useMemo(() => {
    if (!taxonomy || !allConcepts || !concept) return null;
    let bucketName = "";
    let topic: { id: string; name: string } | null = null;
    for (const b of taxonomy.buckets) {
      for (const t of b.topics) {
        if (t.skills.some((s) => s.id === concept.skill_id)) {
          bucketName = b.name;
          topic = { id: t.id, name: t.name };
        }
      }
    }
    const topicBySkill = new Map<string, string>();
    for (const b of taxonomy.buckets) {
      for (const t of b.topics) {
        for (const s of t.skills) topicBySkill.set(s.id, t.id);
      }
    }
    const siblings = allConcepts.filter((c) => topicBySkill.get(c.skill_id) === topic?.id);
    const idx = siblings.findIndex((c) => c.id === concept.id);
    const orderedSiblings = idx >= 0 ? siblings : [concept, ...siblings];
    const selfIdx = orderedSiblings.findIndex((c) => c.id === concept.id);
    return {
      bucketName,
      topic,
      prev: selfIdx > 0 ? orderedSiblings[selfIdx - 1] : null,
      next: selfIdx < orderedSiblings.length - 1 ? orderedSiblings[selfIdx + 1] : null,
      position: orderedSiblings.length > 1 ? `${selfIdx + 1} of ${orderedSiblings.length}` : null,
    };
  }, [taxonomy, allConcepts, concept]);

  // deck_id -> explorer path for per-item "open in file manager"
  const deckPaths = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of concept?.source_decks ?? []) map.set(d.deck_id, d.source_path);
    return map;
  }, [concept]);

  async function openDeck(deckId?: string) {
    const path = deckId ? deckPaths.get(deckId) : concept?.source_decks?.[0]?.source_path;
    if (!path) return;
    try {
      await api.openSource(path);
      setOpenFailed(false);
    } catch {
      setOpenFailed(true);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="mb-4 flex items-center gap-1.5 text-sm text-forest-900/60">
        <Link to="/learn" className="inline-flex items-center gap-1.5 hover:text-forest-700">
          <ArrowLeft size={14} /> Learn
        </Link>
        {nav?.topic ? (
          <>
            <ChevronRight size={13} className="text-forest-900/30" aria-hidden />
            <span>{nav.topic.name}</span>
          </>
        ) : null}
        <ChevronRight size={13} className="text-forest-900/30" aria-hidden />
        <span className="font-medium text-forest-900">{concept?.title ?? "…"}</span>
      </nav>

      {error ? <ErrorNote>{error}</ErrorNote> : null}
      {!concept ? <Loading /> : (
        <>
          <PageHeader
            title={concept.title}
            sub={nav ? `${nav.bucketName} · ${nav.topic?.name ?? concept.skill_id}` : concept.skill_id}
          />

          {nav && (nav.prev || nav.next) ? (
            <div className="mb-6 flex items-center justify-between gap-3 text-sm">
              {nav.prev ? (
                <Link
                  to={`/learn/${encodeURIComponent(nav.prev.id)}`}
                  onMouseEnter={() => nav.prev && api.prefetchConcept(nav.prev.id)}
                  className="inline-flex items-center gap-1.5 border border-paper-300 px-3 py-1.5 text-forest-900/70 hover:border-forest-500 hover:text-forest-700"
                >
                  <ArrowLeft size={13} aria-hidden /> {nav.prev.title}
                </Link>
              ) : <span />}
              {nav.position ? (
                <span className="text-xs text-forest-900/40">{nav.position}</span>
              ) : <span />}
              {nav.next ? (
                <Link
                  to={`/learn/${encodeURIComponent(nav.next.id)}`}
                  onMouseEnter={() => nav.next && api.prefetchConcept(nav.next.id)}
                  className="inline-flex items-center gap-1.5 border border-paper-300 px-3 py-1.5 text-forest-900/70 hover:border-forest-500 hover:text-forest-700"
                >
                  {nav.next.title} <ArrowRight size={13} aria-hidden />
                </Link>
              ) : <span />}
            </div>
          ) : null}

          <Card className="px-5 py-4">
            <h2 className="text-sm font-semibold text-forest-900">Summary</h2>
            <p className="mt-2 text-sm leading-relaxed text-forest-900/80">{concept.summary}</p>
          </Card>

          {/* Formulas left, teaching slides top-right — the slide IS the lesson */}
          {concept.formulas.length > 0 || concept.media.length > 0 ? (
            <div className={`mt-4 gap-4 ${concept.formulas.length > 0 && concept.media.length > 0 ? "grid md:grid-cols-2" : ""}`}>
              {concept.formulas.length > 0 ? (
                <Card className="px-5 py-4">
                  <h2 className="text-sm font-semibold text-forest-900">Formulas &amp; rules</h2>
                  <ul className="mt-2 space-y-1.5">
                    {concept.formulas.map((f, i) => (
                      <li key={i} className="border-l-2 border-forest-500 pl-3 text-sm text-forest-900/80">
                        {f}
                      </li>
                    ))}
                  </ul>
                </Card>
              ) : null}
              {concept.media.length > 0 ? (
                <Card className="px-0 py-4">
                  <h2 className="px-5 text-sm font-semibold text-forest-900">
                    Teaching slides <span className="font-normal text-forest-900/40">({concept.media.length})</span>
                  </h2>
                  <ul className="mt-2 space-y-2">
                    {concept.media.map((m, i) => (
                      <MediaBlock key={i} m={m} onOpen={(deckId) => void openDeck(deckId)} />
                    ))}
                  </ul>
                </Card>
              ) : null}
            </div>
          ) : null}

          {concept.code_blocks.length > 0 ? (
            <Card className="mt-4 px-0 py-4">
              <h2 className="px-5 text-sm font-semibold text-forest-900">Code walkthroughs</h2>
              <ul className="mt-2 space-y-3">
                {concept.code_blocks.map((b, i) => (
                  <CodeBlock key={i} block={b} onOpen={(deckId) => void openDeck(deckId)} />
                ))}
              </ul>
            </Card>
          ) : null}

          {concept.examples.length > 0 ? (
            <Card className="mt-4 px-0 py-4">
              <h2 className="px-5 text-sm font-semibold text-forest-900">
                Worked examples <span className="font-normal text-forest-900/40">({concept.examples.length})</span>
              </h2>
              <ul className="mt-2 divide-y divide-paper-200">
                {concept.examples.map((ex, i) => (
                  <ExampleBlock key={i} ex={ex} onOpen={(deckId) => void openDeck(deckId)} />
                ))}
              </ul>
            </Card>
          ) : null}

          {concept.common_mistakes.length > 0 ? (
            <Card className="mt-4 px-5 py-4">
              <h2 className="text-sm font-semibold text-forest-900">Common mistakes</h2>
              <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-forest-900/80">
                {concept.common_mistakes.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </Card>
          ) : null}

          {/* Citations: short name up top, full provenance + explorer open here */}
          {concept.source_decks?.length > 0 ? (
            <Card className="mt-4 px-5 py-4">
              <h2 className="text-sm font-semibold text-forest-900">Citations</h2>
              <p className="mt-1 text-xs text-forest-900/45">
                Full sources for every example and slide on this page.
              </p>
              <ul className="mt-2 space-y-2">
                {concept.source_decks.map((d, i) => (
                  <li key={d.deck_id} className="flex items-start justify-between gap-3 text-sm">
                    <span className="min-w-0">
                      <span className="text-forest-900/80">
                        [{i + 1}] {d.short_name ?? d.source_file}
                      </span>
                      <span className="ml-2 text-xs text-forest-900/40">{d.slide_count} slides</span>
                      <span className="block truncate text-[11px] text-forest-900/35" title={d.source_file}>
                        {d.source_file}
                      </span>
                    </span>
                    <button
                      onClick={() => void openDeck(d.deck_id)}
                      className="inline-flex shrink-0 items-center gap-1.5 border border-paper-300 px-2.5 py-1 text-xs text-forest-700 hover:border-forest-500"
                      title="Reveal this deck in File Explorer"
                    >
                      <FolderOpen size={12} aria-hidden /> Open
                    </button>
                  </li>
                ))}
              </ul>
              {openFailed ? (
                <p className="mt-2 text-xs text-clay-600">
                  Could not open the file explorer (backend may be running on another machine).
                </p>
              ) : null}
            </Card>
          ) : null}

          {/* Bottom prev/next for the reading flow */}
          {nav && (nav.prev || nav.next) ? (
            <div className="mt-6 flex items-center justify-between gap-3 border-t border-paper-200 pt-4 text-sm">
              {nav.prev ? (
                <Link
                  to={`/learn/${encodeURIComponent(nav.prev.id)}`}
                  onMouseEnter={() => nav.prev && api.prefetchConcept(nav.prev.id)}
                  className="inline-flex items-center gap-1.5 text-forest-700 hover:text-forest-600"
                >
                  <ArrowLeft size={13} aria-hidden /> {nav.prev.title}
                </Link>
              ) : <span />}
              {nav.next ? (
                <Link
                  to={`/learn/${encodeURIComponent(nav.next.id)}`}
                  onMouseEnter={() => nav.next && api.prefetchConcept(nav.next.id)}
                  className="inline-flex items-center gap-1.5 text-forest-700 hover:text-forest-600"
                >
                  {nav.next.title} <ArrowRight size={13} aria-hidden />
                </Link>
              ) : <span />}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
