from typing import List
from contextlib import contextmanager
from sqlalchemy import create_engine, select
from sqlalchemy import or_  # ✅ 這邊 import or_ 函式
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from model import Base  # ✅ 這邊 import model.py 裡面的 Base
from model import Product  # ✅ 這邊 import model.py 裡面的 Product
from dotenv import load_dotenv
from logger_setup import get_logger  # ✅ 這邊 import logger_setup.py 裡面的 get_logger
from config import Config
import logging
import csv
import os

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
# 🧠 建立 session factory
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)
logger = get_logger(__name__,log_file="logs/dropit.log", level=logging.DEBUG)
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

def insert_new_products(products: List[Product]):
    """
    只將資料庫中還沒有的 products（用 url 驗證）插入；
    若全部都已存在，則不做任何事。
    """
    # 先蒐集所有欲插入的 URL
    incoming_urls = [p.url for p in products]

    with get_session() as session:
        # 查出已存在的那一批 URL
        stmt = select(Product.url).where(Product.url.in_(incoming_urls))
        existing = session.execute(stmt).scalars().all()
        existing_set = set(existing)

        # 過濾出真正要新增的 products
        new_products = [p for p in products if p.url not in existing_set]

        if not new_products:
            logger.info("No new products to insert; all URLs already exist.")
            return

        try:
            session.add_all(new_products)
            session.commit()
            logger.info(
                f"Inserted {len(new_products)} new products into DB; "
                f"skipped {len(products) - len(new_products)} duplicates."
            )
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(
                f"Error inserting {len(new_products)} new products: {e}",
                exc_info=True
            )
            # 準備 CSV 備援資料
            failed = [
                {'name': getattr(p, 'name', None),
                 'price': getattr(p, 'price', None),
                 'unit': getattr(p, 'unit', None),
                 'url': getattr(p, 'url', None)}
                for p in new_products
            ]
            try:
                save_products_to_csv(failed)
                logger.info(f"Saved {len(failed)} failed products to CSV fallback.")
            except Exception as csv_e:
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