from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"
    DATABASE_PATH = INSTANCE_DIR / "gost_terms.db"
    UPLOAD_FOLDER = INSTANCE_DIR / "uploads"

    SECRET_KEY = "dev-secret-key-change-me"
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".pdf", ".docx"}