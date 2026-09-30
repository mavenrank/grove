from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GROVE_", env_file=".env", extra="ignore")

    app_name: str = "Grove"
    # TEMPORARY (2026-09-20): default 8000 is occupied by another application
    # on this machine; flipped to 8001 until it frees up. Override anytime with
    # GROVE_PORT=<port>. Standard port per product decision remains 8000.
    port: int = 8001
    data_dir: Path = REPO_ROOT / "data"
    content_dir: Path = REPO_ROOT / "content"
    db_filename: str = "grove.db"
    # Slide images extracted by the ingestion pipeline (served read-only).
    media_dir: Path = REPO_ROOT / "content" / "media"

    # CORS: local Vite dev origins (standard ports).
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # Test blueprints: question counts and derived duration (one minute per question).
    allowed_question_counts: list[int] = [5, 10, 15, 20]
    seconds_per_question: int = 60
    blueprint_version: str = "blueprint-1"

    # Security knobs.
    rate_limit_per_minute: int = 240
    rate_limit_create_session_per_minute: int = 12
    max_events_per_batch: int = 200
    max_event_payload_bytes: int = 2048
    max_event_body_bytes: int = 256 * 1024

    # Learner identity is deployment-scoped for now (single-learner decision).
    default_learner: str = "local-learner"

    # QOL: allow the app to reveal an ingested source deck in the local file
    # explorer. This is a deliberate local-dev convenience (single-learner,
    # localhost-only product) — it is disabled when source_root is unset.
    enable_source_open: bool = True

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename

    @property
    def releases_dir(self) -> Path:
        return self.content_dir / "releases"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.media_dir.mkdir(parents=True, exist_ok=True)
