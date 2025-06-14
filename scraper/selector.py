# selectors.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Selector:
    NAME: str = 'div.fp-item-name span a'
    PRICE: str = 'div.fp-item-price span.fp-item-base-price'
    UNIT: str = 'div.fp-item-price span.fp-item-size'
    URL: str = 'div.fp-item-name span a'  # same as NAME，因為 href 在 name tag
    LIST_OF_PRODUCTS: str = 'ul.fp-product-list div.fp-item-content'
    NEXT_PAGE_BTN: str = 'li.fp-pager-item-next a.fp-btn-next'
    NEXT_PAGE_BTN_PARENT: str = 'li.fp-pager-item-next'

@dataclass(frozen=True)
class ProductDetailSelector:
    NAME: str = 'h1.fp-page-header.fp-page-title'
    PRICE: str = 'div.fp-item-detail.fp-item-detail-lg div.fp-item-price span.fp-item-base-price'
    UNIT: str = 'div.fp-item-price span.fp-item-size'
    
    LOCATIOIN: str = 'div.fp-item-location'
    SKU: str = 'div.fp-item-upc'