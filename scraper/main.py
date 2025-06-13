from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logger_setup import get_logger
from db import insert_all_products
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

    while True:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, Selector.LIST_OF_PRODUCTS))
        )

        products = scrape_page(driver)
        
        for p in products:
            if p.url not in seen_urls:
                seen_urls.add(p.url)
                all_products.append(p)
        logger.debug(f"Scraped {len(products)} products from current page.")
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, Selector.NEXT_PAGE_BTN)
            next_btn_container = driver.find_element(By.CSS_SELECTOR, Selector.NEXT_PAGE_BTN_PARENT)
            if 'fp-disabled' in next_btn.get_attribute('class'):
                break
            actions = ActionChains(driver)
            actions.move_to_element(next_btn).click(next_btn).perform()
            actions.move_to_element(next_btn_container).click(next_btn_container).perform()
            logger.debug("Clicked next page button.")
            driver.save_screenshot("temp/debug_click.png")
            WebDriverWait(driver, 8).until(EC.staleness_of(next_btn))
        except NoSuchElementException:
            break

    return all_products


def save_to_json(data, filename='output.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_urls(num_pages=1):
    if num_pages < 1:
        return []
    base_url = 'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page='
    return [f'{base_url}{page}' for page in range(1, num_pages + 1)]

if __name__ == "__main__":
    url = 'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page=1'
    
    driver = setup_driver(headless=False)
    products = scrape_all_pages_with_pagination(driver, url)
    logger.debug(f"Total products scraped: {len(products)}")
    insert_all_products(products)
        
