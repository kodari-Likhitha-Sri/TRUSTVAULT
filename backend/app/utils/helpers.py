from datetime import datetime, timezone

def format_file_size(size_in_bytes):
    """Convert raw byte count into human-readable representation."""
    if not size_in_bytes:
        return '0 KB'
    bytes_float = float(size_in_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_float < 1024.0:
            return f"{bytes_float:.1f} {unit}"
        bytes_float /= 1024.0
    return f"{bytes_float:.1f} TB"

def get_file_icon(file_type):
    """Return Bootstrap Icon class for a file extension."""
    ft = (file_type or '').lower().lstrip('.')
    if ft == 'pdf':
        return 'bi-file-earmark-pdf text-danger'
    elif ft in ['doc', 'docx']:
        return 'bi-file-earmark-word text-primary'
    elif ft in ['ppt', 'pptx']:
        return 'bi-file-earmark-ppt text-warning'
    elif ft in ['png', 'jpg', 'jpeg', 'webp', 'gif']:
        return 'bi-file-earmark-image text-success'
    elif ft in ['xls', 'xlsx', 'csv']:
        return 'bi-file-earmark-spreadsheet text-success'
    elif ft in ['zip', 'rar', 'tar', 'gz']:
        return 'bi-file-earmark-zip text-secondary'
    return 'bi-file-earmark-text text-secondary'
