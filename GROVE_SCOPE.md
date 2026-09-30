# Grove

## Product scope and architecture decision record

> **Canonical cross-repository handoff:** See [GROVE_HANDOFF.md](GROVE_HANDOFF.md)
> for the consolidated product scope, decisions, staged roadmap, repository
> boundaries, security model, content pipeline, and open questions.

**Status:** Product direction and prototype baseline. The production backend loop is
not implemented yet.

**Purpose:** A lightweight aptitude and reasoning learning application with concept review, flashcards, server-authoritative tests, detailed attempt analytics, and a private content-ingestion pipeline.

**Working name:** Grove.

## 1. Core principles

1. Keep the learner application small and fast.
2. Keep learning content out of the frontend bundle and source repository.
3. Keep answer keys, grading rules, and test state on the backend.
4. Treat the browser as an untrusted client for scoring and authorization.
5. Record detailed client interaction timing for personal analytics, but keep official scoring server-side.
6. Make content versioned, reviewable, reproducible, and importable.
7. Do not build complex assessment science until the basic evidence and workflow are working.

## 2. Deliberate v1 boundary

### Included

- Concept and formula pages
- Simplified flashcards
- Two active aptitude/reasoning buckets
- Server-created test sessions
- One-question-at-a-time question delivery
- Server-side scoring and test finalization
- Client-side timing and interaction telemetry
- Tab visibility and fullscreen event logging
- Test history
- Topic and skill-level performance summaries
- Weak-area recommendations
- Private PowerPoint ingestion CLI
- Human review before content publication
- Versioned content releases

### Explicitly deferred

- Mobile application
- Offline synchronization
- IRT, CAT, percentile, or formal ability claims
- Webcam or audio proctoring
- Device lockdown
- Public file uploads
- Collaborative authoring
- Runtime question generation for learners
- Automatic publication of LLM-generated content
- Complex prerequisite graphs
- Advanced spaced-repetition algorithms
- Verbal and abstract/spatial buckets
- Moodle, QTI, or other LMS integrations in the first build

## 3. Learner-facing application

The learner application has four primary sections:

### Learn

- Browse bucket, topic, and concept
- Read short explanations
- View formulas, rules, worked examples, and common mistakes
- Navigate to related flashcards and questions

### Flashcards

- View a simplified concept or formula
- Reveal the explanation or example
- Mark `again` or `remember`
- Store basic review history
- Later generate a review queue from weak skills

Flashcards are approved content. The learner frontend does not call an LLM to create them live.

### Test

- Choose a fixed test blueprint
- Receive questions from the backend
- Answer, skip, revisit, and mark for review
- See a server-controlled countdown
- Receive no correctness feedback during the test
- Submit for server-side evaluation

### History

- Test score and completion date
- Accuracy by bucket, topic, and skill
- Time spent by question and question family
- Answer changes and review marks
- Weak-area indicators
- Improvement or deterioration over recent attempts

## 4. Security model in plain language

The goal is not to create a legally secure proctored examination environment. The goal is to protect the application, answer keys, scoring, and personal data while making test mode meaningfully isolated.

### What the system guarantees

- Correct answers never leave the backend before results are intentionally released.
- Grading logic and scoring weights remain on the backend.
- The client receives only the current question and its options.
- Learning content is not loaded into the test interface.
- The client cannot submit its own score.
- The server owns test expiry, attempt state, and final scoring.
- Users cannot access another user's attempts or history.
- Content ingestion is not available from the public frontend.

### What is intentionally out of scope

- Preventing screenshots
- Preventing use of another device
- Proving that nobody else is helping
- Detecting every browser extension or modified browser
- OS-level keyboard or application lockdown

For a personal learning tool, these are not reasons to build a heavyweight proctoring system.

## 5. Test-mode isolation

The preferred arrangement is a separate lightweight test entry point, and eventually a separate test origin if useful.

The test interface must not import or preload:

- Concepts
- Flashcards
- Formulas
- Explanations
- Answer keys
- Skill metadata
- Difficulty metadata
- Future questions

When entering test mode, the frontend should clear learner query state, session state, and client caches that are not needed for the test. The test interface should use `Cache-Control: no-store` responses and should not persist test data in `localStorage`, IndexedDB, or service-worker caches.

Clearing the frontend is a data-minimization measure, not a promise that a browser's memory can be physically wiped. That is acceptable because the test interface should never have loaded the learning library or answer keys in the first place.

## 6. Test-session protocol

### Server-owned state machine

```text
created → active → submitted
                 ↘ expired
                 ↘ cancelled
```

### Flow

1. An authenticated user creates a test attempt.
2. The server selects an immutable test revision, question order, and option permutations.
3. The server stores the start time, deadline, user, blueprint version, and attempt state.
4. The client requests the next question.
5. The server returns one question and an opaque, session-specific question ticket.
6. The client submits the selected option and an idempotency key.
7. The server verifies the ticket, attempt, option, state, deadline, and authorization.
8. The server stores the answer and issues the next question.
9. Final submission atomically locks the attempt and calculates the score.
10. Results and explanations are released according to the test policy.

### Public question response

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

The response must not include:

- `correct_option_id`
- `is_correct`
- `answer_hash`
- `explanation`
- `grading_rule`
- `skill_id`
- `difficulty`
- `generator_parameters`
- Full question-bank identifiers
- Future questions

Separate public and private response models should be used as allowlists. Never serialize database objects directly into learner responses.

## 7. Timing and interaction analytics

The client owns detailed observational timing. The server owns official test validity and scoring.

### Client events

```text
test_started
question_shown
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

For every question, derive:

- Active dwell time
- Time before the first answer
- Time after the first answer
- Number of answer changes
- Time while marked for review
- Number of revisits
- Time while the page was hidden
- Server receipt time

The product should call this **active dwell time**, not reading time. A browser cannot know exactly when a user has read a question.

Client timing is stored as `client_observed`. It is useful for personal analytics but may be altered by a modified client. It must not determine the official score.

### Useful interpretation patterns

| Pattern | Possible signal |
|---|---|
| Fast and correct | Strong fluency |
| Slow and correct | Concept understood, fluency needs work |
| Fast and incorrect | Carelessness or misreading |
| Slow and incorrect | Concept or method difficulty |
| Many revisions | Low confidence |
| Frequent review marks | High uncertainty or cognitive load |

## 8. Learner analysis

The learner model should not collapse everything into one aptitude score.

Track these independent signals per skill:

- Accuracy
- Recent accuracy
- Active time compared with similar questions
- Answer-change rate
- Review-mark rate
- Difficulty level handled
- Consistency across tests
- Number of attempts
- Recent improvement or decline

Compare timing only within the same:

```text
skill + question type + editorial difficulty
```

Use the learner's own median as the initial baseline. Do not compare a simple arithmetic question with a difficult multi-step puzzle.

### Suggested statuses

```text
unseen
developing
slow_but_accurate
inaccurate
inconsistent
strong
needs_review
```

Recommended evidence rules:

- Fewer than five attempts: show `insufficient evidence`.
- Repeated wrong answers: show a concept or method concern.
- Correct but unusually slow: show a fluency concern.
- Fast but inaccurate: show an accuracy or reading concern.
- Correct, efficient, and consistent: show a strong signal.
- Recent decline: recommend review even if the long-term record is good.

## 9. Initial taxonomy

Start with two active buckets and keep the data model extensible.

### Quantitative reasoning

1. `quant.numbers`
   - Arithmetic
   - Divisibility
   - Factors and multiples

2. `quant.fractions_ratios_percentages`
   - Fractions
   - Ratios
   - Proportions
   - Percentages

3. `quant.averages_mixtures_finance`
   - Averages
   - Mixtures
   - Profit and loss
   - Simple interest

4. `quant.time_work_speed`
   - Time and work
   - Speed, distance, and time
   - Pipes and work-rate problems

5. `quant.algebra_data`
   - Equations
   - Expressions
   - Tables and charts
   - Basic data interpretation

### Logical and analytical reasoning

1. `logic.patterns_sequences`
   - Number series
   - Letter series
   - Pattern completion

2. `logic.syllogisms_relations`
   - Syllogisms
   - Inequalities
   - Blood relations
   - Directions

3. `logic.arrangements`
   - Seating arrangements
   - Ordering
   - Grouping
   - Constraint puzzles

4. `logic.coding_decoding`
   - Coding-decoding
   - Symbol substitution
   - Classification

5. `logic.statements_inference`
   - Assumptions
   - Conclusions
   - Arguments
   - Cause and effect

Future buckets, not active in v1:

- Verbal and critical reasoning
- Abstract and spatial reasoning

### Content hierarchy

```text
Bucket
  → Topic
    → Skill
      → Question family
        → Question instance
```

The skill is the unit of learner progress.

Authoring rules:

- Every question has exactly one primary skill.
- A question may reference zero to two concepts.
- Secondary skills are optional metadata and do not receive duplicate evidence.
- Difficulty is editorial, not a calibrated ability parameter.
- Use three initial difficulty levels: direct, multi-step, and transfer/novel.

## 10. Content and question model

### Content entities

```text
Bucket
Topic
Concept
Skill
Flashcard
QuestionFamily
Question
ContentRelease
SourceReference
```

### User entities

```text
User
TestBlueprint
TestSession
SessionQuestion
Answer
TestEvent
ScoreSummary
SkillEvidence
```

Every test session stores:

- Content-release version
- Blueprint version
- Server selection seed
- Question ordering
- Option ordering
- Start time and deadline
- Final score

This keeps historical tests reproducible after content changes.

## 11. Repository and data separation

### Repositories

```text
grove-frontend/
  React, Vite, TypeScript, learner UI, test UI

grove-backend/
  FastAPI, authentication, test sessions, scoring, history, migrations, tests

content/
  Taxonomy, concepts, flashcards, approved questions, templates, ingestion tools, manifests
```

The frontend repository contains application code only. It must not contain question data, answer keys, flashcards, PowerPoint files, or user history.

### Runtime data stores

```text
content.db
  Read-only approved content and versioned releases

userdata.db
  Users, tests, answers, events, scores, and skill evidence
```

For a single-instance lightweight deployment, SQLite is appropriate. For a hosted multi-user deployment, use PostgreSQL. User data belongs in a database or protected data directory, not in Git.

## 12. PowerPoint and LLM ingestion pipeline

The public frontend has no ingestion feature.

```text
Original PPTX
  ↓
Extract slide text and tables
  ↓
Normalize with slide-level provenance
  ↓
Propose bucket, topic, concept, and skill
  ↓
Draft flashcards and questions
  ↓
Validate schemas and answers
  ↓
Human review
  ↓
Create immutable content release
  ↓
Import release into backend
```

The first parser can use `python-pptx` for slide text, shapes, and tables. Images, OCR, speaker notes, and complex diagrams can be added later.

Each extracted record retains:

```json
{
  "deck_id": "aptitude-basics-01",
  "source_hash": "...",
  "slide_number": 17,
  "title": "Percentages",
  "text": "...",
  "source_file": "percentages.pptx"
}
```

PowerPoint processing should run in an isolated environment with file-size limits, no macro execution, no unnecessary network access, and temporary-file cleanup.

Treat slide text as untrusted input. LLM-generated content is always a draft. The model must not be able to publish directly to the production database.

## 13. LLM authoring boundary

The LLM may:

- Classify extracted material
- Suggest topics and skills
- Draft concept summaries
- Draft flashcards
- Draft static questions
- Draft distractors and misconception labels
- Propose parameterized question families
- Suggest explanations
- Detect likely duplicates
- Critique draft quality

The LLM may not be the sole authority for:

- Mathematical correctness
- Logic-puzzle correctness
- Exactly-one-correct-answer checks
- Final difficulty
- Diagnostic or high-stakes publication

The safe workflow is:

```text
LLM draft → strict schema validation → deterministic checks → human review → publish
```

For numerical and logical variants, prefer deterministic generators and answer evaluators. The LLM can create the template and constraints, while code generates seeded variants and verifies answers.

## 14. Suggested API surface

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/me

GET  /api/content/topics
GET  /api/content/concepts
GET  /api/flashcards

POST /api/test-sessions
GET  /api/test-sessions/{id}/question
POST /api/test-sessions/{id}/answer
POST /api/test-sessions/{id}/events
POST /api/test-sessions/{id}/finish

GET  /api/history
GET  /api/insights
```

Administrative ingestion endpoints are not part of the public API in v1. Content is imported through a private command or controlled deployment step.

## 15. Security checklist

- HTTPS in every non-local deployment
- Secure, HttpOnly, SameSite session cookie
- CSRF protection for state-changing requests
- Argon2id password hashing
- Exact-origin CORS if cross-origin deployment is unavoidable
- Object-level authorization on every user-owned resource
- Separate administrative authorization
- Strict request and response schemas
- Rate limits on login, session creation, question retrieval, answers, and finalization
- Replay protection and idempotency keys
- Database transactions around answer and final-submission state changes
- `Cache-Control: no-store` for personalized test responses
- Restrictive Content Security Policy
- No secrets in frontend environment variables
- Redacted logs
- No production stack traces
- Automated tests that assert answer keys never appear in public responses
- Tests for ID tampering, replay, expiry, race conditions, CSRF, XSS, and excessive data exposure

## 16. FOSS-friendly building blocks

- React, Vite, shadcn/ui, and Radix for the frontend
- FastAPI and Pydantic for the backend
- SQLite initially, PostgreSQL later
- `python-pptx` for initial PowerPoint extraction
- A small Python CLI for ingestion
- Langflow if a visual LLM workflow becomes useful
- Haystack or LangGraph if the production authoring workflow becomes complex
- LiteLLM if switching between hosted and local models becomes important
- Promptfoo or DeepEval later for generation regression tests

The private CLI is enough for v1. A full admin dashboard should only be added after the ingestion and approval workflow becomes repetitive.

## 17. Definition of done for the first build

The first build is complete when:

1. A user can read approved concepts and flashcards.
2. A user can start a fixed test.
3. The server delivers questions without answer keys.
4. The client records detailed question events and timing.
5. The server scores and finalizes the test.
6. The user can view history and topic/skill summaries.
7. A PowerPoint deck can be processed privately into reviewed content drafts.
8. Approved content can be imported as a versioned release.
9. No learning data or answer keys are embedded in the frontend build.
10. Security tests cover authorization, replay, expiry, and public-response leakage.

## References

- [FastAPI security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [MDN Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API)
- [MDN Fullscreen API](https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API)
- [python-pptx documentation](https://python-pptx.readthedocs.io/en/latest/)
- [GPT-5.6 Luna documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
