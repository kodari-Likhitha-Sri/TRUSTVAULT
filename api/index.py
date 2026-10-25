import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app, db

app = create_app()

try:
    with app.app_context():
        db.create_all()
except Exception as e:
    # Log warning but allow application to respond to health checks / requests
    print(f"Warning: db.create_all() during Vercel cold-start: {e}")
