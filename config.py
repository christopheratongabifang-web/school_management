import os
from pathlib import Path

basedir = Path(__file__).resolve().parent
instance_dir = basedir / 'instance'
instance_dir.mkdir(exist_ok=True)
instance_db = instance_dir / 'database.db'

class Config:
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development').lower()
    SECRET_KEY = os.environ.get('SECRET_KEY')

    if FLASK_ENV == 'production' and not SECRET_KEY:
        raise RuntimeError('SECRET_KEY environment variable must be set in production.')
    if not SECRET_KEY:
        SECRET_KEY = 'dev-secret-key-for-local-testing-only'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{instance_db.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = FLASK_ENV == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = 3600
    PREFERRED_URL_SCHEME = 'https' if FLASK_ENV == 'production' else 'http'
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
