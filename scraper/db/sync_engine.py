# db/sync_engine.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraper.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_size=5)
SessionLocal = sessionmaker(bind=engine,autoflush=True, autocommit=False)
