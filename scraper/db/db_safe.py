import logging
from functools import wraps
import asyncio

logger = logging.getLogger("db_logger")

def db_safe(log_msg: str = "DB operation failed"):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.exception(f"{log_msg}: {e}")
                    raise  # 或 return None，看你策略
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.exception(f"{log_msg}: {e}")
                    raise
            return wrapper
    return decorator
