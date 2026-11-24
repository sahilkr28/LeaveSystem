import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL environment indicator is active
os.environ["VERCEL"] = "1"

from app.app import app

# Expose both 'app' and 'handler' for Vercel WSGI runtime
handler = app
