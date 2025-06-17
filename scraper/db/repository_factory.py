# repository_factory.py

from .product_repo import ProductRepository
from .sync_engine import SessionLocal
from .async_engine import AsyncSessionLocal

def get_product_repo() -> ProductRepository:
    return ProductRepository(sync_session_factory=SessionLocal, async_session_factory=AsyncSessionLocal)
