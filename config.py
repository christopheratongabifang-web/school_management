import os
<<<<<<< HEAD
from datetime import timedelta
from pathlib import Path


class Config:
    # Use DATABASE_URL if present. Otherwise, use PostgreSQL only when explicit
    # Postgres env vars are provided; otherwise fallback to a local SQLite file.
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME')

    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)

    default_sqlite_path = INSTANCE_DIR / 'database.db'
    legacy_sqlite_path = INSTANCE_DIR / 'school_management.db'

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif DB_USER and DB_HOST and DB_NAME:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD or ""}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    elif default_sqlite_path.exists() or not legacy_sqlite_path.exists():
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{default_sqlite_path.as_posix()}'
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{legacy_sqlite_path.as_posix()}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Environment mode helps secure cookie defaults.
    ENV = os.environ.get('FLASK_ENV', os.environ.get('ENV', 'development'))
    DEBUG = os.environ.get('DEBUG', 'True' if ENV == 'development' else 'False').lower() == 'true'

    # Secret key for sessions and CSRF protection.
    # In production, this must be set explicitly.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if SECRET_KEY is None and ENV != 'production':
        SECRET_KEY = os.urandom(24).hex()

    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True' if ENV == 'production' else 'False') == 'True'
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('SESSION_LIFETIME_MINUTES', '60')))
    SESSION_PROTECTION = 'strong'
=======

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'school-expense-tracker-secret-key-12345'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
