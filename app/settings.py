import os
from pathlib import Path

# En la VM puede ser: /data/files
BASE_STORAGE_PATH = Path(os.getenv("BASE_STORAGE_PATH", "/data/files"))
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
API_TOKEN = os.getenv("API_TOKEN", "")
REQUIRE_API_TOKEN = os.getenv("REQUIRE_API_TOKEN", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


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
