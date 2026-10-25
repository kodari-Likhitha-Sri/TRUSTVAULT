import os
import flask
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

ENDPOINT_ALIASES = {
    'main.index': 'auth.index',
    'main.login': 'auth.login',
    'main.register': 'auth.register',
    'main.logout': 'auth.logout',
    'main.dashboard': 'dashboard.index',
    'main.documents': 'documents.documents',
    'main.upload': 'documents.upload',
    'main.document_detail': 'documents.document_detail',
    'main.download_document': 'documents.download_document',
    'main.edit_document': 'documents.edit_document',
    'main.delete_document': 'documents.delete_document',
    'main.share_document': 'permissions.share_document',
    'main.revoke_permission': 'permissions.revoke_permission',
    'main.categories': 'documents.categories',
    'main.search': 'documents.search',
    'main.admin_users': 'users.admin_users',
    'main.users_management': 'users.admin_users',
    'main.update_user_role': 'users.change_role',
    'main.delete_user': 'users.delete_user',
    'main.activity_logs': 'audit.logs',
    'main.admin_logs': 'audit.logs',
    'main.clear_logs': 'audit.logs',
    'main.profile': 'users.profile',
    'main.change_password': 'users.change_password',
}

def init_db_schema(app):
    """Ensure all tables and enterprise columns exist in the database."""
    with app.app_context():
        # Import models so db.create_all() registers all tables
        from app.models import User, Document, DocumentVersion, Permission, ActivityLog, Notification
        db.create_all()

        from sqlalchemy import text
        if db.engine.dialect.name == 'sqlite':
            try:
                with db.engine.connect() as conn:
                    # 1. users table schema update
                    cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
                    if cols:
                        if 'department' not in cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100) DEFAULT 'General'"))
                        if 'status' not in cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'Active'"))
                        if 'last_login' not in cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
                        if 'updated_at' not in cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))

                        # Ensure username index allows duplicate usernames while email index enforces uniqueness
                        conn.execute(text("DROP INDEX IF EXISTS ix_users_username"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
                        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

                    # 2. documents table schema update
                    cols = {row[1] for row in conn.execute(text("PRAGMA table_info(documents)")).fetchall()}
                    if cols:
                        if 'filepath' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN filepath VARCHAR(255)"))
                        if 'size' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN size INTEGER DEFAULT 0"))
                        if 'version' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1"))
                        if 'status' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN status VARCHAR(20) DEFAULT 'Active'"))
                        if 'deleted_by' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN deleted_by INTEGER"))
                        if 'deleted_at' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN deleted_at DATETIME"))
                        if 'created_at' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN created_at DATETIME"))
                        if 'updated_at' not in cols:
                            conn.execute(text("ALTER TABLE documents ADD COLUMN updated_at DATETIME"))

                    # 3. permissions table schema update
                    cols = {row[1] for row in conn.execute(text("PRAGMA table_info(permissions)")).fetchall()}
                    if cols:
                        if 'granted_by' not in cols:
                            conn.execute(text("ALTER TABLE permissions ADD COLUMN granted_by INTEGER"))
                        if 'expires_at' not in cols:
                            conn.execute(text("ALTER TABLE permissions ADD COLUMN expires_at DATETIME"))

                    # 4. activity_logs table schema update
                    cols = {row[1] for row in conn.execute(text("PRAGMA table_info(activity_logs)")).fetchall()}
                    if cols:
                        if 'document_id' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN document_id INTEGER"))
                        if 'old_value' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN old_value TEXT"))
                        if 'new_value' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN new_value TEXT"))
                        if 'device' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN device VARCHAR(50)"))
                        if 'browser' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN browser VARCHAR(50)"))
                        if 'created_at' not in cols:
                            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN created_at DATETIME"))

                    conn.commit()
            except Exception:
                pass

def create_app(config_class=Config):
    templates_dir = getattr(config_class, 'TEMPLATES_FOLDER', None)
    if not templates_dir or not os.path.exists(templates_dir):
        base = os.path.abspath(os.path.dirname(__file__))
        candidates = [
            os.path.join(base, '..', '..', 'frontend', 'templates'),
            os.path.join(base, '..', 'templates'),
            os.path.join(base, 'templates'),
        ]
        templates_dir = next((c for c in candidates if os.path.exists(c)), candidates[0])

    static_dir = getattr(config_class, 'STATIC_FOLDER', None)
    if not static_dir or not os.path.exists(static_dir):
        base = os.path.abspath(os.path.dirname(__file__))
        candidates = [
            os.path.join(base, '..', '..', 'frontend', 'static'),
            os.path.join(base, '..', 'static'),
            os.path.join(base, 'static'),
        ]
        static_dir = next((c for c in candidates if os.path.exists(c)), candidates[0])

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Ensure upload directories exist
    upload_dirs = [
        os.path.join(app.config['UPLOAD_FOLDER'], 'pdf'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'images'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'docs'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'ppt'),
        app.config['AVATAR_FOLDER']
    ]
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)

    # Register modular blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.documents.routes import documents_bp
    from app.permissions.routes import permissions_bp
    from app.users.routes import users_bp
    from app.audit.routes import audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(audit_bp)

    # Seamless template backward compatibility for url_for
    original_url_for = flask.url_for

    def smart_url_for(endpoint, **values):
        target = ENDPOINT_ALIASES.get(endpoint, endpoint)
        try:
            return original_url_for(target, **values)
        except Exception:
            # Fallback scan across registered blueprints
            short = endpoint.split('.')[-1]
            for bp_name in ['auth', 'dashboard', 'documents', 'permissions', 'users', 'audit']:
                candidate = f"{bp_name}.{short}"
                try:
                    return original_url_for(candidate, **values)
                except Exception:
                    continue
            return original_url_for(endpoint, **values)

    @app.context_processor
    def inject_smart_url_for():
        return dict(url_for=smart_url_for)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    # Initialize schema
    init_db_schema(app)

    return app
