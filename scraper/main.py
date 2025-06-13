from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logger_setup import get_logger
from db import insert_new_products
from selector import Selector
from model import Product
from decimal import Decimal, InvalidOperation
from typing import List, Optional
import logging
import csv
import json


logger = get_logger(__name__, log_file="logs/dropit.log", level=logging.DEBUG)

def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def close_driver(driver):
    if driver:
        driver.quit()
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

        # 用 keyword args 建立 Product 實例
        results.append(Product(
            name=product_name,
            price=product_price,
            unit=product_unit,
            url=full_url
        ))

    return results

def scrape_page(driver):
    html = driver.page_source
    return extract_product_info(html)

def scrape_all_pages_with_pagination(driver, base_url):
    all_products = []
    seen_urls = set()
    driver.get(base_url)

    # 初次等待商品列表出現
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, Selector.LIST_OF_PRODUCTS))
    )

    while True:
        # 確保列表已經載入
        products = scrape_page(driver)
        for p in products:
            if p.url not in seen_urls:
                seen_urls.add(p.url)
                all_products.append(p)
        logger.debug(f"Scraped {len(products)} products from current page.")

        try:
            # 找到下一頁按鈕
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, Selector.NEXT_PAGE_BTN))
            )
            next_btn_container = driver.find_element(By.CSS_SELECTOR, Selector.NEXT_PAGE_BTN_PARENT)

            # 如果按鈕上有禁用 class，就跳出
            if 'fp-disabled' in next_btn.get_attribute('class'):
                logger.debug("Next button is disabled; end of pagination.")
                break

            # 記錄當前列表容器，等它變 stale
            container = driver.find_element(By.CSS_SELECTOR, Selector.LIST_OF_PRODUCTS)
            # 點擊
            ActionChains(driver).move_to_element(next_btn_container).click().perform()
            ActionChains(driver).move_to_element(next_btn).click().perform()
            logger.debug("Clicked next page button.")

            # 等容器失效（整頁刷新或部分更新）
            WebDriverWait(driver, 10).until(EC.staleness_of(container))
            # 再等新的列表出現
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, Selector.LIST_OF_PRODUCTS))
            )
        except (NoSuchElementException, TimeoutException):
            logger.debug("No next button or timeout waiting; end of pagination.")
            break

    return all_products
def run_category_scraper(category_name: str, url: str) -> None:
    """
    Scrape all pages for one category, 填入 category_name, 並存庫。
    """
    driver = setup_driver(headless=False)
    try:
        raw_products = scrape_all_pages_with_pagination(driver, url)
        logger.info(f"[{category_name}] Scraped {len(raw_products)} raw products.")
        
        # 填入 category
        products: List[Product] = []
        for rp in raw_products:
            rp.category = category_name
            products.append(rp)
        
        insert_new_products(products)
    finally:
        driver.quit()

def save_to_json(data, filename='output.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def print_longest_property_lengths(products):
    if not products:
        logger.debug("No products.")
        return

    max_lengths = {}

    # 支援 dict 或 ORM object
    for p in products:
        attrs = p if isinstance(p, dict) else vars(p)
        for key, value in attrs.items():
            val_str = str(value) if value is not None else ''
            max_lengths[key] = max(max_lengths.get(key, 0), len(val_str))

    for key, length in max_lengths.items():
        logger.debug(f"{key}: max length = {length}")
def main():
    """
    主程式：可支援多個 category，同時呼叫 run_category_scraper
    """
    # 你可以用 dict 來管理多個 category 與對應 URL
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
        
