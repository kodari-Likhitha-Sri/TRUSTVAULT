from datetime import datetime, timezone, time
from sqlalchemy import or_, cast, String
from app import db
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.user import User

class DocumentRepository:
    @staticmethod
    def get_by_id(doc_id, include_deleted=False):
        if not doc_id:
            return None
        doc = db.session.get(Document, int(doc_id))
        if doc and not include_deleted and doc.status == 'Deleted':
            return None
        return doc

    @staticmethod
    def get_by_owner(owner_id, include_deleted=False):
        query = Document.query.filter_by(owner_id=owner_id)
        if not include_deleted:
            query = query.filter(Document.status == 'Active')
        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_by_category(category, include_deleted=False):
        query = Document.query.filter_by(category=category)
        if not include_deleted:
            query = query.filter(Document.status == 'Active')
        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_all(include_deleted=False):
        query = Document.query
        if not include_deleted:
            query = query.filter(Document.status == 'Active')
        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_trash(user=None):
        query = Document.query.filter(Document.status == 'Deleted')
        if user and not user.is_admin:
            query = query.filter(Document.owner_id == user.id)
        return query.order_by(Document.deleted_at.desc()).all()

    @staticmethod
    def search(query_text=None, category=None, file_type=None, upload_date=None, status='Active', accessible_doc_ids=None, user=None):
        query = Document.query

        if status:
            query = query.filter(Document.status == status)

        # RBAC scope restriction if provided
        if user and not user.is_admin:
            if accessible_doc_ids is not None:
                query = query.filter(
                    or_(Document.owner_id == user.id, Document.id.in_(accessible_doc_ids))
                )
            else:
                query = query.filter(Document.owner_id == user.id)

        if query_text:
            query = query.join(User, Document.owner_id == User.id).filter(
                or_(
                    Document.title.ilike(f"%{query_text}%"),
                    Document.original_filename.ilike(f"%{query_text}%"),
                    Document.description.ilike(f"%{query_text}%"),
                    User.username.ilike(f"%{query_text}%"),
                    cast(Document.created_at, String).ilike(f"%{query_text}%")
                )
            )

        if category:
            query = query.filter(Document.category == category)

        if file_type:
            query = query.filter(Document.file_type == file_type.lower())

        if upload_date:
            try:
                target_date = datetime.strptime(upload_date, '%Y-%m-%d').date()
                start_dt = datetime.combine(target_date, time.min)
                end_dt = datetime.combine(target_date, time.max)
                query = query.filter(Document.created_at >= start_dt, Document.created_at <= end_dt)
            except ValueError:
                pass

        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def create(title, filename, original_filename, filepath, subfolder, file_type, size, category, description, owner_id):
        now = datetime.now(timezone.utc)
        doc = Document(
            title=title.strip(),
            filename=filename,
            original_filename=original_filename,
            filepath=filepath,
            subfolder=subfolder,
            file_type=file_type.lower(),
            size=size,
            file_size=size,
            category=category,
            description=description,
            owner_id=owner_id,
            version=1,
            status='Active',
            created_at=now,
            updated_at=now,
            upload_date=now
        )
        db.session.add(doc)
        db.session.flush()  # Populates doc.id

        # Automatically create initial Version 1 record in DocumentVersion
        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            uploaded_by=owner_id,
            filename=filename,
            filepath=filepath,
            file_size=size,
            change_notes='Initial upload',
            uploaded_at=now
        )
        db.session.add(v1)
        db.session.commit()
        return doc

    @staticmethod
    def create_version(document, filename, filepath, file_size, uploaded_by_id, change_notes=None):
        now = datetime.now(timezone.utc)
        new_version_num = (document.version or 1) + 1

        version_record = DocumentVersion(
            document_id=document.id,
            version_number=new_version_num,
            uploaded_by=uploaded_by_id,
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            change_notes=change_notes or f'Version {new_version_num} update',
            uploaded_at=now
        )
        db.session.add(version_record)

        # Update active document metadata to point to newest version
        document.version = new_version_num
        document.filename = filename
        document.filepath = filepath
        document.size = file_size
        document.file_size = file_size
        document.updated_at = now
        db.session.commit()
        return version_record

    @staticmethod
    def update(document, **kwargs):
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        document.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return document

    @staticmethod
    def soft_delete(document, deleted_by_id):
        document.status = 'Deleted'
        document.deleted_by = deleted_by_id
        document.deleted_at = datetime.now(timezone.utc)
        document.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return document

    @staticmethod
    def restore(document):
        document.status = 'Active'
        document.deleted_by = None
        document.deleted_at = None
        document.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return document

    @staticmethod
    def hard_delete(document):
        db.session.delete(document)
        db.session.commit()
        return True

    @staticmethod
    def count(status='Active'):
        query = Document.query
        if status:
            query = query.filter(Document.status == status)
        return query.count()

    @staticmethod
    def count_today_uploads():
        today = datetime.now(timezone.utc).date()
        start = datetime.combine(today, time.min)
        return Document.query.filter(
            Document.status == 'Active',
            Document.created_at >= start
        ).count()
