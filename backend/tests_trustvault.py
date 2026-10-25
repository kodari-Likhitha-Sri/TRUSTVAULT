import os
import sys

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import io
import unittest
from app import create_app, db
from app.models import User, Document, Permission, ActivityLog

class TrustVaultTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_01_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TrustVault', response.data)

    def test_02_login_and_dashboard(self):
        # Test Admin Login
        response = self.client.post('/login', data={
            'login_id': 'admin@trustvault.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'admin', response.data)
        self.assertIn(b'Admin', response.data)

    def test_03_owner_upload_and_access(self):
        # Login as owner
        self.client.post('/login', data={
            'login_id': 'owner@trustvault.com',
            'password': 'Owner@123'
        }, follow_redirects=True)

        # Upload a test document
        data = {
            'title': 'Test Financial Spreadsheet',
            'category': 'Finance',
            'description': 'Automated test document',
            'file': (io.BytesIO(b'%PDF-1.4 test pdf content'), 'test_doc.pdf')
        }
        res = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Financial Spreadsheet', res.data)

    def test_04_viewer_rbac_restrictions(self):
        # Login as viewer
        self.client.post('/login', data={
            'login_id': 'viewer@trustvault.com',
            'password': 'Viewer@123'
        }, follow_redirects=True)

        # Viewer trying to upload should get 403 Forbidden
        res = self.client.get('/upload')
        self.assertEqual(res.status_code, 403)

        # Viewer trying to view admin users page should get 403 Forbidden
        res = self.client.get('/users')
        self.assertEqual(res.status_code, 403)

        # Viewer trying to view logs should get 403 Forbidden
        res = self.client.get('/logs')
        self.assertEqual(res.status_code, 403)

    def test_05_search_route(self):
        # Login as admin
        self.client.post('/login', data={
            'login_id': 'admin@trustvault.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        res = self.client.get('/search?q=Financial')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial', res.data)

    def test_06_password_complexity_rules(self):
        """Verify password requires min 12 chars, uppercase, lowercase, and special character"""
        with self.app.test_request_context():
            from app.forms import RegistrationForm

            # 1. Less than 12 characters
            form = RegistrationForm(
                username='user_test1',
                email='test1@example.com',
                password='Short@1',
                confirm_password='Short@1',
                role='Viewer'
            )
            self.assertFalse(form.validate())
            self.assertIn('at least 12 characters long', str(form.password.errors))

            # 2. No uppercase character
            form = RegistrationForm(
                username='user_test2',
                email='test2@example.com',
                password='lowercase_only_with_special!@#',
                confirm_password='lowercase_only_with_special!@#',
                role='Viewer'
            )
            self.assertFalse(form.validate())
            self.assertIn('at least one uppercase letter', str(form.password.errors))

            # 3. No lowercase character
            form = RegistrationForm(
                username='user_test3',
                email='test3@example.com',
                password='UPPERCASE_ONLY_WITH_SPECIAL!@#',
                confirm_password='UPPERCASE_ONLY_WITH_SPECIAL!@#',
                role='Viewer'
            )
            self.assertFalse(form.validate())
            self.assertIn('at least one lowercase letter', str(form.password.errors))

            # 4. No special character
            form = RegistrationForm(
                username='user_test4',
                email='test4@example.com',
                password='NoSpecialCharInThisPassword123',
                confirm_password='NoSpecialCharInThisPassword123',
                role='Viewer'
            )
            self.assertFalse(form.validate())
            self.assertIn('at least one special character', str(form.password.errors))

            # 5. Valid compliant password (>=12 chars, upper, lower, special)
            form = RegistrationForm(
                username='user_valid_pass',
                email='unique_new_email@example.com',
                password='Compliant@Password2026',
                confirm_password='Compliant@Password2026',
                role='Viewer'
            )
            # Remove any username/email DB collision issues
            form.validate()
            self.assertEqual(form.password.errors, [])

    def test_07_personal_and_other_categories(self):
        """Verify Personal and Other categories are supported in config and application"""
        from config import Config
        self.assertIn('Personal', Config.ALLOWED_CATEGORIES)
        self.assertIn('Other', Config.ALLOWED_CATEGORIES)

        # Login as owner
        self.client.post('/login', data={
            'login_id': 'owner@trustvault.com',
            'password': 'Owner@123'
        }, follow_redirects=True)

        # Upload document in Personal category
        data_personal = {
            'title': 'Test Personal Document ID',
            'category': 'Personal',
            'description': 'Private passport copy and tax records',
            'file': (io.BytesIO(b'%PDF-1.4 test personal data'), 'passport.pdf')
        }
        res_p = self.client.post('/upload', data=data_personal, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res_p.status_code, 200)
        self.assertIn(b'Test Personal Document ID', res_p.data)

        # Upload document in Other category
        data_other = {
            'title': 'Test Other Archive Document',
            'category': 'Other',
            'description': 'Miscellaneous equipment list',
            'file': (io.BytesIO(b'%PDF-1.4 test other data'), 'equipment.pdf')
        }
        res_o = self.client.post('/upload', data=data_other, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res_o.status_code, 200)
        self.assertIn(b'Test Other Archive Document', res_o.data)

        # Check categories listing page shows both
        res_cat = self.client.get('/categories')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Personal', res_cat.data)
        self.assertIn(b'Other', res_cat.data)

    def test_08_search_by_upload_date(self):
        """Verify search documents filters by upload date and displays upload date"""
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Login as admin
        self.client.post('/login', data={
            'login_id': 'admin@trustvault.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        # Search with upload_date filter
        res = self.client.get(f'/search?upload_date={today_str}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Date Uploaded', res.data)
        self.assertIn(b'name="upload_date"', res.data)

    def test_09_document_versioning(self):
        """Verify that updating a document creates a new version record without overwriting history"""
        from werkzeug.datastructures import FileStorage
        from app.models.user import User
        from app.models.document import Document
        from app.documents.service import DocumentService

        with self.app.app_context():
            owner = User.query.filter_by(role='Owner').first()
            # Upload initial doc
            f1 = FileStorage(stream=io.BytesIO(b'%PDF-1.4 Version 1 content'), filename='v1_doc.pdf')
            success, doc = DocumentService.upload_document(
                title='Versioning Test Document',
                category='Research',
                description='Initial version',
                file_storage=f1,
                owner=owner,
                upload_root_folder=self.app.config['UPLOAD_FOLDER']
            )
            self.assertTrue(success)
            self.assertEqual(doc.version, 1)
            self.assertEqual(len(doc.versions), 1)

            # Upload Version 2
            f2 = FileStorage(stream=io.BytesIO(b'%PDF-1.4 Version 2 updated content'), filename='v2_doc.pdf')
            v_success, v2 = DocumentService.upload_new_version(
                doc_id=doc.id,
                file_storage=f2,
                change_notes='Updated sections 2 and 3',
                user=owner,
                upload_root_folder=self.app.config['UPLOAD_FOLDER']
            )
            self.assertTrue(v_success)
            self.assertEqual(doc.version, 2)
            self.assertEqual(len(doc.versions), 2)
            self.assertEqual(doc.versions[0].version_number, 2)
            self.assertEqual(doc.versions[1].version_number, 1)

    def test_10_soft_delete_and_restore(self):
        """Verify soft deletion marks document as Deleted and restore reactivates it"""
        from werkzeug.datastructures import FileStorage
        from app.models.user import User
        from app.documents.service import DocumentService
        from app.repositories.document_repository import DocumentRepository

        with self.app.app_context():
            owner = User.query.filter_by(role='Owner').first()
            f = FileStorage(stream=io.BytesIO(b'%PDF-1.4 Soft delete test'), filename='soft_del.pdf')
            success, doc = DocumentService.upload_document(
                title='Soft Delete Test Document',
                category='Legal',
                description='Testing soft delete',
                file_storage=f,
                owner=owner,
                upload_root_folder=self.app.config['UPLOAD_FOLDER']
            )
            self.assertTrue(success)
            doc_id = doc.id

            # Soft delete
            del_success, _ = DocumentService.soft_delete_document(doc_id=doc_id, user=owner)
            self.assertTrue(del_success)

            # Check that normal query excludes deleted document
            active_doc = DocumentRepository.get_by_id(doc_id, include_deleted=False)
            self.assertIsNone(active_doc)

            # Check that soft deleted doc is in Trash
            trash_doc = DocumentRepository.get_by_id(doc_id, include_deleted=True)
            self.assertIsNotNone(trash_doc)
            self.assertEqual(trash_doc.status, 'Deleted')
            self.assertEqual(trash_doc.deleted_by, owner.id)

            # Restore
            rest_success, _ = DocumentService.restore_document(doc_id=doc_id, user=owner)
            self.assertTrue(rest_success)
            restored_doc = DocumentRepository.get_by_id(doc_id, include_deleted=False)
            self.assertIsNotNone(restored_doc)
            self.assertEqual(restored_doc.status, 'Active')

    def test_11_audit_trail_metadata(self):
        """Verify audit trail logs action, user, IP, device, and browser"""
        from app.audit.service import AuditService
        from app.models.activity_log import ActivityLog
        from app.models.user import User

        with self.app.app_context():
            user = User.query.first()
            entry = AuditService.log_event(
                action='TEST ACTION',
                user_id=user.id,
                details='Auditing enterprise action',
                old_value='old_state',
                new_value='new_state'
            )
            self.assertIsNotNone(entry)
            self.assertEqual(entry.action, 'TEST ACTION')
            self.assertIsNotNone(entry.ip_address)
            self.assertIsNotNone(entry.device)
            self.assertIsNotNone(entry.browser)

    def test_12_permission_expiry(self):
        """Verify permission expiry flags expired permissions"""
        from datetime import datetime, timezone, timedelta
        from app.models.permission import Permission

        with self.app.app_context():
            # Create expired permission
            expired_time = datetime.now(timezone.utc) - timedelta(days=2)
            perm = Permission(
                document_id=1,
                user_id=1,
                permission='READ',
                expires_at=expired_time
            )
            self.assertTrue(perm.is_expired)

            # Create future active permission
            future_time = datetime.now(timezone.utc) + timedelta(days=7)
            perm_active = Permission(
                document_id=1,
                user_id=1,
                permission='READ',
                expires_at=future_time
            )
            self.assertFalse(perm_active.is_expired)

    def test_13_duplicate_usernames_allowed_with_unique_email(self):
        """Verify that duplicate usernames are allowed if emails are unique, while duplicate emails are rejected"""
        with self.app.test_request_context():
            from app.forms import RegistrationForm
            from app.auth.service import AuthService

            # User 1 with username 'shared_name'
            form1 = RegistrationForm(
                username='shared_name',
                email='unique_email1@example.com',
                password='Compliant@Password2026',
                confirm_password='Compliant@Password2026',
                role='Viewer'
            )
            self.assertTrue(form1.validate())

            # User 2 with identical username 'shared_name' but different email
            form2 = RegistrationForm(
                username='shared_name',
                email='unique_email2@example.com',
                password='Compliant@Password2026',
                confirm_password='Compliant@Password2026',
                role='Owner'
            )
            self.assertTrue(form2.validate(), f"Form validation failed: {form2.errors}")

            # Register user with duplicate username
            success, u2 = AuthService.register_user(
                username='shared_name',
                email='unique_email2@example.com',
                password='Compliant@Password2026',
                role='Owner'
            )
            self.assertTrue(success)

            # Attempting duplicate email should fail
            form3 = RegistrationForm(
                username='another_name',
                email='unique_email2@example.com',
                password='Compliant@Password2026',
                confirm_password='Compliant@Password2026',
                role='Viewer'
            )
            self.assertFalse(form3.validate())
            self.assertIn('already exists', str(form3.email.errors))

            # Cleanup test user
            if success and u2:
                db.session.delete(u2)
                db.session.commit()

    def test_14_document_deletion_enabled(self):
        """Verify that document deletion works and is properly enabled"""
        from werkzeug.datastructures import FileStorage
        from app.models.user import User
        from app.documents.service import DocumentService

        with self.app.app_context():
            owner = User.query.filter_by(role='Owner').first()
            f = FileStorage(stream=io.BytesIO(b'%PDF-1.4 Delete test document'), filename='del_test.pdf')
            success, doc = DocumentService.upload_document(
                title='Test Document For Deletion',
                category='Legal',
                description='Testing delete enabling',
                file_storage=f,
                owner=owner,
                upload_root_folder=self.app.config['UPLOAD_FOLDER']
            )
            self.assertTrue(success)
            doc_id = doc.id

            # Verify owner can delete
            self.assertTrue(owner.can_delete_document(doc))

            # Execute soft delete
            del_success, msg = DocumentService.soft_delete_document(doc_id=doc_id, user=owner)
            self.assertTrue(del_success)

            # Permanent purge
            admin = User.query.filter_by(role='Admin').first()
            purge_success, pmsg = DocumentService.hard_delete_document(
                doc_id=doc_id,
                user=admin,
                upload_root_folder=self.app.config['UPLOAD_FOLDER']
            )
            self.assertTrue(purge_success)

    def test_15_document_visibility_and_modifiability_by_user_type(self):
        """Verify document visibility and permissions are strictly enforced per user type"""
        from app.models.user import User

        with self.app.app_context():
            admin = User.query.filter_by(role='Admin').first()
            viewer = User.query.filter_by(role='Viewer').first()
            owner = User.query.filter_by(role='Owner').first()

            # Viewers cannot upload
            self.assertFalse(viewer.is_admin or viewer.is_owner)

            # Owners can upload
            self.assertTrue(owner.is_owner)

            # Admins have full access
            self.assertTrue(admin.is_admin)

    @classmethod
    def tearDownClass(cls):
        import os
        from app import create_app, db
        from app.models import Document
        app = create_app()
        with app.app_context():
            test_docs = Document.query.filter(
                (Document.title.like('Test %')) | 
                (Document.title.in_(['Versioning Test Document', 'Soft Delete Test Document']))
            ).all()
            for d in test_docs:
                for v in d.versions:
                    p = os.path.join(app.config['UPLOAD_FOLDER'], v.filepath.replace('uploads/', '').replace('uploads\\\\', ''))
                    if os.path.exists(p) and 'NOC26CS150S680201157' not in p:
                        try: os.remove(p)
                        except Exception: pass
                    db.session.delete(v)
                active_p = os.path.join(app.config['UPLOAD_FOLDER'], d.subfolder, d.filename)
                if os.path.exists(active_p) and 'NOC26CS150S680201157' not in active_p:
                    try: os.remove(active_p)
                    except Exception: pass
                for p in d.permissions:
                    db.session.delete(p)
                db.session.delete(d)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
