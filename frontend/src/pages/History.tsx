import { api, useApiData, type History as HistoryData } from "../api";
import { Empty, ErrorNote, Loading, PageHeader } from "../ui";

export function History() {
  const { data, error } = useApiData<HistoryData>(() => api.history());

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="History" sub="Recent activity, newest first within each type." />
      {error ? <ErrorNote>{error}</ErrorNote> : null}
      {!data ? (
        <Loading />
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 text-sm font-semibold text-forest-900">Recent tests</h2>
            {data.tests.length === 0 ? (
              <Empty>No tests yet.</Empty>
            ) : (
              <ul className="divide-y divide-paper-200 border border-paper-300 bg-white">
                {data.tests.map((t) => (
                  <li key={t.session_id} className="flex items-center justify-between px-4 py-3 text-sm">
                    <div>
                      <span className="font-medium text-forest-900">
                        {t.question_count}-question test
                      </span>
                      <span className="ml-2 text-xs text-forest-900/50">
                        {new Date(t.submitted_at ?? t.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-forest-900/70">
                      {t.state === "submitted" && t.accuracy !== null ? (
                        <>
                          {t.correct}/{t.question_count} · {Math.round(t.accuracy * 100)}%
                        </>
                      ) : (
                        <span className="text-xs">{t.state}</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-forest-900">Recent learning</h2>
            {data.learning.length === 0 ? (
              <Empty>No concepts viewed yet.</Empty>
            ) : (
              <ul className="divide-y divide-paper-200 border border-paper-300 bg-white">
                {data.learning.map((l, i) => (
                  <li key={`${l.concept_id}-${i}`} className="flex items-center justify-between px-4 py-3 text-sm">
                    <span className="text-forest-900">{l.title}</span>
                    <span className="text-xs text-forest-900/50">
                      {new Date(l.viewed_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-forest-900">Recent flashcards</h2>
            {data.flashcards.length === 0 ? (
              <Empty>No flashcards reviewed yet.</Empty>
            ) : (
              <ul className="divide-y divide-paper-200 border border-paper-300 bg-white">
                {data.flashcards.map((f, i) => (
                  <li key={`${f.flashcard_id}-${i}`} className="flex items-center justify-between px-4 py-3 text-sm">
                    <span className="text-forest-900">
                      {f.flashcard_id}{" "}
                      <span className={f.action === "again" ? "text-clay-600" : "text-forest-600"}>
                        · {f.action}
                      </span>
                    </span>
                    <span className="text-xs text-forest-900/50">
                      {new Date(f.reviewed_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
