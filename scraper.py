import asyncio
import aiohttp
import time
import logging
import json
import csv
import os
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
import pandas as pd

from models import Book, ScrapingResult
from config import ScraperConfig, SiteConfig, PERIPLUS_CONFIG, DEFAULT_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataScraper:
    """Scalable data scraper with configurable parameters"""
    
    def __init__(self, site_config: SiteConfig, scraper_config: ScraperConfig):
        self.site_config = site_config
        self.scraper_config = scraper_config
        self.ua = UserAgent()
        self.session = None
        self.books_scraped = []
        self.errors = []
        
        # Create output directory if it doesn't exist
        os.makedirs(self.scraper_config.output_directory, exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.scraper_config.concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.scraper_config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.ua.random}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get random headers for requests"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def _fetch_page(self, url: str, retries: int = None) -> Optional[str]:
        """Fetch a single page with retry logic"""
        if retries is None:
            retries = self.scraper_config.max_retries
        
        for attempt in range(retries + 1):
            try:
                async with self.session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully fetched: {url}")
                        return content
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed for {url}: {str(e)}"
                logger.error(error_msg)
                if attempt == retries:
                    self.errors.append(error_msg)
                else:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    def _parse_book(self, book_element, category: str) -> Optional[Book]:
        """Parse a single book element"""
        try:
            # Extract title
            title_elem = book_element.select_one(self.site_config.selectors["title"])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract author
            author_elem = book_element.select_one(self.site_config.selectors["author"])
            author = None
            if author_elem:
                author = author_elem.get_text(strip=True)
            else:
                # Try alternative selector for nested author links
                author_section = book_element.select_one(".product-author")
                if author_section:
                    author_links = author_section.find_all('a')
                    for link in author_links:
                        text = link.get_text(strip=True)
                        if text and text != "":
                            author = text
                            break
            
            # Extract price
            price_elem = book_element.select_one(self.site_config.selectors["price"])
            price = None
            if price_elem:
                # Find the actual price (not crossed out price)
                price_divs = price_elem.find_all('div')
                for div in price_divs:
                    text = div.get_text(strip=True)
                    # Look for the current price (not crossed out)
                    if text and 'Rp' in text and 'text-decoration:line-through' not in str(div):
                        price = text
                        break
                if not price:
                    price = price_elem.get_text(strip=True)
            
            # Extract image URL
            image_elem = book_element.select_one(self.site_config.selectors["image"])
            image_url = None
            if image_elem:
                image_url = image_elem.get('src') or image_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.site_config.base_url, image_url)
            
            # Extract product URL
            link_elem = book_element.select_one(self.site_config.selectors["link"])
            product_url = None
            if link_elem:
                product_url = link_elem.get('href')
                if product_url and not product_url.startswith('http'):
                    product_url = urljoin(self.site_config.base_url, product_url)
            
            # Extract availability
            availability_elem = book_element.select_one(self.site_config.selectors["availability"])
            availability = availability_elem.get_text(strip=True) if availability_elem else None
            
            if title:  # Only create book if we have at least a title
                return Book(
                    title=title,
                    author=author,
                    price=price,
                    image_url=image_url,
                    product_url=product_url,
                    availability=availability,
                    category=category
                )
                
        except Exception as e:
            logger.error(f"Error parsing book element: {str(e)}")
            self.errors.append(f"Error parsing book: {str(e)}")
        
        return None
    
    def _parse_page(self, html_content: str, category: str) -> List[Book]:
        """Parse books from a page"""
        soup = BeautifulSoup(html_content, 'lxml')
        books = []
        
        # Find all book containers
        book_elements = soup.select(self.site_config.selectors["product_container"])
        logger.info(f"Found {len(book_elements)} product elements on page")
        
        # Filter to only actual books (not categories)
        actual_books = []
        for element in book_elements:
            link = element.select_one("a")
            if link and link.get('href'):
                href = link.get('href')
                # Only include items that are actual products (have /p/ in URL), not categories (/c/)
                if '/p/' in href:
                    actual_books.append(element)
        
        logger.info(f"Filtered to {len(actual_books)} actual book products")
        
        for book_element in actual_books:
            book = self._parse_book(book_element, category)
            if book:
                books.append(book)
        
        return books
    
    def _get_next_page_url(self, html_content: str, current_url: str) -> Optional[str]:
        """Extract next page URL from current page"""
        soup = BeautifulSoup(html_content, 'lxml')
        next_link = soup.select_one(self.site_config.pagination_selector)
        
        if next_link:
            next_url = next_link.get('href')
            if next_url:
                if not next_url.startswith('http'):
                    next_url = urljoin(self.site_config.base_url, next_url)
                return next_url
        
        return None
    
    def _build_category_url(self, category_param: str, page: int = 1) -> str:
        """Build URL for a specific category and page"""
        base_url = self.site_config.base_url
        params = {
            'route': 'product/category',
            'anl': category_param
        }
        
        if page > 1:
            params['page'] = str(page)
        
        # Construct URL with parameters
        return f"{base_url}?{urlencode(params)}"
    
    async def scrape_category(self, category_name: str, category_param: str, max_pages: int = None) -> List[Book]:
        """Scrape books from a specific category"""
        if max_pages is None:
            max_pages = self.scraper_config.max_pages
        
        books = []
        current_page = 1
        
        logger.info(f"Starting to scrape category '{category_name}' (param: {category_param})")
        
        while current_page <= max_pages:
            url = self._build_category_url(category_param, current_page)
            logger.info(f"Scraping page {current_page}: {url}")
            
            html_content = await self._fetch_page(url)
            if not html_content:
                logger.error(f"Failed to fetch page {current_page}")
                break
            
            page_books = self._parse_page(html_content, category_name)
            if not page_books:
                logger.info(f"No books found on page {current_page}, stopping pagination")
                break
            
            books.extend(page_books)
            logger.info(f"Scraped {len(page_books)} books from page {current_page}")
            
            # Check for next page
            next_url = self._get_next_page_url(html_content, url)
            if not next_url:
                logger.info("No more pages found")
                break
            
            current_page += 1
            
            # Delay between requests
            if self.scraper_config.delay_between_requests > 0:
                await asyncio.sleep(self.scraper_config.delay_between_requests)
        
        logger.info(f"Completed scraping category '{category_name}': {len(books)} books from {current_page} pages")
        return books
    
    async def scrape_multiple_categories(self, categories: Dict[str, str], max_pages: int = None) -> Dict[str, List[Book]]:
        """Scrape multiple categories concurrently"""
        tasks = []
        for category_name, category_param in categories.items():
            task = self.scrape_category(category_name, category_param, max_pages)
            tasks.append((category_name, task))
        
        results = {}
        for category_name, task in tasks:
            try:
                books = await task
                results[category_name] = books
            except Exception as e:
                logger.error(f"Error scraping category {category_name}: {str(e)}")
                self.errors.append(f"Error scraping category {category_name}: {str(e)}")
                results[category_name] = []
        
        return results
    
    def _save_to_json(self, data: Union[List[Book], ScrapingResult], filename: str):
        """Save data to JSON file"""
        filepath = os.path.join(self.scraper_config.output_directory, filename)
        
        if isinstance(data, list):
            json_data = [book.model_dump() for book in data]
        else:
            json_data = data.model_dump()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Data saved to {filepath}")
    
    def _save_to_csv(self, books: List[Book], filename: str):
        """Save books to CSV file"""
        if not books:
            logger.warning("No books to save to CSV")
            return
        
        filepath = os.path.join(self.scraper_config.output_directory, filename)
        
        # Convert to DataFrame
        df = pd.DataFrame([book.model_dump() for book in books])
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Data saved to {filepath}")
    
    def save_results(self, result: ScrapingResult):
        """Save scraping results in the specified format(s)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{result.site_name}_{result.category}_{timestamp}"
        
        if self.scraper_config.output_format in ["json", "both"]:
            self._save_to_json(result, f"{base_filename}.json")
        
        if self.scraper_config.output_format in ["csv", "both"]:
            self._save_to_csv(result.books, f"{base_filename}.csv")
    
    async def run_scraper(self, category_name: str = "new_releases", max_pages: int = None) -> ScrapingResult:
        """Main method to run the scraper"""
        start_time = datetime.now()
        
        # Get category parameter
        if category_name in self.site_config.category_params:
            category_param = self.site_config.category_params[category_name]
        else:
            category_param = category_name  # Assume it's already a parameter
        
        # Scrape the category
        books = await self.scrape_category(category_name, category_param, max_pages)
        
        end_time = datetime.now()
        
        # Create result object
        result = ScrapingResult(
            site_name=self.site_config.name,
            category=category_name,
            total_books=len(books),
            pages_scraped=min(max_pages or self.scraper_config.max_pages, 
                            (len(books) // 20) + 1 if books else 1),  # Estimate pages
            books=books,
            scraping_started=start_time,
            scraping_completed=end_time,
            success=len(books) > 0,
            errors=self.errors
        )
        
        # Save results
        self.save_results(result)
        
        return result