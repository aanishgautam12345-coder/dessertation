"""JobMatch - Flask App Entry Point.

Run with:
    python run.py

Then open http://localhost:5000
"""

import os
from webapp.app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    app.run(debug=debug, host=host, port=5000, exclude_patterns=["venv/*"])
