from io import BytesIO
import mimetypes
import uuid
from pathlib import Path
from urllib.parse import unquote

import aiofiles
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from typing import List
from app.settings import (
    API_TOKEN,
    BASE_STORAGE_PATH,
    BASE_URL,
    FILE_RULES,
    REQUIRE_API_TOKEN,
)

app = FastAPI(title="File API")

IMAGE_FORMAT_BY_MIME = {
    "image/jpeg": ("JPEG", ".jpg"),
    "image/png": ("PNG", ".png"),
    "image/webp": ("WEBP", ".webp"),
}


def verify_token(x_api_key: str | None = Header(default=None)):
    if not REQUIRE_API_TOKEN:
        return

    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="Server token is not configured")

    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")


def detect_kind(mime: str) -> str:
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    return "document"


def sanitize_filename(filename: str) -> str:
    safe = Path(filename or "file").name.strip().replace(" ", "_")
    return safe or "file"


async def save_binary_file(upload: UploadFile, output_path: Path, max_bytes: int) -> None:
    written = 0
    async with aiofiles.open(output_path, "wb") as out:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                raise HTTPException(status_code=413, detail="File too large")
            await out.write(chunk)


def process_image_bytes(raw: bytes, mime: str) -> bytes:
    target_format, _ = IMAGE_FORMAT_BY_MIME[mime]

    try:
        with Image.open(BytesIO(raw)) as img:
            img = img.convert("RGB") if target_format == "JPEG" else img.copy()
            img.thumbnail((1920, 1920))
            out = BytesIO()
            if target_format == "JPEG":
                img.save(out, format="JPEG", optimize=True, quality=82, progressive=True)
            elif target_format == "PNG":
                img.save(out, format="PNG", optimize=True, compress_level=9)
            elif target_format == "WEBP":
                img.save(out, format="WEBP", method=6, quality=80)
            return out.getvalue()
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid image file") from exc


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    model: str = Form(...),
    record_id: int = Form(...),
    client_name: str = Form(None),
    client_dni: str = Form(None),
    _: None = Depends(verify_token),
):
    dest_dir = BASE_STORAGE_PATH / model / str(record_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    out = []

    for f in files:
        content_type = (f.content_type or "").lower()
        if not content_type:
            raise HTTPException(status_code=422, detail="Missing content type")

        kind = detect_kind(content_type)
        rules = FILE_RULES[kind]
        if content_type not in rules["mime"]:
            raise HTTPException(status_code=422, detail=f"Unsupported MIME type: {content_type}")

        max_bytes = int(rules["max_mb"]) * 1024 * 1024
        original_name = sanitize_filename(f.filename)
        extension = Path(original_name).suffix.lower()

        if kind == "image":
            raw = await f.read()
            if len(raw) > max_bytes:
                raise HTTPException(status_code=413, detail="File too large")
            processed = process_image_bytes(raw, content_type)
            _, preferred_ext = IMAGE_FORMAT_BY_MIME[content_type]
            extension = preferred_ext
            safe_name = f"{uuid.uuid4().hex}{extension}"
            path = dest_dir / safe_name
            async with aiofiles.open(path, "wb") as out_file:
                await out_file.write(processed)
        else:
            safe_name = f"{uuid.uuid4().hex}{extension}"
            path = dest_dir / safe_name
            await save_binary_file(f, path, max_bytes)

        out.append({
            "filename": safe_name,
            "url": f"{BASE_URL}/files/{model}/{record_id}/{safe_name}",
        })

    return {"status": "ok", "files": out}


@app.get("/files/{model}/{record_id}/{filename}")
def get_file(model: str, record_id: int, filename: str):
    filename = unquote(filename)

    path = BASE_STORAGE_PATH / model / str(record_id) / filename

    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "application/octet-stream"

    return FileResponse(
        path,
        media_type=mime,
        filename=path.name,
        headers={
            "Content-Disposition": f'inline; filename="{path.name}"'
        }
    )
