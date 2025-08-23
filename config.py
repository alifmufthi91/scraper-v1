from dataclasses import dataclass
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ScraperConfig:
    """Configuration class for the scraper"""
    base_url: str
    category_param: str
    max_pages: int = 5
    delay_between_requests: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    output_format: str = "json"  # json, csv, or both
    output_directory: str = "output"
    concurrent_requests: int = 5

@dataclass
class SiteConfig:
    """Configuration for specific website scraping"""
    name: str
    base_url: str
    selectors: Dict[str, str]
    pagination_selector: str
    category_params: Dict[str, str]

# Periplus website configuration
PERIPLUS_CONFIG = SiteConfig(
    name="periplus",
    base_url="https://www.periplus.com/index.php",
    selectors={
        "product_container": "div.single-product",
        "title": "h3 a",
        "author": ".product-author a",
        "price": ".product-price",
        "image": ".product-img img.default-img",
        "link": "h3 a",
        "availability": ".product-binding"
    },
    pagination_selector="ul.pagination li a[rel='next']",
    category_params={
        "new_releases": "103",
        "bestsellers": "104",  # Example - need to verify
        "featured": "105"      # Example - need to verify
    }
)

# Default scraper configuration
DEFAULT_CONFIG = ScraperConfig(
    base_url=PERIPLUS_CONFIG.base_url,
    category_param="103",  # Default to new releases
    max_pages=int(os.getenv("MAX_PAGES", "5")),
    delay_between_requests=float(os.getenv("DELAY", "1.0")),
    max_retries=int(os.getenv("MAX_RETRIES", "3")),
    timeout=int(os.getenv("TIMEOUT", "30")),
    output_format=os.getenv("OUTPUT_FORMAT", "json"),
    output_directory=os.getenv("OUTPUT_DIR", "output"),
    concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "5"))
)