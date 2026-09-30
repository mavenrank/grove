"""Deep PPTX extraction: grouped shapes, slide classification, image media.

The source decks teach on *explanation slides* whose content is often embedded
as pictures (formulas rendered as images) with small text frames. To make Learn
useful we therefore:

  - recurse into grouped shapes for text
  - extract meaningful pictures (deduped, downscaled, JPEG-compressed)
  - classify each slide: title / explanation / question / other

File-safety (handoff §13): everything is treated as untrusted input — bounded
sizes, no macro execution, temp work dir, hash-deduped media.
"""
from __future__ import annotations

import hashlib
import io
import re
from typing import Any

from pptx.enum.shapes import MSO_SHAPE_TYPE

QUESTION_MARKER = re.compile(
    r"question\s*\d+|\bques\.?\s*\d+|\banswer\s*:|^\s*[a-d]\)\s+\S",
    re.I | re.M,
)
FORMULA_LINE = re.compile(r"[=×÷%±√]|\bof\b.*%|/\s*100", re.I)

# Slides whose whole point is ceremony, not teaching: their images are logos,
# contact icons, and template backgrounds — never learning material.
CEREMONY_SLIDE = re.compile(
    r"thank you|thanks|\bthanks!\b|any questions|q\s*&\s*a|\bquiz\s*time\b|"
    r"contact us|for queries|follow us|\bagenda\b|\bobjectives\b",
    re.I,
)

MIN_IMAGE_BYTES = 12 * 1024      # skip icons/decorations
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # skip absurd embedded objects
MAX_DIMENSION = 1400             # downscale target
JPEG_QUALITY = 82


def iter_shapes(shapes):
    """Yield every shape, recursing into groups."""
    for sh in shapes:
        yield sh
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            try:
                yield from iter_shapes(sh.shapes)
            except Exception:
                pass


def process_image_blob(blob: bytes) -> dict[str, Any] | None:
    """Normalize one embedded image; returns {id, mime, bytes} or None."""
    if len(blob) < MIN_IMAGE_BYTES or len(blob) > MAX_IMAGE_BYTES:
        return None
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(blob))
        img.load()
        if img.width < 200 or img.height < 200:
            return None
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        out = io.BytesIO()
        if img.mode in ("RGBA", "LA", "P"):
            # flatten transparency onto white for JPEG
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        data = out.getvalue()
        if len(data) > 500 * 1024:
            return None
        image_id = hashlib.sha256(data).hexdigest()[:16]
        return {"image_id": image_id, "mime": "image/jpeg", "data": data}
    except Exception:
        # untrusted input: a broken image never fails the run
        return None


def extract_slide_content(slide, first_of_many: bool = False) -> dict[str, Any]:
    """Texts (recursed), pictures, and a heuristic slide kind."""
    texts: list[str] = []
    images: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for sh in iter_shapes(slide.shapes):
        try:
            if sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if t:
                    texts.append(t)
        except Exception:
            pass
        try:
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                blob = sh.image.blob
                h = hashlib.sha256(blob).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append({"blob": blob})
        except Exception:
            pass

    # classification — question > ceremony > title-slide > explanation > other.
    # Title and ceremony slides carry logos, template backgrounds, and contact
    # icons; their media must never reach the learning gallery.
    joined = "\n".join(texts)
    if QUESTION_MARKER.search(joined):
        kind = "question"
    elif CEREMONY_SLIDE.search(joined):
        kind = "other"
    elif first_of_many:
        kind = "title"  # deck covers are provider branding in this corpus
    elif images and (not texts or all(len(t) < 120 for t in texts)):
        kind = "explanation"  # picture-led teaching slide
    elif images:
        kind = "explanation"
    elif joined and len(joined) > 30:
        kind = "explanation"
    else:
        kind = "other"

    return {"texts": texts, "image_blobs": images, "kind": kind}
