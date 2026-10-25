from app.repositories.audit_repository import AuditRepository
from app.utils.device_detector import get_client_ip, get_device_info

class AuditService:
    @staticmethod
    def log_event(action, user_id=None, document_id=None, old_value=None, new_value=None, req=None, details=None):
        """
        Record a comprehensive audit trail entry including IP, device, and browser.
        """
        ip = get_client_ip(req)
        device, browser = get_device_info(req)

        return AuditRepository.create_log(
            action=action.upper(),
            user_id=user_id,
            document_id=document_id,
            old_value=old_value,
            new_value=new_value or details,
            ip_address=ip,
            device=device,
            browser=browser,
            details=details or new_value
        )

    @staticmethod
    def get_audit_trail(limit=100, user_id=None, document_id=None, action=None):
        return AuditRepository.get_recent(limit=limit, user_id=user_id, document_id=document_id, action=action)

    @staticmethod
    def count_total_logs():
        return AuditRepository.count()
