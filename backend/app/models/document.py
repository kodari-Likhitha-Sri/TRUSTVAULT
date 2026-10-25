from datetime import datetime, timezone
import os
from app import db
from app.utils.helpers import format_file_size, get_file_icon

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=True)
    subfolder = db.Column(db.String(20), nullable=False, default='docs')  # 'pdf', 'images', 'docs', 'ppt'
    file_type = db.Column(db.String(20), nullable=False)  # 'pdf', 'docx', 'png', etc.
    size = db.Column(db.Integer, default=0)
    file_size = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default='Active', nullable=False, index=True)  # 'Active', 'Deleted'
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    deleter = db.relationship('User', foreign_keys=[deleted_by], backref='deleted_documents', lazy=True)
    permissions = db.relationship('Permission', backref='document', lazy=True, cascade='all, delete-orphan')
    versions = db.relationship(
        'DocumentVersion',
        backref='document',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='DocumentVersion.version_number.desc()'
    )

    @property
    def file_path(self):
        """Relative path from static directory"""
        if self.filepath:
            return self.filepath.replace('\\', '/')
        return os.path.join('uploads', self.subfolder, self.filename).replace('\\', '/')

    @property
    def effective_size(self):
        return self.size or self.file_size or 0

    @property
    def human_size(self):
        return format_file_size(self.effective_size)

    @property
    def icon_class(self):
        return get_file_icon(self.file_type)

    @property
    def is_deleted(self):
        return self.status.lower() == 'deleted'

    def __repr__(self):
        return f'<Document {self.title} (v{self.version}, {self.category}, {self.status})>'
