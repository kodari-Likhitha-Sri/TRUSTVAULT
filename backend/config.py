import os

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, '..'))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'trustvault-super-secure-key-2026-xyz-987'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BACKEND_DIR, 'trustvault.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 20 MB max file size (Phase 7)
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    
    # Frontend directory paths
    FRONTEND_DIR = FRONTEND_DIR
    TEMPLATES_FOLDER = os.path.join(FRONTEND_DIR, 'templates')
    STATIC_FOLDER = os.path.join(FRONTEND_DIR, 'static')
    
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
    AVATAR_FOLDER = os.path.join(STATIC_FOLDER, 'images', 'avatars')
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'ppt', 'pptx', 'png', 'jpg', 'jpeg'}
    
    ALLOWED_CATEGORIES = [
        'Personal',
        'Academic',
        'Finance',
        'Legal',
        'Work',
        'HR',
        'Medical',
        'Research',
        'Education',
        'Other'
    ]
