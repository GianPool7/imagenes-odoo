from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import shutil, uuid, mimetypes
from urllib.parse import unquote


from app.settings import BASE_STORAGE_PATH, FILE_RULES, API_TOKEN

app = FastAPI(title="File API")

BASE_URL = "http://20.100.100.58:80"


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
    _: None = Depends(verify_token),
):
    dest_dir = BASE_STORAGE_PATH / model / str(record_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    out = []

    for f in files:
        kind = detect_kind(f.content_type)
        rules = FILE_RULES[kind]

        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        path = dest_dir / safe_name

        with path.open("wb") as buf:
            shutil.copyfileobj(f.file, buf)

        out.append({
            "filename": safe_name,
            "url": f"{BASE_URL}/files/{model}/{record_id}/{safe_name}",
        })

    return {"status": "ok", "files": out}


# 🔥 AQUÍ ESTÁ EL FIX IMPORTANTE

@app.get("/files/{model}/{record_id}/{filename}")
def get_file(model: str, record_id: int, filename: str):
    # 🔥 CLAVE: decodificar nombre
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