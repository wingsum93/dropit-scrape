# Converted version of your Selenium scraper using Playwright
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logger_setup import get_logger
from db import insert_new_products
from selector import Selector
from model import Product
from decimal import Decimal, InvalidOperation
from typing import List, Optional
import logging
import json
import time

logger = get_logger(__name__, log_file="logs/dropit.log", level=logging.DEBUG)

BASE_URL = 'https://www.dropit.bm'

def extract_product_info(html) -> List[Product]:
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select(Selector.LIST_OF_PRODUCTS)
    results: List[Product] = []

    for item in items:
        name_tag = item.select_one(Selector.NAME)
        price_tag = item.select_one(Selector.PRICE)
        unit_tag = item.select_one(Selector.UNIT)

        product_name = name_tag.text.strip() if name_tag else 'N/A'
        product_price_with_dollar = price_tag.text.strip() if price_tag else 'N/A'
        product_unit = unit_tag.text.strip() if unit_tag else 'N/A'
        product_url = name_tag['href'] if name_tag and 'href' in name_tag.attrs else 'N/A'
        full_url = urljoin(BASE_URL, product_url) if product_url else 'N/A'

        product_price: Optional[Decimal] = None
        if product_price_with_dollar.startswith('$'):
            try:
                product_price = Decimal(product_price_with_dollar[1:])
            except InvalidOperation:
                product_price = None

        results.append(Product(
            name=product_name,
            price=product_price,
            unit=product_unit,
            url=full_url
        ))

    return results

def scrape_page(page):
    html = page.content()
    return extract_product_info(html)

def scrape_all_pages_with_pagination(page, base_url, category_name):
    all_products = []
    seen_urls = set()
    page.goto(base_url)

    page.wait_for_selector(Selector.LIST_OF_PRODUCTS, timeout=20000)

    current_page = 1

    while True:
        products = scrape_page(page)
        for p in products:
            if p.url not in seen_urls:
                seen_urls.add(p.url)
                all_products.append(p)
        logger.debug(f"Scraped {len(products)} products from page {current_page}.")

        try:
            next_btn = page.query_selector(Selector.NEXT_PAGE_BTN)
            if not next_btn or 'fp-disabled' in next_btn.get_attribute('class'):
                logger.debug("Next button is disabled; end of pagination.")
                break

            with page.expect_navigation(wait_until="load", timeout=10000):
                next_btn.click()

            page.wait_for_selector(Selector.LIST_OF_PRODUCTS, timeout=20000)
            current_page += 1

            # Rate limiting: wait 1.5 seconds between pages
            time.sleep(1.5)

        except PlaywrightTimeout:
            logger.debug("No next button or timeout waiting; end of pagination.")
            break

    # Save screenshot of the last page
    screenshot_path = f"screenshots/{category_name}_page_{current_page}.png"
    page.screenshot(path=screenshot_path, full_page=True)
    logger.info(f"Saved screenshot to {screenshot_path}")
    logger.info(f"Last page number for category '{category_name}': {current_page}")

    return all_products

def run_category_scraper(category_name: str, url: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            raw_products = scrape_all_pages_with_pagination(page, url, category_name)
            logger.info(f"[{category_name}] Scraped {len(raw_products)} raw products.")

            products: List[Product] = []
            for rp in raw_products:
                rp.category = category_name
                products.append(rp)

            insert_new_products(products)
        finally:
            browser.close()

def save_to_json(data, filename='output.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def print_longest_property_lengths(products):
    if not products:
        logger.debug("No products.")
        return

    max_lengths = {}
    for p in products:
        attrs = p if isinstance(p, dict) else vars(p)
        for key, value in attrs.items():
            val_str = str(value) if value is not None else ''
            max_lengths[key] = max(max_lengths.get(key, 0), len(val_str))

    for key, length in max_lengths.items():
        logger.debug(f"{key}: max length = {length}")

def main():
    category_map = {
        #"frozen food": "https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page=1",
        "bakery": "https://www.dropit.bm/shop/bakery/d/22886616#!/?limit=96&page=1",
        "BWS": "https://www.dropit.bm/shop/beer_wine_spirits/d/22886618#!/?limit=96&page=1",
        "dairy": "https://www.dropit.bm/shop/dairy/d/22886620#!/?limit=96&page=1",
        "deli": "https://www.dropit.bm/shop/deli/d/22886622#!/?limit=96&page=1",
        "home_floral": "https://www.dropit.bm/shop/home_floral/d/22886626#!/?limit=96&page=1",
        "meat": "https://www.dropit.bm/shop/meat/d/22886628#!/?limit=96&page=1",
        "pantry": "https://www.dropit.bm/shop/pantry/d/22886630#!/?limit=96&page=1",
        "produce": "https://www.dropit.bm/shop/produce/d/22886632#!/?limit=96&page=1",
        "seafood": "https://www.dropit.bm/shop/seafood/d/22886634#!/?limit=96&page=1",
    }

    for cat, url in category_map.items():
        run_category_scraper(cat, url)

if __name__ == "__main__":
    main()
