from datetime import datetime, timezone
from app import db

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission = db.Column(db.String(20), nullable=False, default='READ')  # 'READ', 'EDIT', 'DELETE'
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    granted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'user_id', name='unique_doc_user_permission'),
    )

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        # Normalize timezone-naive or timezone-aware
        exp = self.expires_at
        now = datetime.now(timezone.utc)
        if exp.tzinfo is None:
            now = datetime.utcnow()
        return exp < now

    def __repr__(self):
        return f'<Permission doc:{self.document_id} user:{self.user_id} {self.permission}>'
