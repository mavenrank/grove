import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";
import { api, useApiData, type Concept, type Taxonomy } from "../api";
import { Card, ErrorNote, Loading, PageHeader } from "../ui";

/** Learn: bucket → topic accordion. Expanding a topic lists its concepts. */
export function Learn() {
  const { data: taxonomy, error: taxError } = useApiData<Taxonomy>(() => api.taxonomy());
  const { data: concepts, error: conceptError } = useApiData<Concept[]>(() => api.concepts());
  const [openTopics, setOpenTopics] = useState<Set<string>>(new Set());
  const error = taxError ?? conceptError;

  // start with the first topic of each bucket open (preserve user state on refresh)
  useEffect(() => {
    if (!taxonomy) return;
    setOpenTopics((prev) => {
      if (prev.size > 0) return prev;
      const first = new Set<string>();
      for (const b of taxonomy.buckets) {
        if (b.topics[0]) first.add(b.topics[0].id);
      }
      return first;
    });
  }, [taxonomy]);

  // exact mapping: concept -> topic that declares its skill
  const conceptsByTopic = useMemo(() => {
    const map = new Map<string, Concept[]>();
    if (!taxonomy || !concepts) return map;
    const topicBySkill = new Map<string, string>();
    for (const b of taxonomy.buckets) {
      for (const t of b.topics) {
        for (const s of t.skills) topicBySkill.set(s.id, t.id);
      }
    }
    for (const c of concepts) {
      const topicId = topicBySkill.get(c.skill_id);
      if (!topicId) continue;
      const list = map.get(topicId) ?? [];
      list.push(c);
      map.set(topicId, list);
    }
    return map;
  }, [taxonomy, concepts]);

  function toggleTopic(topicId: string) {
    setOpenTopics((prev) => {
      const next = new Set(prev);
      if (next.has(topicId)) next.delete(topicId);
      else next.add(topicId);
      return next;
    });
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Learn"
        sub="Concepts, formulas, worked examples, and the original teaching slides from approved content."
      />
      {error ? <ErrorNote>{error}</ErrorNote> : null}
      {!taxonomy || !concepts ? (
        <Loading />
      ) : (
        <div className="space-y-8">
          {taxonomy.buckets.map((b) => {
            const bucketTopics = b.topics.filter((t) => (conceptsByTopic.get(t.id) ?? []).length > 0);
            return (
              <section key={b.id}>
                <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-forest-900/50">
                  {b.name}
                </h2>
                {bucketTopics.length === 0 ? (
                  <Card className="px-4 py-4 text-sm text-forest-900/40">
                    No published concepts in this bucket yet.
                  </Card>
                ) : (
                  <div className="divide-y divide-paper-200 border border-paper-300 bg-white">
                    {bucketTopics.map((t) => {
                      const items = conceptsByTopic.get(t.id) ?? [];
                      const open = openTopics.has(t.id);
                      return (
                        <div key={t.id}>
                          <button
                            onClick={() => toggleTopic(t.id)}
                            aria-expanded={open}
                            className="flex w-full items-center gap-2 px-4 py-3 text-left hover:bg-paper-50"
                          >
                            {open ? (
                              <ChevronDown size={15} className="text-forest-700" aria-hidden />
                            ) : (
                              <ChevronRight size={15} className="text-forest-900/40" aria-hidden />
                            )}
                            <span className="flex-1 text-sm font-medium text-forest-900">{t.name}</span>
                            <span className="text-xs text-forest-900/40">{items.length}</span>
                          </button>
                          {open ? (
                            <ul className="border-t border-paper-200 bg-paper-50">
                              {items.map((c) => (
                                <li key={c.id}>
                                  <Link
                                    to={`/learn/${encodeURIComponent(c.id)}`}
                                    onMouseEnter={() => api.prefetchConcept(c.id)}
                                    onFocus={() => api.prefetchConcept(c.id)}
                                    className="flex items-center justify-between py-2.5 pl-10 pr-4 text-sm hover:bg-paper-100"
                                  >
                                    <span className="flex items-center gap-2 text-forest-900">
                                      <BookOpen size={13} className="text-forest-900/30" aria-hidden />
                                      {c.title}
                                    </span>
                                    <span className="text-xs text-forest-900/40">
                                      {c.examples.length > 0 ? `${c.examples.length} examples` : ""}
                                      {c.media.length > 0 ? ` · ${c.media.length} slides` : ""}
                                    </span>
                                  </Link>
                                </li>
                              ))}
                            </ul>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
