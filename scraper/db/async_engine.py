# db/async_engine.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from scraper.config import Config

async_engine = create_async_engine(Config.SQLALCHEMY_DATABASE_URI_ASYNC, pool_size=5)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)