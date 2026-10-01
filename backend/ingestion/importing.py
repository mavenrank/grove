"""Revalidate reviewed work, then install verified delivery media (#7/#8/#31)."""
from __future__ import annotations

import io
import json
import os
import tempfile
from pathlib import Path

from .pack_contract import content_digest, validate_pack


def write_candidate(path: Path, payload: dict) -> bool:
    """Atomic exclusive publication; identical content preserves original dates."""
    if path.is_symlink():
        raise ValueError("candidate path must not be a symlink")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    try:
        try:
            os.link(temporary, path)
            return True
        except FileExistsError:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if (not isinstance(existing, dict) or existing.get("content_sha256") != content_digest(existing)
                    or content_digest(existing) != content_digest(payload)):
                raise ValueError("immutable candidate conflict; choose a new version/work directory")
            return False
    finally:
        temporary.unlink()


def prepare_import(payload: dict, work: Path) -> Path:
    """The reviewed catalog is required; a JSON approval flag is insufficient."""
    validate_pack(payload)
    catalog_path = work / "catalog.json"
    if not catalog_path.is_file():
        raise ValueError("import requires the reviewed work directory with catalog.json")
    from .pipeline import Pipeline, sha256_file

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    source = Path(payload["source_root"]).resolve()
    for ref in payload["source_refs"]:
        path = (source / ref["source_path"]).resolve()
        if not path.is_relative_to(source) or not path.is_file() or sha256_file(path) != ref["source_hash"]:
            raise ValueError(f"source missing, changed or outside source root: {ref['source_path']}")
    pipeline = Pipeline(source, work)
    try:
        report = pipeline.validate(catalog)
        candidate = pipeline.pack(catalog, report, pipeline.organize(catalog), payload["version"], True)
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid reviewed catalog; re-extract into a new work directory") from exc
    if content_digest(candidate) != content_digest(payload):
        raise ValueError("pack does not match the currently validated reviewed work directory")
    return pipeline.media_dir


def media_blob(path: Path, mid: str, root: Path) -> bytes:
    from PIL import Image
    from .extract import MAX_OUTPUT_BYTES, MAX_DIMENSION
    from .pipeline import sha256_file

    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"missing or unsafe delivery media: {mid}")
    if path.stat().st_size > MAX_OUTPUT_BYTES or sha256_file(path)[:16] != mid:
        raise ValueError(f"delivery media hash/size mismatch: {mid}")
    blob = path.read_bytes()
    # Verify the bytes we will install too, in case the file changed after stat.
    import hashlib
    if len(blob) > MAX_OUTPUT_BYTES or hashlib.sha256(blob).hexdigest()[:16] != mid:
        raise ValueError(f"delivery media changed during verification: {mid}")
    try:
        with Image.open(io.BytesIO(blob)) as img:
            if img.format != "JPEG" or max(img.size) > MAX_DIMENSION:
                raise ValueError(f"invalid delivery JPEG: {mid}")
            img.verify()
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"invalid delivery JPEG: {mid}") from exc
    return blob


def install_media(media_ids: list[str], source: Path, destination: Path) -> None:
    """Preflight all files; preserve existing assets, copy JPEGs only, no originals."""
    for mid in media_ids:
        blob = media_blob(source / f"{mid}.jpg", mid, source)
        target = destination / f"{mid}.jpg"
        if target.exists() or target.is_symlink():
            if media_blob(target, mid, destination) != blob:
                raise ValueError(f"delivery media identity collision: {mid}")
    destination.mkdir(parents=True, exist_ok=True)
    for mid in media_ids:
        target = destination / f"{mid}.jpg"
        if target.exists():
            continue
        blob = media_blob(source / f"{mid}.jpg", mid, source)
        with tempfile.NamedTemporaryFile(dir=destination, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(blob)
        try:
            try:
                os.link(temporary, target)
            except FileExistsError:
                if media_blob(target, mid, destination) != blob:
                    raise ValueError(f"delivery media identity collision: {mid}")
        finally:
            temporary.unlink()
