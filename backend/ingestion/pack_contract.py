"""Versioned local pack boundary; native evidence stays intact for review (#7/#8)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from app.lessons import Lesson

PACK_SCHEMA_VERSION = 1
ORGANIZATION_VERSION = 1
Text = Annotated[str, Field(min_length=1)]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
MediaID = Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]
Version = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]


class Record(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Source(Record):
    deck_id: Text
    source_file: Text
    source_path: Text
    source_hash: Hash
    slide_number: Annotated[int, Field(ge=1)]
    slide_id: Text
    deck_label: str = ""
    surface: Literal["slide", "notes"] = "slide"
    role: Literal["prompt", "choices_and_solution"] | None = None


class Deck(Record):
    deck_id: Text
    source_file: Text
    source_path: Text
    source_hash: Hash
    slide_count: Annotated[int, Field(ge=1)]
    short_name: str = ""
    skill_id: str = ""
    status: Literal["active", "deferred"] = "active"


class Reference(Deck):
    skill_id: Text
    status: Literal["active", "deferred"]


class Evidence(Record):
    source: Source
    media_ids: list[MediaID]
    blocks: list[dict[str, Any]]
    notes_media_ids: list[MediaID]
    notes_blocks: list[dict[str, Any]]


class Example(Evidence):
    prompt: Text
    options: Annotated[dict[Literal["a", "b", "c", "d", "e"], Text], Field(min_length=2, max_length=5)]
    answer: Literal["a", "b", "c", "d", "e"]
    explanation: str
    answer_status: Literal["notes_confirmed"]
    answer_evidence: Annotated[list[dict[str, Any]], Field(min_length=1)]
    source_parts: list[Source] = []


class Question(Example):
    notes_raw: Text
    issues: Annotated[list[dict[str, Any]], Field(max_length=0)]
    unmapped_option_text: Annotated[list[str], Field(max_length=0)]
    media_sources: dict[MediaID, Source] = {}


class Segment(Evidence):
    texts: list[str]
    raw_texts: list[str]
    notes: str
    issues: list[dict[str, Any]]
    content_mode: Literal["text_only", "image_only", "hybrid", "empty"]


class Code(Record):
    language: Text
    code: Text
    source: Source


class Media(Record):
    image_id: MediaID
    source: Source


class Candidates(Record):
    formulas: list[Text]
    code_blocks: list[Code]
    examples: list[Example]


class Concept(Record):
    id: Text
    skill_id: Text
    title: Text
    summary: Text
    summary_status: Literal["native_text_candidate"]
    formulas: list[Text]
    code_blocks: list[Code]
    examples: list[Example]
    learning_segments: list[Segment]
    review_candidates: Candidates
    truncations: list[dict[str, Any]]
    media: list[Media]
    common_mistakes: list[str]
    related_families: list[str]
    source_decks: Annotated[list[Deck], Field(min_length=1)]
    question_review_count: Literal[0]
    lesson: Lesson | None = None


class Authored(Record):
    authored: Literal[True]


class Card(Record):
    id: Text
    skill_id: Text
    front: Text
    back: Text
    kind: Literal["formula", "rule", "approach", "shortcut", "mindset"]
    source: Source | Authored


class Approval(Record):
    method: Literal["operator-approve-after-pipeline-validation"]
    reviewed_at: Text
    catalog_sha256: Hash
    draft_sha256: Hash
    unresolved_review_items: Literal[0]


class Pack(Record):
    schema_version: Literal[1]
    extraction_version: Literal[3]
    organization_version: Literal[1]
    release_id: Literal["grove-ingested"]
    version: Version
    generated_at: Text
    approved: Literal[True]
    approval: Approval
    content_sha256: Hash
    source: Text
    source_root: Text
    concepts: Annotated[list[Concept], Field(min_length=1)]
    flashcards: list[Card]
    question_pool: list[Question]
    families: Annotated[list[dict[str, Any]], Field(max_length=0)]
    media_ids: list[MediaID]
    source_refs: Annotated[list[Reference], Field(min_length=1)]
    stats: dict[str, int]


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_version(version: str) -> None:
    try:
        TypeAdapter(Version).validate_python(version, strict=True)
    except ValidationError as exc:
        raise ValueError("version must be a safe 1–64 character identifier") from exc


def content_digest(payload: dict) -> str:
    # Timestamps do not change content identity; the first file keeps its dates.
    value = {k: v for k, v in payload.items() if k not in {"generated_at", "content_sha256"}}
    if isinstance(value.get("approval"), dict):
        value["approval"] = {k: v for k, v in value["approval"].items() if k != "reviewed_at"}
    return digest(value)


def nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def validate_pack(payload: dict) -> None:
    """Reject legacy/draft/malformed approved JSON before any store/media write."""
    if not isinstance(payload, dict) or payload.get("approved") is not True:
        raise ValueError("pack must be explicitly approved (boolean true)")
    try:
        Pack.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"invalid pack schema: {exc}") from exc
    if payload["content_sha256"] != content_digest(payload):
        raise ValueError("pack content digest mismatch")
    for concept in payload["concepts"]:
        if concept.get("lesson") and concept["lesson"]["review_status"] != "reviewed":
            raise ValueError("draft lessons cannot be included in an approved pack")
    for stamp in (payload["generated_at"], payload["approval"]["reviewed_at"]):
        if datetime.fromisoformat(stamp).tzinfo is None:
            raise ValueError("pack timestamps must include a timezone")
    refs = {d["deck_id"]: d for d in payload["source_refs"]}
    if len(refs) != len(payload["source_refs"]):
        raise ValueError("duplicate source identity")
    for ref in refs.values():
        path = PurePosixPath(ref["source_path"])
        if path.is_absolute() or ".." in path.parts or "\\" in str(path) or ":" in str(path):
            raise ValueError("source paths must be normalized relative paths")
    inventory = set(payload["media_ids"])
    observed = set()
    for node in nodes(payload):
        if "source_hash" in node and "deck_id" in node:
            ref = refs.get(node["deck_id"])
            if not ref or any(node[k] != ref[k] for k in ("source_path", "source_hash", "source_file")):
                raise ValueError("citation does not match source allowlist")
        if "slide_number" in node and "deck_id" in node:
            expected = f"{node['deck_id']}@{node['source_hash'][:16]}:slide-{node['slide_number']}"
            if node["slide_number"] > ref["slide_count"] or node["slide_id"] != expected:
                raise ValueError("citation does not match source slide snapshot")
        if "answer" in node and "options" in node and node["answer"] not in node["options"]:
            raise ValueError("answer is absent from choices")
        if "image_id" in node:
            observed.add(node["image_id"])
        for field in ("media_ids", "notes_media_ids"):
            if field in node and node is not payload:
                observed.update(node[field])
    if inventory != observed or len(inventory) != len(payload["media_ids"]):
        raise ValueError("media inventory does not match lesson/question evidence")
    for field in ("concepts", "flashcards"):
        ids = [record["id"] for record in payload[field]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate {field} identity")
    for concept in payload["concepts"]:
        if not concept["learning_segments"] and not concept["examples"]:
            raise ValueError("concept has no retained lesson content")
        if any(refs[d["deck_id"]]["skill_id"] != concept["skill_id"]
               or refs[d["deck_id"]]["status"] != "active" for d in concept["source_decks"]):
            raise ValueError("concept classification does not match active source allowlist")
    question_ids = [(q["source"]["deck_id"], q["source"]["slide_number"]) for q in payload["question_pool"]]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("duplicate question source identity")
