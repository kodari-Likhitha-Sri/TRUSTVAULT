from app.utils.file_handler import (
    get_subfolder_for_extension, validate_file_extension,
    save_uploaded_file, delete_stored_file, save_avatar_picture
)
from app.utils.device_detector import get_client_ip, get_device_info
from app.utils.helpers import format_file_size, get_file_icon

# Backward compatibility aliases
save_document_file = save_uploaded_file
get_file_subfolder = get_subfolder_for_extension
