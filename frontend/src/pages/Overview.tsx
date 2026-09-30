import { Link, useNavigate } from "react-router-dom";
import { BookOpen, Eye, Flame, SquarePen, Target } from "lucide-react";
import { api, useApiData, type History, type Insights, type SkillInsight } from "../api";
import { Button, Card, ErrorNote, IconTip, PageHeader } from "../ui";

const BAND_STYLE: Record<SkillInsight["ui_group"], string> = {
  strong: "border-forest-500 bg-forest-50 text-forest-700",
  on_track: "border-forest-500 bg-forest-50 text-forest-700",
  needs_practice: "border-gold-600 bg-gold-500/15 text-forest-900",
  weak: "border-clay-500 bg-clay-500/10 text-clay-600",
  low_evidence: "border-paper-300 text-forest-900/60",
  unseen: "border-paper-300 text-forest-900/40",
};

const BAND_LABEL: Record<SkillInsight["ui_group"], string> = {
  strong: "Strong",
  on_track: "On track",
  needs_practice: "Needs practice",
  weak: "Weak — relearn",
  low_evidence: "Low evidence",
  unseen: "Not started",
};

export function Overview() {
  const navigate = useNavigate();
  const { data: history, error: historyError } = useApiData<History>(() => api.history());
  const { data: insights, error: insightsError } = useApiData<Insights>(() => api.insights());
  const error = historyError ?? insightsError;

  const testsDone = history?.tests.filter((t) => t.state === "submitted").length ?? 0;
  const recentAccuracy = (() => {
    const accs = (history?.tests ?? [])
      .filter((t) => t.accuracy !== null)
      .slice(0, 5)
      .map((t) => t.accuracy as number);
    if (!accs.length) return null;
    return accs.reduce((a, b) => a + b, 0) / accs.length;
  })();

  const skills = insights?.skills ?? [];
  const attention = skills.filter((s) => s.ui_group === "weak" || s.ui_group === "needs_practice").slice(0, 5);
  const strong = skills.filter((s) => s.ui_group === "strong").slice(0, 3);

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Today's work" />

      {error ? <ErrorNote>{error}</ErrorNote> : null}

      {/* One clear primary action */}
      <Card className="flex items-center justify-between px-6 py-5">
        <div>
          <div className="text-sm font-medium text-forest-900">Take a test</div>
          <div className="mt-0.5 text-xs text-forest-900/50">
            5–20 questions · timed by the server · scored on the server
          </div>
        </div>
        <Button onClick={() => navigate("/tests")}>
          <span className="inline-flex items-center gap-2">
            <SquarePen size={15} /> Enter Test mode
          </span>
        </Button>
      </Card>

      {/* Compact side-by-side indicators */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <Metric
          icon={<Flame size={15} />}
          tip="Practice streak — consecutive days with reviewed cards or tests"
          label="Streak"
          value={"0 days"}
          tone="clay"
        />
        <Metric
          icon={<Target size={15} />}
          tip="Average accuracy over your recent tests"
          label="Accuracy"
          value={recentAccuracy === null ? "—" : `${Math.round(recentAccuracy * 100)}%`}
          tone="forest"
        />
        <Metric
          icon={<Eye size={15} />}
          tip="Tests finalized so far"
          label="Tests given"
          value={String(testsDone)}
          tone="gold"
        />
      </div>

      {/* Skills that deserve attention, with the evidence reason + Learn link */}
      <section className="mt-8">
        <h2 className="text-sm font-semibold text-forest-900">Deserves attention</h2>
        <p className="mt-1 text-xs text-forest-900/50">
          Evidence status per skill (handoff §9): accuracy, pace against your own median, and
          consistency. Links go straight to the matching concept in Learn.
        </p>
        {attention.length === 0 ? (
          <p className="mt-2 text-sm text-forest-900/50">
            {skills.length === 0
              ? "Take your first test to build skill evidence."
              : "No weak areas right now — take a test to keep evidence fresh."}
          </p>
        ) : (
          <ul className="mt-2 divide-y divide-paper-200 border border-paper-300 bg-white">
            {attention.map((s) => (
              <li key={s.skill_id} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
                <div className="min-w-0">
                  <div className="font-medium text-forest-900">{s.skill_name}</div>
                  <div className="mt-0.5 text-xs text-forest-900/50">
                    {s.topic_name} · {Math.round((s.accuracy ?? 0) * 100)}% over {s.attempts} attempts
                    {s.median_dwell_seconds !== null ? ` · ${Math.round(s.median_dwell_seconds)}s median` : ""}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className={`border px-1.5 py-0.5 text-xs ${BAND_STYLE[s.ui_group]}`}>
                    {BAND_LABEL[s.ui_group]}
                  </span>
                  <Link
                    to={`/learn/${encodeURIComponent(s.concept_id)}`}
                    onMouseEnter={() => api.prefetchConcept(s.concept_id)}
                    className="border border-forest-600 px-2 py-1 text-xs font-medium text-forest-700 hover:bg-forest-50"
                  >
                    Learn
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Running strong */}
      {strong.length > 0 ? (
        <section className="mt-8">
          <h2 className="text-sm font-semibold text-forest-900">Running strong</h2>
          <ul className="mt-2 divide-y divide-paper-200 border border-paper-300 bg-white">
            {strong.map((s) => (
              <li key={s.skill_id} className="flex items-center justify-between px-4 py-3 text-sm">
                <span className="text-forest-900">{s.skill_name}</span>
                <span className="text-xs text-forest-900/60">
                  {Math.round((s.accuracy ?? 0) * 100)}% · keep it warm
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* Next study suggestion */}
      <section className="mt-8">
        <h2 className="text-sm font-semibold text-forest-900">Next study</h2>
        <Card className="mt-2 flex items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3 text-sm text-forest-900">
            <BookOpen size={16} className="text-forest-600" aria-hidden />
            Browse concepts in Learn
          </div>
          <Link
            to="/learn"
            className="border border-forest-600 px-3 py-1.5 text-xs font-medium text-forest-700 hover:bg-forest-50"
          >
            Open Learn
          </Link>
        </Card>
      </section>
    </div>
  );
}

function Metric({
  icon,
  tip,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  tip: string;
  label: string;
  value: string;
  tone: "forest" | "clay" | "gold";
}) {
  const bg = { forest: "bg-forest-100", clay: "bg-clay-500/10", gold: "bg-gold-500/15" }[tone];
  return (
    <Card className={`${bg} px-4 py-3`}>
      <div className="flex items-center gap-2">
        <IconTip label={tip}>
          <span tabIndex={0} className="text-forest-700">
            {icon}
          </span>
        </IconTip>
        <span className="text-xs text-forest-900/60">{label}</span>
      </div>
      <div className="mt-1 text-xl font-semibold text-forest-900">{value}</div>
    </Card>
  );
}
