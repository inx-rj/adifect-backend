import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):  
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    ext = ext.strip()
    # valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.xlsx', '.xls']
    valid_extensions = [".svg", ".eps", ".png", ".jpg", ".jpeg", ".gif"]
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension....')
