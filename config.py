import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

    # Configuration for file uploads and processed files
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'

    MAX_CONTENT_LENGTH = 32 * 1024 * 1024