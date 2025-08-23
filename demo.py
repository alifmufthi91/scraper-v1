#!/usr/bin/env python3
"""
Demo script showcasing the Scalable Data Scraper
"""

import asyncio
import json
from scraper import DataScraper
from config import PERIPLUS_CONFIG, ScraperConfig

async def main():
    print("🚀 Scalable Data Scraper Demo")
    print("=" * 60)
    print(f"Target: {PERIPLUS_CONFIG.base_url}")
    print(f"Category: New Releases (anl=103)")
    print()

    # Configure for a quick demo
    config = ScraperConfig(
        base_url=PERIPLUS_CONFIG.base_url,
        category_param="103",
        max_pages=1,
        delay_between_requests=1.0,
        output_format="both",
        output_directory="demo_output"
    )

    print("📋 Configuration:")
    print(f"  - Max pages: {config.max_pages}")
    print(f"  - Delay: {config.delay_between_requests}s")
    print(f"  - Output format: {config.output_format}")
    print(f"  - Output directory: {config.output_directory}")
    print()

    print("🔄 Starting scrape...")
    
    async with DataScraper(PERIPLUS_CONFIG, config) as scraper:
        result = await scraper.run_scraper("new_releases", max_pages=1)
        
        print()
        print("✅ Scraping Results:")
        print(f"  - Books found: {result.total_books}")
        print(f"  - Pages scraped: {result.pages_scraped}")
        print(f"  - Duration: {result.scraping_completed - result.scraping_started}")
        print(f"  - Success: {result.success}")
        
        if result.errors:
            print(f"  - Errors: {len(result.errors)}")
        
        print()
        print("📚 Sample Books:")
        for i, book in enumerate(result.books[:5], 1):
            print(f"  {i}. {book.title}")
            print(f"     Price: {book.price}")
            print(f"     Format: {book.availability}")
            print(f"     URL: {book.product_url}")
            print()
        
        if len(result.books) > 5:
            print(f"     ... and {len(result.books) - 5} more books")
        
        print()
        print("💾 Output Files:")
        print(f"  - JSON: {config.output_directory}/periplus_new_releases_*.json")
        print(f"  - CSV:  {config.output_directory}/periplus_new_releases_*.csv")
        
        print()
        print("🎯 Key Features Demonstrated:")
        print("  ✓ Async/concurrent scraping")
        print("  ✓ Configurable parameters")
        print("  ✓ Multiple output formats") 
        print("  ✓ Error handling and retries")
        print("  ✓ Rate limiting")
        print("  ✓ Structured data models")
        print("  ✓ Extensible architecture")
        
        print()
        print("🚀 Ready for Production Use!")
        print("Run 'python main.py --help' for all options")

if __name__ == "__main__":
    asyncio.run(main())