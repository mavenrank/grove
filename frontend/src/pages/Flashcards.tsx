import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2, CircleDot, GraduationCap, Layers, RotateCcw, Sparkles, X,
} from "lucide-react";
import {
  api, useApiData, type FlashcardDeck, type FlashcardSessionCard, type Taxonomy,
} from "../api";
import { Button, Card, Empty, ErrorNote, Loading, PageHeader } from "../ui";

type Phase = "deck" | "session" | "done";

interface SessionResult {
  again: number;
  good: number;
  easy: number;
  total: number;
}

const KIND_META: Record<string, { label: string; cls: string }> = {
  formula: { label: "Formula", cls: "border-forest-500 text-forest-700" },
  rule: { label: "Rule", cls: "border-paper-300 text-forest-900/60" },
  approach: { label: "Approach", cls: "border-gold-600 text-gold-600" },
};

const STATE_BADGE: Record<string, { label: string; cls: string }> = {
  new: { label: "New", cls: "bg-forest-100 text-forest-700" },
  learning: { label: "Learning", cls: "bg-gold-500/15 text-gold-600" },
  review: { label: "Review", cls: "bg-paper-200 text-forest-900/60" },
  strong: { label: "Strong", cls: "bg-forest-600/10 text-forest-700" },
};

/** Render **bold** spans inside authored card text. */
function Rich({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? (
          <strong key={i} className="font-semibold text-forest-900">{p.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}

export function Flashcards() {
  const { data: decks } = useApiData<FlashcardDeck[]>(() => api.flashcardDecks());
  const { data: taxonomy } = useApiData<Taxonomy>(() => api.taxonomy());

  const [phase, setPhase] = useState<Phase>("deck");
  const [deckTopic, setDeckTopic] = useState<string | null>(null); // null = all
  const [limit, setLimit] = useState(20);

  // session state
  const [queue, setQueue] = useState<FlashcardSessionCard[]>([]);
  const [pos, setPos] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [result, setResult] = useState<SessionResult>({ again: 0, good: 0, easy: 0, total: 0 });
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const seenRef = useRef<Set<string>>(new Set());

  const card = queue[pos];

  const posRef = useRef(pos);
  posRef.current = pos;
  const flippedRef = useRef(flipped);
  flippedRef.current = flipped;
  const cardRef = useRef<FlashcardSessionCard | null>(null);
  cardRef.current = card;
  const busyRef = useRef(busy);
  busyRef.current = busy;
  const queueLenRef = useRef(queue.length);
  queueLenRef.current = queue.length;

  // skill names for the completion screen
  const skillName = useMemo(() => {
    if (!taxonomy) return new Map<string, string>();
    const m = new Map<string, string>();
    for (const b of taxonomy.buckets)
      for (const t of b.topics)
        for (const s of t.skills) m.set(s.id, s.name);
    return m;
  }, [taxonomy]);

  function startSession(topic: string | null) {
    setDeckTopic(topic);
    setSessionError(null);
    setPhase("session");
    setQueue([]);
    setPos(0);
    setFlipped(false);
    setResult({ again: 0, good: 0, easy: 0, total: 0 });
    api.flashcardSession(limit, topic ?? undefined)
      .then((cards) => {
        if (cards.length === 0) {
          setPhase("deck");
          setSessionError("Nothing due right now — all caught up. Come back later or pick another deck.");
          return;
        }
        setQueue(cards);
      })
      .catch(() => {
        setPhase("deck");
        setSessionError("Could not load the review session. Is the backend running?");
      });
  }

  /** Record a view once per card (server dedupes across sessions). */
  useEffect(() => {
    if (phase !== "session" || !card || seenRef.current.has(card.id)) return;
    seenRef.current.add(card.id);
    void api.recordFlashcardViews([card.id]).catch(() => undefined);
  }, [phase, card]);

  const flip = useCallback(() => setFlipped((f) => !f), []);

  // space / enter flips; 1/2/3 grade (only meaningful after the flip)
  useEffect(() => {
    if (phase !== "session") return;
    const h = (e: KeyboardEvent) => {
      if (e.code === "Space" || e.code === "Enter") {
        e.preventDefault();
        flip();
        return;
      }
      if (flippedRef.current && (e.key === "1" || e.key === "2" || e.key === "3")) {
        e.preventDefault();
        const rating = e.key === "1" ? "again" : e.key === "2" ? "good" : "easy";
        void grade(rating);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
    // grade reads queue/pos/busy via refs of the live render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, flip]);

  async function grade(rating: "again" | "good" | "easy") {
    const card = cardRef.current;
    if (!card || busyRef.current) return;
    setBusy(true);
    try {
      await api.gradeFlashcard(card.id, rating);
      setResult((r) => ({ ...r, [rating]: r[rating] + 1, total: r.total + 1 }));
      if (rating === "again") {
        // recycle: push a copy to the end of today's queue (Quizlet-style)
        setQueue((q) => [...q, card]);
      }
      if (posRef.current + 1 >= queueLenRef.current + (rating === "again" ? 1 : 0)) {
        setPhase("done");
      } else {
        setPos((p) => p + 1);
        setFlipped(false);
      }
    } catch {
      setSessionError("Could not save that grade. Check the backend and try again.");
    } finally {
      setBusy(false);
    }
  }

  const deckName = (topicId: string | null) => {
    if (!topicId) return "All decks";
    return decks?.find((d) => d.topic_id === topicId)?.topic_name ?? topicId;
  };

  // ------------------------------------------------------------------ deck
  if (phase === "deck") {
    const totalDue = decks?.reduce((n, d) => n + d.due_cards, 0) ?? 0;
    const totalNew = decks?.reduce((n, d) => n + d.new_cards, 0) ?? 0;
    return (
      <div className="mx-auto max-w-4xl">
        <PageHeader
          title="Flashcards"
          sub="Formula and rule recall with spaced repetition — what you rate 'again' comes back sooner."
        />
        {sessionError ? <ErrorNote>{sessionError}</ErrorNote> : null}

        {/* Session length */}
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-forest-900/50">Session length:</span>
          {[10, 20, 30].map((n) => (
            <button
              key={n}
              onClick={() => setLimit(n)}
              aria-pressed={limit === n}
              className={`border px-2.5 py-1 ${
                limit === n
                  ? "border-forest-600 bg-forest-100 text-forest-700"
                  : "border-paper-300 text-forest-900/60 hover:bg-paper-100"
              }`}
            >
              {n} cards
            </button>
          ))}
        </div>

        {/* Deck grid */}
        {!decks ? (
          <Loading />
        ) : decks.length === 0 ? (
          <Empty>No flashcard decks in this release yet.</Empty>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <button
              key="__all__"
              onClick={() => startSession(null)}
              className="group border border-forest-600 bg-forest-600 p-4 text-left text-paper-50 transition hover:bg-forest-700"
            >
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-semibold">
                  <Sparkles className="h-4 w-4" /> Mixed review
                </span>
                {totalDue + totalNew > 0 && (
                  <span className="border border-paper-50/40 px-1.5 py-0.5 text-xs">
                    {totalDue + totalNew} ready
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-paper-50/70">
                Due cards across every topic, most overdue first.
              </p>
            </button>
            {decks.map((d) => (
              <button
                key={d.topic_id}
                onClick={() => startSession(d.topic_id)}
                className="group border border-paper-300 bg-white p-4 text-left transition hover:border-forest-500"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-xs uppercase tracking-wide text-forest-900/40">{d.bucket_name}</div>
                    <div className="text-sm font-semibold text-forest-900">{d.topic_name}</div>
                  </div>
                  {d.due_cards > 0 && (
                    <span className="bg-gold-500/15 px-1.5 py-0.5 text-xs font-semibold text-gold-600">
                      {d.due_cards} due
                    </span>
                  )}
                </div>
                {/* mastery bar: strong share of the deck */}
                <div className="mt-3 h-1.5 w-full bg-paper-200">
                  <div
                    className="h-1.5 bg-forest-500"
                    style={{ width: `${Math.round((d.coverage ?? 0) * 100)}%` }}
                  />
                </div>
                <div className="mt-2 flex gap-3 text-xs text-forest-900/50">
                  <span>{d.total_cards} cards</span>
                  {d.new_cards > 0 && <span>{d.new_cards} new</span>}
                  {d.strong_cards > 0 && <span>{d.strong_cards} strong</span>}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* How it works */}
        <Card className="mt-6 px-5 py-4">
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-forest-900/60">
            <span><strong className="text-forest-900">Again</strong> — forgot it; returns in minutes</span>
            <span><strong className="text-forest-900">Good</strong> — recalled; grows the gap</span>
            <span><strong className="text-forest-900">Easy</strong> — instant recall; grows it faster</span>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------- session
  if (phase === "session" && !card) return <Loading />;

  if (phase === "session") {
    const remaining = queue.length - pos;
    const progress = queue.length ? (pos / queue.length) * 100 : 0;
    return (
      <div className="mx-auto max-w-3xl">
        {/* progress bar */}
        <div className="flex items-center gap-4">
          <button onClick={() => setPhase("deck")} className="flex items-center gap-1 text-xs text-forest-900/50 hover:text-forest-900">
            <X className="h-3.5 w-3.5" /> End session
          </button>
          <div className="h-1.5 flex-1 bg-paper-200">
            <div className="h-1.5 bg-forest-500 transition-all" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-xs tabular-nums text-forest-900/50">{remaining} left</span>
        </div>

        {sessionError ? <div className="mt-3"><ErrorNote>{sessionError}</ErrorNote></div> : null}

        {/* flip card */}
        <div className="flip-scene mt-5">
          <div
            className={`flip-card min-h-72 w-full cursor-pointer select-none ${flipped ? "is-flipped" : ""}`}
            onClick={flip}
            role="button"
            tabIndex={0}
            aria-label="Flashcard — click or press Space to flip"
          >
            {/* front */}
            <Card className="flip-face">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-forest-900/40">
                {card.kind in KIND_META && (
                  <span className={`border px-1.5 py-0.5 ${KIND_META[card.kind].cls}`}>
                    {KIND_META[card.kind].label}
                  </span>
                )}
                {skillName.get(card.skill_id) ?? card.skill_id}
                {card.reps > 0 && <span>· review #{card.reps + 1}</span>}
                {STATE_BADGE[card.state] && (
                  <span className={`px-1.5 py-0.5 normal-case ${STATE_BADGE[card.state].cls}`}>
                    {STATE_BADGE[card.state].label}
                  </span>
                )}
              </div>
              <div className="mt-3 text-center text-xl font-medium text-forest-900">
                <Rich text={card.front} />
              </div>
              <div className="mt-6 text-xs text-forest-900/35">click or press Space to reveal</div>
            </Card>

            {/* back */}
            <Card className="flip-face flip-face--back">
              <div className="mt-auto w-full text-center text-sm leading-relaxed text-forest-900/80">
                <Rich text={card.back} />
              </div>
              <div className="mt-auto text-xs text-forest-900/35">
                grade below — 1 again · 2 good · 3 easy
              </div>
            </Card>
          </div>
        </div>

        {/* grading bar — plain 2D below the card. Buttons inside the rotating
            face are unhittable in Chromium (backface-visibility excludes them
            from hit-testing), so the back shows the answer only and grading
            lives in its own stable bar, like Anki/Quizlet. */}
        {flipped ? (
          <div className="mt-4 grid grid-cols-3 gap-2">
            {(["again", "good", "easy"] as const).map((rating) => (
              <button
                key={rating}
                onClick={() => void grade(rating)}
                disabled={busy}
                className={`border px-4 py-3 text-sm font-medium transition disabled:opacity-50 ${
                  rating === "again"
                    ? "border-red-300 text-red-600 hover:bg-red-50"
                    : rating === "good"
                      ? "border-forest-600 text-forest-700 hover:bg-forest-50"
                      : "border-gold-600 text-gold-600 hover:bg-gold-500/10"
                }`}
              >
                <span className="capitalize">{rating}</span>
                <span className="ml-2 text-xs opacity-60">{card.intervals[rating]}</span>
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-center text-xs text-forest-900/40">
            click the card or press Space to reveal — grading unlocks after the flip
          </p>
        )}
      </div>
    );
  }

  // ------------------------------------------------------------------ done
  const accuracy = result.total ? Math.round(((result.good + result.easy) / result.total) * 100) : 0;
  return (
    <div className="mx-auto max-w-2xl">
      <Card className="mt-8 flex flex-col items-center px-8 py-10 text-center">
        <GraduationCap className="h-10 w-10 text-forest-600" />
        <h2 className="mt-3 text-xl font-semibold text-forest-900">Session complete</h2>
        <p className="mt-1 text-sm text-forest-900/60">
          {deckName(deckTopic)} · {result.total} cards graded
        </p>

        <div className="mt-6 grid w-full grid-cols-3 gap-3">
          {[
            { label: "Again", value: result.again, cls: "text-red-600", icon: CircleDot },
            { label: "Good", value: result.good, cls: "text-forest-700", icon: CheckCircle2 },
            { label: "Easy", value: result.easy, cls: "text-gold-600", icon: Sparkles },
          ].map(({ label, value, cls, icon: Icon }) => (
            <div key={label} className="border border-paper-200 bg-paper-50 px-3 py-4">
              <Icon className={`mx-auto h-5 w-5 ${cls}`} />
              <div className={`mt-1 text-2xl font-semibold tabular-nums ${cls}`}>{value}</div>
              <div className="text-xs text-forest-900/50">{label}</div>
            </div>
          ))}
        </div>

        <p className="mt-4 text-sm text-forest-900/70">
          {result.again === 0
            ? "Perfect run — everything is scheduled forward."
            : `${result.again} card${result.again === 1 ? "" : "s"} will come back soon (later today).`}
        </p>

        {/* weak skills from this session */}
        {(() => {
          const weakSkills = new Set(queue.filter((c) => c.state !== "strong" && c.reps === 0).map((c) => c.skill_id));
          const unique = [...weakSkills].slice(0, 3);
          if (unique.length === 0) return null;
          return (
            <div className="mt-5 w-full text-left">
              <div className="text-xs font-semibold uppercase tracking-wide text-forest-900/40">
                Keep learning
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {unique.map((sid) => (
                  <Link
                    key={sid}
                    to={`/learn/${sid}`}
                    className="border border-paper-300 px-2.5 py-1 text-xs text-forest-700 hover:border-forest-500"
                  >
                    <Layers className="mr-1 inline h-3 w-3" />
                    {skillName.get(sid) ?? sid}
                  </Link>
                ))}
              </div>
            </div>
          );
        })()}

        <div className="mt-7 flex gap-3">
          <Button onClick={() => startSession(deckTopic)}>
            <RotateCcw className="mr-1 inline h-4 w-4" /> Another round
          </Button>
          <Button variant="ghost" onClick={() => setPhase("deck")}>Back to decks</Button>
        </div>
      </Card>
      <p className="mt-3 text-center text-xs text-forest-900/40">
        Recall accuracy this session: {accuracy}%
      </p>
    </div>
  );
}
