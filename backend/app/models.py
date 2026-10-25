"""
Legacy compatibility module for app.models.
Re-exports all models from modular app.models package.
"""
from app.models.user import User, load_user
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.permission import Permission
from app.models.activity_log import ActivityLog
from app.models.notification import Notification
from app.utils.helpers import format_file_size

__all__ = [
    'User',
    'Document',
    'DocumentVersion',
    'Permission',
    'ActivityLog',
    'Notification',
    'format_file_size',
    'load_user'
]
