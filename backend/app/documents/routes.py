import os
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    abort, send_from_directory, current_app
)
from flask_login import current_user, login_required
from app.decorators.auth import owner_required, admin_required
from app.forms import DocumentUploadForm, DocumentEditForm
from app.documents.service import DocumentService
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from config import Config

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/documents')
@login_required
def documents():
    # Role-based default view:
    # Admin defaults to 'all' (can toggle 'my', 'trash')
    # Owner defaults to 'my' (can toggle 'shared', 'trash')
    # Viewer defaults to 'shared'
    default_view = 'all' if current_user.is_admin else ('shared' if current_user.is_viewer else 'my')
    view_mode = request.args.get('view', default_view)
    category_filter = request.args.get('category', '').strip()

    if category_filter and category_filter not in Config.ALLOWED_CATEGORIES:
        category_filter = None

    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()

    user_docs = DocumentService.get_documents_for_user(
        user=current_user,
        view_mode=view_mode,
        category=category_filter
    )

    if search_query:
        sq = search_query.lower()
        user_docs = [
            d for d in user_docs
            if sq in (d.title or '').lower() or
               sq in (d.original_filename or '').lower() or
               sq in (d.description or '').lower() or
               sq in (d.owner.username or '').lower()
        ]

    if sort_by == 'oldest':
        user_docs = sorted(user_docs, key=lambda d: d.upload_date or d.created_at)
    elif sort_by == 'name':
        user_docs = sorted(user_docs, key=lambda d: (d.title or '').lower())
    elif sort_by == 'size':
        user_docs = sorted(user_docs, key=lambda d: d.effective_size, reverse=True)
    else:
        user_docs = sorted(user_docs, key=lambda d: d.upload_date or d.created_at, reverse=True)

    # Compute user permission for each document
    doc_permissions = {}
    for d in user_docs:
        has_access, perm = current_user.can_access_document(d)
        doc_permissions[d.id] = perm

    trash_count = len(DocumentService.get_trash_documents(current_user)) if (current_user.is_admin or current_user.is_owner) else 0

    return render_template(
        'documents.html',
        documents=user_docs,
        doc_permissions=doc_permissions,
        user_perms=doc_permissions,
        view_mode=view_mode,
        category_filter=category_filter,
        search_query=search_query,
        sort_by=sort_by,
        categories=Config.ALLOWED_CATEGORIES,
        trash_count=trash_count
    )

@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@owner_required
def upload():
    form = DocumentUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        success, res = DocumentService.upload_document(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            file_storage=file,
            owner=current_user,
            upload_root_folder=current_app.config['UPLOAD_FOLDER'],
            req=request
        )
        if success:
            flash(f"Document '{res.title}' uploaded and encrypted successfully!", 'success')
            return redirect(url_for('documents.document_detail', doc_id=res.id))
        else:
            flash(f"Upload failed: {res}", 'danger')

    return render_template('upload.html', form=form, categories=Config.ALLOWED_CATEGORIES)

@documents_bp.route('/documents/<int:doc_id>')
@login_required
def document_detail(doc_id):
    doc = DocumentRepository.get_by_id(doc_id, include_deleted=current_user.is_admin)
    if not doc:
        abort(404)

    has_access, perm_level = current_user.can_access_document(doc)
    if not has_access:
        flash('Access Denied: You do not have permission to view this document.', 'danger')
        abort(403)

    permissions_list = doc.permissions
    can_edit = current_user.can_edit_document(doc)
    can_delete = current_user.can_delete_document(doc)
    can_share = current_user.can_share_document(doc)

    return render_template(
        'document_detail.html',
        doc=doc,
        perm_level=perm_level,
        perm_type=perm_level,
        can_edit=can_edit,
        can_delete=can_delete,
        can_share=can_share,
        permissions_list=permissions_list,
        versions=doc.versions
    )

@documents_bp.route('/documents/<int:doc_id>/download')
@login_required
def download_document(doc_id):
    version_id = request.args.get('version_id', type=int)
    success, err, subfolder, filename, download_as = DocumentService.get_document_download_info(
        doc_id=doc_id,
        user=current_user,
        version_id=version_id,
        req=request
    )
    if not success:
        flash(err, 'danger')
        abort(403 if 'Access Denied' in err else 404)

    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    return send_from_directory(
        folder,
        filename,
        as_attachment=True,
        download_name=download_as
    )

@documents_bp.route('/documents/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(doc_id):
    doc = DocumentRepository.get_by_id(doc_id, include_deleted=current_user.is_admin)
    if not doc:
        abort(404)

    if not current_user.can_edit_document(doc):
        flash('Access Denied: You do not have Edit permissions on this document.', 'danger')
        abort(403)

    form = DocumentEditForm(obj=doc)
    if form.validate_on_submit():
        success, res = DocumentService.update_document_metadata(
            doc_id=doc.id,
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            user=current_user,
            req=request
        )
        if success:
            flash('Document details updated successfully!', 'success')
            return redirect(url_for('documents.document_detail', doc_id=doc.id))
        else:
            flash(f"Update failed: {res}", 'danger')

    return render_template('document_edit.html', form=form, doc=doc)

@documents_bp.route('/documents/<int:doc_id>/version', methods=['POST'])
@login_required
def upload_version(doc_id):
    doc = DocumentRepository.get_by_id(doc_id, include_deleted=current_user.is_admin)
    if not doc:
        abort(404)

    if not current_user.can_edit_document(doc):
        flash('Access Denied: You cannot upload new versions.', 'danger')
        abort(403)

    file = request.files.get('version_file')
    change_notes = request.form.get('change_notes', '').strip()

    if not file or file.filename == '':
        flash('Please select a file to upload as the new version.', 'warning')
        return redirect(url_for('documents.document_detail', doc_id=doc.id))

    success, res = DocumentService.upload_new_version(
        doc_id=doc.id,
        file_storage=file,
        change_notes=change_notes,
        user=current_user,
        upload_root_folder=current_app.config['UPLOAD_FOLDER'],
        req=request
    )
    if success:
        flash(f'New version (v{doc.version}) uploaded and tracked successfully!', 'success')
    else:
        flash(f'Failed to upload version: {res}', 'danger')

    return redirect(url_for('documents.document_detail', doc_id=doc.id))

@documents_bp.route('/documents/<int:doc_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_document(doc_id):
    success, msg = DocumentService.soft_delete_document(doc_id=doc_id, user=current_user, req=request)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('documents.documents'))

@documents_bp.route('/documents/<int:doc_id>/restore', methods=['GET', 'POST'])
@login_required
def restore_document(doc_id):
    success, msg = DocumentService.restore_document(doc_id=doc_id, user=current_user, req=request)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('documents.documents'))

@documents_bp.route('/documents/<int:doc_id>/purge', methods=['GET', 'POST'])
@login_required
@admin_required
def purge_document(doc_id):
    success, msg = DocumentService.hard_delete_document(
        doc_id=doc_id,
        user=current_user,
        upload_root_folder=current_app.config['UPLOAD_FOLDER'],
        req=request
    )
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('documents.documents'))

@documents_bp.route('/categories')
@documents_bp.route('/categories/<category_name>')
@login_required
def categories(category_name=None):
    category_stats = []
    for cat in Config.ALLOWED_CATEGORIES:
        count = len(DocumentService.get_documents_for_user(current_user, category=cat))
        category_stats.append({
            'name': cat,
            'count': count
        })

    cat_docs = []
    if category_name and category_name in Config.ALLOWED_CATEGORIES:
        cat_docs = DocumentService.get_documents_for_user(current_user, category=category_name)

    return render_template(
        'categories.html',
        category_stats=category_stats,
        selected_category=category_name,
        selected_docs=cat_docs,
        category_documents=cat_docs
    )

@documents_bp.route('/search')
@login_required
def search():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    file_type = request.args.get('type', '').strip()
    upload_date = request.args.get('upload_date', '').strip() or request.args.get('date', '').strip()

    if category and category not in Config.ALLOWED_CATEGORIES:
        category = ''

    results = DocumentService.search_documents(
        user=current_user,
        query_text=query_text or None,
        category=category or None,
        file_type=file_type or None,
        upload_date=upload_date or None,
        status='Active'
    )

    return render_template(
        'search.html',
        results=results,
        query_text=query_text,
        selected_category=category,
        selected_type=file_type,
        selected_date=upload_date,
        categories=Config.ALLOWED_CATEGORIES
    )
