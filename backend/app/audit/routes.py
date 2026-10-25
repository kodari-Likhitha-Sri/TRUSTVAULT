from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from flask_login import login_required, current_user
import csv
import io
from app.decorators.auth import admin_required
from app.audit.service import AuditService
from app.repositories.user_repository import UserRepository

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs')
@login_required
@admin_required
def logs():
    action_filter = request.args.get('action', '').strip().upper()
    user_filter = request.args.get('user_id', type=int)

    all_logs = AuditService.get_audit_trail(limit=250, user_id=user_filter, action=action_filter or None)
    users = UserRepository.get_all()

    return render_template(
        'logs.html',
        logs=all_logs,
        users=users,
        selected_action=action_filter,
        selected_user=user_filter
    )

@audit_bp.route('/logs/export')
@login_required
@admin_required
def export_logs():
    all_logs = AuditService.get_audit_trail(limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'User', 'Action', 'Details', 'IP Address', 'Device', 'Browser'])

    for log in all_logs:
        username = log.user.username if log.user else 'System'
        time_str = log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
        details = log.new_value or log.details or ''
        writer.writerow([log.id, time_str, username, log.action, details, log.ip_address, log.device, log.browser])

    output.seek(0)
    AuditService.log_event('AUDIT EXPORT', user_id=current_user.id, details='Exported system audit logs to CSV', req=request)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=trustvault_audit_logs.csv"}
    )
