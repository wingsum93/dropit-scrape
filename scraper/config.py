# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 載入 .env 檔（如果有的話）
env_path =  '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """
    Postgres Database Configuration
    使用 environment variables，若沒設定，就 fallback 到預設值（請自行修改）。
    """
    DB_USER = os.getenv('DB_USER', 'myuser')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    DB_NAME = os.getenv('DB_NAME', 'your_dbname')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')

    # SQLAlchemy 的連線字串
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Optional: 其他 SQLAlchemy 設定
    SQLALCHEMY_TRACK_MODIFICATIONS = False
