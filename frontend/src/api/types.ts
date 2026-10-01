/** Type mirrors of backend response models + a caption helper. */

export interface TopicSkill {
  id: string;
  name: string;
}

export interface Topic {
  id: string;
  name: string;
  skills: TopicSkill[];
}

export interface Bucket {
  id: string;
  name: string;
  topics: Topic[];
}

export interface Taxonomy {
  buckets: Bucket[];
}

export interface ConceptExample {
  prompt: string;
  options: Record<string, string>;
  answer: string | null;
  explanation: string;
  source?: { deck_id?: string; slide_number?: number; source_file?: string; deck_label?: string } | null;
}

export interface ConceptMedia {
  image_id: string;
  source?: { deck_id?: string; slide_number?: number; deck_label?: string } | null;
}

export interface ConceptCodeBlock {
  language: string;
  code: string;
  source?: { deck_id?: string; slide_number?: number; deck_label?: string } | null;
}

export interface ConceptSourceDeck {
  deck_id: string;
  source_file: string;
  source_path: string;
  slide_count: number;
  short_name?: string;
}

/** Learner-facing citation: "Percentages 1 · Slide 5" */
export function sourceCaption(
  source: { deck_label?: string; slide_number?: number } | null | undefined,
): string | null {
  if (!source?.deck_label) return null;
  return source.slide_number
    ? `${source.deck_label} · Slide ${source.slide_number}`
    : source.deck_label;
}

export interface Concept {
  id: string;
  skill_id: string;
  title: string;
  summary: string;
  formulas: string[];
  code_blocks: ConceptCodeBlock[];
  examples: ConceptExample[];
  media: ConceptMedia[];
  common_mistakes: string[];
  related_families: string[];
  source_decks: ConceptSourceDeck[];
  lesson?: Lesson | null;
}

export interface LessonCitation {
  deck_id: string; source_file: string; source_path: string; source_hash: string;
  slide_id: string; slide_number: number; surface: "slide" | "notes"; deck_label: string;
}
export interface LessonAsset { image_id: string; sha256: string; mime: "image/jpeg" | "image/png"; width: number; height: number; }
export interface LessonFigure {
  type: "figure"; id: string; image_id: string; source: LessonCitation; shape_id: number;
  block_sha256: string; original_sha256: string; representation: "original_image" | "normalized_preview";
  role: "teaching_diagram" | "example_prompt" | "solution_diagram"; caption: string; alt: string; review_status: "candidate" | "reviewed";
}
export interface LessonStep { title: string; text: string; equation: string; }
export type LessonBlock = LessonFigure
  | { type: "text"; id: string; paragraphs: string[]; sources: LessonCitation[] }
  | { type: "formula"; id: string; expression: string; variables: string[]; conditions: string[]; sources: LessonCitation[] }
  | { type: "steps"; id: string; steps: LessonStep[]; sources: LessonCitation[] }
  | { type: "example"; id: string; prompt: string; givens: string[]; target: string; steps: LessonStep[]; result: string;
      verification: "unverified" | "independent_check"; sources: LessonCitation[]; figures: LessonFigure[] };
export interface Lesson {
  schema_version: 1; id: string; title: string; introduction: string; review_status: "draft" | "reviewed"; assets: LessonAsset[];
  sections: { id: string; title: string; stage: "overview" | "baseline" | "recognition" | "shortcut"; blocks: LessonBlock[] }[];
}
export interface LessonPreview { lesson: Lesson; catalog_sha256: string; draft_only: true; }

export interface Flashcard {
  id: string;
  skill_id: string;
  front: string;
  back: string;
  kind: string;
}

export interface FlashcardIntervals {
  again: string;
  good: string;
  easy: string;
}

/** A card as served in a bounded review session. */
export interface FlashcardSessionCard extends Flashcard {
  state: "new" | "learning" | "review" | "strong";
  due: boolean;
  reps: number;
  intervals: FlashcardIntervals;
}

export interface FlashcardReviewResult {
  accepted: number;
  due_at: string;
  interval_days: number;
}

export interface FlashcardDeck {
  topic_id: string;
  topic_name: string;
  bucket_name: string;
  total_cards: number;
  due_cards: number;
  new_cards: number;
  strong_cards: number;
  coverage: number | null;
}

export interface FlashcardSkillStat {
  skill_id: string;
  skill_name: string;
  topic_id: string | null;
  topic_name: string | null;
  total_cards: number;
  seen_cards: number;
  coverage: number | null;
}

export interface QuestionOption {
  id: "a" | "b" | "c" | "d";
  text: string;
}

export interface Question {
  session_id: string;
  ticket: string;
  position: number;
  total_questions: number;
  prompt: string;
  options: QuestionOption[];
  expires_at: string;
  answered: boolean;
  marked: boolean;
}

export interface SessionCreated {
  session_id: string;
  question_count: number;
  duration_seconds: number;
  deadline_at: string;
  blueprint_version: string;
  release_version: string;
}

export interface ResultPerQuestion {
  position: number;
  family_id: string;
  skill_id: string;
  bucket_id: string | null;
  topic_id: string | null;
  topic_name: string | null;
  difficulty: string;
  answered: boolean;
  chosen: string | null;
  correct_option: string | null;
  is_correct: boolean;
  explanation: string;
  marked: boolean;
  dwell_seconds: number | null;
  revisit_count: number;
  answer_changed: boolean;
  marked_after_seconds: number | null;
}

export interface TestResult {
  session_id: string;
  state: string;
  submitted_at: string | null;
  score: {
    total_questions: number;
    correct: number;
    incorrect: number;
    unanswered: number;
    accuracy: number;
  };
  per_question: ResultPerQuestion[];
  release_version: string;
  blueprint_version: string;
}

export interface HistoryEntryTest {
  session_id: string;
  created_at: string;
  submitted_at: string | null;
  state: string;
  question_count: number;
  duration_seconds: number | null;
  correct: number | null;
  accuracy: number | null;
}

export interface HistoryEntryLearning {
  concept_id: string;
  title: string;
  viewed_at: string;
}

export interface HistoryEntryFlashcard {
  flashcard_id: string;
  action: string;
  reviewed_at: string;
}

export interface History {
  tests: HistoryEntryTest[];
  learning: HistoryEntryLearning[];
  flashcards: HistoryEntryFlashcard[];
}

export interface SkillInsight {
  skill_id: string;
  skill_name: string;
  topic_id: string | null;
  topic_name: string | null;
  concept_id: string;
  attempts: number;
  correct: number;
  accuracy: number | null;
  median_dwell_seconds: number | null;
  marked_rate: number | null;
  status: string;
  ui_group: "strong" | "on_track" | "needs_practice" | "weak" | "low_evidence" | "unseen";
}

export interface TestDetailQuestion {
  position: number;
  prompt: string;
  options: Record<string, string>;
  family_id: string;
  skill_id: string;
  skill_name: string;
  bucket_id: string;
  topic_id: string;
  topic_name: string;
  difficulty: string;
  concept_id: string;
  answered: boolean;
  chosen: string | null;
  correct_option: string | null;
  is_correct: boolean | null;
  explanation: string | null;
  marked: boolean;
  dwell_seconds: number | null;
  personal_median_seconds: number | null;
  pace_vs_personal: number | null;
  revisit_count: number;
  marked_after_seconds: number | null;
  marked_at_view: boolean;
}

export interface TestDetail {
  session_id: string;
  state: string;
  created_at: string;
  submitted_at: string | null;
  question_count: number;
  duration_seconds: number;
  release_version: string;
  blueprint_version: string;
  finalized: boolean;
  score: {
    total_questions: number;
    correct: number;
    incorrect: number;
    unanswered: number;
    accuracy: number;
  } | null;
  questions: TestDetailQuestion[];
}

export interface Insights {
  skills: SkillInsight[];
}
