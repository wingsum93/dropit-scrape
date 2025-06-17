from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy import func 
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from datetime import  datetime
from logger_setup import get_logger
from scraper import Selector, ProductDetailSelector
from db.repository_factory import get_product_repo
import logging
import re
from config import Config

# Import your ORM models
from scraper.db.model import Product, ProductPriceHistory  # adjust import path as needed

# 設定 logging
logger = get_logger(__name__, log_file="logs/fetch_product_detail.log", level=logging.DEBUG)
repo = get_product_repo()
# 抽取 SKU
def extract_sku(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    match = re.search(r'\b\d{8,}\b', text)
    if match:
        return match.group()
    return lines[-1] if lines else ''

# 抽取位置
def extract_location(text: str) -> str:
    if "Location:" in text:
        return text.split("Location:")[1].strip()
    return ''

# 單一產品 fetch 任務
async def fetch_product_detail(prod, browser_semaphore, browser):
    async with browser_semaphore:
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(prod.url, timeout=Config.ONLINE_TIMEOUT * 1000)
            await page.wait_for_selector(
                ProductDetailSelector.PRICE,
                timeout=Config.FETCH_PRODUCT_DETAIL_TIMEOUT * 1000
            )

            price_elem = await page.query_selector(ProductDetailSelector.PRICE)
            sku_elem = await page.query_selector(ProductDetailSelector.SKU)
            location_elem = await page.query_selector(ProductDetailSelector.LOCATION)

            price_text = await price_elem.inner_text() if price_elem else ''
            price_text = price_text.strip()
            try:
                price = float(price_text.replace('$', '').replace(',', ''))
            except ValueError:
                price = None
                logger.error(f"❌ Failed to parse price '{price_text}' @ {prod.url}")

            sku_raw = (await sku_elem.inner_text()).strip() if sku_elem else None
            location_raw = (await location_elem.inner_text()).strip() if location_elem else None
            sku = extract_sku(sku_raw) if sku_raw else None
            location = extract_location(location_raw) if location_raw else None

            return {
                "prod": prod,
                "price": price,
                "sku": sku,
                "location": location
            }

        except PlaywrightTimeoutError:
            logger.warning(f"⏱️ Timeout loading {prod.url}")
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching {prod.url}: {e}")
            raise
        finally:
            await page.close()
            await context.close()

# 批次處理：所有 fetch 成功才寫入
async def run_batch(products, browser, browser_semaphore):
    tasks = [fetch_product_detail(prod, browser_semaphore, browser) for prod in products]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    if any(isinstance(res, Exception) for res in results):
        failed_count = sum(1 for res in results if isinstance(res, Exception))
        logger.warning(f"⚠️ Skip DB write: {failed_count} products failed to fetch.")
        return

    # All success → proceed to DB write
    for result in results:
        prod = result["prod"]
        price = result["price"]
        sku = result["sku"]
        location = result["location"]

        if (prod.sku is None or prod.location is None) and (sku or location):
            repo.update_product(prod, sku=sku, location=location)
            logger.info(f"📝 Updated product {prod.id}: sku={sku}, location={location}")

        if price is not None:
            repo.insert_price_history(prod.id, price)
            logger.info(f"💰 Inserted price history for {prod.id}: {price}")

# 主流程：不斷拿 batch
async def main():
    max_tabs = Config.MAX_TAB_FOR_PRODUCT_DETAIL
    browser_semaphore = asyncio.Semaphore(max_tabs)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not Config.SHOW_UI)

        total = 10
        batch_size = 2
        processed = 0

        while processed < total:
            products = repo.get_product_random(batch_size)
            if not products:
                logger.info("🎯 No more products to process.")
                break

            logger.info(f"📦 Running batch of {len(products)} products...")
            await run_batch(products, browser, browser_semaphore)
            processed += len(products)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
