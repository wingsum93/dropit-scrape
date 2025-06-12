from sqlalchemy import create_engine, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, func
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
    unit = Column(String(50), nullable=True, comment="單位，例如：kg、pcs")
    url = Column(String(2083), unique=True, nullable=False, comment="產品連結")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="建立時間"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最後更新時間"
    )

    def __repr__(self):
        return (
            f"<Product(id={self.id}, name={self.name!r}, price={self.price}, "
            f"unit={self.unit!r}, url={self.url!r})>"
        )

