import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

def get_subfolder_for_extension(extension):
    """Determine organized subfolder based on file extension."""
    ext = extension.lower().replace('.', '')
    if ext == 'pdf':
        return 'pdf'
    elif ext in ['png', 'jpg', 'jpeg', 'webp']:
        return 'images'
    elif ext in ['ppt', 'pptx']:
        return 'ppt'
    elif ext in ['doc', 'docx', 'txt', 'csv', 'xlsx']:
        return 'docs'
    return 'docs'

def validate_file_extension(filename, allowed_extensions):
    """Verify that file extension is in the allowed set."""
    if not filename or '.' not in filename:
        return False, None
    ext = filename.rsplit('.', 1)[1].lower()
    return (ext in allowed_extensions), ext

def save_uploaded_file(file_storage, upload_root_folder, allowed_extensions=None, max_bytes=None):
    """
    Securely save an uploaded document using UUID naming.
    Ensures transactional safety: caller can delete returned absolute_filepath if DB fails.
    """
    original_filename = secure_filename(file_storage.filename)
    if not original_filename:
        original_filename = f"document_{uuid.uuid4().hex[:8]}"

    _, ext = os.path.splitext(original_filename)
    clean_ext = ext.lstrip('.').lower()

    if allowed_extensions and clean_ext not in allowed_extensions:
        raise ValueError(f"File extension '{clean_ext}' is not permitted.")

    subfolder = get_subfolder_for_extension(clean_ext)
    target_dir = os.path.join(upload_root_folder, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    # Secure UUID-based storage name (e.g. 73af8d91acde_filename.pdf)
    unique_token = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_token}_{original_filename}"
    target_absolute_path = os.path.join(target_dir, stored_filename)

    # Save to disk
    file_storage.save(target_absolute_path)
    file_size = os.path.getsize(target_absolute_path)

    if max_bytes and file_size > max_bytes:
        # File exceeds quota, remove immediately
        if os.path.exists(target_absolute_path):
            os.remove(target_absolute_path)
        raise ValueError(f"File exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB.")

    relative_filepath = os.path.join('uploads', subfolder, stored_filename).replace('\\', '/')

    return {
        'stored_filename': stored_filename,
        'original_filename': original_filename,
        'subfolder': subfolder,
        'file_type': clean_ext,
        'file_size': file_size,
        'relative_filepath': relative_filepath,
        'absolute_filepath': target_absolute_path
    }

def delete_stored_file(absolute_filepath):
    """Remove a stored file from filesystem during rollback or permanent purge."""
    try:
        if absolute_filepath and os.path.exists(absolute_filepath):
            os.remove(absolute_filepath)
            return True
    except OSError:
        pass
    return False

def save_avatar_picture(form_picture, avatar_folder):
    """Process and save resized user profile avatar (256x256)."""
    random_hex = uuid.uuid4().hex[:12]
    _, ext = os.path.splitext(form_picture.filename)
    picture_fn = f"avatar_{random_hex}{ext.lower()}"
    os.makedirs(avatar_folder, exist_ok=True)
    picture_path = os.path.join(avatar_folder, picture_fn)

    output_size = (256, 256)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn
