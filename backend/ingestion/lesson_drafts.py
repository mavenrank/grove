"""Compile private, unapproved lessons without modifying native evidence or releases."""
from __future__ import annotations

import json
from pathlib import Path

from app.lesson_media import asset_filename, verified_image
from app.lessons import Figure, Lesson, LessonBundle

from .pack_contract import nodes
from .pipeline import now_iso, sha256_file
from .source_review import contained_file, object_sha256, run_source_reviews


def figures(lesson: Lesson):
    for section in lesson.sections:
        for block in section.blocks:
            if isinstance(block, Figure):
                yield block
            else:
                yield from getattr(block, "figures", [])


def compile_lessons(plan: dict, catalog: dict, source: Path, media: Path, output: Path,
                    review_manifest: dict | None = None, visual_path: Path | None = None,
                    evidence_root: Path | None = None) -> dict:
    source, media, output = source.resolve(), media.resolve(), output.resolve()
    if (set(plan) != {"lesson_plan_version", "lessons", "exclude_review_ids"}
            or type(plan["lesson_plan_version"]) is not int or plan["lesson_plan_version"] != 1
            or not isinstance(plan["exclude_review_ids"], list)
            or any(not isinstance(r, str) for r in plan["exclude_review_ids"])
            or len(set(plan["exclude_review_ids"])) != len(plan["exclude_review_ids"])):
        raise ValueError("invalid lesson plan fields/version/exclusions")
    roots = [source, media] + ([evidence_root.resolve()] if evidence_root else [])
    if (any(output == root or root in output.parents and root in (source, media) or output in root.parents for root in roots)
            or output.exists() and any(output.iterdir())):
        raise ValueError("use a fresh lesson directory that cannot overwrite sources/media/evidence")
    lessons = [Lesson.model_validate(l) for l in plan["lessons"]]
    bundle = LessonBundle(bundle_schema_version=1, approved=False, created_at=now_iso(),
                          catalog_sha256=object_sha256(catalog), lessons=lessons)
    decks = {d["deck_id"]: d for d in catalog["decks"]}
    if len(decks) != len(catalog["decks"]):
        raise ValueError("ambiguous catalog deck identity")
    checked = {}
    snapshots = {}
    for lesson in lessons:
        for node in nodes(lesson.model_dump()):
            if "deck_id" not in node:
                continue
            deck = decks.get(node["deck_id"])
            if not deck or any(node[k] != deck[k] for k in ("source_file", "source_path", "source_hash")):
                raise ValueError("lesson citation differs from catalog source")
            original = contained_file(source, node["source_path"])
            if original not in checked:
                checked[original] = sha256_file(original)
            if checked[original] != deck["source_hash"]:
                raise ValueError("lesson source changed since extraction")
            matches = [s for s in deck["slides"] if s["slide_number"] == node["slide_number"] and s["slide_id"] == node["slide_id"]]
            if len(matches) != 1:
                raise ValueError("lesson citation has an unknown/ambiguous slide")
            snapshots[node["slide_id"]] = (deck, matches[0])
    excluded = set()
    decisions = []
    if plan["exclude_review_ids"]:
        if review_manifest is None or visual_path is None or evidence_root is None:
            raise ValueError("scoped decoration requires the current review manifest and visual evidence")
        # This is an annotation validation, not permission to clear native blockers.
        output.mkdir(parents=True)
        report = run_source_reviews(catalog, source, visual_path, review_manifest, evidence_root, output / "reviews")
        for review_id in plan["exclude_review_ids"]:
            matches = [r for r in report["records"] if r["record"]["review_id"] == review_id]
            if (len(matches) != 1 or matches[0]["status"] != "accepted_annotation"
                    or matches[0]["record"]["decision"] != "decoration_candidate"):
                raise ValueError("exclusion is not a valid exact-shape decoration candidate")
            r = matches[0]["record"]
            excluded.add((r["slide_id"], r["surface"], r["shape_id"]))
            decisions.append({"outcome": "excluded_from_this_draft", "review_id": review_id,
                              "slide_id": r["slide_id"], "surface": r["surface"], "shape_id": r["shape_id"],
                              "source_hash": r["source_hash"], "block_sha256": r["block_sha256"], "reason": r["reason"]})
    blobs, assets, used = {}, {}, set()
    for lesson in lessons:
        by_id = {a.image_id: a for a in lesson.assets}
        for figure in figures(lesson):
            identity = (figure.source.slide_id, figure.source.surface, figure.shape_id)
            if identity in excluded:
                raise ValueError("draft figure conflicts with its exact-shape exclusion")
            _, slide = snapshots[figure.source.slide_id]
            blocks = slide["blocks" if figure.source.surface == "slide" else "notes_blocks"]
            selected = [b for b in blocks if b["shape_id"] == figure.shape_id]
            if (len(selected) != 1 or selected[0]["type"] != "image"
                    or selected[0].get("surface") != figure.source.surface
                    or object_sha256(selected[0]) != figure.block_sha256
                    or selected[0]["source_hash"] != figure.original_sha256):
                raise ValueError("figure does not match the original image occurrence")
            block = selected[0]
            if any(block.get("crop", {}).values()) or block.get("rotation", 0) or block.get("group_path"):
                raise ValueError("cropped/rotated/grouped figure needs a reviewed source-region render")
            asset = by_id[figure.image_id]
            if figure.representation == "original_image":
                expected = f"original-{figure.original_sha256}.bin"
                if block["original_file"] != expected or asset.sha256 != figure.original_sha256:
                    raise ValueError("original image identity mismatch")
            else:
                expected = f"{block['image_id']}.jpg"
                if asset.image_id != block["image_id"]:
                    raise ValueError("normalized image identity mismatch")
            path = contained_file(media, expected)
            data = verified_image(path, asset, media)
            if asset.image_id in blobs and blobs[asset.image_id] != data:
                raise ValueError("shared asset bytes conflict")
            blobs[asset.image_id], assets[asset.image_id] = data, asset
            checked[path] = asset.sha256
            used.add(identity)
            decisions.append({"outcome": "included_figure", "lesson_id": lesson.id, "figure_id": figure.id,
                              "image_id": asset.image_id, "slide_id": figure.source.slide_id, "surface": figure.source.surface,
                              "shape_id": figure.shape_id, "source_hash": figure.source.source_hash,
                              "block_sha256": figure.block_sha256, "review_status": figure.review_status})
    # The rest remains accounted for, not implicitly classified as decoration.
    for _, slide in snapshots.values():
        for surface, blocks in (("slide", slide["blocks"]), ("notes", slide["notes_blocks"])):
            for block in blocks:
                key = (slide["slide_id"], surface, block["shape_id"])
                if block["type"] == "image" and key not in used and key not in excluded:
                    decisions.append({"outcome": "not_selected_needs_review", "slide_id": slide["slide_id"],
                                      "surface": surface, "shape_id": block["shape_id"], "image_id": block["image_id"]})
    for path, expected in checked.items():
        if sha256_file(path) != expected:
            raise ValueError("source/media changed during lesson compilation")
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "media"
    destination.mkdir()
    for image_id, data in blobs.items():
        (destination / asset_filename(assets[image_id])).write_bytes(data)
    bundle.source_decisions = decisions
    payload = bundle.model_dump()
    (output / "lesson-bundle.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
