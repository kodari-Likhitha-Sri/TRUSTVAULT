from datetime import datetime, timezone
from app import db
from app.models.notification import Notification

class NotificationRepository:
    @staticmethod
    def create(user_id, title, message, link=None):
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        try:
            db.session.add(notif)
            db.session.commit()
            return notif
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def get_for_user(user_id, limit=20, unread_only=False):
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_as_read(notif_id):
        notif = db.session.get(Notification, int(notif_id))
        if notif:
            notif.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return True
