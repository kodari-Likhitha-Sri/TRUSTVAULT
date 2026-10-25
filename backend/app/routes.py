import os
from datetime import datetime, timezone, time
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    abort, send_from_directory, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, cast, String

from app import db, bcrypt
from app.models import User, Document, Permission, ActivityLog
from app.forms import (
    RegistrationForm, LoginForm, DocumentUploadForm, DocumentEditForm,
    ShareDocumentForm, ProfileForm, ChangePasswordForm
)
from app.decorators import admin_required, owner_or_admin_required
from app.utils import save_document_file, save_avatar_picture
from config import Config

main_bp = Blueprint('main', __name__)

# ----------------- HOME / LANDING -----------------
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    return render_template('index.html', form=form)


# ----------------- AUTHENTICATION -----------------
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        ActivityLog.log('User Registered', f"User {user.username} registered with role {user.role}", user.id)
        flash(f'Account created successfully for {user.username}! You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', form=form)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.login_id.data.strip()
        user = User.query.filter(
            or_(User.email == login_input.lower(), User.username == login_input)
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            ActivityLog.log('User Login', f"User {user.username} logged in successfully", user.id)
            flash(f'Welcome back, {user.username}! Logged in as {user.role}.', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email/username or password. Please try again.', 'danger')
            
    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    ActivityLog.log('User Logout', f"User {current_user.username} logged out", current_user.id)
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('main.login'))


# ----------------- DASHBOARD -----------------
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Gather statistics based on user role
    total_users = User.query.count()
    total_docs = Document.query.count()
    total_shares = Permission.query.count()

    # User's own documents
    my_docs = Document.query.filter_by(owner_id=current_user.id).order_by(Document.upload_date.desc()).all()
    
    # Shared documents with user
    shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
    shared_doc_ids = [p.document_id for p in shared_perms]
    shared_docs = Document.query.filter(Document.id.in_(shared_doc_ids)).all() if shared_doc_ids else []

    # Category distribution for user/admin
    category_counts = {}
    for cat in Config.ALLOWED_CATEGORIES:
        if current_user.is_admin:
            cnt = Document.query.filter_by(category=cat).count()
        elif current_user.is_owner:
            cnt = Document.query.filter_by(owner_id=current_user.id, category=cat).count()
        else:
            cnt = len([d for d in shared_docs if d.category == cat])
        category_counts[cat] = cnt

    # Activity logs
    if current_user.is_admin:
        recent_activities = ActivityLog.query.order_by(ActivityLog.time.desc()).limit(8).all()
    else:
        recent_activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.time.desc()).limit(6).all()

    # Role stats for admin
    roles_breakdown = {
        'Admin': User.query.filter_by(role='Admin').count(),
        'Owner': User.query.filter_by(role='Owner').count(),
        'Viewer': User.query.filter_by(role='Viewer').count(),
    }

    storage_used_bytes = current_user.get_storage_used_bytes()
    # 100 MB quota per owner account for visual progress
    storage_quota_bytes = 100 * 1024 * 1024
    storage_percentage = min(100, round((storage_used_bytes / storage_quota_bytes) * 100, 1))

    return render_template(
        'dashboard.html',
        total_users=total_users,
        total_docs=total_docs,
        total_shares=total_shares,
        my_docs=my_docs,
        shared_docs=shared_docs,
        shared_perms={p.document_id: p.permission for p in shared_perms},
        category_counts=category_counts,
        recent_activities=recent_activities,
        roles_breakdown=roles_breakdown,
        storage_percentage=storage_percentage,
        categories=Config.ALLOWED_CATEGORIES
    )


# ----------------- UPLOAD DOCUMENTS -----------------
@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@owner_or_admin_required
def upload():
    form = DocumentUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            try:
                stored_name, orig_name, subfolder, file_type, file_size = save_document_file(file)
                doc = Document(
                    title=form.title.data.strip(),
                    filename=stored_name,
                    original_filename=orig_name,
                    subfolder=subfolder,
                    file_type=file_type,
                    file_size=file_size,
                    category=form.category.data,
                    description=form.description.data.strip() if form.description.data else '',
                    owner_id=current_user.id
                )
                db.session.add(doc)
                db.session.commit()

                ActivityLog.log('Document Upload', f"Uploaded '{doc.title}' ({doc.original_filename}) into {doc.category}", current_user.id)
                flash(f"Document '{doc.title}' uploaded successfully into {doc.category} category!", 'success')
                return redirect(url_for('main.documents'))
            except Exception as e:
                db.session.rollback()
                flash(f"Failed to upload document: {str(e)}", 'danger')

    return render_template('upload.html', form=form, categories=Config.ALLOWED_CATEGORIES)


# ----------------- MY DOCUMENTS / VAULT -----------------
@main_bp.route('/documents')
@login_required
def documents():
    # Filter mode for admin: all or mine
    view_mode = request.args.get('view', 'all' if current_user.is_viewer else 'mine')
    category_filter = request.args.get('category', '').strip()

    if current_user.is_admin and view_mode == 'all':
        query = Document.query
    elif current_user.is_viewer:
        shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
        shared_doc_ids = [p.document_id for p in shared_perms]
        query = Document.query.filter(Document.id.in_(shared_doc_ids)) if shared_doc_ids else Document.query.filter(False)
    else:
        # Owner view: their documents + any shared with them
        shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
        shared_doc_ids = [p.document_id for p in shared_perms]
        query = Document.query.filter(or_(Document.owner_id == current_user.id, Document.id.in_(shared_doc_ids)))

    if category_filter and category_filter in Config.ALLOWED_CATEGORIES:
        query = query.filter(Document.category == category_filter)

    docs = query.order_by(Document.upload_date.desc()).all()
    
    # Map user permissions for each document
    user_perms = {}
    for doc in docs:
        can_access, perm_type = current_user.can_access_document(doc)
        user_perms[doc.id] = perm_type

    return render_template(
        'documents.html',
        documents=docs,
        user_perms=user_perms,
        view_mode=view_mode,
        category_filter=category_filter,
        categories=Config.ALLOWED_CATEGORIES
    )


# ----------------- DOCUMENT DETAIL / PREVIEW -----------------
@main_bp.route('/document/<int:doc_id>')
@login_required
def document_detail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    can_access, perm_type = current_user.can_access_document(doc)
    
    # Phase 12 RBAC Check
    if not can_access:
        flash('Access Denied: You do not have permission to view this document.', 'danger')
        abort(403)

    permissions_list = Permission.query.filter_by(document_id=doc.id).all()
    can_edit = current_user.can_edit_document(doc)
    can_delete = current_user.can_delete_document(doc)
    can_share = current_user.can_share_document(doc)

    return render_template(
        'document_detail.html',
        doc=doc,
        perm_type=perm_type,
        can_edit=can_edit,
        can_delete=can_delete,
        can_share=can_share,
        permissions_list=permissions_list
    )


# ----------------- DOWNLOAD DOCUMENT -----------------
@main_bp.route('/document/<int:doc_id>/download')
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    can_access, _ = current_user.can_access_document(doc)
    
    if not can_access:
        flash('Access Denied: You do not have permission to download this document.', 'danger')
        abort(403)

    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.subfolder)
    ActivityLog.log('Document Download', f"Downloaded '{doc.title}' ({doc.original_filename})", current_user.id)

    return send_from_directory(
        folder,
        doc.filename,
        as_attachment=True,
        download_name=doc.original_filename
    )


# ----------------- EDIT DOCUMENT -----------------
@main_bp.route('/document/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not current_user.can_edit_document(doc):
        flash('Access Denied: You do not have edit permission for this document.', 'danger')
        abort(403)

    form = DocumentEditForm(obj=doc)
    if form.validate_on_submit():
        doc.title = form.title.data.strip()
        doc.category = form.category.data
        doc.description = form.description.data.strip() if form.description.data else ''
        db.session.commit()

        ActivityLog.log('Document Edited', f"Updated metadata for '{doc.title}'", current_user.id)
        flash(f"Document '{doc.title}' updated successfully.", 'success')
        return redirect(url_for('main.document_detail', doc_id=doc.id))

    return render_template('document_edit.html', form=form, doc=doc)


# ----------------- DELETE DOCUMENT -----------------
@main_bp.route('/document/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not current_user.can_delete_document(doc):
        flash('Access Denied: Only the owner or an administrator can delete this document.', 'danger')
        abort(403)

    title = doc.title
    # Attempt to remove file from disk
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.subfolder, doc.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    db.session.delete(doc)
    db.session.commit()

    ActivityLog.log('Document Deleted', f"Deleted document '{title}'", current_user.id)
    flash(f"Document '{title}' was permanently deleted.", 'info')
    return redirect(url_for('main.documents'))


# ----------------- SHARE DOCUMENT / PERMISSIONS -----------------
@main_bp.route('/share', methods=['GET', 'POST'])
@main_bp.route('/share/<int:doc_id>', methods=['GET', 'POST'])
@login_required
@owner_or_admin_required
def share_document(doc_id=None):
    doc = None
    if doc_id:
        doc = Document.query.get_or_404(doc_id)
        if not current_user.can_share_document(doc):
            flash('Access Denied: You cannot share documents you do not own.', 'danger')
            abort(403)

    # Documents that current user can share (their own, or all if admin)
    if current_user.is_admin:
        available_docs = Document.query.order_by(Document.title).all()
    else:
        available_docs = Document.query.filter_by(owner_id=current_user.id).order_by(Document.title).all()

    # Potential recipients (all users except current user and document owner)
    recipient_users = User.query.filter(User.id != current_user.id).order_by(User.username).all()

    form = ShareDocumentForm()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email}) - {u.role}") for u in recipient_users]

    if form.validate_on_submit():
        target_doc_id = doc_id or request.form.get('document_id', type=int)
        target_doc = Document.query.get_or_404(target_doc_id)

        if not current_user.can_share_document(target_doc):
            flash('Access Denied: You cannot share this document.', 'danger')
            abort(403)

        selected_user = User.query.get_or_404(form.user_id.data)

        # Prevent sharing with owner
        if selected_user.id == target_doc.owner_id:
            flash(f"{selected_user.username} is already the owner of this document.", 'warning')
            return redirect(url_for('main.share_document', doc_id=target_doc.id))

        existing_perm = Permission.query.filter_by(
            document_id=target_doc.id,
            user_id=selected_user.id
        ).first()

        if existing_perm:
            existing_perm.permission = form.permission.data
            existing_perm.granted_at = datetime.now(timezone.utc)
            db.session.commit()
            action_msg = f"Updated access to '{form.permission.data}' for {selected_user.username} on '{target_doc.title}'"
        else:
            new_perm = Permission(
                document_id=target_doc.id,
                user_id=selected_user.id,
                permission=form.permission.data
            )
            db.session.add(new_perm)
            db.session.commit()
            action_msg = f"Granted '{form.permission.data}' access to {selected_user.username} on '{target_doc.title}'"

        ActivityLog.log('Permission Changed', action_msg, current_user.id)
        flash(action_msg, 'success')
        return redirect(url_for('main.share_document', doc_id=target_doc.id))

    # Existing permissions for this document (if selected) or overall shares
    if doc:
        active_shares = Permission.query.filter_by(document_id=doc.id).all()
    else:
        active_shares = Permission.query.join(Document).filter(
            Document.owner_id == current_user.id
        ).all() if not current_user.is_admin else Permission.query.all()

    return render_template(
        'share.html',
        form=form,
        doc=doc,
        available_docs=available_docs,
        active_shares=active_shares
    )


@main_bp.route('/share/revoke/<int:perm_id>', methods=['POST'])
@login_required
@owner_or_admin_required
def revoke_permission(perm_id):
    perm = Permission.query.get_or_404(perm_id)
    doc = perm.document
    
    if not current_user.can_share_document(doc):
        flash('Access Denied: You cannot revoke permissions on this document.', 'danger')
        abort(403)

    recipient_name = perm.user.username
    doc_title = doc.title
    db.session.delete(perm)
    db.session.commit()

    ActivityLog.log('Permission Revoked', f"Revoked access for {recipient_name} on '{doc_title}'", current_user.id)
    flash(f"Access for {recipient_name} on '{doc_title}' has been revoked.", 'info')
    
    return redirect(request.referrer or url_for('main.share_document'))


# ----------------- SEARCH DOCUMENTS -----------------
@main_bp.route('/search')
@login_required
def search():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    file_type = request.args.get('type', '').strip()
    upload_date = request.args.get('upload_date', '').strip() or request.args.get('date', '').strip()

    # Determine base document query according to user permissions
    if current_user.is_admin:
        doc_query = Document.query
    elif current_user.is_viewer:
        shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
        shared_doc_ids = [p.document_id for p in shared_perms]
        doc_query = Document.query.filter(Document.id.in_(shared_doc_ids)) if shared_doc_ids else Document.query.filter(False)
    else:
        shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
        shared_doc_ids = [p.document_id for p in shared_perms]
        doc_query = Document.query.filter(or_(Document.owner_id == current_user.id, Document.id.in_(shared_doc_ids)))

    if query_text:
        # Search by Title, original filename, description, owner's username, or upload date string
        doc_query = doc_query.join(User, Document.owner_id == User.id).filter(
            or_(
                Document.title.ilike(f"%{query_text}%"),
                Document.original_filename.ilike(f"%{query_text}%"),
                Document.description.ilike(f"%{query_text}%"),
                User.username.ilike(f"%{query_text}%"),
                cast(Document.upload_date, String).ilike(f"%{query_text}%")
            )
        )

    if category and category in Config.ALLOWED_CATEGORIES:
        doc_query = doc_query.filter(Document.category == category)

    if file_type:
        doc_query = doc_query.filter(Document.file_type == file_type.lower())

    if upload_date:
        try:
            target_date = datetime.strptime(upload_date, '%Y-%m-%d').date()
            start_dt = datetime.combine(target_date, time.min)
            end_dt = datetime.combine(target_date, time.max)
            doc_query = doc_query.filter(Document.upload_date >= start_dt, Document.upload_date <= end_dt)
        except ValueError:
            pass

    results = doc_query.order_by(Document.upload_date.desc()).all()

    return render_template(
        'search.html',
        results=results,
        query_text=query_text,
        selected_category=category,
        selected_type=file_type,
        selected_date=upload_date,
        categories=Config.ALLOWED_CATEGORIES
    )


# ----------------- CATEGORIES -----------------
@main_bp.route('/categories')
@main_bp.route('/categories/<category_name>')
@login_required
def categories(category_name=None):
    category_stats = []
    
    for cat in Config.ALLOWED_CATEGORIES:
        if current_user.is_admin:
            cnt = Document.query.filter_by(category=cat).count()
        elif current_user.is_viewer:
            shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
            shared_doc_ids = [p.document_id for p in shared_perms]
            cnt = Document.query.filter(Document.id.in_(shared_doc_ids), Document.category == cat).count() if shared_doc_ids else 0
        else:
            shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
            shared_doc_ids = [p.document_id for p in shared_perms]
            cnt = Document.query.filter(
                or_(Document.owner_id == current_user.id, Document.id.in_(shared_doc_ids)),
                Document.category == cat
            ).count()
        category_stats.append({'name': cat, 'count': cnt})

    selected_docs = []
    if category_name and category_name in Config.ALLOWED_CATEGORIES:
        if current_user.is_admin:
            query = Document.query.filter_by(category=category_name)
        elif current_user.is_viewer:
            shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
            shared_doc_ids = [p.document_id for p in shared_perms]
            query = Document.query.filter(Document.id.in_(shared_doc_ids), Document.category == category_name) if shared_doc_ids else Document.query.filter(False)
        else:
            shared_perms = Permission.query.filter_by(user_id=current_user.id).all()
            shared_doc_ids = [p.document_id for p in shared_perms]
            query = Document.query.filter(
                or_(Document.owner_id == current_user.id, Document.id.in_(shared_doc_ids)),
                Document.category == category_name
            )
        selected_docs = query.order_by(Document.upload_date.desc()).all()

    return render_template(
        'categories.html',
        category_stats=category_stats,
        selected_category=category_name,
        selected_docs=selected_docs
    )


# ----------------- ADMIN: USER MANAGEMENT -----------------
@main_bp.route('/users')
@login_required
@admin_required
def users_management():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=all_users)


@main_bp.route('/users/<int:user_id>/update-role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['Admin', 'Owner', 'Viewer']:
        old_role = user.role
        user.role = new_role
        db.session.commit()
        ActivityLog.log('Role Changed', f"Admin {current_user.username} changed {user.username}'s role from {old_role} to {new_role}", current_user.id)
        flash(f"Updated {user.username}'s role to {new_role}.", 'success')
    return redirect(url_for('main.users_management'))


@main_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('main.users_management'))

    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    ActivityLog.log('User Deleted', f"Admin {current_user.username} deleted user {username}", current_user.id)
    flash(f"User {username} and associated permissions have been deleted.", 'info')
    return redirect(url_for('main.users_management'))


# ----------------- ADMIN: ACTIVITY LOGS -----------------
@main_bp.route('/logs')
@login_required
@admin_required
def activity_logs():
    action_filter = request.args.get('action', '').strip()
    query = ActivityLog.query
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)

    logs = query.order_by(ActivityLog.time.desc()).limit(200).all()
    actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [a[0] for a in actions]

    return render_template('logs.html', logs=logs, actions=actions, selected_action=action_filter)


@main_bp.route('/logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    ActivityLog.query.delete()
    db.session.commit()
    ActivityLog.log('Logs Cleared', f"Activity logs purged by {current_user.username}", current_user.id)
    flash('Activity logs have been cleared.', 'info')
    return redirect(url_for('main.activity_logs'))


# ----------------- PROFILE MANAGEMENT -----------------
@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    if form.validate_on_submit() and 'submit' in request.form:
        # Check uniqueness if username or email changed
        new_username = form.username.data.strip()
        new_email = form.email.data.strip().lower()

        existing_user = User.query.filter(User.username == new_username, User.id != current_user.id).first()
        if existing_user:
            flash('That username is already taken by another account.', 'danger')
            return redirect(url_for('main.profile'))

        existing_email = User.query.filter(User.email == new_email, User.id != current_user.id).first()
        if existing_email:
            flash('That email address is already in use by another account.', 'danger')
            return redirect(url_for('main.profile'))

        current_user.username = new_username
        current_user.email = new_email

        if form.profile_pic.data:
            pic_fn = save_avatar_picture(form.profile_pic.data)
            current_user.profile_pic = pic_fn

        db.session.commit()
        ActivityLog.log('Profile Updated', f"User {current_user.username} updated profile info", current_user.id)
        flash('Your profile details have been updated!', 'success')
        return redirect(url_for('main.profile'))

    user_logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.time.desc()).limit(10).all()

    return render_template(
        'profile.html',
        form=form,
        password_form=password_form,
        user_logs=user_logs
    )


@main_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash('Current password verification failed. Please try again.', 'danger')
            return redirect(url_for('main.profile'))

        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        ActivityLog.log('Password Changed', f"Password changed for user {current_user.username}", current_user.id)
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('main.profile'))

    error_msgs = []
    for field_name, errors in password_form.errors.items():
        for err in errors:
            error_msgs.append(err)
    if error_msgs:
        flash('Password update failed: ' + ' '.join(error_msgs), 'danger')
    else:
        flash('Password update failed. Ensure password is at least 12 characters with uppercase, lowercase, and special character.', 'danger')
    return redirect(url_for('main.profile'))
