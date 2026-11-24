"""
Root Entry Point for Smart Campus Hostel ERP
Enables: gunicorn -w 2 -b 0.0.0.0:5000 app:app (from project root)
and: python app.py
"""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
