from app.repositories.permission_repository import PermissionRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.notification_repository import NotificationRepository
from app.audit.service import AuditService

class PermissionService:
    @staticmethod
    def grant_permission(granter, doc_id, recipient_id, permission_type='READ', expires_at=None, req=None):
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=granter.is_admin)
        if not doc:
            return False, "Document not found."

        if not (granter.is_admin or doc.owner_id == granter.id):
            return False, "Unauthorized: Only the document owner or an administrator can grant access."

        if doc.owner_id == recipient_id:
            return False, "The document owner already has full administrative access."

        recipient = UserRepository.get_by_id(recipient_id)
        if not recipient:
            return False, "Recipient user not found."

        perm = PermissionRepository.upsert(
            doc_id=doc.id,
            user_id=recipient.id,
            permission_type=permission_type.upper(),
            granted_by_id=granter.id,
            expires_at=expires_at
        )

        # Notify recipient
        NotificationRepository.create(
            user_id=recipient.id,
            title=f"New Document Shared: {doc.title}",
            message=f"{granter.username} granted you {permission_type.upper()} access to '{doc.title}'.",
            link=f"/documents/{doc.id}"
        )

        expiry_note = f", expires on {expires_at.strftime('%Y-%m-%d')}" if expires_at else ", permanent"
        AuditService.log_event(
            action='SHARE',
            user_id=granter.id,
            document_id=doc.id,
            new_value=f"recipient={recipient.username}, permission={permission_type.upper()}{expiry_note}",
            details=f"{granter.username} granted {permission_type.upper()} to {recipient.username} on '{doc.title}'",
            req=req
        )

        return True, f"Successfully granted {permission_type.upper()} access to {recipient.username}."

    @staticmethod
    def revoke_permission(user, perm_id, req=None):
        perm = PermissionRepository.get_by_id(perm_id)
        if not perm:
            return False, "Permission record not found."

        doc = perm.document
        if not doc:
            PermissionRepository.delete(perm)
            return True, "Permission removed."

        if not (user.is_admin or doc.owner_id == user.id):
            return False, "Unauthorized: Only the document owner or an administrator can revoke access."

        target_username = perm.user.username if perm.user else 'Unknown'
        doc_title = doc.title

        PermissionRepository.delete(perm)

        # Notify recipient if available
        if perm.user_id:
            NotificationRepository.create(
                user_id=perm.user_id,
                title=f"Access Revoked: {doc_title}",
                message=f"Your access to '{doc_title}' has been revoked by {user.username}."
            )

        AuditService.log_event(
            action='REMOVE ACCESS',
            user_id=user.id,
            document_id=doc.id,
            details=f"{user.username} revoked {perm.permission} access from {target_username} for '{doc_title}'",
            req=req
        )

        return True, f"Access for {target_username} has been revoked."

    @staticmethod
    def get_permissions_for_document(doc_id):
        return PermissionRepository.get_for_document(doc_id, include_expired=True)

    @staticmethod
    def get_shared_with_user(user_id):
        return PermissionRepository.get_for_user(user_id, include_expired=False)
