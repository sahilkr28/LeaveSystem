try:
    from .app import app
except (ImportError, ValueError):
    from app import app

__all__ = ["app"]
