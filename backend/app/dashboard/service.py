from datetime import datetime, timezone
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.audit_repository import AuditRepository
from app.models.document import Document
from app.models.permission import Permission
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.utils.helpers import format_file_size
from config import Config

class DashboardService:
    @staticmethod
    def get_dashboard_metrics(user):
        """
        Aggregate enterprise dashboard metrics tailored for Admin, Owner, and Viewer roles.
        """
        total_users = UserRepository.count()
        total_docs = DocumentRepository.count(status='Active')
        total_shares = Permission.query.count()

        my_docs = DocumentRepository.get_by_owner(user.id, include_deleted=False)

        shared_perms = PermissionRepository.get_for_user(user.id, include_expired=False)
        shared_doc_ids = [p.document_id for p in shared_perms]
        shared_docs = [DocumentRepository.get_by_id(did) for did in shared_doc_ids if DocumentRepository.get_by_id(did)]

        # Category breakdown
        category_counts = {}
        for cat in Config.ALLOWED_CATEGORIES:
            if user.is_admin:
                cnt = Document.query.filter_by(category=cat, status='Active').count()
            elif user.is_owner:
                cnt = Document.query.filter_by(owner_id=user.id, category=cat, status='Active').count()
            else:
                cnt = len([d for d in shared_docs if d.category == cat])
            category_counts[cat] = cnt

        # Recent activities
        if user.is_admin:
            recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
        else:
            recent_activities = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.created_at.desc()).limit(6).all()

        roles_breakdown = {
            'Admin': User.query.filter_by(role='Admin').count(),
            'Owner': User.query.filter_by(role='Owner').count(),
            'Viewer': User.query.filter_by(role='Viewer').count(),
        }

        storage_used_bytes = user.get_storage_used_bytes()
        storage_quota_bytes = 100 * 1024 * 1024
        storage_percentage = min(100, round((storage_used_bytes / storage_quota_bytes) * 100, 1))

        if user.is_admin:
            shared_by_me_count = Permission.query.count()
        else:
            shared_by_me_count = Permission.query.join(Document).filter(Document.owner_id == user.id).count()

        return {
            'total_users': total_users,
            'total_docs': total_docs,
            'total_shares': total_shares,
            'shared_by_me_count': shared_by_me_count,
            'my_docs': my_docs,
            'shared_docs': shared_docs,
            'shared_perms': {p.document_id: p.permission for p in shared_perms},
            'category_counts': category_counts,
            'recent_activities': recent_activities,
            'roles_breakdown': roles_breakdown,
            'storage_used': format_file_size(storage_used_bytes),
            'storage_percentage': storage_percentage,
            'categories': Config.ALLOWED_CATEGORIES
        }
