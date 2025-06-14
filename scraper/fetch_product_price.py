from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy import create_engine, func 
from sqlalchemy.orm import sessionmaker
from datetime import  datetime
from logger_setup import get_logger
from db import get_product_random, update_product, insert_price_history
from selector import Selector,ProductDetailSelector
import logging
import re
from config import Config

# Import your ORM models
from model import Product, ProductPriceHistory  # adjust import path as needed

# 設定 logging
logger = get_logger(__name__, log_file="logs/dropit.log", level=logging.DEBUG)

def extract_sku(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Step 2: Try regex match on whole text (fallback-safe)
    match = re.search(r'\b\d{8,}\b', text)
    if match:
        return match.group()
    
    # Step 3: Fallback to last non-empty line (in case regex fails)
    if lines:
        return lines[-1]
    
    return ''
def extract_location(text: str) -> str:
    if "Location:" in text:
        return text.split("Location:")[1].strip()
    return ''
# 2. 定義抓取細節函式
def scrape_detail(page, url: str):
    """
    使用 page instance 進入產品細節頁面，抓取 price, sku, location
    回傳 tuple(price: float, sku: str, location: str)
    """
    try:
        page.goto(url, timeout=Config.ONLINE_TIMEOUT*1000)
        # 等待關鍵元素載入
        page.wait_for_selector(ProductDetailSelector.PRICE, timeout=Config.FETCH_PRODUCT_DETAIL_TIMEOUT*1000)
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout loading {url}")
        return None, None, None

    # 提取資料 (請替換成實際的 selector)
    price_text = page.query_selector(ProductDetailSelector.PRICE).inner_text().strip()
    sku_elem = page.query_selector(ProductDetailSelector.SKU)
    location_elem = page.query_selector(ProductDetailSelector.LOCATIOIN)
    logger.info(f"Scraping {url} - Price: {price_text}, SKU: {sku_elem}, Location: {location_elem}")
    # 清理與轉型
    try:
        price = float(price_text.replace('$', '').replace(',', ''))
    except ValueError:
        price = None
        logger.error(f"Failed to parse price from '{price_text}' @ {url}")

    sku_raw = sku_elem.inner_text().strip() if sku_elem else None
    sku = extract_sku(sku_raw) if sku_raw else None
    location_raw = location_elem.inner_text().strip() if location_elem else None
    location = extract_location(location_raw) if location_raw else None
    return price, sku, location

# 3. 主程式邏輯
def main():
    
    products = get_product_random(limit=1000)
    logger.info(f"Fetched {len(products)} products from DB")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()

        for prod in products:
            # 只有在 sku 或 location 為空時才更新
            needs_update = prod.sku is None or prod.location is None
            price, sku, location = scrape_detail(page, prod.url)

            if needs_update and (sku or location):
                # 如果有新的 sku 或 location，則更新產品
                update_product(prod,sku=sku, location=location)
                logger.info(f"Updated product {prod.id}: sku={sku}, location={location}")

            # 不論是否需要更新，都要記錄價格歷史
            if price is not None:
                # 新增價格歷史紀錄
                insert_price_history(prod.id,price=price)
                logger.info(f"Inserted price history for product {prod.id}: {price}")

            # 避免過度頻繁，建議稍微延遲
            page.wait_for_timeout(500)  # 0.5 秒

        # 最後提交所有變更
        
        browser.close()
    

if __name__ == "__main__":
    main()
