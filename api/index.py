import os
import sys
import traceback
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL environment indicator is active
os.environ["VERCEL"] = "1"

try:
    from app.app import app
except Exception as e:
    err_trace = traceback.format_exc()
    print(f"[FATAL VERCEL INITIALIZATION ERROR]:\n{err_trace}")
    from flask import Flask, Response
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all_error(path):
        return Response(
            f"""<!DOCTYPE html>
<html>
<head><title>Application Startup Notice</title></head>
<body style="font-family: system-ui, sans-serif; padding: 30px; background: #0d1e34; color: #fff;">
  <h2 style="color: #ff6b6b;">⚠️ Application Initialization Error on Vercel</h2>
  <p>The Flask application failed to start due to the following exception:</p>
  <pre style="background: #1a2a40; color: #a4b7cc; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 14px;">{err_trace}</pre>
</body>
</html>""",
            status=500,
            mimetype="text/html"
        )
