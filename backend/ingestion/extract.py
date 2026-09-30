"""Bounded native PPTX extraction, with reviewable structure and loss reports.

Pictures are evidence, not OCR. Keeping a crop never establishes its meaning.
Every source shape remains represented; unsupported semantics are review items.
"""
from __future__ import annotations

import hashlib
import io
import re
import warnings
from typing import Any

from pptx.enum.shapes import MSO_SHAPE_TYPE

QUESTION_MARKER = re.compile(
    r"question\s*\d+|\bques\.?\s*\d+|\banswer\s*:|^\s*[a-d]\)\s+\S", re.I | re.M,
)
FORMULA_LINE = re.compile(r"[=×÷%±√]|\bof\b.*%|/\s*100", re.I)
# Only whole-slide ceremony matches are excluded. An explanation containing
# 'objectives' or 'any questions' must not be erased by a substring match (#6).
CEREMONY_SLIDE = re.compile(
    r"(?:thank\s+you|thanks!?|any questions\??|q\s*&\s*a|contact us|follow us)", re.I,
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MAX_DIMENSION = 1400
MAX_OUTPUT_BYTES = 500 * 1024
JPEG_QUALITY = 82
DRAWING_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def issue(code: str, message: str, *, severity: str = "review", **context) -> dict[str, Any]:
    return {"code": code, "message": message, "severity": severity, **context}


def iter_shapes(shapes):
    """Compatibility iterator, including groups. Extraction below reports errors."""
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(shape.shapes)


def inspect_image_blob(blob: bytes) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Normalize for delivery while retaining the original in the work directory.

    Small compressed formula images and thin diagrams are valid evidence; byte
    size and a 200 px minimum are not reliable decoration tests (#6).
    """
    if len(blob) > MAX_IMAGE_BYTES:
        return None, [issue("image_byte_limit", f"Image exceeds {MAX_IMAGE_BYTES} bytes")]
    try:
        from PIL import Image, ImageOps

        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(blob)) as opened:
                if opened.width * opened.height > MAX_IMAGE_PIXELS:
                    return None, [issue("image_pixel_limit", f"Image exceeds {MAX_IMAGE_PIXELS} pixels")]
                original_size = list(opened.size)
                image_format = (opened.format or "bin").lower()
                opened.load()
                img = ImageOps.exif_transpose(opened).convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        bg.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        out = io.BytesIO()
        bg.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        data = out.getvalue()
        if len(data) > MAX_OUTPUT_BYTES:
            return None, [issue("image_output_limit", f"Preview exceeds {MAX_OUTPUT_BYTES} bytes")]
        losses = []
        if list(bg.size) != original_size:
            losses.append(issue("image_downscaled", "Delivery preview downscaled; original retained",
                                severity="info", original_size=original_size, preview_size=list(bg.size)))
        return {
            "image_id": hashlib.sha256(data).hexdigest()[:16], "mime": "image/jpeg", "data": data,
            "source_hash": hashlib.sha256(blob).hexdigest(), "original_size": original_size,
            "preview_size": list(bg.size), "original_format": image_format,
        }, losses
    except Exception as exc:
        return None, [issue("image_decode_failed", f"Cannot decode image: {type(exc).__name__}")]


def process_image_blob(blob: bytes) -> dict[str, Any] | None:
    """Legacy convenience API; adapters use inspect_image_blob for its report."""
    return inspect_image_blob(blob)[0]


def _paragraphs(frame) -> list[dict[str, Any]]:
    return [{"text": p.text, "level": p.level, "runs": [
        {"text": run.text, "bold": run.font.bold, "italic": run.font.italic,
         "baseline": run._r.rPr.get("baseline") if run._r.rPr is not None else None}
        for run in p.runs
    ]} for p in frame.paragraphs]


def extract_slide_content(slide, first_of_many: bool = False) -> dict[str, Any]:
    texts: list[str] = []
    images: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    def walk(shapes, transform=(1.0, 1.0, 0.0, 0.0), ancestors=()):
        sx, sy, tx, ty = transform
        for sh in shapes:
            sid = sh.shape_id
            base = {"shape_id": sid, "name": sh.name, "group_path": list(ancestors),
                    "bounds_emu": {"left": round(sh.left * sx + tx), "top": round(sh.top * sy + ty),
                                   "width": round(sh.width * sx), "height": round(sh.height * sy)},
                    "rotation": sh.rotation, "source_order": len(blocks)}
            try:
                if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                    blocks.append({**base, "type": "group"})
                    xfrm = sh._element.grpSpPr.xfrm
                    off = xfrm.find(DRAWING_NS + "chOff")
                    ext = xfrm.find(DRAWING_NS + "chExt")
                    gx = sh.width / int(ext.get("cx")) if ext is not None and int(ext.get("cx")) else 1
                    gy = sh.height / int(ext.get("cy")) if ext is not None and int(ext.get("cy")) else 1
                    ox = int(off.get("x")) if off is not None else 0
                    oy = int(off.get("y")) if off is not None else 0
                    if sh.rotation or xfrm.get("flipH") or xfrm.get("flipV"):
                        issues.append(issue("group_transform_unresolved", "Rotated/flipped group needs visual layout review", shape_id=sid))
                    walk(sh.shapes, (sx * gx, sy * gy, tx + sx * (sh.left - ox * gx),
                                    ty + sy * (sh.top - oy * gy)), (*ancestors, sid))
                elif sh.has_table:
                    rows = [[{"text": cell.text, "paragraphs": _paragraphs(cell.text_frame),
                              "is_merge_origin": cell.is_merge_origin, "is_spanned": cell.is_spanned,
                              "span_width": cell.span_width, "span_height": cell.span_height}
                             for cell in row.cells] for row in sh.table.rows]
                    table_text = "\n".join("\t".join(cell["text"] for cell in row) for row in rows)
                    texts.append(table_text)
                    blocks.append({**base, "type": "table", "rows": rows,
                                   "column_widths_emu": [c.width for c in sh.table.columns], "text": table_text})
                elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    blob = sh.image.blob
                    blocks.append({**base, "type": "image", "source_hash": hashlib.sha256(blob).hexdigest(),
                                   "crop": {"left": sh.crop_left, "right": sh.crop_right,
                                            "top": sh.crop_top, "bottom": sh.crop_bottom}})
                    images.append({"blob": blob, "shape_id": sid})
                elif sh.has_text_frame:
                    raw = sh.text_frame.text
                    placeholder = str(sh.placeholder_format.type) if sh.is_placeholder else None
                    blocks.append({**base, "type": "text", "text": raw, "paragraphs": _paragraphs(sh.text_frame),
                                   "placeholder": placeholder})
                    if raw.strip():
                        texts.append(raw.strip())
                    elif sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                        issues.append(issue("vector_semantics_unresolved", "Unlabelled drawing shape needs visual review", shape_id=sid))
                else:
                    blocks.append({**base, "type": "unsupported", "shape_type": str(sh.shape_type)})
                    issues.append(issue("unsupported_shape", f"Unsupported shape: {sh.shape_type}", shape_id=sid))
                if any(el.tag.rsplit("}", 1)[-1] in {"oMath", "oMathPara"} for el in sh._element.iter()):
                    issues.append(issue("native_equation_unresolved", "Office Math equation is preserved in source but not interpreted", shape_id=sid))
            except Exception as exc:
                blocks.append({**base, "type": "extraction_error"})
                issues.append(issue("shape_extract_failed", f"Shape extraction failed: {type(exc).__name__}", shape_id=sid))

    walk(slide.shapes)
    blocks.sort(key=lambda b: (b["bounds_emu"]["top"], b["bounds_emu"]["left"], b["source_order"]))
    for order, block in enumerate(blocks):
        block["reading_order"] = order
    joined = "\n".join(texts)
    nonempty_text = [b for b in blocks if b["type"] == "text" and b["text"].strip()]
    cover = (first_of_many and not images and not issues and len(nonempty_text) <= 2
             and all(b.get("placeholder") and ("TITLE" in b["placeholder"] or "SUBTITLE" in b["placeholder"])
                     for b in nonempty_text) and bool(nonempty_text) and len(joined) <= 140
             and not FORMULA_LINE.search(joined) and not any(b["type"] == "table" for b in blocks))
    if QUESTION_MARKER.search(joined):
        kind, reason = "question", "question_marker"
    elif CEREMONY_SLIDE.fullmatch(joined.strip()) and not images and not issues:
        kind, reason = "other", "whole_slide_ceremony"
    elif cover:
        kind, reason = "title", "short_title_placeholders"
    elif joined or images or issues:
        kind, reason = "explanation", "content_present"
    else:
        kind, reason = "other", "empty"
    mode = "hybrid" if joined and images else "image_only" if images else "text_only" if joined else "non_text" if issues else "empty"
    if images and kind in {"question", "explanation"}:
        issues.append(issue("visual_semantics_unresolved", "Image content/diagram relationships require OCR or manual interpretation"))
    return {"texts": texts, "image_blobs": images, "blocks": blocks, "kind": kind,
            "kind_reason": reason, "content_mode": mode, "issues": issues,
            "reading_order_method": "top-left-then-source-order"}
