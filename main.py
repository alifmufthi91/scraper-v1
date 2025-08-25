#!/usr/bin/env python3
"""
Scalable Data Scraper - Main Entry Point
Author: AI Assistant
Description: A flexible and scalable web scraper for e-commerce sites
"""

import asyncio
import argparse
import logging
from typing import Optional

from scraper import DataScraper
from config import PERIPLUS_CONFIG, DEFAULT_CONFIG, ScraperConfig
from models import ScrapingResult

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scraper.log')
        ]
    )

def create_custom_config(args) -> ScraperConfig:
    """Create custom scraper configuration from CLI arguments"""
    config = ScraperConfig(
        base_url=DEFAULT_CONFIG.base_url,
        category_param=args.category_param or DEFAULT_CONFIG.category_param,
        max_pages=args.max_pages or DEFAULT_CONFIG.max_pages,
        delay_between_requests=args.delay or DEFAULT_CONFIG.delay_between_requests,
        max_retries=args.retries or DEFAULT_CONFIG.max_retries,
        timeout=args.timeout or DEFAULT_CONFIG.timeout,
        output_format=args.output_format or DEFAULT_CONFIG.output_format,
        output_directory=args.output_dir or DEFAULT_CONFIG.output_directory,
        concurrent_requests=args.concurrent or DEFAULT_CONFIG.concurrent_requests
    )
    return config

async def run_single_category_scraper(args):
    """Run scraper for a single category"""
    config = create_custom_config(args)
    
    async with DataScraper(PERIPLUS_CONFIG, config) as scraper:
        result = await scraper.run_scraper(
            category_name=args.category,
            max_pages=args.max_pages
        )
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"SCRAPING COMPLETED")
        print(f"{'='*50}")
        print(f"Site: {result.site_name}")
        print(f"Category: {result.category}")
        print(f"Total Books: {result.total_books}")
        print(f"Pages Scraped: {result.pages_scraped}")
        print(f"Success: {result.success}")
        print(f"Duration: {result.scraping_completed - result.scraping_started}")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")
        
        print(f"\nResults saved to: {config.output_directory}")
        return result

async def run_multiple_categories_scraper(args):
    """Run scraper for multiple categories"""
    config = create_custom_config(args)
    categories = {}
    
    # Parse categories from command line (format: "name1:param1,name2:param2")
    if args.categories:
        for category_pair in args.categories.split(','):
            if ':' in category_pair:
                name, param = category_pair.split(':', 1)
                categories[name.strip()] = param.strip()
            else:
                # Use predefined categories from config
                if category_pair.strip() in PERIPLUS_CONFIG.category_params:
                    categories[category_pair.strip()] = PERIPLUS_CONFIG.category_params[category_pair.strip()]
    
    if not categories:
        # Default to all predefined categories
        categories = PERIPLUS_CONFIG.category_params
    
    async with DataScraper(PERIPLUS_CONFIG, config) as scraper:
        results = await scraper.scrape_multiple_categories(categories, args.max_pages)
        
        # Print summary for all categories
        print(f"\n{'='*60}")
        print(f"MULTIPLE CATEGORIES SCRAPING COMPLETED")
        print(f"{'='*60}")
        
        total_books = 0
        for category_name, books in results.items():
            total_books += len(books)
            print(f"{category_name}: {len(books)} books")
        
        print(f"\nTotal Books Across All Categories: {total_books}")
        print(f"Results saved to: {config.output_directory}")
        
        return results

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Scalable Data Scraper for E-commerce Sites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape new releases (default category) with default settings
  python main.py
  
  # Scrape up to 10 pages from new releases
  python main.py --max-pages 10
  
  # Scrape specific category by parameter
  python main.py --category-param 104 --category bestsellers
  
  # Scrape multiple categories
  python main.py --multiple --categories "new_releases,bestsellers"
  
  # Custom configuration
  python main.py --max-pages 5 --delay 2.0 --output-format both --output-dir ./data
  
  # Run with debug logging
  python main.py --log-level DEBUG --max-pages 2
        """
    )
    
    # Basic scraping options
    parser.add_argument('--category', default='new_releases',
                       help='Category name to scrape (default: new_releases)')
    parser.add_argument('--category-param', 
                       help='Category parameter for URL (e.g., 103 for new releases)')
    parser.add_argument('--max-pages', type=int, default=5,
                       help='Maximum number of pages to scrape (default: 5)')
    
    # Multiple categories
    parser.add_argument('--multiple', action='store_true',
                       help='Scrape multiple categories')
    parser.add_argument('--categories',
                       help='Comma-separated categories (name:param or just name for predefined)')
    
    # Request configuration
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--retries', type=int, default=3,
                       help='Maximum number of retries per request (default: 3)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--concurrent', type=int, default=5,
                       help='Number of concurrent requests (default: 5)')
    
    # Output configuration
    parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory (default: output)')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run scraper
    try:
        if args.multiple:
            asyncio.run(run_multiple_categories_scraper(args))
        else:
            asyncio.run(run_single_category_scraper(args))
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())