from flask_login import login_user, logout_user
from app.repositories.user_repository import UserRepository
from app.audit.service import AuditService

class AuthService:
    @staticmethod
    def register_user(username, email, password, role='Owner', department='General', req=None):
        existing_email = UserRepository.get_by_email(email)
        if existing_email:
            return False, "An account with this email already exists."

        user = UserRepository.create(
            username=username,
            email=email,
            password=password,
            role=role,
            department=department,
            status='Active'
        )

        AuditService.log_event(
            action='REGISTRATION',
            user_id=user.id,
            details=f"New user registered: {user.username} ({user.role}) in {user.department}",
            req=req
        )

        return True, user

    @staticmethod
    def authenticate_user(login_id, password, remember=False, req=None):
        from app.models.user import User
        clean_id = (login_id or '').strip()
        # 1. Unique email match takes precedence
        user = UserRepository.get_by_email(clean_id)
        if not user:
            # 2. Match by username (support duplicate usernames by verifying password)
            candidates = User.query.filter_by(username=clean_id).all()
            for cand in candidates:
                if cand.check_password(password):
                    user = cand
                    break
            if not user and candidates:
                user = candidates[0]

        if not user:
            AuditService.log_event(
                action='FAILED LOGIN',
                details=f"Failed login attempt for unknown ID: {login_id}",
                req=req
            )
            return False, "Invalid email/username or password."

        if not user.is_active_account:
            AuditService.log_event(
                action='FAILED LOGIN',
                user_id=user.id,
                details=f"Login attempt on suspended/inactive account: {user.username}",
                req=req
            )
            return False, "Your account has been deactivated or suspended. Please contact your administrator."

        if not user.check_password(password):
            AuditService.log_event(
                action='FAILED LOGIN',
                user_id=user.id,
                details=f"Incorrect password attempt for user: {user.username}",
                req=req
            )
            return False, "Invalid email/username or password."

        # Successful authentication
        login_user(user, remember=remember)
        UserRepository.update_last_login(user)

        AuditService.log_event(
            action='LOGIN',
            user_id=user.id,
            details=f"User {user.username} successfully logged in",
            req=req
        )

        return True, user

    @staticmethod
    def logout_current_user(user, req=None):
        if user and user.is_authenticated:
            AuditService.log_event(
                action='LOGOUT',
                user_id=user.id,
                details=f"User {user.username} logged out",
                req=req
            )
        logout_user()
        return True
