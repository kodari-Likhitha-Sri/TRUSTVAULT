"""
Legacy compatibility module for app.decorators.
Re-exports from app.decorators.auth.
"""
from app.decorators.auth import admin_required, owner_required, owner_or_admin_required, permission_required

__all__ = [
    'admin_required',
    'owner_required',
    'owner_or_admin_required',
    'permission_required'
]
