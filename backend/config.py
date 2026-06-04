import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Use an absolute path so it always uses the same database file regardless of starting directory
    _base_dir = os.path.abspath(os.path.dirname(__file__))
    _db_path = os.path.join(_base_dir, "instance", "pet_system.db")
    
    # Ensure the parent directory (instance) exists
    os.makedirs(os.path.dirname(_db_path), exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-pethotel-2026-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))  # seconds


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False

