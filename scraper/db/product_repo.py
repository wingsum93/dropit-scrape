from typing import List
from contextlib import contextmanager
from sqlalchemy import create_engine, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import or_  # ✅ 這邊 import or_ 函式
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from scraper.db.model import Base  # ✅ 這邊 import model.py 裡面的 Base
from scraper.db.model import Product  # ✅ 這邊 import model.py 裡面的 Product
from scraper.db.model import ProductPriceHistory  # ✅ 這邊 import model.py 裡面的 ProductPriceHistory

from dotenv import load_dotenv
from logger_setup import get_logger  # ✅ 這邊 import logger_setup.py 裡面的 get_logger
from config import Config
from typing import Callable, AsyncGenerator, Generator
import logging
import csv
import os
from datetime import date



# 🧠 建立 session factory
logger = get_logger(__name__,log_file="logs/db_logger.log", level=logging.DEBUG)
CSV_FILE = 'temp/failed_products.csv'
FIELDNAMES = ['name', 'price', 'unit', 'url']

class ProductRepository:
    def __init__(
        self,
        sync_session_factory: Callable[[], Session],
        async_session_factory: Callable[[], AsyncSession],
    ):
        self._sync_session_factory = sync_session_factory
        self._async_session_factory = async_session_factory


    @staticmethod
    def init_db():
        """
        初始化資料庫（建立資料表），只需執行一次。
        """
        try:
            Base.metadata.create_all(bind=Session)
            logger.info("✅ Database initialized successfully.")
        except Exception as e:
            logger.exception(f"❌ Failed to initialize DB: {e}")
            raise

    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        db = self._sync_session_factory()
        try:
            yield db
        finally:
            db.close()

    async def get_session_async(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._async_session_factory() as session:
            yield session
            
    def get_product_random(self, limit: int = 10) -> list[Product]:
        """
        隨機取得指定數量的產品，條件為今天尚未有任何價格歷史記錄（sync 版本）。
        """
        today = date.today()
        with self.get_session() as db:
            subq = (
                db.query(ProductPriceHistory)
                .filter(
                    ProductPriceHistory.product_id == Product.id,
                    func.date(ProductPriceHistory.created_at) == today
                )
            )
            products = (
                db.query(Product)
                .filter(~subq.exists())
                .order_by(func.random())
                .limit(limit)
                .all()
            )
            logger.debug(f"📦 [SYNC] Fetched {len(products)} random products without price history on {today}")
            return products

    async def get_product_random_async(self, limit: int = 10) -> list[Product]:
        """
        隨機取得指定數量的產品，條件為今天尚未有任何價格歷史記錄（async 版本）。
        """
        today = date.today()
        async with self.get_session_async() as session:
            subq = (
                select(ProductPriceHistory.product_id)
                .where(
                    ProductPriceHistory.product_id == Product.id,
                    func.date(ProductPriceHistory.created_at) == today
                )
            )

            stmt = (
                select(Product)
                .where(~subq.exists())
                .order_by(func.random())
                .limit(limit)
            )
            result = await session.execute(stmt)
            products = result.scalars().all()
            logger.debug(f"📦 [ASYNC] Fetched {len(products)} random products without price history on {today}")
            return products
        
    def insert_new_products(self, products: List[Product]):
        """
        只將資料庫中還沒有的 products（用 url 驗證）插入；
        若全部都已存在，則不做任何事。
        """
        # 先蒐集所有欲插入的 URL
        incoming_urls = [p.url for p in products]

        with self.get_session() as session:
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




    def get_products_missing_sku_or_location(self) -> list[Product]:
        """
        Retrieve all products where sku 或 location 欄位為 NULL。
        """
        with self.get_session() as db:
            return (
                db.query(Product)
                .filter(or_(Product.sku == None,
                            Product.location == None))
                .all()
            )

    def fetch_all_products(self) -> list[Product]:
        """從 DB 讀取所有 Product"""
        with self.get_session() as db:
            products = db.query(Product).all()
            logger.debug(f"Fetched {len(products)} products from DB")
            return products

    def update_product(self, prod, sku: str = None, location: str = None):
        """更新 product 的 sku 與 location 欄位"""
        with self.get_session() as db:
            if sku:
                prod.sku = sku
            if location:
                prod.location = location
            prod.updated_at = func.current_date()
            db.add(prod)
            db.commit()
            logger.debug(f"Updated product {prod.id}: sku={sku}, location={location}")


    def insert_price_history(self, product_id: int, price: float):
        """新增一筆 ProductPriceHistory 紀錄"""
        with self.get_session() as db:
            record = ProductPriceHistory(
                product_id=product_id,
                price=price,
                created_at=date.today()
            )
            db.add(record)
            db.commit()
            logger.debug(f"Inserted price history for product {product_id}: {price}")

    def get_product_random(self, limit: int = 10) -> list[Product]:
        """
        隨機取得指定數量的產品，條件為今天尚未有任何價格歷史記錄。
        """
        with self.get_session() as db:
            today = date.today()
            # 子查詢：檢查當日是否已有價格歷史
            subq = db.query(ProductPriceHistory).filter(
                ProductPriceHistory.product_id == Product.id,
                func.date(ProductPriceHistory.created_at) == today
            )
            products = (
                db.query(Product)
                .filter(~subq.exists())
                .order_by(func.random())
                .limit(limit)
                .all()
            )
            logger.debug(f"Fetched {len(products)} random products without price history on {today}")
            return products
        
    def get_product_without_today_price_record(self) -> list[Product]:
        """
        取得all的產品，條件為今天尚未有任何價格歷史記錄。
        """
        with self.get_session() as db:
            today = date.today()
            # 建立 correlated EXISTS 子查詢
            history_exists = exists().where(
                (ProductPriceHistory.product_id == Product.id) &
                (func.date(ProductPriceHistory.created_at) == today)
            )
            products = (
                db.query(Product)
                .filter(~history_exists)
                .all()
            )
            logger.debug(f"Fetched {len(products)} random products without price history on {today}")
            return products



# ----------------------------------
## main entry point
if __name__ == "__main__":
    ProductRepository.init_db()
    logger.debug("Database initialized successfully.")
# ----------------------------------
# 這段程式碼會建立一個 SQLite 資料庫，並定義一個 `JobAd` 表格。