/** Endpoint functions. Read calls go through the SWR cache; mutations go
 *  straight to the wire and let the cache module decide invalidation. */
import { request } from "./client";
import { getCached } from "./cache";
import type {
  Flashcard,
  FlashcardDeck,
  FlashcardReviewResult,
  FlashcardSessionCard,
  FlashcardSkillStat,
  History,
  Insights,
  Question,
  SessionCreated,
  Taxonomy,
  Concept,
  TestResult,
  TestDetail,
} from "./types";
import type { TestEvent } from "./telemetry";

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  // reads: stale-while-revalidate cache — instant revisits, background refresh
  taxonomy: () => getCached<Taxonomy>("/api/content/taxonomy", 60_000),
  concepts: () => getCached<Concept[]>("/api/content/concepts", 60_000),
  concept: (id: string) =>
    getCached<Concept>(`/api/content/concepts/${encodeURIComponent(id)}`, 60_000),
  flashcards: () => getCached<Flashcard[]>("/api/content/flashcards", 60_000),
  flashcardStats: () => getCached<FlashcardSkillStat[]>("/api/flashcards/stats"),
  flashcardDecks: () => getCached<FlashcardDeck[]>("/api/flashcards/decks"),
  /** Ephemeral per-session queue — deliberately NOT cached: grading a card
   *  changes what a new session would serve, and a background revalidate must
   *  never swap the deck mid-session. */
  flashcardSession: (limit = 20, topic?: string) =>
    request<FlashcardSessionCard[]>(
      `/api/flashcards/session?limit=${limit}${topic ? `&topic=${encodeURIComponent(topic)}` : ""}`,
    ),

  /** Warm the read cache before navigation (hover/focus prefetch). */
  prefetch: (...paths: string[]): void => {
    for (const p of paths) void getCached(p).catch(() => undefined);
  },
  prefetchConcept: (id: string): void =>
    api.prefetch(`/api/content/concepts/${encodeURIComponent(id)}`),
  recordFlashcardViews: (flashcard_ids: string[]) =>
    request<{ accepted: number }>("/api/flashcard-views", {
      method: "POST",
      body: JSON.stringify({ flashcard_ids }),
    }),

  media: async (imageId: string): Promise<string> => {
    // media is immutable within a release — cache hard
    const m = await getCached<{ image_id: string; mime: string; data_base64: string }>(
      `/api/media/${encodeURIComponent(imageId)}`,
      10 * 60_000,
    );
    return `data:${m.mime};base64,${m.data_base64}`;
  },

  openSource: (source_path: string) =>
    request<{ opened: string }>("/api/source/open", {
      method: "POST",
      body: JSON.stringify({ source_path }),
    }),

  recordConceptView: (concept_id: string, title: string) =>
    request<{ accepted: number }>("/api/concept-views", {
      method: "POST",
      body: JSON.stringify({ concept_id, title }),
    }),

  gradeFlashcard: (flashcard_id: string, rating: "again" | "good" | "easy") =>
    request<FlashcardReviewResult>("/api/flashcard-reviews", {
      method: "POST",
      body: JSON.stringify({ flashcard_id, rating }),
    }),

  createSession: (question_count: number, duration_minutes?: number) =>
    request<SessionCreated>("/api/test-sessions", {
      method: "POST",
      body: JSON.stringify(
        duration_minutes ? { question_count, duration_minutes } : { question_count },
      ),
    }),

  getQuestion: (sessionId: string, position?: number) =>
    request<Question>(
      position === undefined
        ? `/api/test-sessions/${sessionId}/question`
        : `/api/test-sessions/${sessionId}/question/${position}`,
    ),

  submitAnswer: (sessionId: string, position: number, ticket: string, option: string) =>
    request<{ accepted: boolean; remaining: number }>(
      `/api/test-sessions/${sessionId}/answer?position=${position}`,
      { method: "POST", body: JSON.stringify({ ticket, option }) },
    ),

  markQuestion: (sessionId: string, position: number, marked: boolean) =>
    request<{ marked: boolean }>(
      `/api/test-sessions/${sessionId}/mark/${position}`,
      { method: "POST", body: JSON.stringify({ marked }) },
    ),

  sendEvents: (sessionId: string, events: TestEvent[]) =>
    request<{ accepted: number }>(`/api/test-sessions/${sessionId}/events`, {
      method: "POST",
      body: JSON.stringify({ events }),
    }),

  sendDwell: (sessionId: string, position: number, seconds: number, kind: "active" | "hidden" | "unfocused" = "active") =>
    request<{ accepted: number }>(`/api/test-sessions/${sessionId}/dwell`, {
      method: "POST",
      body: JSON.stringify({ position, seconds, kind }),
    }),

  finish: (sessionId: string) =>
    request<TestResult>(`/api/test-sessions/${sessionId}/finish`, { method: "POST" }),

  result: (sessionId: string) =>
    getCached<TestResult>(`/api/test-sessions/${sessionId}/result`, 5 * 60_000),

  history: () => getCached<History>("/api/history"),
  insights: () => getCached<Insights>("/api/insights"),
  testDetail: (sessionId: string) =>
    getCached<TestDetail>(`/api/history/tests/${encodeURIComponent(sessionId)}`, 5 * 60_000),
};
