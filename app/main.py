from fastapi import FastAPI, UploadFile, File, Form, HTTPException,Header, Depends
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import shutil, uuid
import mimetypes

from app.settings import BASE_STORAGE_PATH, FILE_RULES,API_TOKEN



app = FastAPI(title="File API")

BASE_URL = "http://127.0.0.1:8000"  # ⚠️ en prod será el dominio real

def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")


def detect_kind(mime: str) -> str:
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    return "document"

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
    _: None = Depends(verify_token),  # 👈 protección
):
    if not model or record_id <= 0:
        raise HTTPException(400, "Contexto inválido")

    dest_dir = BASE_STORAGE_PATH / model / str(record_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    out = []
    for f in files:
        kind = detect_kind(f.content_type)
        rules = FILE_RULES.get(kind)
        if not rules or f.content_type not in rules["mime"]:
            raise HTTPException(400, f"Tipo no permitido: {f.content_type}")

        # tamaño real
        f.file.seek(0, 2)
        size = f.file.tell()
        f.file.seek(0)
        if size > rules["max_mb"] * 1024 * 1024:
            raise HTTPException(400, f"Archivo muy grande ({kind})")

        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        path = dest_dir / safe_name
        with path.open("wb") as buf:
            shutil.copyfileobj(f.file, buf)

        out.append({
            "filename": safe_name,
            "original_name": f.filename,
            "type": kind,
            "size": size,
            "model": model,
            "record_id": record_id,
            "client_name": client_name,
            "client_dni": client_dni,
            "url": f"{BASE_URL}/files/{model}/{record_id}/{safe_name}",

        })

    return {"status": "ok", "count": len(out), "files": out}

@app.get("/files/{model}/{record_id}/{filename}")
def get_file(model: str, record_id: int, filename: str):
    path = BASE_STORAGE_PATH / model / str(record_id) / filename

    if not path.exists():
        raise HTTPException(status_code=404)

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
