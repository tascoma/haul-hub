import mimetypes
import uuid
from pathlib import Path

from supabase import Client


def upload_file(
    client: Client,
    bucket: str,
    data: bytes,
    filename: str,
    folder: str = "",
) -> str:
    """Upload bytes to a Supabase Storage bucket and return the public URL."""
    ext = Path(filename).suffix
    key = f"{folder}/{uuid.uuid4()}{ext}".lstrip("/")
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    client.storage.from_(bucket).upload(
        path=key,
        file=data,
        file_options={"content-type": content_type, "upsert": "false"},
    )

    return client.storage.from_(bucket).get_public_url(key)


def delete_file(client: Client, bucket: str, url: str) -> None:
    """Delete a file from a Supabase Storage bucket by its public URL."""
    # Extract the storage key from the public URL.
    # Public URLs follow: <supabase_url>/storage/v1/object/public/<bucket>/<key>
    marker = f"/object/public/{bucket}/"
    key = url.split(marker, 1)[-1]
    client.storage.from_(bucket).remove([key])
