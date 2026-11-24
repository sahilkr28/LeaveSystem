import os
import socket
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application Configuration Settings"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-campus-hostel-portal-secret-key-prod-2026')
    
    # Database Configuration:
    # Uses DATABASE_URL (e.g. postgresql://user:pass@host:5432/dbname).
    # If unset, defaults to local SQLite file database.
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url:
        # Standardize postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        # Default local SQLite database
        # If running in Vercel, AWS Lambda, or any environment where filesystem is read-only:
        is_serverless = bool(
            os.environ.get('VERCEL') or
            os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or
            os.environ.get('LAMBDA_TASK_ROOT') or
            not os.access(str(BASE_DIR), os.W_OK)
        )
        if is_serverless:
            import tempfile
            default_sqlite_path = Path(tempfile.gettempdir()) / "hostel_erp.db"
        else:
            default_sqlite_path = BASE_DIR / "hostel_erp.db"

        try:
            default_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        SQLALCHEMY_DATABASE_URI = f"sqlite:///{default_sqlite_path.as_posix()}"

    # Warden Portal Authentication Password
    WARDEN_PASSWORD = os.environ.get('WARDEN_PASSWORD', 'warden123')

    # Node / Hostname Telemetry
    HOST_NAME = socket.gethostname()
    
    # Application Metadata
    APP_NAME = "Smart Campus Hostel & Leave Management ERP"
    PORTAL_VERSION = "v2.5.0-LTS"
    CAMPUS_NAME = "National Institute of Technology & Engineering Campus"
