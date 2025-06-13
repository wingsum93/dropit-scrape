from sqlalchemy import create_engine, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime,Date, func
)
from sqlalchemy.ext.declarative import declarative_base


# 1. Define base model
class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="產品名稱")
    price = Column(Numeric(10, 2), nullable=False, comment="價格")
    unit = Column(String(40), nullable=True, comment="單位，例如：kg、pcs")
    url = Column(String(500), unique=True, nullable=False, comment="產品連結")
    category = Column(String(20), nullable=True, comment="產品類別")
    sku = Column(String(15), nullable=True, comment="SKU/UPC")
    location = Column(String(20), nullable=True, comment="產品位置")
    created_at = Column(
        Date,
        server_default=func.current_date(),
        nullable=False,
        comment="建立日期"
    )
    updated_at = Column(
        Date,
        server_default=func.current_date(),
        onupdate=func.current_date(),
        nullable=False,
        comment="最後更新日期"
    )

    def __repr__(self):
        return (
            f"<Product(id={self.id}, name={self.name!r}, price={self.price}, "
            f"unit={self.unit!r}, url={self.url!r})>"
        )
class ProductPriceHistory(Base):
    __tablename__ = 'product_price_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False, comment="產品ID")
    price = Column(Numeric(10, 2), nullable=False, comment="價格")
    created_at = Column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        comment="建立日期（每日一筆）"
    )

    def __repr__(self):
        return (
            f"<ProductPriceHistory(id={self.id}, product_id={self.product_id}, "
            f"price={self.price}, created_at={self.created_at})>"
        )
