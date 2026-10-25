from datetime import datetime, timezone
import os
from app import db
from app.utils.helpers import format_file_size

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    change_notes = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='versions_uploaded', lazy=True)

    @property
    def human_size(self):
        return format_file_size(self.file_size)

    @property
    def file_path(self):
        return self.filepath.replace('\\', '/')

    def __repr__(self):
        return f'<DocumentVersion doc:{self.document_id} v:{self.version_number}>'
