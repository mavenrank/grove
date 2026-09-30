"""SQLite DDL. Two logical stores in one file (single-learner deployment):

  - content store: immutable published releases (re-imports create new rows)
  - runtime store: sessions, questions, answers, events, scores, flashcard reviews
"""

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS content_releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    manifest TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE (release_id, version)
);

CREATE TABLE IF NOT EXISTS test_sessions (
    id TEXT PRIMARY KEY,
    learner TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('created','active','submitted','expired','cancelled')),
    question_count INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    seed TEXT NOT NULL,
    blueprint_version TEXT NOT NULL,
    release_id TEXT NOT NULL,
    release_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    deadline_at TEXT NOT NULL,
    submitted_at TEXT,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS session_questions (
    session_id TEXT NOT NULL REFERENCES test_sessions(id),
    position INTEGER NOT NULL,
    ticket TEXT NOT NULL,
    family_id TEXT NOT NULL,
    question_ref TEXT NOT NULL,
    question_json TEXT NOT NULL,   -- full private question incl. answer
    public_json TEXT NOT NULL,     -- allowlisted public payload
    answered INTEGER NOT NULL DEFAULT 0,
    answer_option TEXT,
    is_correct INTEGER,
    answered_at TEXT,
    marked INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, position)
);

CREATE TABLE IF NOT EXISTS client_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES test_sessions(id),
    position INTEGER,
    event_type TEXT NOT NULL,
    client_time REAL,
    server_time TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS score_summaries (
    session_id TEXT PRIMARY KEY REFERENCES test_sessions(id),
    total_questions INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    incorrect INTEGER NOT NULL,
    unanswered INTEGER NOT NULL,
    accuracy REAL NOT NULL,
    duration_seconds INTEGER NOT NULL,
    finalized_at TEXT NOT NULL,
    per_question TEXT NOT NULL,
    release_version TEXT NOT NULL,
    blueprint_version TEXT NOT NULL,
    seed TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flashcard_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL,      -- opaque flashcard ref
    release_id TEXT NOT NULL,
    release_version TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('again','remember')),
    reviewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concept_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT NOT NULL,
    title TEXT NOT NULL,
    viewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flashcard_schedule (
    flashcard_id TEXT PRIMARY KEY,
    ease REAL NOT NULL DEFAULT 2.5,
    interval_days REAL NOT NULL DEFAULT 0,
    due_at TEXT NOT NULL,           -- ISO UTC; due when <= now
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    last_rated_at TEXT
);

CREATE TABLE IF NOT EXISTS flashcard_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flashcard_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    release_id TEXT NOT NULL,
    release_version TEXT NOT NULL,
    viewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_timing (
    session_id TEXT NOT NULL REFERENCES test_sessions(id),
    position INTEGER NOT NULL,
    first_shown_at TEXT NOT NULL,
    last_active_at TEXT,
    answer_changed INTEGER NOT NULL DEFAULT 0,
    revisit_count INTEGER NOT NULL DEFAULT 0,
    marked_after_seconds REAL,
    dwell_seconds REAL NOT NULL DEFAULT 0,
    marked INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, position)
);

CREATE TABLE IF NOT EXISTS question_dwell_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES test_sessions(id),
    position INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    seconds REAL NOT NULL,
    kind TEXT NOT NULL DEFAULT 'active'
);
"""
