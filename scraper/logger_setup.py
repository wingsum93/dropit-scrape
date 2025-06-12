# logger_setup.py
import logging
from logging.handlers import RotatingFileHandler
import os

def get_logger(
    name: str,
    log_file: str = "app.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
    fmt: str = "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S"
) -> logging.Logger:
    """
    回傳一個設定好的 logger instance。
    
    參數：
      - name: logger 名稱，一般用 __name__。
      - log_file: 日誌檔名，可傳絕對或相對路徑。
      - level: logging 等級，預設 INFO。
      - max_bytes, backup_count: RotatingFileHandler 參數。
      - fmt, datefmt: 日誌格式字串及時間格式字串。
    
    範例：
      logger = get_logger(__name__, "myapp.log", logging.DEBUG)
      logger.info("Start!")
    """
    # 避免重複 add handler
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Handler
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )

    # Formatter
    formatter = logging.Formatter(fmt, datefmt=datefmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 同時輸出到 console（可選）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
