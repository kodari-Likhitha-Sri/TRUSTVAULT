from datetime import datetime, timezone
from flask import request
from app import db
from app.utils.device_detector import get_client_ip, get_device_info

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True, index=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    device = db.Column(db.String(50), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Legacy compatibility fields
    details = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    @classmethod
    def log(cls, action, details='', user_id=None, document_id=None, old_value=None, new_value=None, req=None):
        r = req or (request if request else None)
        ip = get_client_ip(r)
        device, browser = get_device_info(r)

        entry = cls(
            user_id=user_id,
            action=action,
            document_id=document_id,
            old_value=old_value,
            new_value=new_value or details,
            details=details or new_value,
            ip_address=ip,
            device=device,
            browser=browser,
            created_at=datetime.now(timezone.utc),
            time=datetime.now(timezone.utc)
        )
        try:
            db.session.add(entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return entry

    def __repr__(self):
        return f'<ActivityLog {self.action} user:{self.user_id} at {self.created_at}>'
