import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, type TestDetail } from "../api";
import { Button, Card, Empty, ErrorNote, Loading, PageHeader } from "../ui";

export function Results() {
  const location = useLocation();
  const [result, setResult] = useState<TestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sessionId = (location.state as { sessionId?: string } | null)?.sessionId;
    if (!sessionId) {
      setError("No result to show. Start a test from the Tests page.");
      return;
    }
    (async () => {
      try {
        setResult(await api.testDetail(sessionId));
      } catch {
        setError("Could not load this result.");
      }
    })();
  }, [location.state]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader title="Results" />
        <ErrorNote>{error}</ErrorNote>
        <div className="mt-4">
          <Link to="/tests" className="text-sm text-forest-700 underline">Start a test</Link>
        </div>
      </div>
    );
  }
  if (!result) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader title="Results" />
        <Loading />
      </div>
    );
  }

  if (!result.score) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader title="Results" />
        <Empty>This test is not finalized yet — results appear once it is submitted or expires.</Empty>
      </div>
    );
  }
  const { score } = result;
  const avgDwell = (() => {
    const ds = result.questions.filter((q) => q.dwell_seconds !== null).map((q) => q.dwell_seconds as number);
    return ds.length ? ds.reduce((a, b) => a + b, 0) / ds.length : null;
  })();
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title={result.state === "expired" ? "Test expired" : "Test complete"}
        sub={`Scored on the server · release ${result.release_version} · blueprint ${result.blueprint_version}`}
      />

      <div className="grid grid-cols-4 gap-4">
        <Card className="px-4 py-3">
          <div className="text-xs text-forest-900/60">Correct</div>
          <div className="mt-1 text-2xl font-semibold text-forest-700">{score.correct}</div>
        </Card>
        <Card className="px-4 py-3">
          <div className="text-xs text-forest-900/60">Incorrect</div>
          <div className="mt-1 text-2xl font-semibold text-clay-600">{score.incorrect}</div>
        </Card>
        <Card className="px-4 py-3">
          <div className="text-xs text-forest-900/60">Unanswered</div>
          <div className="mt-1 text-2xl font-semibold text-forest-900/60">{score.unanswered}</div>
        </Card>
        <Card className="px-4 py-3">
          <div className="text-xs text-forest-900/60">Accuracy</div>
          <div className="mt-1 text-2xl font-semibold text-forest-900">
            {Math.round(score.accuracy * 100)}%
          </div>
        </Card>
      </div>

      {avgDwell !== null ? (
        <p className="mt-4 text-sm text-forest-900/60">
          Average active time per question: <strong className="text-forest-900">{Math.round(avgDwell)}s</strong>
        </p>
      ) : null}

      <h2 className="mt-8 text-sm font-semibold text-forest-900">Topic breakdown</h2>
      <ul className="mt-2 divide-y divide-paper-200 border border-paper-300 bg-white">
        {Object.entries(
          result.questions.reduce<Record<string, { total: number; correct: number }>>((acc, q) => {
            acc[q.topic_name] ??= { total: 0, correct: 0 };
            acc[q.topic_name].total += 1;
            if (q.is_correct) acc[q.topic_name].correct += 1;
            return acc;
          }, {}),
        ).map(([topic, { total, correct }]) => (
          <li key={topic} className="flex items-center justify-between px-4 py-2.5 text-sm">
            <span className="text-forest-900">{topic}</span>
            <span className={correct / total >= 0.5 ? "text-forest-600" : "text-clay-600"}>
              {correct}/{total}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to={`/tests/${result.session_id}`}>
          <Button>Full question-by-question review</Button>
        </Link>
        <Link to="/history">
          <Button variant="secondary">View history</Button>
        </Link>
        <Link to="/tests">
          <Button variant="secondary">Take another test</Button>
        </Link>
      </div>
    </div>
  );
}
