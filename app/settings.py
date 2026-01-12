from pathlib import Path

# En la VM: Path("/data/files")
BASE_STORAGE_PATH = Path("/data/files")

API_TOKEN = "f1b4rPr0_UPLOAD_2026_v1$$"


# Límites simples (ajusta luego)
MAX_FILE_SIZE_MB = 20
ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

FILE_RULES = {
    "image": {
        "mime": {"image/jpeg", "image/png", "image/webp"},
        "max_mb": 10,
    },
    "video": {
        "mime": {"video/mp4", "video/webm"},
        "max_mb": 500,
    },
    "document": {
        "mime": {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
        "max_mb": 50,
    },
}
