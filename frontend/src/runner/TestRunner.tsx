import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, Flag, Timer, TriangleAlert } from "lucide-react";
import {
  ApiError,
  api,
  type Question,
  type SessionCreated,
  type TestEventType,
} from "../api";
import { useTelemetry } from "../ui";

type Phase = "starting" | "running" | "submitting" | "done" | "error";

interface AnswerState {
  option: string | null;
  marked: boolean;
}

/** Durable per-question active-dwell tracker (handoff §8.7).
 *
 * - Time accumulates per position across revisits (never resets to zero).
 * - Every pause (navigate away, tab hide, window blur) flushes the open
 *   segment into the accumulator, so leaving a question banks its time.
 * - Segments are POSTed to the server, which sums them per question;
 *   the client and server therefore agree even across reloads.
 * - `markAt` snapshots accumulated time the moment the learner flags the
 *   question, giving "decided to come back later after N s".
 */
class DwellTracker {
  private current: number | null = null;
  private openedAt = 0;
  private accumulated = new Map<number, number>();
  private markAt = new Map<number, number>();
  private hiddenSince: { position: number; kind: "hidden" | "unfocused"; at: number } | null = null;

  enter(position: number, kind: TestEventType = "question_shown") {
    void kind;
    if (this.current === position) return;
    this.flushCurrent();
    this.current = position;
    this.openedAt = performance.now();
  }

  markNow(position: number) {
    if (!this.markAt.has(position)) {
      this.markAt.set(position, this.snapshot(position));
    }
  }

  pause(kind: "hidden" | "unfocused") {
    if (this.current === null || this.hiddenSince) return;
    this.flushCurrent();
    this.hiddenSince = { position: this.current, kind, at: performance.now() };
  }

  resume() {
    if (!this.hiddenSince) return;
    const { position } = this.hiddenSince;
    this.hiddenSince = null;
    this.current = position;
    this.openedAt = performance.now();
  }

  /** Move focus to another question; returns {position, seconds} to persist. */
  leave(): { position: number; seconds: number; kind: "active" } | null {
    if (this.current === null) return null;
    this.flushCurrent();
    const position = this.current;
    const seconds = this.accumulated.get(position) ?? 0;
    this.current = null;
    return seconds > 0.5 ? { position, seconds, kind: "active" } : null;
  }

  snapshot(position: number): number {
    const base = this.accumulated.get(position) ?? 0;
    if (this.current === position && !this.hiddenSince) {
      return base + (performance.now() - this.openedAt) / 1000;
    }
    return base;
  }

  /** Seconds spent before the first mark-for-review on this question. */
  markedAfter(position: number): number | null {
    return this.markAt.get(position) ?? null;
  }

  /** Persist everything currently banked; returns pending segments. */
  drain(): Array<{ position: number; seconds: number; kind: "active" | "hidden" | "unfocused" }> {
    const out: Array<{ position: number; seconds: number; kind: "active" | "hidden" | "unfocused" }> = [];
    this.flushCurrent();
    for (const [position, seconds] of this.accumulated) {
      if (seconds > 0.5) {
        out.push({ position, seconds: Math.round(seconds * 10) / 10, kind: "active" });
        this.accumulated.set(position, 0);
      }
    }
    if (this.hiddenSince) {
      const { position, kind, at } = this.hiddenSince;
      const secs = (performance.now() - at) / 1000;
      if (secs > 0.5) out.push({ position, seconds: Math.round(secs * 10) / 10, kind });
      this.hiddenSince = null;
      this.current = position;
      this.openedAt = performance.now();
    }
    return out;
  }

  private flushCurrent() {
    if (this.current === null) return;
    if (!this.hiddenSince) {
      const delta = (performance.now() - this.openedAt) / 1000;
      this.accumulated.set(this.current, (this.accumulated.get(this.current) ?? 0) + delta);
    }
    this.openedAt = performance.now();
  }
}

export function TestRunner() {
  const navigate = useNavigate();
  const { buffer } = useTelemetry();
  const [phase, setPhase] = useState<Phase>("starting");
  const [error, setError] = useState<string | null>(null);

  const [session, setSession] = useState<SessionCreated | null>(null);
  const [questions, setQuestions] = useState<Record<number, Question>>({});
  const [answers, setAnswers] = useState<Record<number, AnswerState>>({});
  const [position, setPosition] = useState(0);
  const [lockdownNote, setLockdownNote] = useState<string | null>(null);
  const [timerMode, setTimerMode] = useState<"remaining" | "elapsed">("remaining");

  const sessionIdRef = useRef<string | null>(null);
  const submittedRef = useRef(false);
  const questionsRef = useRef<Record<number, Question>>({});
  questionsRef.current = questions;
  const dwellRef = useRef(new DwellTracker());
  const positionRef = useRef(0);
  positionRef.current = position;
  const dwellPostRef = useRef<Promise<void>>(Promise.resolve());

  const count = (() => {
    try {
      return (history.state?.usr?.testConfig?.count as number | undefined) ?? 10;
    } catch {
      return 10;
    }
  })();

  const durationMinutes = (() => {
    try {
      const v = history.state?.usr?.testConfig?.duration_minutes as number | undefined;
      return v && v >= 1 ? Math.round(v) : undefined;
    } catch {
      return undefined;
    }
  })();

  /** Serialize dwell POSTs so segments land in order. */
  const postDwell = useCallback(
    (sessionId: string, position: number, seconds: number, kind: "active" | "hidden" | "unfocused") => {
      dwellPostRef.current = dwellPostRef.current
        .then(async () => {
          await api.sendDwell(sessionId, position, seconds, kind);
        })
        .catch(() => undefined);
    },
    [],
  );

  // ---------------------------------------------------------------
  // Telemetry: visibility + focus + beforeunload guard
  // ---------------------------------------------------------------
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "hidden") {
        buffer.record("visibility_hidden");
        buffer.record("page_hidden");
        dwellRef.current.pause("hidden");
        setLockdownNote("Tab hidden — this is recorded in your test report.");
        if (sessionIdRef.current) {
          const p = positionRef.current;
          const seg = dwellRef.current.snapshot(p);
          if (seg > 0.5) postDwell(sessionIdRef.current, p, seg, "active");
        }
        void buffer.flush();
      } else {
        buffer.record("visibility_visible");
        dwellRef.current.resume();
        setLockdownNote(null);
      }
    };
    const onBlur = () => {
      buffer.record("focus_lost");
      dwellRef.current.pause("unfocused");
    };
    const onFocus = () => {
      buffer.record("focus_gained");
      dwellRef.current.resume();
    };
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (submittedRef.current || !sessionIdRef.current) return;
      e.preventDefault();
      e.returnValue = "";
    };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("blur", onBlur);
    window.addEventListener("focus", onFocus);
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("blur", onBlur);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [buffer, postDwell]);

  // ---------------------------------------------------------------
  // Test-mode lockdown: block exit intents, context menu, selection.
  // ---------------------------------------------------------------
  useEffect(() => {
    if (phase !== "running") return;
    const block = (e: Event) => {
      e.preventDefault();
      setLockdownNote("Test mode: leaving the test surface is recorded.");
      window.setTimeout(() => setLockdownNote((n) => (n === null ? null : n)), 2500);
    };
    const onMouseOut = (e: MouseEvent) => {
      if (!e.relatedTarget && (e as MouseEvent).clientY <= 0) {
        setLockdownNote("Stay in the test — moving outside is recorded in telemetry.");
        window.setTimeout(() => setLockdownNote(null), 2500);
      }
    };
    const onContextMenu = (e: MouseEvent) => e.preventDefault();
    const onSelectStart = (e: Event) => e.preventDefault();
    document.addEventListener("dragstart", block);
    document.addEventListener("mouseout", onMouseOut);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("selectstart", onSelectStart);
    return () => {
      document.removeEventListener("dragstart", block);
      document.removeEventListener("mouseout", onMouseOut);
      document.removeEventListener("contextmenu", onContextMenu);
      document.removeEventListener("selectstart", onSelectStart);
    };
  }, [phase]);

  // ---------------------------------------------------------------
  // Session creation
  // ---------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await api.createSession(count, durationMinutes);
        if (cancelled) return;
        setSession(s);
        sessionIdRef.current = s.session_id;
        buffer.attach(s.session_id);
        buffer.record("test_started");
        const q = await api.getQuestion(s.session_id, 0);
        if (cancelled) return;
        setQuestions((prev) => ({ ...prev, [0]: q }));
        buffer.record("question_shown", 0);
        dwellRef.current.enter(0);
        setPosition(0);
        setPhase("running");
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof ApiError ? e.message : "Could not start the test.");
        setPhase("error");
      }
    })();
    return () => {
      cancelled = true;
      if (!submittedRef.current && sessionIdRef.current) void buffer.flush();
    };
  }, [buffer, count]);

  // ---------------------------------------------------------------
  // Submission (drains dwell debt first so nothing is lost)
  // ---------------------------------------------------------------
  const doSubmit = useCallback(async () => {
    if (submittedRef.current || !sessionIdRef.current) return;
    submittedRef.current = true;
    setPhase("submitting");
    try {
      buffer.record("test_submitted");
      const sid = sessionIdRef.current;
      for (const seg of dwellRef.current.drain()) {
        postDwell(sid, seg.position, seg.seconds, seg.kind);
      }
      await dwellPostRef.current;
      await buffer.flush();
      await api.finish(sid);
      setPhase("done");
      navigate("/results", { state: { sessionId: sid } });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not submit the test.");
      setPhase("error");
    }
  }, [buffer, navigate, postDwell]);

  const submitRef = useRef(doSubmit);
  submitRef.current = doSubmit;

  const [remaining, setRemaining] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!session) return;
    const deadline = new Date(session.deadline_at).getTime();
    const startedAt = Date.now();
    const tick = () => {
      setRemaining(Math.max(0, Math.round((deadline - Date.now()) / 1000)));
      setElapsed(Math.round((Date.now() - startedAt) / 1000));
      if (deadline - Date.now() <= 0) void submitRef.current?.();
    };
    tick();
    const iv = window.setInterval(tick, 250);
    return () => window.clearInterval(iv);
  }, [session]);

  // Periodic dwell sync: banked time reaches the server even mid-question.
  useEffect(() => {
    if (phase !== "running") return;
    const iv = window.setInterval(() => {
      if (!sessionIdRef.current || submittedRef.current) return;
      const segs = dwellRef.current.drain();
      for (const seg of segs) postDwell(sessionIdRef.current, seg.position, seg.seconds, seg.kind);
    }, 5000);
    return () => window.clearInterval(iv);
  }, [phase, postDwell]);

  // ---------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------
  const goTo = useCallback(
    async (pos: number, eventType: TestEventType) => {
      if (!session || !sessionIdRef.current) return;
      const total = session.question_count;
      const clamped = Math.max(0, Math.min(total - 1, pos));
      const from = positionRef.current;
      if (from !== clamped) {
        buffer.record(eventType, clamped, { from });
        const left = dwellRef.current.leave();
        if (left && left.position >= 0) {
          postDwell(sessionIdRef.current, left.position, left.seconds, left.kind);
        }
      }
      if (!questionsRef.current[clamped]) {
        try {
          const q = await api.getQuestion(sessionIdRef.current, clamped);
          setQuestions((prev) => ({ ...prev, [clamped]: q }));
          buffer.record("question_shown", clamped);
        } catch {
          /* keep current view on transient failure */
        }
      } else {
        buffer.record("question_focused", clamped);
      }
      dwellRef.current.enter(clamped);
      setPosition(clamped);
    },
    [session, buffer, postDwell],
  );

  // ---------------------------------------------------------------
  // Answering
  // ---------------------------------------------------------------
  const choose = useCallback(
    async (optionId: string) => {
      const q = questions[position];
      if (!q || !sessionIdRef.current) return;
      const previous = answers[position]?.option ?? null;
      buffer.record(previous ? "answer_changed" : "answer_selected", position, {
        from: previous,
        to: optionId,
      });
      setAnswers((prev) => ({
        ...prev,
        [position]: { option: optionId, marked: prev[position]?.marked ?? q.marked },
      }));
      try {
        await api.submitAnswer(sessionIdRef.current, position, q.ticket, optionId);
      } catch (e) {
        if (e instanceof ApiError && e.code === "stale ticket") {
          const fresh = await api.getQuestion(sessionIdRef.current, position);
          setQuestions((prev) => ({ ...prev, [position]: fresh }));
        }
      }
    },
    [position, questions, answers, buffer],
  );

  const toggleMark = useCallback(async () => {
    const q = questions[position];
    if (!q || !sessionIdRef.current) return;
    const next = !(answers[position]?.marked ?? q.marked);
    buffer.record(next ? "marked_for_review" : "unmarked_for_review", position);
    if (next) dwellRef.current.markNow(position);
    setAnswers((prev) => ({
      ...prev,
      [position]: { option: prev[position]?.option ?? null, marked: next },
    }));
    try {
      await api.markQuestion(sessionIdRef.current, position, next);
    } catch {
      /* best-effort */
    }
  }, [position, questions, answers, buffer]);

  // ---------------------------------------------------------------
  // Render — chrome-less: no app nav, no links out, test surface only.
  // ---------------------------------------------------------------
  if (phase === "starting") {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-paper-50">
        <p className="text-sm text-forest-900/60">Preparing your test…</p>
        <p className="mt-2 text-xs text-forest-900/40">{count} questions · server-timed</p>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-paper-50 px-6">
        <TriangleAlert className="text-clay-600" size={28} />
        <p className="max-w-md text-center text-sm text-forest-900/70">{error}</p>
        <button
          onClick={() => navigate("/tests")}
          className="border border-forest-600 px-4 py-2 text-sm text-forest-700 hover:bg-forest-50"
        >
          Back to Tests
        </button>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="flex h-screen items-center justify-center bg-paper-50">
        <p className="text-sm text-forest-900/60">Scoring on the server…</p>
      </div>
    );
  }

  if (!session) return null;

  const q = questions[position];
  const total = session.question_count;
  const answeredCount = Object.values(answers).filter((a) => a.option).length;
  const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  const timerValue = timerMode === "remaining" ? fmt(remaining ?? 0) : fmt(elapsed);

  return (
    <div className="flex h-screen select-none flex-col bg-paper-50" aria-hidden={false}>
      <div className="flex items-center justify-between border-b border-paper-300 bg-white px-6 py-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTimerMode((m) => (m === "remaining" ? "elapsed" : "remaining"))}
            title="Toggle between time left and time spent"
            className="flex items-center gap-2 rounded-sm border border-paper-300 px-2.5 py-1 hover:bg-paper-100"
          >
            <Timer size={15} className="text-forest-700" aria-hidden />
            <span
              className={`font-mono text-sm ${(remaining ?? 1) < 60 && timerMode === "remaining" ? "text-clay-600" : "text-forest-900"}`}
            >
              {timerValue}
            </span>
            <span className="text-[10px] uppercase tracking-wide text-forest-900/40">
              {timerMode === "remaining" ? "left" : "spent"}
            </span>
          </button>
          <span className="text-sm text-forest-900/60">
            Question {position + 1} of {total}
          </span>
          {lockdownNote ? (
            <span className="flex items-center gap-1.5 border border-gold-600 bg-gold-500/15 px-2 py-1 text-xs text-forest-900">
              <EyeOff size={13} aria-hidden /> {lockdownNote}
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs text-forest-900/40">
              <Eye size={13} aria-hidden /> test mode
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-forest-900/50">{answeredCount} answered</span>
          <button
            onClick={() => void doSubmit()}
            disabled={phase === "submitting"}
            className="bg-forest-600 px-4 py-1.5 text-sm font-medium text-paper-50 hover:bg-forest-700 disabled:opacity-60"
          >
            Submit test
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-8 py-8">
            {q ? (
              <>
                <p className="max-w-3xl text-lg leading-relaxed text-forest-900">{q.prompt}</p>
                <div className="mt-8 max-w-3xl space-y-3">
                  {q.options.map((opt) => {
                    const selected = answers[position]?.option === opt.id;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => void choose(opt.id)}
                        aria-pressed={selected}
                        className={`flex w-full items-start gap-4 border px-5 py-4 text-left text-sm ${
                          selected
                            ? "border-forest-600 bg-forest-50"
                            : "border-paper-300 bg-white hover:border-forest-500"
                        }`}
                      >
                        <span
                          className={`font-medium ${selected ? "text-forest-700" : "text-forest-900/50"}`}
                        >
                          {opt.id.toUpperCase()}
                        </span>
                        <span className="text-forest-900">{opt.text}</span>
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => void toggleMark()}
                  className="mt-8 flex items-center gap-2 text-sm text-forest-900/60 hover:text-forest-700"
                >
                  <Flag size={15} className={answers[position]?.marked ? "text-gold-600" : ""} />
                  {answers[position]?.marked ? "Marked for review" : "Mark for review"}
                </button>
              </>
            ) : (
              <p className="animate-pulse text-sm text-forest-900/50">Loading question…</p>
            )}
          </div>

          <div className="border-t border-paper-300 bg-white px-8 py-3">
            <div className="flex items-center justify-between">
              <button
                onClick={() => void goTo(position - 1, "previous_question")}
                disabled={position === 0}
                className="border border-paper-300 px-4 py-2 text-sm text-forest-900/70 hover:bg-paper-100 disabled:opacity-40"
              >
                Previous
              </button>
              <div className="flex gap-1.5" role="group" aria-label="Question navigator">
                {Array.from({ length: total }, (_, i) => {
                  const a = answers[i];
                  const isMarked = a?.marked;
                  return (
                    <button
                      key={i}
                      onClick={() => void goTo(i, "question_revisited")}
                      aria-label={`Question ${i + 1}${a?.option ? ", answered" : ""}${isMarked ? ", marked" : ""}`}
                      className={`h-8 w-8 border text-xs ${
                        i === position
                          ? "border-forest-600 bg-forest-600 text-paper-50"
                          : a?.option
                            ? isMarked
                              ? "border-gold-600 bg-gold-500/15 text-forest-900"
                              : "border-forest-500 bg-forest-50 text-forest-700"
                            : isMarked
                              ? "border-gold-600 text-gold-600"
                              : "border-paper-300 text-forest-900/60"
                      }`}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>
              <button
                onClick={() => void goTo(position + 1, "next_question")}
                disabled={position === total - 1}
                className="border border-paper-300 px-4 py-2 text-sm text-forest-900/70 hover:bg-paper-100 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
