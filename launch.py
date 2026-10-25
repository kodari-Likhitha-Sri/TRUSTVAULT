import os
import sys
import time
import threading
import webbrowser

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app, db

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:5000"
    print(f"\n✨ Opening TrustVault in your browser: {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    print("=" * 65)
    print("   🛡️  TrustVault - Secure Document Management Platform")
    print("=" * 65)
    print("Initializing database...")
    app = create_app()
    with app.app_context():
        db.create_all()

    # Launch browser automatically
    threading.Thread(target=open_browser, daemon=True).start()

    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Running server on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)
