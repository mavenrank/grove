import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen } from "lucide-react";
import { api, useApiData, type TestDetail, type TestDetailQuestion } from "../api";
import { Card, Empty, ErrorNote, Loading, PageHeader } from "../ui";

function fmtSecs(s: number | null | undefined): string {
  if (s === null || s === undefined) return "—";
  if (s < 60) return `${Math.round(s)}s`;
  return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

function PaceBadge({ pq }: { pq: TestDetailQuestion }) {
  if (!pq.answered) {
    return <span className="border border-paper-300 px-1.5 py-0.5 text-xs text-forest-900/50">skipped</span>;
  }
  if (pq.is_correct === null) return null;
  if (pq.is_correct) {
    if (pq.pace_vs_personal !== null && pq.pace_vs_personal > 1.5) {
      return <span className="border border-gold-600 bg-gold-500/15 px-1.5 py-0.5 text-xs text-forest-900">slow but correct</span>;
    }
    return <span className="border border-forest-500 bg-forest-50 px-1.5 py-0.5 text-xs text-forest-700">correct</span>;
  }
  if (pq.pace_vs_personal !== null && pq.pace_vs_personal < 0.75) {
    return <span className="border border-clay-500 bg-clay-500/10 px-1.5 py-0.5 text-xs text-clay-600">fast but wrong</span>;
  }
  return <span className="border border-clay-500 bg-clay-500/10 px-1.5 py-0.5 text-xs text-clay-600">wrong</span>;
}

function QuestionRow({ q }: { q: TestDetailQuestion }) {
  return (
    <li className="px-5 py-4">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-mono text-forest-900/40">Q{q.position + 1}</span>
        <span className="bg-forest-100 px-1.5 py-0.5 font-medium text-forest-700">{q.bucket_id}</span>
        <span className="text-forest-900/60">{q.topic_name}</span>
        <span className="text-forest-900/40">›</span>
        <span className="text-forest-900/70">{q.skill_name}</span>
        <span className="text-forest-900/40">· {q.difficulty.replace("_", " ")}</span>
        <span className="ml-auto"><PaceBadge pq={q} /></span>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-forest-900">{q.prompt}</p>

      <ul className="mt-2 space-y-1">
        {Object.entries(q.options).map(([id, text]) => {
          const isChosen = q.chosen === id;
          const isCorrectOpt = q.is_correct !== null && q.correct_option === id;
          return (
            <li
              key={id}
              className={`flex items-start gap-2 px-2 py-1 text-sm ${
                isCorrectOpt
                  ? "border-l-2 border-forest-500 bg-forest-50 text-forest-900"
                  : isChosen
                    ? "border-l-2 border-clay-500 bg-clay-500/10 text-forest-900"
                    : ""
              }`}
            >
              <span className="font-medium text-forest-900/60">{id.toUpperCase()}</span>
              <span className="text-forest-900/80">{text}</span>
            </li>
          );
        })}
      </ul>

      {/* The detailed time-tracking row */}
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-forest-900/60">
        <span>
          Time on question: <strong className="text-forest-900">{fmtSecs(q.dwell_seconds)}</strong>
        </span>
        <span>
          Your median on this type:{" "}
          <strong className="text-forest-900">{fmtSecs(q.personal_median_seconds)}</strong>
        </span>
        {q.pace_vs_personal !== null ? (
          <span className={q.pace_vs_personal > 1.5 ? "text-gold-600" : "text-forest-900/50"}>
            {q.pace_vs_personal > 1.5
              ? `slower than usual (×${q.pace_vs_personal.toFixed(2)})`
              : q.pace_vs_personal < 0.75
                ? `faster than usual (×${q.pace_vs_personal.toFixed(2)})`
                : "at your usual pace"}
          </span>
        ) : null}
        {q.marked ? (
          <span className="text-gold-600">
            marked after {fmtSecs(q.marked_after_seconds)} — came back later
          </span>
        ) : null}
        {q.revisit_count > 0 ? <span>revisited {q.revisit_count}×</span> : null}
        <span>{q.answered ? `answered ${q.chosen?.toUpperCase()}` : "left unanswered"}</span>
        {q.is_correct !== null ? (
          <span>
            correct answer: <strong>{q.correct_option ? q.correct_option.toUpperCase() : "—"}</strong>
          </span>
        ) : null}
      </div>

      {q.explanation ? (
        <div className="mt-2 border-l-2 border-forest-500 pl-3 text-xs leading-relaxed text-forest-900/70">
          {q.explanation}
        </div>
      ) : null}

      {/* Intelligent link-out: same topic in the Learn module */}
      <Link
        to={`/learn/${encodeURIComponent(q.concept_id)}`}
        onMouseEnter={() => api.prefetchConcept(q.concept_id)}
        className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-forest-700 underline hover:text-forest-600"
      >
        <BookOpen size={12} aria-hidden /> Review {q.topic_name} in Learn
      </Link>
    </li>
  );
}

export function TestDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, error: fetchError } = useApiData<TestDetail | null>(
    () => (sessionId ? api.testDetail(sessionId) : Promise.resolve(null)),
  );
  const detail = sessionId ? data : null;
  const error = fetchError
    ? "Could not load this test. It may not be finalized yet."
    : null;

  return (
    <div className="mx-auto max-w-4xl">
      <Link to="/tests" className="mb-4 inline-flex items-center gap-1.5 text-sm text-forest-900/60 hover:text-forest-700">
        <ArrowLeft size={14} /> Back to Tests
      </Link>
      {error ? <ErrorNote>{error}</ErrorNote> : null}
      {!detail && !error ? <Loading /> : null}
      {detail ? (
        <>
          <PageHeader
            title={detail.state === "expired" ? "Test (expired)" : "Test review"}
            sub={`Taken ${new Date(detail.submitted_at ?? detail.created_at).toLocaleString()} · ${
              detail.question_count
            } questions · server-timed ${Math.round(detail.duration_seconds / 60)} min`}
          />

          {detail.score ? (
            <div className="grid grid-cols-4 gap-4">
              <Card className="px-4 py-3">
                <div className="text-xs text-forest-900/60">Correct</div>
                <div className="mt-1 text-2xl font-semibold text-forest-700">{detail.score.correct}</div>
              </Card>
              <Card className="px-4 py-3">
                <div className="text-xs text-forest-900/60">Incorrect</div>
                <div className="mt-1 text-2xl font-semibold text-clay-600">{detail.score.incorrect}</div>
              </Card>
              <Card className="px-4 py-3">
                <div className="text-xs text-forest-900/60">Unanswered</div>
                <div className="mt-1 text-2xl font-semibold text-forest-900/60">{detail.score.unanswered}</div>
              </Card>
              <Card className="px-4 py-3">
                <div className="text-xs text-forest-900/60">Accuracy</div>
                <div className="mt-1 text-2xl font-semibold text-forest-900">
                  {Math.round(detail.score.accuracy * 100)}%
                </div>
              </Card>
            </div>
          ) : (
            <Empty>This test is not finalized yet — metrics appear once it is submitted or expires.</Empty>
          )}

          <h2 className="mt-8 text-sm font-semibold text-forest-900">Question-by-question</h2>
          <p className="mt-1 text-xs text-forest-900/50">
            Active time per question is measured client-side, survives revisits (it accumulates rather
            than restarting), and is compared with your own median on the same skill and family.
          </p>
          <ul className="mt-2 divide-y divide-paper-200 border border-paper-300 bg-white">
            {detail.questions.map((q) => (
              <QuestionRow key={q.position} q={q} />
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
