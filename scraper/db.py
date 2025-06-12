from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from scraper.model import Base  # ✅ 這邊 import model.py 裡面的 Base
from dotenv import load_dotenv
from config import Config
import os

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
# 🧠 建立 session factory
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)

# 🏗️ 初始化資料表（只需跑一次）
def init_db():
    Base.metadata.create_all(bind=engine)

# 🧪 Dependency: 取得一個 session
def get_session() -> Session:
    return SessionLocal()


def insert_all_job_ads(job_ads):
    """
    將所有的 JobAd 寫入資料庫
    :param job_ads: List[JobAd]
    """
    session = get_session()
    try:
        session.add_all(job_ads)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error inserting {len(job_ads)} job ads: {e}")
    finally:
        session.close()






# ----------------------------------
## main entry point
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
# ----------------------------------
# 這段程式碼會建立一個 SQLite 資料庫，並定義一個 `JobAd` 表格。