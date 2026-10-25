import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def get_file_subfolder(extension):
    ext = extension.lower().replace('.', '')
    if ext == 'pdf':
        return 'pdf'
    elif ext in ['png', 'jpg', 'jpeg', 'webp']:
        return 'images'
    elif ext in ['ppt', 'pptx']:
        return 'ppt'
    elif ext in ['doc', 'docx']:
        return 'docs'
    return 'docs'

def save_document_file(file_storage):
    original_filename = secure_filename(file_storage.filename)
    if not original_filename:
        original_filename = f"document_{uuid.uuid4().hex[:8]}"

    _, ext = os.path.splitext(original_filename)
    clean_ext = ext.lstrip('.').lower()
    subfolder = get_file_subfolder(clean_ext)
    
    unique_name = f"{uuid.uuid4().hex[:12]}_{original_filename}"
    target_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(target_folder, exist_ok=True)
    
    target_path = os.path.join(target_folder, unique_name)
    file_storage.save(target_path)
    
    file_size = os.path.getsize(target_path)
    
    return unique_name, original_filename, subfolder, clean_ext, file_size

def save_avatar_picture(form_picture):
    random_hex = uuid.uuid4().hex[:12]
    _, ext = os.path.splitext(form_picture.filename)
    picture_fn = f"avatar_{random_hex}{ext.lower()}"
    picture_path = os.path.join(current_app.config['AVATAR_FOLDER'], picture_fn)
    
    # Resize image for avatar (256x256)
    output_size = (256, 256)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn
