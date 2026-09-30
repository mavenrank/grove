"""Concept assembly: learning segments → one reviewable concept per skill."""
from __future__ import annotations

import re
from typing import Any

from .flashcards import draft_flashcards
from .gates import NOISE_TOKENS, concept_formula
from .labels import short_deck_label
from .questions import parse_question_slide
from .text import FORMULA_LINE, clean_lines, looks_like_code


def organize_deck(deck: dict[str, Any], media_ids_by_slide: dict[Any, list[str]],
                  template_media: set[str] | None = None) -> dict[str, Any]:
    """Split one deck into learning segments and question records.

    Slide keys may be ints (fresh run) or strings (catalog re-read from JSON);
    both are accepted. Media ids in `template_media` (provider logos, template
    backgrounds, contact icons reused across many decks) are dropped.
    """
    learning: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    template_media = template_media or set()
    deck_label = short_deck_label(deck["source_file"])

    def media_for(slide_no: int) -> list[str]:
        mids = (media_ids_by_slide.get(slide_no)
                or media_ids_by_slide.get(str(slide_no))
                or [])
        return [m for m in mids if m not in template_media]

    for slide in deck["slides"]:
        kind = slide.get("kind", "other")
        slide_no = slide["slide_number"]
        src = {"deck_id": deck["deck_id"], "slide_number": slide_no,
               "source_file": deck["source_file"], "deck_label": deck_label}
        if kind == "question":
            q = parse_question_slide({**slide, "deck_id": deck["deck_id"],
                                      "source_file": deck["source_file"]})
            if q:
                q["source"]["deck_label"] = deck_label
                q["media_ids"] = media_for(slide_no)
                questions.append(q)
        elif kind == "explanation":
            texts = clean_lines(slide["texts"])
            if texts or media_for(slide_no):
                learning.append({
                    "texts": texts,
                    "notes": slide.get("notes", ""),
                    "media_ids": media_for(slide_no),
                    "source": src,
                })
        # title/agenda/other slides: text kept in catalog, not organized further

    return {"learning": learning, "questions": questions}


def assemble_concepts(skill_id: str, decks: list[dict[str, Any]],
                      organized: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build one concept per skill from its decks' learning material."""
    segments: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    source_decks: list[dict[str, Any]] = []

    for deck, org in zip(decks, organized):
        segments.extend(org["learning"])
        questions.extend(org["questions"])
        source_decks.append({
            "deck_id": deck["deck_id"],
            "source_file": deck["source_file"],
            "source_path": deck.get("source_path", ""),
            "source_hash": deck["source_hash"],
            "slide_count": deck["slide_count"],
            "short_name": short_deck_label(deck["source_file"]),
        })

    if not segments and not questions:
        return None

    verified = [q for q in questions if q["answer"]]

    # summary: from the first explanation segments with real text
    summary_parts: list[str] = []
    for seg in segments:
        for t in seg["texts"]:
            if looks_like_code(t) or NOISE_TOKENS.search(t):
                continue
            if len(t) > 40 and not FORMULA_LINE.search(t[:40]):
                summary_parts.append(t)
        if len(summary_parts) >= 2:
            break
    summary = (" ".join(summary_parts)[:600]) or (
        f"Teaching material assembled from {len(segments)} explanation slides across "
        f"{len(source_decks)} deck(s). Review the slides and examples, then refine this summary."
    )

    # Code blocks are extracted as structured objects (language-labelled,
    # copyable) rather than being flattened into prose or formulas.
    code_blocks: list[dict[str, Any]] = []
    seen_code: set[str] = set()

    # Formulas & rules: the authored, general card fronts first (they are the
    # canonical formulas for this skill), then strictly-gated mined lines.
    # Anything prose-shaped, code-shaped, or example-specific is rejected.
    from ..authored_cards import authored_flashcards
    formulas: list[str] = []
    seen_formulas: set[str] = set()
    for card in authored_flashcards(skill_id):
        if card["kind"] in ("formula", "rule") and card["front"].lower() not in seen_formulas:
            seen_formulas.add(card["front"].lower())
            formulas.append(card["front"])
    for seg in segments:
        for t in seg["texts"]:
            if looks_like_code(t):
                key = t.strip()
                if key not in seen_code:
                    seen_code.add(key)
                    from .text import detect_code_language
                    code_blocks.append({
                        "language": detect_code_language(t),
                        "code": t.strip(),
                        "source": seg["source"],
                    })
                continue
            if NOISE_TOKENS.search(t):
                continue  # stray code fragments never become teaching formulas
            if t.lower() in seen_formulas:
                continue
            gated = concept_formula(t)
            if gated:
                seen_formulas.add(gated.lower())
                formulas.append(gated)
    formulas = formulas[:12]

    media: list[dict[str, Any]] = []
    seen_media: set[str] = set()
    for seg in segments:
        for mid in seg["media_ids"]:
            if mid not in seen_media:
                seen_media.add(mid)
                media.append({"image_id": mid,
                              "source": seg["source"]})

    examples = [
        {
            "prompt": q["prompt"],
            "options": q["options"],
            "answer": q["answer"],
            "explanation": (q["explanation"]
                            or re.sub(r"^\s*answer\s*(?:is)?\s*[:\-]?\s*[A-Ea-e]\b[).:]?\s*",
                                      "", q.get("notes_raw", ""), count=1).strip()),
            "source": q["source"],
        }
        for q in verified[:20]
    ]

    title = skill_id.split(".")[-1].replace("_", " ").title()
    return {
        "id": f"concept.{skill_id}",
        "skill_id": skill_id,
        "title": title,
        "summary": summary,
        "formulas": formulas,
        "code_blocks": code_blocks[:8],
        "examples": examples,
        "media": media,
        "common_mistakes": [],
        "related_families": [],
        "source_decks": source_decks,
        "question_review_count": len(questions) - len(verified),
    }


def organize_all(catalog: dict[str, Any], media_ids: dict[str, dict[int, list[str]]],
                 template_media: set[str] | None = None) -> dict[str, Any]:
    """Organize every unique active deck; group results by skill."""
    by_skill: dict[str, dict[str, Any]] = {}
    for deck in catalog["decks"]:
        if deck["status"] != "active" or "duplicate_of" in deck:
            continue
        skill = deck["skill_id"]
        slide_media = media_ids.get(deck["deck_id"], {})
        org = organize_deck(deck, slide_media, template_media=template_media)
        entry = by_skill.setdefault(skill, {"decks": [], "organized": []})
        entry["decks"].append(deck)
        entry["organized"].append(org)

    concepts: list[dict[str, Any]] = []
    flashcards: list[dict[str, Any]] = []
    question_pool: list[dict[str, Any]] = []
    for skill, entry in sorted(by_skill.items()):
        concept = assemble_concepts(skill, entry["decks"], entry["organized"])
        if concept:
            concepts.append(concept)
        all_segments = [seg for org in entry["organized"] for seg in org["learning"]]
        skill_questions = [q for org in entry["organized"] for q in org["questions"]]
        verified = [q for q in skill_questions if q["answer"]]
        question_pool.extend(skill_questions)
        flashcards.extend(draft_flashcards(skill, all_segments, verified))

    return {
        "organized_at": None,  # stamped by pipeline
        "concepts": concepts,
        "flashcards": flashcards,
        "question_pool": question_pool,
        "stats": {
            "skills": len(by_skill),
            "concepts": len(concepts),
            "learning_segments": sum(len(o["learning"]) for e in by_skill.values() for o in e["organized"]),
            "flashcards": len(flashcards),
            "questions_total": len(question_pool),
            "questions_verified": sum(1 for q in question_pool if q["answer"]),
        },
    }
