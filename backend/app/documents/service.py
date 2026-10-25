import os
from datetime import datetime, timezone
from app import db
from app.repositories.document_repository import DocumentRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository
from app.audit.service import AuditService
from app.utils.file_handler import save_uploaded_file, delete_stored_file
from config import Config

class DocumentService:
    @staticmethod
    def upload_document(title, category, description, file_storage, owner, upload_root_folder, req=None):
        """
        Transactional upload:
        1. Validate extension & size
        2. Generate UUID filename and save file to disk
        3. Create Document and initial DocumentVersion in DB
        4. Log audit event
        If DB or file step fails -> complete rollback!
        """
        saved_info = None
        try:
            saved_info = save_uploaded_file(
                file_storage=file_storage,
                upload_root_folder=upload_root_folder,
                allowed_extensions=Config.ALLOWED_EXTENSIONS,
                max_bytes=Config.MAX_CONTENT_LENGTH
            )

            doc = DocumentRepository.create(
                title=title,
                filename=saved_info['stored_filename'],
                original_filename=saved_info['original_filename'],
                filepath=saved_info['relative_filepath'],
                subfolder=saved_info['subfolder'],
                file_type=saved_info['file_type'],
                size=saved_info['file_size'],
                category=category,
                description=description,
                owner_id=owner.id
            )

            AuditService.log_event(
                action='UPLOAD',
                user_id=owner.id,
                document_id=doc.id,
                new_value=f"title='{doc.title}', category='{doc.category}', file='{doc.original_filename}', size={doc.human_size}",
                details=f"User {owner.username} uploaded document '{doc.title}' ({doc.human_size})",
                req=req
            )

            return True, doc
        except Exception as e:
            db.session.rollback()
            if saved_info and saved_info.get('absolute_filepath'):
                delete_stored_file(saved_info['absolute_filepath'])
            return False, str(e)

    @staticmethod
    def upload_new_version(doc_id, file_storage, change_notes, user, upload_root_folder, req=None):
        """
        Create a new document version without overwriting the previous version.
        """
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=user.is_admin)
        if not doc:
            return False, "Document not found."

        if not user.can_edit_document(doc):
            return False, "Unauthorized: You do not have permission to upload new versions of this document."

        saved_info = None
        try:
            saved_info = save_uploaded_file(
                file_storage=file_storage,
                upload_root_folder=upload_root_folder,
                allowed_extensions=Config.ALLOWED_EXTENSIONS,
                max_bytes=Config.MAX_CONTENT_LENGTH
            )

            old_version = doc.version
            version_record = DocumentRepository.create_version(
                document=doc,
                filename=saved_info['stored_filename'],
                filepath=saved_info['relative_filepath'],
                file_size=saved_info['file_size'],
                uploaded_by_id=user.id,
                change_notes=change_notes
            )

            AuditService.log_event(
                action='NEW VERSION',
                user_id=user.id,
                document_id=doc.id,
                old_value=f"version={old_version}",
                new_value=f"version={doc.version}, notes='{change_notes}'",
                details=f"User {user.username} uploaded Version {doc.version} for '{doc.title}'",
                req=req
            )

            return True, version_record
        except Exception as e:
            db.session.rollback()
            if saved_info and saved_info.get('absolute_filepath'):
                delete_stored_file(saved_info['absolute_filepath'])
            return False, str(e)

    @staticmethod
    def update_document_metadata(doc_id, title, category, description, user, req=None):
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=user.is_admin)
        if not doc:
            return False, "Document not found."

        if not user.can_edit_document(doc):
            return False, "Unauthorized: You do not have permission to edit this document."

        old_meta = f"title='{doc.title}', category='{doc.category}'"
        DocumentRepository.update(
            doc,
            title=title.strip(),
            category=category,
            description=description
        )

        AuditService.log_event(
            action='EDIT',
            user_id=user.id,
            document_id=doc.id,
            old_value=old_meta,
            new_value=f"title='{doc.title}', category='{doc.category}'",
            details=f"User {user.username} updated document metadata for '{doc.title}'",
            req=req
        )

        return True, doc

    @staticmethod
    def soft_delete_document(doc_id, user, req=None):
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=True)
        if not doc:
            return False, "Document not found."

        if not user.can_delete_document(doc):
            return False, "Unauthorized: Only the document owner or an administrator can delete this document."

        if doc.status == 'Deleted':
            return False, "Document is already in Trash."

        DocumentRepository.soft_delete(doc, deleted_by_id=user.id)

        AuditService.log_event(
            action='DELETE',
            user_id=user.id,
            document_id=doc.id,
            details=f"User {user.username} moved document '{doc.title}' to Trash (soft delete)",
            req=req
        )

        return True, f"Document '{doc.title}' moved to Trash. It can be restored by an Admin or Owner."

    @staticmethod
    def restore_document(doc_id, user, req=None):
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=True)
        if not doc:
            return False, "Document not found."

        if not (user.is_admin or doc.owner_id == user.id):
            return False, "Unauthorized: Only the document owner or an administrator can restore this document."

        DocumentRepository.restore(doc)

        AuditService.log_event(
            action='RESTORE',
            user_id=user.id,
            document_id=doc.id,
            details=f"User {user.username} restored document '{doc.title}' from Trash",
            req=req
        )

        return True, f"Document '{doc.title}' has been successfully restored."

    @staticmethod
    def hard_delete_document(doc_id, user, upload_root_folder, req=None):
        if not user.is_admin:
            return False, "Unauthorized: Permanent purge is restricted to Administrators."

        doc = DocumentRepository.get_by_id(doc_id, include_deleted=True)
        if not doc:
            return False, "Document not found."

        title = doc.title

        # Delete physical files of all versions
        for v in doc.versions:
            path = os.path.join(upload_root_folder, v.filepath.replace('uploads/', ''))
            delete_stored_file(path)

        active_path = os.path.join(upload_root_folder, doc.subfolder, doc.filename)
        delete_stored_file(active_path)

        DocumentRepository.hard_delete(doc)

        AuditService.log_event(
            action='PURGE',
            user_id=user.id,
            details=f"Admin {user.username} permanently purged document '{title}' and all its versions",
            req=req
        )

        return True, f"Document '{title}' and all version files permanently purged."

    @staticmethod
    def get_document_download_info(doc_id, user, version_id=None, req=None):
        doc = DocumentRepository.get_by_id(doc_id, include_deleted=user.is_admin)
        if not doc:
            return False, "Document not found.", None, None

        has_access, _ = user.can_access_document(doc)
        if not has_access:
            return False, "Access Denied: You do not have permission to download this document.", None, None

        target_filename = doc.filename
        target_subfolder = doc.subfolder
        download_as = doc.original_filename

        if version_id:
            from app.models.document_version import DocumentVersion
            ver = db.session.get(DocumentVersion, int(version_id))
            if ver and ver.document_id == doc.id:
                target_filename = ver.filename
                download_as = f"v{ver.version_number}_{doc.original_filename}"

        AuditService.log_event(
            action='DOWNLOAD',
            user_id=user.id,
            document_id=doc.id,
            details=f"User {user.username} downloaded '{download_as}'",
            req=req
        )

        return True, None, target_subfolder, target_filename, download_as

    @staticmethod
    def search_documents(user, query_text=None, category=None, file_type=None, upload_date=None, status='Active'):
        accessible_ids = []
        if not user.is_admin:
            perms = PermissionRepository.get_for_user(user.id, include_expired=False)
            accessible_ids = [p.document_id for p in perms]

        return DocumentRepository.search(
            query_text=query_text,
            category=category,
            file_type=file_type,
            upload_date=upload_date,
            status=status,
            accessible_doc_ids=accessible_ids,
            user=user
        )

    @staticmethod
    def get_documents_for_user(user, view_mode='all', category=None):
        if user.is_admin:
            if view_mode == 'my':
                docs = DocumentRepository.get_by_owner(user.id, include_deleted=False)
            else:
                docs = DocumentRepository.get_all(include_deleted=False)
        elif user.is_viewer:
            perms = PermissionRepository.get_for_user(user.id, include_expired=False)
            doc_ids = [p.document_id for p in perms]
            docs = [DocumentRepository.get_by_id(did) for did in doc_ids if DocumentRepository.get_by_id(did)]
        else:  # Owner
            if view_mode == 'my':
                docs = DocumentRepository.get_by_owner(user.id, include_deleted=False)
            elif view_mode == 'shared':
                perms = PermissionRepository.get_for_user(user.id, include_expired=False)
                doc_ids = [p.document_id for p in perms]
                docs = [DocumentRepository.get_by_id(did) for did in doc_ids if DocumentRepository.get_by_id(did)]
            else:
                perms = PermissionRepository.get_for_user(user.id, include_expired=False)
                doc_ids = [p.document_id for p in perms]
                my_docs = DocumentRepository.get_by_owner(user.id, include_deleted=False)
                shared_docs = [DocumentRepository.get_by_id(did) for did in doc_ids if DocumentRepository.get_by_id(did)]
                # Unique union
                seen = set()
                docs = []
                for d in my_docs + shared_docs:
                    if d.id not in seen:
                        seen.add(d.id)
                        docs.append(d)

        if category:
            docs = [d for d in docs if d.category == category]

        return docs

    @staticmethod
    def get_trash_documents(user):
        return DocumentRepository.get_trash(user=user)
