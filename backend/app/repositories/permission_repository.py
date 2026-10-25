from datetime import datetime, timezone
from app import db
from app.models.permission import Permission

class PermissionRepository:
    @staticmethod
    def get_by_id(perm_id):
        if not perm_id:
            return None
        return db.session.get(Permission, int(perm_id))

    @staticmethod
    def get_by_doc_and_user(doc_id, user_id):
        return Permission.query.filter_by(document_id=doc_id, user_id=user_id).first()

    @staticmethod
    def get_for_user(user_id, include_expired=False):
        perms = Permission.query.filter_by(user_id=user_id).all()
        if not include_expired:
            perms = [p for p in perms if not p.is_expired]
        return perms

    @staticmethod
    def get_for_document(doc_id, include_expired=False):
        perms = Permission.query.filter_by(document_id=doc_id).all()
        if not include_expired:
            perms = [p for p in perms if not p.is_expired]
        return perms

    @staticmethod
    def upsert(doc_id, user_id, permission_type, granted_by_id=None, expires_at=None):
        perm = Permission.query.filter_by(document_id=doc_id, user_id=user_id).first()
        now = datetime.now(timezone.utc)
        if perm:
            perm.permission = permission_type
            perm.granted_by = granted_by_id
            perm.granted_at = now
            perm.expires_at = expires_at
        else:
            perm = Permission(
                document_id=doc_id,
                user_id=user_id,
                permission=permission_type,
                granted_by=granted_by_id,
                granted_at=now,
                expires_at=expires_at
            )
            db.session.add(perm)
        db.session.commit()
        return perm

    @staticmethod
    def delete(perm):
        db.session.delete(perm)
        db.session.commit()
        return True

    @staticmethod
    def delete_by_doc_and_user(doc_id, user_id):
        perm = Permission.query.filter_by(document_id=doc_id, user_id=user_id).first()
        if perm:
            db.session.delete(perm)
            db.session.commit()
            return True
        return False
