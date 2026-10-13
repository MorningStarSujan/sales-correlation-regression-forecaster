import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.environ.get("VERCEL") == "1"

# Vercel's application filesystem is read-only. For a temporary academic demo,
# use /tmp; on a normal local run, preserve the original project paths.
if IS_VERCEL:
    DATA_DIR = Path(os.environ.get("APP_DATA_DIR", "/tmp/sales-forecaster/data"))
    DATABASE_PATH = Path(
        os.environ.get(
            "DATABASE_PATH",
            "/tmp/sales-forecaster/sales_forecaster.db",
        )
    )
else:
    DATA_DIR = Path(os.environ.get("APP_DATA_DIR", str(BASE_DIR / "data")))
    DATABASE_PATH = Path(
        os.environ.get(
            "DATABASE_PATH",
            str(BASE_DIR / "database" / "sales_forecaster.db"),
        )
    )


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or (
        "local-development-only-change-this-secret" if not IS_VERCEL else os.urandom(32).hex()
    )
    DATA_DIR = DATA_DIR
    UPLOAD_FOLDER = Path(
        os.environ.get("UPLOAD_FOLDER", str(DATA_DIR / "uploads"))
    )
    REPORT_FOLDER = Path(
        os.environ.get("REPORT_FOLDER", str(DATA_DIR / "reports"))
    )
    DATABASE_PATH = DATABASE_PATH
    SAMPLE_DATA_PATH = BASE_DIR / "data" / "sample_sales_data.csv"

    MAX_CONTENT_LENGTH = int(
        os.environ.get(
            "MAX_CONTENT_LENGTH",
            str(4 * 1024 * 1024 if IS_VERCEL else 16 * 1024 * 1024),
        )
    )
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
