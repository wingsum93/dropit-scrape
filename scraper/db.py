from typing import List
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import or_  # ✅ 這邊 import or_ 函式
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from model import Base  # ✅ 這邊 import model.py 裡面的 Base
from model import Product  # ✅ 這邊 import model.py 裡面的 Product
from dotenv import load_dotenv
from config import Config
import logging
import csv
import os

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
# 🧠 建立 session factory
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)
logger = logging.getLogger(__name__)
CSV_FILE = 'temp/failed_products.csv'
FIELDNAMES = ['name', 'price', 'unit', 'url']

# 🏗️ 初始化資料表（只需跑一次）
def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_products_to_csv(products: List[dict]):
    """
    備援：將多筆 products dict 寫入 CSV；
    若檔案不存在就先寫入 header。
    """
    # 照實說，如果連這裡都錯，代表環境太糟需要人工干預
    try:
        os.makedirs(os.path.dirname(CSV_FILE) or '.', exist_ok=True)
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            for prod in products:
                writer.writerow({
                    'name':  prod.get('name'),
                    'price': prod.get('price'),
                    'unit':  prod.get('unit'),
                    'url':   prod.get('url'),
                })
        logger.info(f"Saved {len(products)} products to CSV fallback.")
    except Exception as e:
        # 照實說：CSV 寫入失敗，應該立刻告警或手動處理
        logger.critical(f"Failed to write fallback CSV: {e}", exc_info=True)
        raise

def insert_all_products(products: List[Product]):
    """
    將所有的 Product 寫入資料庫；若 DB 寫入失敗，備援寫入 CSV。
    :param products: List[Product]
    """
    # get_session 現在是一個 context manager
    with get_session() as session:
        try:
            session.add_all(products)
            session.commit()
            logger.info(f"Successfully inserted {len(products)} products into DB.")
            return
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(
                f"Error inserting {len(products)} products into DB: {e}",
                exc_info=True
            )

            # 準備 CSV 備援資料
            failed = [
                {
                    'name':  getattr(p, 'name', None),
                    'price': getattr(p, 'price', None),
                    'unit':  getattr(p, 'unit', None),
                    'url':   getattr(p, 'url', None),
                }
                for p in products
            ]

            # CSV 備援
            try:
                save_products_to_csv(failed)
                logger.info(f"Saved {len(failed)} failed products to CSV fallback.")
            except Exception as csv_e:
                # 照實說：如果連寫 CSV 都失敗，要有適當告警或 raise
                logger.critical(
                    f"Failed to write fallback CSV: {csv_e}",
                    exc_info=True
                )
                raise


def get_products_missing_sku_or_location() -> list[Product]:
    """
    Retrieve all products where sku 或 location 欄位為 NULL。
    """
    with get_session() as db:
        return (
            db.query(Product)
              .filter(or_(Product.sku == None,
                          Product.location == None))
              .all()
        )




# ----------------------------------
## main entry point
if __name__ == "__main__":
    init_db()
    logger.debug("Database initialized successfully.")
# ----------------------------------
# 這段程式碼會建立一個 SQLite 資料庫，並定義一個 `JobAd` 表格。