import os
import sys

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from datetime import datetime, timezone
from app import create_app, db
from app.models import User, ActivityLog

def seed_database():
    """
    Seeds initial user accounts only if database has no users.
    No default documents are seeded (documents are uploaded manually by Admin and Owner).
    """
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.first():
            print("Database already contains user accounts. Skipping user seeding.")
            return

        print("Seeding TrustVault demo user accounts (zero default documents seeded)...")

        # Create Standard Demo Users
        admin = User(
            username='admin',
            email='admin@trustvault.com',
            role='Admin',
            department='Security Operations',
            status='Active'
        )
        admin.set_password('Admin@123')

        owner = User(
            username='sarah_owner',
            email='owner@trustvault.com',
            role='Owner',
            department='Finance',
            status='Active'
        )
        owner.set_password('Owner@123')

        viewer = User(
            username='david_viewer',
            email='viewer@trustvault.com',
            role='Viewer',
            department='General',
            status='Active'
        )
        viewer.set_password('Viewer@123')

        alex = User(
            username='alex_analyst',
            email='alex@trustvault.com',
            role='Owner',
            department='Engineering',
            status='Active'
        )
        alex.set_password('Alex@123')

        db.session.add_all([admin, owner, viewer, alex])
        db.session.commit()

        # Initial System Activity Logs
        logs = [
            ActivityLog(user_id=admin.id, action='SYSTEM_INIT', details='TrustVault system environment configured and operational', ip_address='127.0.0.1'),
            ActivityLog(user_id=admin.id, action='REGISTRATION', details='System Administrator account initialized', ip_address='127.0.0.1'),
            ActivityLog(user_id=owner.id, action='REGISTRATION', details='Sarah (Owner) account registered', ip_address='127.0.0.1'),
            ActivityLog(user_id=viewer.id, action='REGISTRATION', details='David (Viewer) account registered', ip_address='127.0.0.1'),
        ]
        db.session.add_all(logs)
        db.session.commit()

        print("TrustVault demo users seeded successfully!")
        print("Note: In accordance with system policy, no default documents are seeded.")
        print("Admin and Owner accounts should upload documents through the web interface.")
        print("\nAccounts:")
        print("1. Admin:  admin@trustvault.com   | Pass: Admin@123")
        print("2. Owner:  owner@trustvault.com   | Pass: Owner@123")
        print("3. Viewer: viewer@trustvault.com  | Pass: Viewer@123")

if __name__ == '__main__':
    seed_database()
