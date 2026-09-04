import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'careercompass-super-secret-key-2026')
    MONGO_URI = os.environ.get(
        'MONGO_URI',
        os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/career_compass')
    )
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'career_compass')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
    
    # Gemini AI configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
