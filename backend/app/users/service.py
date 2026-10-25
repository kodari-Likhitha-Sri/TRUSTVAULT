from app.repositories.user_repository import UserRepository
from app.audit.service import AuditService
from app.utils.file_handler import save_avatar_picture

class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def list_all_users(status=None, role=None):
        return UserRepository.get_all(status=status, role=role)

    @staticmethod
    def update_profile(user, username, email, profile_pic_file=None, avatar_folder=None, req=None):
        clean_user = username.strip()
        clean_email = email.strip().lower()

        # Check collisions for unique email only

        if clean_email != user.email:
            existing = UserRepository.get_by_email(clean_email)
            if existing and existing.id != user.id:
                return False, "Email address is already in use by another account."

        old_info = f"username={user.username}, email={user.email}"
        user.username = clean_user
        user.email = clean_email

        if profile_pic_file and avatar_folder:
            pic_fn = save_avatar_picture(profile_pic_file, avatar_folder)
            user.profile_pic = pic_fn

        UserRepository.update(user)

        AuditService.log_event(
            action='PROFILE UPDATE',
            user_id=user.id,
            old_value=old_info,
            new_value=f"username={user.username}, email={user.email}",
            details=f"User {user.username} updated profile information",
            req=req
        )

        return True, user

    @staticmethod
    def change_password(user, current_password, new_password, req=None):
        if not user.check_password(current_password):
            return False, "Current password verification failed. Please try again."

        user.set_password(new_password)
        UserRepository.update(user)

        AuditService.log_event(
            action='PASSWORD CHANGE',
            user_id=user.id,
            details=f"User {user.username} successfully updated their password",
            req=req
        )

        return True, "Your password has been changed successfully!"

    @staticmethod
    def change_user_role(admin_user, target_user_id, new_role, req=None):
        if not admin_user.is_admin:
            return False, "Unauthorized: Admin privileges required."

        target = UserRepository.get_by_id(target_user_id)
        if not target:
            return False, "User not found."

        if target.id == admin_user.id and new_role.lower() != 'admin':
            return False, "You cannot remove administrative privileges from yourself."

        old_role = target.role
        target.role = new_role
        UserRepository.update(target)

        AuditService.log_event(
            action='ROLE CHANGE',
            user_id=admin_user.id,
            old_value=f"user={target.username}, role={old_role}",
            new_value=f"user={target.username}, role={new_role}",
            details=f"Admin {admin_user.username} modified role of {target.username} to {new_role}",
            req=req
        )

        return True, f"Role for {target.username} updated to {new_role}."

    @staticmethod
    def change_user_status(admin_user, target_user_id, new_status, req=None):
        if not admin_user.is_admin:
            return False, "Unauthorized: Admin privileges required."

        target = UserRepository.get_by_id(target_user_id)
        if not target:
            return False, "User not found."

        if target.id == admin_user.id:
            return False, "You cannot deactivate or suspend your own account."

        old_status = target.status
        target.status = new_status
        UserRepository.update(target)

        AuditService.log_event(
            action='STATUS CHANGE',
            user_id=admin_user.id,
            old_value=f"user={target.username}, status={old_status}",
            new_value=f"user={target.username}, status={new_status}",
            details=f"Admin {admin_user.username} changed status of {target.username} to {new_status}",
            req=req
        )

        return True, f"Account status for {target.username} set to {new_status}."

    @staticmethod
    def delete_user(admin_user, target_user_id, req=None):
        if not admin_user.is_admin:
            return False, "Unauthorized: Admin privileges required."

        target = UserRepository.get_by_id(target_user_id)
        if not target:
            return False, "User not found."

        if target.id == admin_user.id:
            return False, "You cannot delete your own account."

        target_name = target.username
        UserRepository.delete(target)

        AuditService.log_event(
            action='DELETE USER',
            user_id=admin_user.id,
            details=f"Admin {admin_user.username} deleted user {target_name}",
            req=req
        )

        return True, f"User {target_name} has been removed from the system."
