"""Local filesystem storage. Drop-in for the Supabase version we'll swap back in later.

Files are written to <repo>/backend/uploads/<bucket>/<folder>/<uuid>.<ext> and served
via the /uploads StaticFiles mount in app.main.
"""

import mimetypes
import uuid
from pathlib import Path

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"
URL_PREFIX = "/uploads"


def _safe_segment(value: str) -> str:
    # Strip path separators / parent refs so callers can't escape UPLOAD_ROOT.
    return value.replace("..", "").strip("/\\")


def upload_file(bucket: str, data: bytes, filename: str, folder: str = "") -> str:
    """Write bytes to local storage and return a URL servable by the FastAPI app."""
    ext = Path(filename).suffix
    name = f"{uuid.uuid4().hex}{ext}"

    bucket_segment = _safe_segment(bucket)
    folder_segment = _safe_segment(folder)

    target_dir = UPLOAD_ROOT / bucket_segment / folder_segment
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / name
    target_path.write_bytes(data)

    _ = mimetypes.guess_type(filename)  # parity with Supabase version (it sets content-type)

    rel = target_path.relative_to(UPLOAD_ROOT).as_posix()
    return f"{URL_PREFIX}/{rel}"


def delete_file(bucket: str, url: str) -> None:
    """Delete a previously-uploaded file by URL. No-op if it doesn't exist."""
    prefix = f"{URL_PREFIX}/"
    if not url.startswith(prefix):
        return
    rel = url[len(prefix):]
    target = UPLOAD_ROOT / rel
    try:
        target.resolve().relative_to(UPLOAD_ROOT.resolve())
    except ValueError:
        return  # path traversal guard
    target.unlink(missing_ok=True)
