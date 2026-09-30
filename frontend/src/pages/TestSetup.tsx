import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, SquarePen } from "lucide-react";
import { api, useApiData, type History, type HistoryEntryTest } from "../api";
import { Button, Card, Empty, ErrorNote, Loading, PageHeader } from "../ui";

const COUNTS = [5, 10, 15, 20]; // final values belong to the server blueprint

export function TestSetup() {
  const navigate = useNavigate();
  const [count, setCount] = useState(10);
  const [customMinutes, setCustomMinutes] = useState<string>("");
  const { data: history, error } = useApiData<History>(() => api.history());
  const tests: HistoryEntryTest[] | null = history?.tests ?? null;

  // duration: custom number input, falling back to 1 min/question.
  const parsedMinutes = customMinutes.trim() === "" ? null : Math.max(1, Math.min(180, Number(customMinutes)));
  const customInvalid = customMinutes.trim() !== "" &&
    (Number.isNaN(Number(customMinutes)) || Number(customMinutes) < 1 || Number(customMinutes) > 180);
  const effectiveMinutes = parsedMinutes ?? count;

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Take a Test" sub="Questions are delivered one at a time by the backend and scored on the server." />

      <Card className="px-6 py-6">
        <div className="flex items-center gap-3">
          <SquarePen size={18} className="text-forest-600" aria-hidden />
          <h2 className="text-sm font-semibold text-forest-900">Test setup</h2>
        </div>

        <div className="mt-5">
          <div className="text-sm text-forest-900/70">Number of questions</div>
          <div className="mt-2 flex gap-2">
            {COUNTS.map((c) => (
              <button
                key={c}
                onClick={() => setCount(c)}
                aria-pressed={count === c}
                className={`border px-5 py-2.5 text-sm font-medium ${
                  count === c
                    ? "border-forest-600 bg-forest-600 text-paper-50"
                    : "border-paper-300 bg-white text-forest-900 hover:border-forest-500"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-5 border-t border-paper-200 pt-4">
          <div className="text-sm text-forest-900/70">Time allowed</div>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2">
              <input
                type="number"
                inputMode="numeric"
                min={1}
                max={180}
                step={1}
                value={customMinutes}
                onChange={(e) => setCustomMinutes(e.target.value)}
                placeholder="—"
                aria-label="Custom time in minutes"
                className={`w-20 border bg-white px-3 py-2 text-sm font-medium text-forest-900 outline-none ${
                  customInvalid
                    ? "border-clay-500"
                    : customMinutes.trim() !== ""
                      ? "border-forest-600"
                      : "border-paper-300 focus:border-forest-500"
                }`}
              />
              <span className="text-sm text-forest-900/70">minutes</span>
            </label>
            <span className="text-xs text-forest-900/40">leave empty for the default pace</span>
          </div>
          <div className="mt-2 text-lg font-semibold text-forest-900">
            {effectiveMinutes} minute{effectiveMinutes === 1 ? "" : "s"}
            <span className="ml-2 text-xs font-normal text-forest-900/50">
              {customMinutes.trim() === ""
                ? "1 minute per question"
                : `≈ ${Math.round((effectiveMinutes * 60) / count)}s per question`}
            </span>
          </div>
          {customInvalid ? (
            <p className="mt-1 text-xs text-clay-600">Enter a whole number between 1 and 180.</p>
          ) : (
            <p className="mt-1 text-xs text-forest-900/40">
              The server sets the official deadline when the test starts.
            </p>
          )}
        </div>

        <div className="mt-6">
          <Button
            disabled={customInvalid}
            onClick={() =>
              navigate("/tests/run", {
                state: {
                  testConfig: {
                    count,
                    duration_minutes: parsedMinutes ?? undefined,
                  },
                },
              })
            }
          >
            Enter Test mode
          </Button>
        </div>
      </Card>

      <p className="mt-4 text-xs leading-relaxed text-forest-900/40">
        During the test you can answer, change answers, revisit questions, and mark items for
        review. Correctness and scoring stay on the server until you submit. Test mode runs
        chrome-less: navigation, copy, and context menus are disabled while it is active.
      </p>

      <section className="mt-10">
        <h2 className="text-sm font-semibold text-forest-900">Your tests</h2>
        <p className="mt-1 text-xs text-forest-900/50">
          Every test you have taken, with per-question timing and topic review.
        </p>
        {error ? <ErrorNote>{error}</ErrorNote> : null}
        {!tests && !error ? (
          <Loading />
        ) : tests && tests.length === 0 ? (
          <Empty>No tests yet — your first one will appear here.</Empty>
        ) : tests ? (
          <ul className="mt-3 divide-y divide-paper-200 border border-paper-300 bg-white">
            {tests.map((t) => (
              <li key={t.session_id}>
                <button
                  onClick={() => navigate(`/tests/${t.session_id}`)}
                  onMouseEnter={() => api.prefetch(`/api/history/tests/${encodeURIComponent(t.session_id)}`)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left text-sm hover:bg-paper-50"
                >
                  <div>
                    <div className="font-medium text-forest-900">
                      {t.question_count}-question test
                      {t.state === "expired" ? (
                        <span className="ml-2 border border-gold-600 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-gold-600">
                          expired
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-0.5 text-xs text-forest-900/50">
                      {new Date(t.submitted_at ?? t.created_at).toLocaleString()}
                      {t.duration_seconds ? ` · ${Math.round(t.duration_seconds / 60)} min` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {t.state === "submitted" && t.accuracy !== null ? (
                      <span className={t.accuracy >= 0.6 ? "text-forest-600" : "text-clay-600"}>
                        {t.correct}/{t.question_count} · {Math.round(t.accuracy * 100)}%
                      </span>
                    ) : (
                      <span className="text-xs text-forest-900/50">{t.state}</span>
                    )}
                    <ChevronRight size={15} className="text-forest-900/30" aria-hidden />
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
