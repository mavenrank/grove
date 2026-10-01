"""Static lesson-image verification, shared by draft compiler and preview delivery."""
import hashlib
import io
from pathlib import Path

from .lessons import LessonAsset


def asset_filename(asset: LessonAsset) -> str:
    return asset.image_id + (".png" if asset.mime == "image/png" else ".jpg")


def verified_image(path: Path, asset: LessonAsset, root: Path) -> bytes:
    from PIL import Image
    root = root.resolve()
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("lesson image missing or outside its media root")
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("lesson image exceeds byte limit")
    data = path.read_bytes()
    if len(data) > 8 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != asset.sha256:
        raise ValueError("lesson image bytes do not match their asset identity")
    try:
        with Image.open(io.BytesIO(data)) as image:
            mime = {"JPEG": "image/jpeg", "PNG": "image/png"}.get(image.format)
            if (mime != asset.mime or image.size != (asset.width, asset.height)
                    or image.width * image.height > 25_000_000 or getattr(image, "n_frames", 1) != 1):
                raise ValueError("lesson image format/dimensions are invalid")
            image.verify()
    except (OSError, SyntaxError) as exc:
        raise ValueError("lesson image cannot be decoded") from exc
    return data
