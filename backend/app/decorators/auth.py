from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from app.repositories.document_repository import DocumentRepository
from app.repositories.permission_repository import PermissionRepository

def admin_required(f):
    """Requires authenticated administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first to continue.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Admin privileges are strictly required to access this resource.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Requires Admin or Owner role (Viewers cannot access)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first to continue.', 'warning')
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin or current_user.is_owner):
            flash('Your role (Viewer) does not permit this action.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Backward compatibility alias
owner_or_admin_required = owner_required

def permission_required(required_level="READ"):
    """
    Validates dynamic permission level ('READ', 'EDIT', 'DELETE') on document resource.
    Resolves doc_id from route kwargs (doc_id or id).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in first to continue.', 'warning')
                return redirect(url_for('auth.login'))

            doc_id = kwargs.get('doc_id') or kwargs.get('id')
            if not doc_id:
                return f(*args, **kwargs)

            doc = DocumentRepository.get_by_id(doc_id, include_deleted=current_user.is_admin)
            if not doc:
                abort(404)

            # Administrators have full bypass access
            if current_user.is_admin:
                return f(*args, **kwargs)

            # Document owner has full access
            if doc.owner_id == current_user.id:
                return f(*args, **kwargs)

            # Check explicit permission grant
            perm = PermissionRepository.get_by_doc_and_user(doc.id, current_user.id)
            if not perm or perm.is_expired:
                flash('Access denied or your document access permission has expired.', 'danger')
                abort(403)

            p_type = perm.permission.upper()
            req_type = required_level.upper()

            # Permission Hierarchy: DELETE > EDIT > READ
            levels = {'READ': 1, 'EDIT': 2, 'DELETE': 3}
            if levels.get(p_type, 0) < levels.get(req_type, 1):
                flash(f'Insufficient permissions. You need {req_type} access for this action.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
