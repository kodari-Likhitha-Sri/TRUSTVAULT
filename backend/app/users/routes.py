from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app.decorators.auth import admin_required
from app.forms import ProfileForm, ChangePasswordForm
from app.users.service import UserService
from app.audit.service import AuditService

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
@admin_required
def admin_users():
    status_filter = request.args.get('status')
    role_filter = request.args.get('role')
    all_users = UserService.list_all_users(status=status_filter, role=role_filter)
    return render_template('users.html', users=all_users)

@users_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    new_role = request.form.get('role')
    if new_role not in ['Admin', 'Owner', 'Viewer']:
        flash('Invalid role selection.', 'danger')
        return redirect(url_for('users.admin_users'))

    success, msg = UserService.change_user_role(current_user, user_id, new_role, req=request)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('users.admin_users'))

@users_bp.route('/users/<int:user_id>/status', methods=['POST'])
@login_required
@admin_required
def change_status(user_id):
    new_status = request.form.get('status')
    if new_status not in ['Active', 'Suspended', 'Inactive']:
        flash('Invalid status selection.', 'danger')
        return redirect(url_for('users.admin_users'))

    success, msg = UserService.change_user_status(current_user, user_id, new_status, req=request)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('users.admin_users'))

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    success, msg = UserService.delete_user(current_user, user_id, req=request)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('users.admin_users'))

@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    if form.validate_on_submit() and 'profile_pic' in request.files:
        pic_file = form.profile_pic.data if form.profile_pic.data else None
        success, res = UserService.update_profile(
            user=current_user,
            username=form.username.data,
            email=form.email.data,
            profile_pic_file=pic_file,
            avatar_folder=current_app.config['AVATAR_FOLDER'],
            req=request
        )
        if success:
            flash('Your profile details have been updated successfully!', 'success')
            return redirect(url_for('users.profile'))
        else:
            flash(res, 'danger')

    user_logs = AuditService.get_audit_trail(limit=15, user_id=current_user.id)
    return render_template(
        'profile.html',
        form=form,
        password_form=password_form,
        user_logs=user_logs
    )

@users_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        success, msg = UserService.change_password(
            user=current_user,
            current_password=password_form.current_password.data,
            new_password=password_form.new_password.data,
            req=request
        )
        flash(msg, 'success' if success else 'danger')
        return redirect(url_for('users.profile'))

    errors = []
    for field_name, err_list in password_form.errors.items():
        for e in err_list:
            errors.append(e)
    flash('Password update failed: ' + ' '.join(errors) if errors else 'Ensure password meets complexity requirements.', 'danger')
    return redirect(url_for('users.profile'))
