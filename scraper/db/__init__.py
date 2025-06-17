# __init__.py
"""
初始化 repository 與 session factory 出口。
你可以直接 from my_package import ProductRepository 使用。
"""

from .product_repo import ProductRepository
from .async_engine import AsyncSessionLocal
from .sync_engine import SessionLocal
from .model import Base, Product, ProductPriceHistory
from .db_safe import db_safe
from .repository_factory import get_product_repo

__all__ = ["ProductRepository", "SessionLocal", "AsyncSessionLocal"]
