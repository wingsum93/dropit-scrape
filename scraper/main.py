from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import json

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

def extract_product_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('div.fp-item-content')
    results = []

    for item in items:
        name_tag = item.select_one('div.fp-item-name span a')
        price_tag = item.select_one('div.fp-item-price span.fp-item-base-price')
        unit_tag = item.select_one('div.fp-item-price span.fp-item-size')
        

        product_name = name_tag.text.strip() if name_tag else 'N/A'
        product_price = price_tag.text.strip() if price_tag else 'N/A'
        product_unit = unit_tag.text.strip() if unit_tag else 'N/A'
        product_url = name_tag['href'] if name_tag and 'href' in name_tag.attrs else 'N/A'
        full_url = urljoin(BASE_URL, product_url) if product_url else 'N/A'

        results.append({
            'name': product_name,
            'price': product_price,
            'unit': product_unit,
            'url': full_url
        })

    return results

def scrape_page(driver, url):
    driver.get(url)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".fp-item-content"))
    )

    html = driver.page_source
    return extract_product_info(html)

def scrape_multiple_pages(urls):
    driver = setup_driver(headless=False)
    try:
        all_products = []
        seen_urls = set()
        for url in urls:
            print(f"Scraping {url} ...")
            products = scrape_page(driver, url)
            for p in products:
                if p['url'] not in seen_urls:
                    seen_urls.add(p['url'])
                    all_products.append(p)
                else:
                    print(f"Duplicate found: {p['url']}")
            all_products.extend(products)
        return all_products
    finally:
        close_driver(driver)


def save_to_json(data, filename='output.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_csv(data, filename='output.csv'):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'unit', 'price', 'url'])
        writer.writeheader()
        writer.writerows(data)

def generate_urls(num_pages=1):
    if num_pages < 1:
        return []
    base_url = 'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page='
    return [f'{base_url}{page}' for page in range(1, num_pages + 1)]

if __name__ == "__main__":
    urls = [
        'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page=1',
        'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page=2',
        'https://www.dropit.bm/shop/frozen_foods/d/22886624#!/?limit=96&page=3',
    ]
    products = scrape_multiple_pages(urls)
    print(f"Total products scraped: {len(products)}")
    save_to_csv(products, 'products.csv')
    for product in products:
        print(product)
        
