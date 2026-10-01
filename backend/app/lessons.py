"""Versioned ordered lessons: shared assets, distinct source figure occurrences."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1, max_length=10_000, pattern=r"\S")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
MediaID = Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]


class LessonRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Citation(LessonRecord):
    deck_id: Text
    source_file: Text
    source_path: Text
    source_hash: Hash
    slide_id: Text
    slide_number: Annotated[int, Field(ge=1)]
    deck_label: str = ""
    surface: Literal["slide", "notes"] = "slide"


class LessonAsset(LessonRecord):
    image_id: MediaID
    sha256: Hash
    mime: Literal["image/jpeg", "image/png"]
    width: Annotated[int, Field(ge=1, le=4096)]
    height: Annotated[int, Field(ge=1, le=4096)]

    @model_validator(mode="after")
    def content_identity(self):
        if self.sha256[:16] != self.image_id:
            raise ValueError("asset ID must identify delivery bytes")
        return self


class Figure(LessonRecord):
    type: Literal["figure"]
    id: Text
    image_id: MediaID
    source: Citation
    shape_id: Annotated[int, Field(ge=1)]
    block_sha256: Hash
    original_sha256: Hash
    representation: Literal["original_image", "normalized_preview"]
    role: Literal["teaching_diagram", "example_prompt", "solution_diagram"]
    caption: Text
    alt: Text
    review_status: Literal["candidate", "reviewed"] = "candidate"


class TextBlock(LessonRecord):
    type: Literal["text"]
    id: Text
    paragraphs: Annotated[list[Text], Field(min_length=1)]
    sources: Annotated[list[Citation], Field(min_length=1)]


class FormulaBlock(LessonRecord):
    type: Literal["formula"]
    id: Text
    expression: Text
    variables: Annotated[list[Text], Field(min_length=1)]
    conditions: Annotated[list[Text], Field(min_length=1)]
    sources: Annotated[list[Citation], Field(min_length=1)]


class Step(LessonRecord):
    title: Text
    text: Text
    equation: str = ""


class StepsBlock(LessonRecord):
    type: Literal["steps"]
    id: Text
    steps: Annotated[list[Step], Field(min_length=1)]
    sources: Annotated[list[Citation], Field(min_length=1)]


class ExampleBlock(LessonRecord):
    type: Literal["example"]
    id: Text
    prompt: Text
    givens: Annotated[list[Text], Field(min_length=1)]
    target: Text
    steps: Annotated[list[Step], Field(min_length=1)]
    result: Text
    verification: Literal["unverified", "independent_check"]
    sources: Annotated[list[Citation], Field(min_length=1)]
    figures: list[Figure] = []


Block = Annotated[TextBlock | FormulaBlock | StepsBlock | ExampleBlock | Figure, Field(discriminator="type")]


class LessonSection(LessonRecord):
    id: Text
    title: Text
    stage: Literal["overview", "baseline", "recognition", "shortcut"]
    blocks: Annotated[list[Block], Field(min_length=1)]


class Lesson(LessonRecord):
    schema_version: Literal[1]
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")]
    title: Text
    introduction: Text
    review_status: Literal["draft", "reviewed"]
    assets: list[LessonAsset]
    sections: Annotated[list[LessonSection], Field(min_length=1)]

    @model_validator(mode="after")
    def associations(self):
        assets = {a.image_id for a in self.assets}
        if len(assets) != len(self.assets):
            raise ValueError("duplicate asset identity")
        ids, used = [], set()
        figures = []
        for section in self.sections:
            ids.append(section.id)
            for block in section.blocks:
                ids.append(block.id)
                if isinstance(block, Figure):
                    figures.append(block)
                elif isinstance(block, ExampleBlock):
                    figures.extend(block.figures)
                    ids.extend(f.id for f in block.figures)
                    if self.review_status == "reviewed" and block.verification != "independent_check":
                        raise ValueError("reviewed lesson has an unverified worked example")
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate lesson/figure occurrence identity")
        for figure in figures:
            used.add(figure.image_id)
            if self.review_status == "reviewed" and figure.review_status != "reviewed":
                raise ValueError("reviewed lesson has an unreviewed figure")
        if used != assets:
            raise ValueError("lesson asset inventory must match its figure uses")
        return self


class LessonPreviewOut(LessonRecord):
    lesson: Lesson
    catalog_sha256: Hash
    draft_only: Literal[True] = True


class LessonBundle(LessonRecord):
    bundle_schema_version: Literal[1]
    approved: Literal[False]
    created_at: Text
    catalog_sha256: Hash
    lessons: Annotated[list[Lesson], Field(min_length=1)]
    source_decisions: list[dict] = []

    @model_validator(mode="after")
    def draft_identity(self):
        if len({l.id for l in self.lessons}) != len(self.lessons) or any(l.review_status != "draft" for l in self.lessons):
            raise ValueError("preview bundles require distinct draft lessons")
        assets = {}
        for lesson in self.lessons:
            for asset in lesson.assets:
                if asset.image_id in assets and assets[asset.image_id] != asset:
                    raise ValueError("conflicting shared asset metadata")
                assets[asset.image_id] = asset
        return self
