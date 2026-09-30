/** Telemetry event types (handoff §8.7) and the bounded flush buffer. */
import { api } from "./endpoints";

export type TestEventType =
  | "test_started"
  | "question_shown"
  | "question_focused"
  | "answer_selected"
  | "answer_changed"
  | "marked_for_review"
  | "unmarked_for_review"
  | "next_question"
  | "previous_question"
  | "question_revisited"
  | "visibility_hidden"
  | "visibility_visible"
  | "focus_lost"
  | "focus_gained"
  | "page_hidden"
  | "test_submitted";

export interface TestEvent {
  type: TestEventType;
  position?: number;
  client_time?: number;
  payload?: Record<string, string | number | boolean | null>;
}

/** Bounded telemetry buffer: flushes at size or interval, survives route changes. */
export class TelemetryBuffer {
  private events: TestEvent[] = [];
  private timer: number | null = null;
  readonly maxBatch = 60;
  readonly flushMs = 10_000;

  constructor(private sessionId: string | null = null) {}

  attach(sessionId: string) {
    this.sessionId = sessionId;
  }

  record(type: TestEventType, position?: number, payload?: Record<string, string | number | boolean | null>) {
    if (!this.sessionId) return;
    this.events.push({ type, position, client_time: performance.now(), payload });
    if (this.events.length >= this.maxBatch) void this.flush();
    else this.schedule();
  }

  private schedule() {
    if (this.timer !== null) return;
    this.timer = window.setTimeout(() => {
      this.timer = null;
      void this.flush();
    }, this.flushMs);
  }

  async flush(): Promise<void> {
    if (!this.sessionId || this.events.length === 0) return;
    const batch = this.events.splice(0, this.maxBatch);
    try {
      await api.sendEvents(this.sessionId, batch);
    } catch {
      // telemetry is best-effort; drop on failure to keep the loop responsive
    }
  }
}
