from datetime import datetime, timezone
from app import db
from app.models.user import User

class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        if not user_id:
            return None
        return db.session.get(User, int(user_id))

    @staticmethod
    def get_by_email(email):
        if not email:
            return None
        return User.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def get_by_username(username):
        if not username:
            return None
        return User.query.filter_by(username=username.strip()).first()

    @staticmethod
    def get_by_login_id(login_id):
        if not login_id:
            return None
        clean_id = login_id.strip()
        return User.query.filter(
            (User.email == clean_id.lower()) | (User.username == clean_id)
        ).first()

    @staticmethod
    def get_all(status=None, role=None, department=None):
        query = User.query
        if status:
            query = query.filter(User.status == status)
        if role:
            query = query.filter(User.role == role)
        if department:
            query = query.filter(User.department == department)
        return query.order_by(User.created_at.desc()).all()

    @staticmethod
    def create(username, email, password, role='Owner', department='General', status='Active'):
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            role=role,
            department=department,
            status=status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user, **kwargs):
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return user

    @staticmethod
    def update_last_login(user):
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        return user

    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()
        return True

    @staticmethod
    def count(status='Active', role=None):
        query = User.query
        if status:
            query = query.filter(User.status == status)
        if role:
            query = query.filter(User.role == role)
        return query.count()
