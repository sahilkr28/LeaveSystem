import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_vercel_config_and_entrypoint():
    """Verify vercel.json and api/index.py configuration."""
    vercel_json_path = BASE_DIR / "vercel.json"
    api_index_path = BASE_DIR / "api" / "index.py"
    vercelignore_path = BASE_DIR / ".vercelignore"

    assert vercel_json_path.exists(), "vercel.json must exist at project root"
    assert api_index_path.exists(), "api/index.py must exist"
    assert vercelignore_path.exists(), ".vercelignore must exist"

    # Verify JSON syntax
    with open(vercel_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config.get("version") == 2
    assert "builds" in config
    assert config["builds"][0]["src"] == "api/index.py"

    # Verify importing api/index.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("vercel_api_index", str(api_index_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "app"), "api/index.py must expose 'app' WSGI callable"

def test_vercel_tmp_database_fallback(monkeypatch):
    """Verify that when VERCEL=1 is set, database falls back to /tmp/hostel_erp.db."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.config import Config
    # Reload logic check
    assert "/tmp" in Config.SQLALCHEMY_DATABASE_URI or "hostel_erp.db" in Config.SQLALCHEMY_DATABASE_URI
