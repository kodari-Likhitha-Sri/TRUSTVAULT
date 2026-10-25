from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.decorators.auth import owner_required
from app.forms import ShareDocumentForm
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.permission_repository import PermissionRepository
from app.permissions.service import PermissionService

permissions_bp = Blueprint('permissions', __name__)

@permissions_bp.route('/share', methods=['GET', 'POST'])
@permissions_bp.route('/share/<int:doc_id>', methods=['GET', 'POST'])
@login_required
@owner_required
def share_document(doc_id=None):
    doc = None
    if doc_id:
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=current_user.is_admin)
        if not doc:
            abort(404)
        if not current_user.can_share_document(doc):
            flash('Access Denied: You cannot share documents you do not own.', 'danger')
            abort(403)

    if current_user.is_admin:
        available_docs = DocumentRepository.get_all(include_deleted=False)
    else:
        available_docs = DocumentRepository.get_by_owner(current_user.id, include_deleted=False)

    recipient_users = [u for u in UserRepository.get_all() if u.id != current_user.id]

    form = ShareDocumentForm()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email}) - {u.role}") for u in recipient_users]

    if form.validate_on_submit():
        target_doc_id = doc_id or request.form.get('document_id', type=int)
        target_doc = DocumentRepository.get_by_id(target_doc_id, include_deleted=current_user.is_admin)
        if not target_doc:
            abort(404)

        if not current_user.can_share_document(target_doc):
            flash('Access Denied: You cannot share this document.', 'danger')
            abort(403)

        success, msg = PermissionService.grant_permission(
            granter=current_user,
            doc_id=target_doc.id,
            recipient_id=form.user_id.data,
            permission_type=form.permission.data,
            req=request
        )
        flash(msg, 'success' if success else 'warning')
        return redirect(url_for('permissions.share_document', doc_id=target_doc.id))

    if doc:
        active_shares = PermissionRepository.get_for_document(doc.id, include_expired=True)
    else:
        if current_user.is_admin:
            from app.models.permission import Permission
            active_shares = Permission.query.all()
        else:
            from app.models.permission import Permission
            from app.models.document import Document
            active_shares = Permission.query.join(Document).filter(
                Document.owner_id == current_user.id
            ).all()

    return render_template(
        'share.html',
        form=form,
        doc=doc,
        available_docs=available_docs,
        active_shares=active_shares
    )

@permissions_bp.route('/share/revoke/<int:perm_id>', methods=['POST'])
@login_required
@owner_required
def revoke_permission(perm_id):
    success, msg = PermissionService.revoke_permission(current_user, perm_id, req=request)
    flash(msg, 'info' if success else 'danger')
    return redirect(url_for('permissions.share_document'))
