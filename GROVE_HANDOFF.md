# Grove — Product, Architecture, and Delivery Handoff

**Status:** Canonical working handoff

**Last consolidated:** 2026-09-19

**Product name:** Grove

**Purpose:** Preserve the decisions, boundaries, feature plan, technical direction,
and deferred ideas agreed for the Grove aptitude and reasoning application so that
future work can continue without reconstructing the project from conversation
history.

This document is intentionally broader than an implementation checklist. It records
what the product is, what it is not, why the main boundaries exist, what belongs in
each repository, and the order in which the product should be built.

---

## 1. Executive decision

Grove is a small, lightweight, single-learner aptitude and reasoning practice
application.

The first useful version has three connected concerns:

1. **Learn:** short, structured concepts, rules, formulas, worked examples, and
   common mistakes.
2. **Practice:** simplified flashcards and review prompts.
3. **Test:** a tightly isolated test mode that receives only the question currently
   being answered, records detailed client-side interaction telemetry, and sends
   answers to the backend for authoritative scoring.

The application is deliberately not a general learning platform, a social product,
a full learning-management system, a proctoring system, or an assessment-science
research platform in its first stages.

The smallest credible architecture is:

```text
content  →  approved content releases  →  grove-backend  →  grove-frontend
                                                     ↑                 ↓
                                              scores, history      interaction events
```

The learner browser is a rendering and interaction client. It is not the source of
truth for content, answers, scoring, test state, or learner history.

---

## 2. How to use this document

This file is the cross-repository handoff. It should be read before adding a new
feature that affects more than one repository.

The repository-local documentation remains useful for implementation details:

```text
grove-frontend/docs/  frontend decisions, roadmap, research, and runbooks
grove-backend/docs/   backend decisions, roadmap, research, and runbooks
content/        content scope and the local learning-data boundary
```

When documents conflict, use this order:

1. A newer explicit product decision in this handoff.
2. A durable ADR that does not contradict a newer product decision.
3. The selected proposal.
4. The roadmap and research notes.
5. Existing prototype behavior.

Prototype behavior is not automatically a product decision. A screen can exist only
to make a future contract visible.

### Change-control rule

Before materially expanding the product:

1. Update this handoff with the decision and its stage.
2. Add or update an ADR when the change affects a repository boundary, security
   boundary, persistence choice, or public API contract.
3. Update the relevant repository roadmap.
4. Only then implement the change.

---

## 3. The original problem and the tightened scope

The original idea was broad: build an aptitude and reasoning system with many
subjects and topics, question banks, randomized assessment, timing, score history,
learner analysis, recommendations, flashcards, LLM-assisted question creation,
PowerPoint ingestion, FOSS tooling, and eventually a mobile client with sync.

That would be too large as a first project. The scope was intentionally tightened to
protect the central learning loop:

```text
approved content → learn a concept → take a focused test → score on the server
→ inspect simple history → return to a weak concept
```

The first implementation must prove that loop before adding adaptive testing,
accounts, synchronization, calibration, or a large authoring platform.

### What was kept

- Aptitude and reasoning content.
- A clear taxonomy of buckets, topics, skills, and question families.
- Concepts and formulas.
- Simplified flashcards.
- A test mode with a timer and question navigation.
- Detailed per-question client timing and interaction events.
- Server-side answer evaluation and score calculation.
- Test history and future skill evidence.
- Randomized but reproducible question variants.
- PowerPoint-to-content ingestion as a private, reviewable pipeline.
- LLM assistance for authoring, never direct publication.
- A future path to mobile through a small API contract.

### What was deliberately removed from the first build

- A large platform with many active domains.
- User profiles and user-facing account features.
- Social features.
- Public content uploads.
- A full CMS.
- Runtime LLM question generation for a learner.
- Automatic publication of generated questions.
- Browser-side answer keys.
- Browser-side scoring.
- Heavy anti-cheat or legally meaningful proctoring claims.
- IRT, CAT, percentile claims, or formal aptitude measurement.
- Offline synchronization.
- A mobile codebase.
- Complex prerequisite graphs.
- Advanced spaced repetition.
- LMS integrations.

---

## 4. Product principles

These principles should guide decisions that are not explicitly listed elsewhere.

1. **Keep the learner application small and fast.**
2. **Keep learning data out of the frontend application repository and bundle.**
3. **Keep answer keys, scoring rules, and authoritative test state on the backend.**
4. **Treat browser input as untrusted for authorization and scoring.**
5. **Collect detailed client observations without pretending they are unalterable
   evidence.**
6. **Make content versioned, reviewable, reproducible, and importable.**
7. **Prefer a private CLI and a small API over a premature content platform.**
8. **Use deterministic code for mathematical and logical correctness wherever
   possible.**
9. **Do not make one number pretend to be a complete aptitude assessment.**
10. **Avoid solving future multi-user and mobile problems before the single-learner
    loop works.**
11. **Prefer clear, quiet interfaces over a dashboard full of tiles, pills, and
    helper copy.**

---

## 5. Current product boundary

### Included in the intended first usable slice

- Learnable concepts and formulas.
- Two active aptitude/reasoning buckets.
- Topic and skill navigation.
- Simplified flashcards.
- A server-created test session.
- A test question delivered one at a time.
- A configurable number of questions.
- A question-count-derived duration, initially one minute per question.
- Question navigation, answer selection, answer changes, and mark-for-review.
- Client-observed per-question timing.
- Visibility/focus event logging.
- Server-side scoring and finalization.
- Recent test history.
- Recent learning activity.
- Recent flashcard activity.
- Basic topic/skill evidence returned by the backend.
- A private PowerPoint ingestion workflow.
- Human review before content is published.
- Versioned content releases.

### Deferred, not deleted forever

- A richer per-test analysis view.
- Exact question-by-question answer review in history.
- Timing comparison against personal and question-family averages.
- Composite learner statuses such as developing, strong, or needs review.
- Automated weak-area recommendations.
- Review scheduling based on weak skills.
- Authenticated operator access for Admin.
- Postgres.
- Background workers and object storage.
- Mobile and synchronization.
- Calibrated assessment models.

The detailed evidence model remains a future backend capability, but the current
History presentation is intentionally simple. It should show recent tests, recent
learning, and recent flashcards rather than opening with a large set of statistical
readouts or a complex analysis dashboard.

---

## 6. Learner-facing features

### 6.1 Overview

The Overview page is a small return point into the learning loop.

It may show:

- A compact “Today’s work” heading.
- One clear start-test action.
- Three compact practice indicators:
  - streak;
  - accuracy;
  - focused time.
- A short list of skills or topics that deserve attention.
- A small next-study suggestion.
- A concept shelf.

Visual decisions already made:

- The three indicators stay side by side to save vertical space.
- Each uses a desaturated version of its general color as the background.
- Icons have tooltips that spell out the metric.
- Avoid large metric tiles and unnecessary explanatory subtext.
- Keep the heading and the space below it compact.
- Do not add a profile or user footer.

The Overview is a navigation surface, not the place to implement a full learner
model.

### 6.2 Learn

Learn is the source of explanations, not the test interface.

The learner can browse:

```text
Bucket → Topic → Skill/Concept
```

A concept page may contain:

- A short explanation.
- Formulae or rules.
- A worked example.
- Common mistakes.
- A simplified summary.
- Related flashcards.
- Related practice question families.

Learn content comes from an approved content release. It should not be hard-coded
as the long-term source of truth in React.

### 6.3 Flashcards

Flashcards are deliberately simple at first.

The first version should support:

- A concise concept, rule, or formula front.
- A short explanation or example.
- `Again` and `Remember` actions.
- Basic review history.

The current visual direction keeps the existing flashcard treatment and explicitly
notes that flashcard decks, formula cards, and review scheduling are planned for a
future release.

Flashcards are approved content. The learner frontend must not call an LLM directly
to generate flashcards during use.

### 6.4 Tests

The learner-facing navigation label is **Tests**. The setup view is **Take a Test**.

The entry screen should contain:

- A notepad/pen-style icon.
- The smaller “Take a Test” title.
- A question-count control.
- A displayed time derived from the selected number of questions.
- An “Enter Test mode” action.

The question-count relationship is initially:

```text
5 questions  →  5 minutes
10 questions → 10 minutes
15 questions → 15 minutes
20 questions → 20 minutes
```

The final allowed values belong to the server blueprint. The frontend display is
only a preview of the selected test configuration.

During a test, the learner may:

- Read the current question.
- Select an answer.
- Change an answer.
- Move forward or backward where the blueprint permits it.
- Mark a question for review.
- Revisit a question.
- Submit the attempt.

The learner must not receive correctness feedback or the answer key before the
test policy allows results to be released.

### 6.5 History

The current History page is intentionally a recent-activity view, in descending
order within each activity type:

1. Recent tests.
2. Recent learning done.
3. Recent flashcards reviewed.

The current page should not begin with the previous three large stat readouts such
as focused time, tests given, and accuracy. It should also not be dominated by the
discarded expandable test-analysis treatment.

The later evidence model may support a deeper test detail view. That is a staged
feature, not a reason to make the first History page heavy.

---

## 7. Visual and interaction direction

The product direction moved away from a dashboard of cards and chips.

### Keep

- Flat, rectangular sections.
- Hairline rules.
- A restrained forest, paper, sage, clay, and gold palette.
- Strong typography for important titles.
- One clear primary action per screen.
- Compact spacing where the screen is informational.
- Accessible focus states.
- Reduced-motion support.
- Tooltips for icon-only metrics.

### Avoid

- Pill-shaped controls and badges unless a future decision explicitly requires one.
- Decorative top-level helper copy.
- Repeating explanatory subtext that does not help the next action.
- Large tile grids for simple information.
- User/profile controls.
- A sidebar footer that scrolls out of the viewport.
- Monospace treatment for ordinary user-facing copy.
- Security jargon in the learner UI such as “Secure session.”

The interface can explain an action plainly. Security belongs in the implementation
and the technical documentation, not in intimidating learner-facing labels.

---

## 8. Test-mode security boundary

### 8.1 The actual goal

Grove is a personal learning application, not a legally proctored examination
system. The goal is to protect:

- answer keys;
- scoring and grading rules;
- test state;
- learning-only content;
- user history;
- content-authoring operations.

The goal is not to prove that a person is physically alone or that a modified
browser cannot observe its own screen.

### 8.2 Explicitly out of scope

The application will not promise to prevent:

- another device being used;
- screenshots or screen recording;
- browser extensions;
- a modified browser or modified JavaScript;
- every kind of operating-system-level inspection;
- another person helping the learner.

These limitations are accepted. Building heavyweight proctoring would make the
application larger without solving the user’s main need.

### 8.3 What test mode must guarantee

- The browser never receives the correct option before results are released.
- The browser never receives scoring weights or grading rules.
- The browser never receives a complete test with all future questions unless the
  future blueprint explicitly allows that exposure.
- The browser receives only the minimum payload needed for the current question.
- The learning library is not preloaded into the test interface.
- The client cannot submit its own score.
- The backend owns test state, expiry, finalization, and scoring.
- Content ingestion is not available to the public learner surface.
- Personalized responses are not casually cached.

If someone inspects the question response, they may see the current question and its
options. They should not see the answer, explanation, future questions, or the
private content identifiers needed to reconstruct the bank.

### 8.4 Flush and isolation behavior

When a test begins, the client should:

1. leave the learning route;
2. clear learner-only query state;
3. clear client caches that are not needed by the test;
4. avoid `localStorage`, IndexedDB, or service-worker persistence for test content;
5. use `Cache-Control: no-store` for personalized test responses;
6. load only the current test payload;
7. restore learning surfaces after the test ends.

Clearing state is a data-minimization measure. A browser cannot be promised to
physically erase every byte of memory. That is acceptable because the test route
should never have received the learning library or answer keys in the first place.

### 8.5 Server-owned test lifecycle

```text
created → active → submitted
                 ↘ expired
                 ↘ cancelled
```

The server creates and owns the session. It stores:

- the deployment-scoped learner or future user reference;
- the immutable content-release version;
- the blueprint version;
- the selected question plan;
- the server selection seed;
- the order and option permutations;
- the start time;
- the deadline;
- the state;
- the submitted answers;
- the final score.

The server must reject:

- answers for another session;
- answers after expiry;
- duplicate finalization;
- invalid option identifiers;
- out-of-order or replayed state transitions;
- requests that cross the deployment’s authorization boundary.

### 8.6 Minimal question protocol

The public question response should be an explicit allowlist, for example:

```json
{
  "ticket": "opaque-session-question-token",
  "position": 3,
  "prompt": "A train travels...",
  "options": [
    {"id": "a", "text": "..."},
    {"id": "b", "text": "..."},
    {"id": "c", "text": "..."},
    {"id": "d", "text": "..."}
  ],
  "expires_at": "2026-09-16T10:45:00Z"
}
```

It must not include:

- `correct_option_id`;
- `is_correct`;
- `answer_hash`;
- `explanation`;
- `grading_rule`;
- private skill identifiers if they are not needed by the current UI;
- internal difficulty parameters;
- generator parameters;
- full question-bank identifiers;
- future questions.

Database objects must never be serialized directly into learner responses. Use
separate public and private response models.

### 8.7 Timing decision

The user wants detailed client-side analytics. The client therefore records the
interaction timeline, while the server remains authoritative for score and expiry.

The client may record:

```text
test_started
question_shown
question_focused
answer_selected
answer_changed
marked_for_review
unmarked_for_review
next_question
previous_question
question_revisited
visibility_hidden
visibility_visible
fullscreen_entered
fullscreen_exited
page_hidden
heartbeat_missed
test_submitted
```

Per question, derive where possible:

- active dwell time;
- time before the first answer;
- time after the first answer;
- number of answer changes;
- time while marked for review;
- number of revisits;
- hidden or unfocused intervals;
- client monotonic timestamps;
- server receipt timestamps.

The product should call this **active dwell time**, not exact reading time. A
browser cannot know precisely when a person has finished reading a question.

The client can pause its active segment when the question is no longer active, the
page is hidden, focus leaves the test, or the learner moves to another question.
Every pause/resume transition should be represented by an event rather than silently
changing a final duration.

Client timings are stored as observations and may be altered by a modified client.
They are valuable for personal analytics but must not determine official score.

The server uses its own session start/deadline timestamps to enforce expiry. The
frontend may show a responsive countdown, but it must not be trusted to decide
whether a test is valid.

---

## 9. Learner model and evidence

The learner model must not reduce aptitude to a single correctness number.

### Independent signals

Track these per skill or question family when enough evidence exists:

1. Accuracy.
2. Recent accuracy.
3. Active time compared with similar questions.
4. Recent consistency.
5. Answer-change rate.
6. Review-mark rate.
7. Number of attempts.
8. Difficulty level handled.
9. Recent improvement or deterioration.

The previous idea that a skill becomes solid after a fixed number of recent correct
answers is not sufficient and is not the current learner-state rule.

### Fair timing comparison

Timing should be compared within a reasonably similar group:

```text
same skill + same question family/type + similar editorial difficulty
```

Do not compare a direct arithmetic question with a difficult multi-step logic puzzle
as though they were the same task.

Use the learner’s own median as the first personal baseline. A broader population
average can be added later only if there is trustworthy data and a clear reason to
use it.

### Initial evidence statuses

Use descriptive statuses rather than declaring a permanent aptitude label:

```text
unseen
insufficient_evidence
developing
slow_but_accurate
inaccurate
inconsistent
strong
needs_review
```

Evidence guidance:

- Fewer than five comparable attempts: show `insufficient_evidence`.
- Repeated wrong answers: indicate a concept or method concern.
- Correct but unusually slow answers: indicate a fluency concern.
- Fast but incorrect answers: indicate an accuracy, carelessness, or reading
  concern.
- Many answer changes: indicate uncertainty or low confidence.
- Frequent review marks: indicate uncertainty or cognitive load.
- Correct, efficient, and consistent performance: indicate a strong signal.
- Recent deterioration: recommend review even when long-term performance is good.

These are guidance rules, not final psychometric claims.

### Future detailed test evidence

If the deeper analysis view is reintroduced, a test detail page may show:

- exact question text;
- answer given;
- correct answer after release policy permits it;
- result;
- active time;
- personal or question-family average time;
- answer changes;
- review marks;
- related bucket/topic/skill;
- a link back to the concept;
- the evidence signals contributing to a descriptive status.

This is a later feature. The current History page remains a compact activity list.

---

## 10. Aptitude and reasoning taxonomy

The first release should have two active high-level buckets. This is enough to make
the data model meaningful without pretending to cover every kind of reasoning.

### 10.1 Quantitative reasoning

#### Topic: Numbers

- Arithmetic.
- Divisibility.
- Factors and multiples.
- Number properties.

#### Topic: Fractions, ratios, and percentages

- Fractions.
- Ratios.
- Proportions.
- Percentages.
- Percent change.

#### Topic: Averages, mixtures, and finance

- Averages.
- Mixtures and alligation.
- Profit and loss.
- Simple interest.
- Basic financial arithmetic.

#### Topic: Time, work, and speed

- Time and work.
- Speed, distance, and time.
- Pipes and work-rate problems.
- Relative speed.

#### Topic: Algebra and data

- Equations.
- Expressions.
- Tables and charts.
- Basic data interpretation.

### 10.2 Logical and analytical reasoning

#### Topic: Patterns and sequences

- Number series.
- Letter series.
- Pattern completion.
- Odd-one-out patterns.

#### Topic: Syllogisms and relations

- Syllogisms.
- Inequalities.
- Blood relations.
- Directions.

#### Topic: Arrangements and constraints

- Seating arrangements.
- Ordering.
- Grouping.
- Constraint puzzles.

#### Topic: Coding and classification

- Coding-decoding.
- Symbol substitution.
- Classification.
- Rule discovery.

#### Topic: Statements and inference

- Assumptions.
- Conclusions.
- Arguments.
- Cause and effect.
- Inference from a set of facts.

### Future buckets

These are intentionally not active in the first release:

- Verbal and critical reasoning.
- Abstract reasoning.
- Spatial reasoning.

They may be added after the first two buckets have useful content and reliable
tracking.

### Content hierarchy

```text
Bucket
  → Topic
    → Skill / concept
      → Question family
        → Question instance / generated variant
```

The **skill** is the unit of learner progress. A question family describes the
underlying pattern. A question instance is a particular wording and parameter set.

Authoring rules:

- Every question has exactly one primary skill.
- A question may reference zero to two concepts.
- Secondary tags are metadata and do not receive duplicate evidence.
- Editorial difficulty is separate from calibrated ability.
- Start with three editorial difficulty levels:
  - `direct`;
  - `multi_step`;
  - `transfer` / `novel`.

---

## 11. Question randomness and assessment breadth

Randomness is useful for preventing memorization and making a short test sample a
broader range of a skill. It must be reproducible and must not make correctness
unclear.

### Preferred approach

Use server-selected, seeded question families:

1. The server receives a test blueprint and a selection seed.
2. The server selects a balanced set of skills and families.
3. Deterministic generators create parameterized instances.
4. Deterministic answer evaluators calculate the correct result.
5. Options are permuted with the same server-side seed.
6. The question order and seed are stored with the session.
7. The current question is delivered without the answer key.

This gives randomness while preserving reproducibility for history, debugging, and
future review.

### What randomness may control

- Question-family selection.
- Skill coverage within a blueprint.
- Parameter values.
- Number values and ranges.
- Wording templates with verified meaning.
- Option ordering.
- Test order.

### What randomness must not control without validation

- Whether a question has exactly one answer.
- Whether the generated values create a degenerate case.
- Whether a distractor accidentally becomes correct.
- Whether the question remains within the intended difficulty.
- Whether a logic puzzle has a valid solution.

### LLM-generated variants

The LLM may propose templates, constraints, distractors, or explanations. It should
not generate an unverified live question directly into a learner test.

For numerical and logical questions, prefer:

```text
reviewed template + deterministic generator + deterministic evaluator
```

The question bank should store enough provenance to reproduce an instance without
revealing generator parameters to the learner.

### Initial coverage policy

The first blueprints should be simple and explicit, for example:

- a fixed number of questions from each active bucket;
- a minimum number of distinct skills;
- a mix of direct and multi-step questions;
- no repeated family in a short test unless intentionally configured;
- a seed stored for reproducibility.

Adaptive testing is not required for the first version.

---

## 12. Content, question, and release model

### Content entities

```text
Bucket
Topic
Concept
Skill
Formula
Flashcard
QuestionFamily
Question
QuestionVariant
SourceReference
ContentRelease
```

### Runtime assessment entities

```text
DeploymentLearner / future User
TestBlueprint
TestSession
SessionQuestion
Answer
TestEvent
ScoreSummary
SkillEvidence
FlashcardReview
```

Every finalized test should retain:

- content-release version;
- blueprint version;
- server selection seed;
- question order;
- option order;
- start time and deadline;
- submitted answers;
- score summary;
- client-observed event data;
- server receipt times.

This keeps history reproducible after content changes.

### Content-release rule

Approved content is published as an immutable release. A later correction creates a
new release; it silently mutates neither old tests nor old evidence.

---

## 13. PowerPoint and LLM ingestion

The user has a large collection of PowerPoint material. Ingestion is important, but
it must not turn the learner frontend into an upload system.

### Current decision

- The public learner frontend has no ingestion endpoint.
- Admin is visible as a sidebar destination because ingestion is an operator
  workflow, not a learner workflow.
- The initial ingestion implementation is a controlled local CLI or worker.
- A full Admin upload/publishing interface is only added after the pipeline is
  reliable and its authorization boundary exists.
- Generated content is never published automatically.

### Pipeline

```text
Original PPTX
    ↓
Extract slide text, tables, notes, and available media
    ↓
Normalize into a reviewable intermediate artifact
    ↓
Retain source provenance and content hashes
    ↓
Propose bucket, topic, concept, skill, and question family
    ↓
Draft concept summaries, formula cards, flashcards, and questions
    ↓
Run schema, duplicate, arithmetic, and answer-uniqueness checks
    ↓
Human review and correction
    ↓
Create an immutable content pack / release
    ↓
Import the approved release into the backend
```

### Source provenance

Each extracted record should retain information such as:

```json
{
  "deck_id": "aptitude-basics-01",
  "source_hash": "...",
  "source_file": "percentages.pptx",
  "slide_number": 17,
  "title": "Percentages",
  "text": "..."
}
```

The source reference must survive into drafts and, where appropriate, approved
content so a reviewer can locate the original slide.

### Initial FOSS-friendly tools

- `python-pptx` for extracting slide text, shapes, and tables.
- A small Python ingestion CLI, kept outside the learner frontend.
- Schema validation using Pydantic or JSON Schema.
- Deterministic Python validators for arithmetic and answer uniqueness.
- SQLite or newline-delimited artifacts for local review.
- Git in `content` for versioning source, normalized records, and approved
  packs.

Potential later tools, only if the workflow earns the complexity:

- Langflow for visual authoring workflows.
- Haystack or LangGraph for a more complex multi-step pipeline.
- LiteLLM for switching between hosted and local model providers.
- Promptfoo or DeepEval for generation regression tests.
- A background worker and object storage for large decks.

The first implementation does not need a visual LLM orchestration platform. A
controlled CLI is easier to audit and faster to change.

### LLM responsibilities

An LLM may:

- classify extracted material;
- suggest bucket, topic, skill, and family labels;
- draft concept summaries;
- draft flashcards and formula summaries;
- draft static question text;
- draft distractors and misconception labels;
- propose parameterized question families;
- suggest explanations;
- detect likely duplicates;
- critique draft quality.

An LLM is not the sole authority for:

- mathematical correctness;
- logic-puzzle correctness;
- exactly-one-correct-answer validation;
- final difficulty;
- publication of diagnostic or high-stakes content.

The safe authoring path is:

```text
LLM draft
  → strict schema validation
  → deterministic correctness checks
  → duplicate and quality checks
  → human review
  → approved content release
```

The requested high-reasoning LLM/subagent approach may be used for research and
drafting when available, but model choice must remain configurable. No model call
belongs in the learner frontend or in the official scoring path.

### File-safety requirements

PowerPoint processing must:

- treat slide text and embedded media as untrusted input;
- enforce file-size and job-size limits;
- never execute macros;
- use a temporary working directory;
- avoid unnecessary network access;
- clean up temporary files;
- preserve an audit trail of the source and generated artifacts.

---

## 14. Repository boundaries

The repositories remain separate because the learning-data boundary is important
and because the backend contract can later support mobile. The coordination overhead
is accepted and managed with a small shared contract and this handoff document.

### 14.1 `grove-frontend`

Location:

```text
frontend/
```

Remote:

```text
git@github.com:mavenrank/grove-frontend.git
```

Owns:

- React UI.
- Vite build.
- TypeScript components.
- shadcn-style primitives and Radix integrations where useful.
- Responsive learner views.
- Test interaction controls.
- Client telemetry collection and submission.
- Loading, empty, and error states.
- A small typed API client.

Must not contain:

- raw PowerPoint files;
- approved question-bank data as application source;
- answer keys;
- scoring rules;
- private generator parameters;
- user history;
- runtime database files;
- secrets.

Tooling decisions:

- React + Vite + TypeScript.
- Bun as package manager and script runner.
- A soft fixed development port of `5175`.
- Future mobile can reuse the domain/API contract without reusing the browser UI.

### 14.2 `grove-backend`

Location:

```text
backend/
```

Remote:

```text
git@github.com:mavenrank/grove-backend.git
```

Owns:

- FastAPI application.
- Pydantic request and response models.
- Test-session state.
- Server-side scoring.
- Expiry and finalization.
- History and evidence queries.
- Content-release delivery.
- Event validation and storage.
- API security.
- Future controlled ingestion boundary.
- Database migrations and backend tests.

Tooling decisions:

- `uv` is the Python package manager and environment manager.
- Python is softly pinned to `3.12` through `.python-version`.
- The project requirement remains flexible enough to change the runtime deliberately.
- A soft development port of `8001` is used by default.
- SQLite is the first persistence target.
- PostgreSQL is a later deployment choice, not a current dependency.

### 14.3 Content boundary

Reviewed content is delivered through versioned releases, separately from learner records.

### 14.4 User data separation

“Keep user data separate” means user data must stay out of source repositories and
out of the content repository. It does not require a Git repository containing live
personal data.

The recommended first deployment is a protected runtime data directory or SQLite
database that is:

- outside the frontend repository;
- outside the content repository;
- excluded from Git;
- backed up separately;
- access-controlled by the deployment.

For a future multi-user deployment, the same logical data can move to PostgreSQL.
The decision about accounts and multi-user identity remains deferred.

---

## 15. Single-learner and account decision

The current product is single-learner and deployment-scoped.

Do not add:

- profile screens;
- profile footers;
- social identity;
- account settings;
- password reset flows;
- multi-user personalization;
- user administration;
- cross-device identity;

unless that decision is explicitly revisited.

The backend may keep a clean seam for a future `user_id` or deployment learner
identity, but it should not force account complexity into the first usable loop.

This is separate from data persistence: the single learner still needs test history,
answers, timing evidence, and flashcard review records.

---

## 16. Admin decision

Admin is a visible sidebar destination because ingestion is an important operator
workflow and should not be hidden behind an undocumented route.

However:

- Admin visibility is not authorization.
- The current Admin surface is a shell/placeholder.
- The learner frontend cannot upload arbitrary data into production.
- Write operations remain disabled until backend authorization, validation, and audit
  logging exist.
- The first real ingestion path may be a local CLI rather than a browser upload.
- A future Admin UI should show job status and review errors, not bypass review.

The safe progression is:

```text
local CLI → controlled backend import → reviewable Admin shell → gated Admin writes
```

---

## 17. Backend API shape

The API should be small and noun/action oriented. It should not expose database
tables as the public design.

### Content reads

```text
GET /api/content/buckets
GET /api/content/topics
GET /api/content/concepts/{concept_id}
GET /api/flashcards
```

These responses contain only approved learner-safe content.

### Test lifecycle

```text
POST /api/test-sessions
GET  /api/test-sessions/{session_id}/question
POST /api/test-sessions/{session_id}/answer
POST /api/test-sessions/{session_id}/events
POST /api/test-sessions/{session_id}/finish
```

The eventual contract should support:

- blueprint selection;
- question count;
- server-created deadline;
- opaque question tickets;
- idempotency keys;
- answer submission;
- review marks;
- bounded event batches;
- finalization;
- result release policy.

### History and learner evidence

```text
GET /api/history
GET /api/history/tests/{test_id}
GET /api/insights
GET /api/skills/{skill_id}/evidence
```

The test-detail and evidence endpoints can be added after the simple History page
and server persistence work.

### Admin and ingestion

Administrative ingestion endpoints are not part of the public learner API in the
first release. Use a local command or controlled deployment step until the
authorization boundary exists.

---

## 18. API security baseline

The security implementation should be explained plainly and verified in tests.

Required controls when the real API is built:

- HTTPS in every non-local deployment.
- Exact-origin CORS if cross-origin deployment is unavoidable.
- Strict Pydantic request and response models.
- Public response allowlists.
- No direct database-object serialization.
- Rate limits on session creation, question retrieval, answer submission, event
  ingestion, login if added, and finalization.
- Request size limits and event-count limits.
- Replay protection and idempotency keys.
- Transactions around answer and final-submission state changes.
- State-machine checks for every test transition.
- Object-level authorization for every user-owned resource if accounts are later
  enabled.
- Separate administrative authorization.
- `Cache-Control: no-store` for personalized test responses.
- Restrictive Content Security Policy.
- No secrets in frontend environment variables.
- Redacted logs.
- Safe error responses without production stack traces.
- Audit records for scoring finalization and content publication.

If accounts are introduced later, add:

- secure, HttpOnly, SameSite session cookies or an equally deliberate session model;
- CSRF protection for state-changing cookie-authenticated requests;
- Argon2id password hashing if passwords are owned by Grove;
- account recovery and data deletion policy;
- per-user access checks on every history/test resource.

### Security tests

Before calling the secure test loop complete, add tests for:

- answer-key leakage in public responses;
- unauthorized session access;
- ID tampering;
- replayed answers;
- duplicate finalization;
- expired sessions;
- invalid options;
- race conditions around finalization;
- excessive event payloads;
- excessive data exposure;
- CSRF where applicable;
- XSS-safe rendering of imported text;
- unauthorized content publication.

---

## 19. Phased roadmap

The stage names are intentionally small. Do not start a later stage merely because
its technology is interesting.

### Stage 0 — Decisions and repository baseline

**Status: Done / documented**

- Name the project Grove.
- Create separate frontend, backend, and local content repositories.
- Keep learning data out of the app repositories.
- Define the FastAPI/React split.
- Define Bun and uv tooling.
- Define development ports `5175` and `8001`.
- Add version and changelog files to the application repositories.
- Add repo-local docs, roadmaps, proposals, ADRs, and runbooks.
- Record that user/profile features are deferred.
- Record that Admin is a visible destination but not an open upload path.

### Stage 1 — Lightweight learner shell

**Status: Prototype exists; integration pending**

Deliver:

- Overview.
- Learn navigation.
- Flashcard shell.
- Simple History activity lists.
- Tests setup screen.
- Admin placeholder.
- Responsive sidebar.
- Compact metrics and tooltips.
- No profile/user footer.
- No learning data embedded as the long-term source of truth.

Exit condition:

- The UI shows the intended surfaces without pretending the backend is connected.

### Stage 2 — Content model and private ingestion MVP

**Status: Next**

Deliver:

- Initial taxonomy files.
- Concept and formula schema.
- Flashcard schema.
- Question-family schema.
- Question-instance schema.
- PowerPoint extraction CLI.
- Slide-level provenance.
- LLM-assisted draft artifacts.
- Deterministic validation.
- Human review workflow.
- Immutable content-pack manifest.

Exit condition:

- One source deck can become a reviewed, versioned content pack without the learner
  frontend uploading anything.

### Stage 3 — Server-authoritative test loop

**Status: Next**

Deliver:

- SQLite schema and migrations.
- Published-content reads.
- Test blueprint.
- Test-session creation.
- One-question delivery.
- Question-count and deadline rules.
- Answer submission.
- Review-mark persistence.
- Server-side scoring.
- Atomic finalization.
- Result summary.

Exit condition:

- A learner can complete a test while the browser never receives the answer key or
  scoring rule.

### Stage 4 — Client telemetry and simple history

**Status: Planned**

Deliver:

- Client event collection.
- Per-question active dwell calculation.
- Answer-change and review events.
- Visibility/focus events.
- Bounded event submission.
- Server receipt timestamps.
- Recent tests list.
- Recent learning list.
- Recent flashcard list.
- Basic result/history API.

Exit condition:

- A completed test produces enough structured evidence to inspect what happened,
  without making the current History UI complex.

### Stage 5 — Learner evidence and recommendations

**Status: Planned / deliberately after the basic loop**

Deliver:

- Skill-level aggregates.
- Question-family timing baselines.
- Accuracy and recent consistency.
- Answer-change and review rates.
- Attempts and difficulty handled.
- Improvement/deterioration signals.
- Descriptive statuses with insufficient-evidence handling.
- Weak-area recommendations.
- Optional deeper test detail view.

Exit condition:

- Recommendations are explainable from stored evidence and do not claim a formal
  aptitude score.

### Stage 6 — Controlled Admin workflow

**Status: Later**

Deliver:

- Backend ingestion job boundary.
- Controlled operator authorization.
- Job status.
- Review error display.
- Content-pack import.
- Publication audit events.

Exit condition:

- An operator can process and publish reviewed content without giving the learner
  frontend arbitrary write access.

### Stage 7 — Hardening and deployment

**Status: Later**

Deliver:

- Security test suite.
- Request/rate limits.
- Security headers.
- Backup and restore procedure.
- Structured redacted logs.
- Release compatibility checks between frontend and backend.
- Deployment documentation.

Exit condition:

- The single-learner deployment is maintainable and its security boundary is tested.

### Stage 8 — Explicitly deferred expansion

**Status: Not scheduled**

Only begin after a separate product decision:

- Accounts and multi-user identity.
- Cross-device sync.
- Mobile client.
- Offline read-only learning.
- Postgres.
- Background workers and object storage.
- Adaptive test selection.
- Rasch/1PL, 2PL, IRT, CAT, or percentile reporting.
- DIF/fairness analysis.
- Verbal, abstract, and spatial buckets.
- LMS export/import.
- Social features.

---

## 20. Current implementation status

This section describes the repository state at the time this handoff was
consolidated. It is not a substitute for running the code.

### Frontend

Current prototype includes:

- React + Vite + TypeScript shell.
- Overview, Learn, Flashcards, History, Tests, and Admin surfaces.
- Flatter visual language.
- Rectangular surfaces instead of pill-heavy cards.
- No user/profile surface.
- Admin in the sidebar.
- Compact metric strip with icon tooltips.
- Simple recent-activity History view.
- Tests setup screen with question-count and derived time preview.
- A test interaction prototype.
- Development port `5175`.

Still pending:

- Typed backend API client.
- Real published content reads.
- Real test-session creation.
- Real server-delivered questions.
- Real telemetry submission.
- Real history reads.
- Real flashcard state.
- Loading, empty, and error states for API-backed screens.
- Backend-connected Admin status.

### Backend

Current baseline includes:

- uv-managed FastAPI application.
- Soft Python `3.12` pin.
- Settings foundation.
- Root and health endpoints.
- Initial automated health test.
- Development port `8001`.

Still pending:

- SQLite persistence and migrations.
- Content-release reads.
- Test-session state machine.
- Question delivery.
- Answer submission.
- Server scoring.
- Event ingestion.
- History and evidence queries.
- Security hardening.
- Controlled ingestion boundary.

### Content

Current direction includes:

- Local Git-tracked content repository.
- Existing source-preserved course material/import area.
- A consolidated product scope document.

Still pending:

- Canonical taxonomy files.
- Normalized concept and formula records.
- Reviewed flashcard packs.
- Reviewed question-family packs.
- Validation tooling.
- Immutable content-release manifests.
- Import into the backend.

---

## 21. Definition of done for the first real release

The first meaningful release is complete when:

1. A learner can read approved concepts and formulas.
2. A learner can review approved flashcards.
3. A learner can start a test with a server-owned session.
4. The backend selects the test questions and stores the deadline.
5. The frontend receives only learner-safe current-question data.
6. The frontend never contains answer keys or scoring rules.
7. The learner can answer, change, revisit, and mark for review.
8. Detailed client timing and interaction events are bounded and stored.
9. The backend scores and finalizes the attempt.
10. Test history is persisted outside the application source repositories.
11. History can show recent tests, learning, and flashcards.
12. A source PowerPoint can be turned into reviewed draft content through the private
    pipeline.
13. Approved content can be imported as an immutable release.
14. Security tests cover answer leakage, authorization, replay, expiry, and final
    submission.
15. The deployment can be backed up and restored without committing personal data
    or live databases to Git.

---

## 22. Decisions that must not be silently reversed

Do not silently:

- put question banks or answer keys in `grove-frontend`;
- put user history in `content`;
- send a complete test and answer key to the browser;
- calculate official score in React;
- let an LLM publish directly to the approved bank;
- add public frontend ingestion;
- add user/profile UI because history exists;
- describe client timing as tamper-proof;
- claim that the app prevents screenshots or other devices;
- introduce Postgres, queues, sync, or mobile before the current loop needs them;
- bring back the complex History analysis view without an explicit product decision;
- turn descriptive learner statuses into formal aptitude claims.

---

## 23. Open questions for a future decision

These are intentionally open rather than accidentally decided in code:

1. Should the first deployment use a purely local single-learner database or a
   protected small server instance?
2. Should the final question-count options remain `5/10/15/20`, or should the
   backend expose a blueprint list?
3. Which content format should become the canonical approved-pack format: JSON,
   YAML, SQLite, or a generated combination?
4. How much of a PowerPoint’s images and speaker notes should be retained in the
   first ingestion release?
5. When should the richer test-detail evidence view return to History?
6. What evidence threshold is sufficient to show a recommendation for a skill?
7. When do the operational benefits of a worker or Postgres justify their cost?
8. When, if ever, should account identity and cross-device use be added?

Until explicitly decided, use the smallest option that preserves the current
boundaries.

---

## 24. Practical next implementation order

The next work should be narrow and vertical:

1. Define the first content schemas in `content`.
2. Create one reviewed concept, one flashcard, and a small set of question families.
3. Add SQLite migrations and typed backend models.
4. Implement `POST /api/test-sessions` and current-question delivery.
5. Add public/private response-model tests proving answer keys do not leak.
6. Replace the frontend static test prototype with the real session contract.
7. Add answer submission and server finalization.
8. Add bounded client telemetry and server receipt times.
9. Connect the simple History page to real recent activity.
10. Add the first evidence aggregate only after real attempts exist.
11. Add the private PowerPoint/LLM ingestion CLI in parallel with content growth,
    not as a public upload feature.

Do not begin with mobile, sync, adaptive testing, a polished Admin CMS, or a large
question-generation platform.

---

## 25. Glossary

**Bucket** — A broad reasoning domain, currently quantitative or logical/analytical.

**Topic** — A major area within a bucket, such as ratios or arrangements.

**Skill** — The unit at which learner evidence is aggregated.

**Question family** — A reusable problem pattern with rules and a validated solution
method.

**Question instance** — One concrete wording and parameterization of a family.

**Content release** — An immutable, reviewed version of learner-safe content and
private assessment data.

**Active dwell time** — Client-observed time during which a question is the active
focus, excluding recorded hidden/unfocused intervals. It is not proof of reading.

**Server-authoritative scoring** — The backend decides correctness and score; the
browser submits answers but cannot choose its own result.

**Admin** — The operator-facing ingestion and publication boundary, not a learner
profile or account-management feature.

**Single-learner deployment** — A deployment used by one learner without the first
release needing multi-user accounts or social identity.

---

## 26. Existing supporting documents

The following documents already exist and should be kept aligned with this handoff:

```text
aptitude/GROVE_SCOPE.md

grove-frontend/docs/README.txt
grove-frontend/docs/roadmap.txt
grove-frontend/docs/research.txt
grove-frontend/docs/proposal.txt
grove-frontend/docs/adr/
grove-frontend/docs/runbooks/

grove-backend/docs/README.txt
grove-backend/docs/roadmap.txt
grove-backend/docs/research.txt
grove-backend/docs/proposal.txt
grove-backend/docs/adr/
grove-backend/docs/runbooks/

GROVE_SCOPE.md
```

This handoff is the single place to understand the whole product. The repository
documents remain the place for implementation-specific details and repeatable
operations.

---

## 27. Addendum — implementation decisions (2026-09-19)

Recorded per the change-control rule in §2 after the first working build.

1. **Monorepo.** `grove-frontend` and `grove-backend` now live together in the
   `grove/` checkout (`backend/`, `frontend/`). The learning-data boundary is
   unchanged — no question data, answer keys, or user history in the frontend;
   no user data in content material.
2. **Standard ports.** Backend `8000`, frontend `5173` (superseding the soft
   ports `8001`/`5175` from §14).
3. **Tooling.** Frontend: bun + React 19 + Vite + Tailwind 4 + Radix tooltip.
   Backend: uv, soft-pinned Python 3.12, FastAPI, SQLite at `backend/data/`.
4. **Ingestion pipeline.** Implemented as the private `grove-ingest` CLI inside
   the backend (`discover → extract → classify → validate → pack → import`),
   with JSON artifacts and per-file/per-slide provenance. Deck titles classify
   onto the §10 taxonomy; unmatched material is preserved as
   `unclassified.deferred` and never published. Approval is explicit
   (`--approve`); the import step refuses unapproved packs.
5. **Question generation.** First release uses reviewed deterministic generator
   families (seeded, option-permuted, exactly four options) matching §11's
   `reviewed template + deterministic generator + deterministic evaluator`
   approach. Ingested decks surface as draft concepts for human authoring.
