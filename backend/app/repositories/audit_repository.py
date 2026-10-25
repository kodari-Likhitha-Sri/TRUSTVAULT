from datetime import datetime, timezone
from app import db
from app.models.activity_log import ActivityLog

class AuditRepository:
    @staticmethod
    def create_log(action, user_id=None, document_id=None, old_value=None, new_value=None, ip_address=None, device=None, browser=None, details=None):
        now = datetime.now(timezone.utc)
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            document_id=document_id,
            old_value=old_value,
            new_value=new_value or details,
            details=details or new_value,
            ip_address=ip_address or '127.0.0.1',
            device=device or 'Desktop',
            browser=browser or 'Browser',
            created_at=now,
            time=now
        )
        try:
            db.session.add(entry)
            db.session.commit()
            return entry
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def get_recent(limit=100, user_id=None, document_id=None, action=None):
        query = ActivityLog.query
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if document_id:
            query = query.filter(ActivityLog.document_id == document_id)
        if action:
            query = query.filter(ActivityLog.action == action)
        return query.order_by(ActivityLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def count():
        return ActivityLog.query.count()
