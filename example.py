#!/usr/bin/env python3
"""
Example usage of the Scalable Data Scraper
This file demonstrates different ways to use the scraper programmatically
"""

import asyncio
import json
from scraper import DataScraper
from config import PERIPLUS_CONFIG, DEFAULT_CONFIG, ScraperConfig

async def example_basic_scraping():
    """Basic example: Scrape new releases with default settings"""
    print("=== Basic Scraping Example ===")
    
    async with DataScraper(PERIPLUS_CONFIG, DEFAULT_CONFIG) as scraper:
        result = await scraper.run_scraper(
            category_name="new_releases",
            max_pages=2  # Limit to 2 pages for example
        )
        
        print(f"Scraped {result.total_books} books from {result.pages_scraped} pages")
        print(f"Duration: {result.scraping_completed - result.scraping_started}")
        
        # Show first few books
        for i, book in enumerate(result.books[:3]):
            print(f"\nBook {i+1}:")
            print(f"  Title: {book.title}")
            print(f"  Author: {book.author}")
            print(f"  Price: {book.price}")

async def example_custom_config():
    """Example with custom configuration"""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom config with faster scraping
    custom_config = ScraperConfig(
        base_url=PERIPLUS_CONFIG.base_url,
        category_param="103",
        max_pages=1,  # Just 1 page
        delay_between_requests=0.5,  # Faster scraping
        output_format="both",  # Save both JSON and CSV
        output_directory="custom_output"
    )
    
    async with DataScraper(PERIPLUS_CONFIG, custom_config) as scraper:
        result = await scraper.run_scraper(
            category_name="new_releases",
            max_pages=1
        )
        
        print(f"Custom scrape completed: {result.total_books} books")
        print(f"Files saved to: {custom_config.output_directory}")

async def example_multiple_categories():
    """Example of scraping multiple categories"""
    print("\n=== Multiple Categories Example ===")
    
    # Configure for faster demo
    demo_config = ScraperConfig(
        base_url=PERIPLUS_CONFIG.base_url,
        category_param="103",
        max_pages=1,  # Just 1 page per category
        delay_between_requests=1.0,
        output_format="json"
    )
    
    categories = {
        "new_releases": "103",
        # Note: Other category parameters would need to be verified
        # "bestsellers": "104",  # Example - may not be correct
    }
    
    async with DataScraper(PERIPLUS_CONFIG, demo_config) as scraper:
        results = await scraper.scrape_multiple_categories(categories, max_pages=1)
        
        total_books = 0
        for category_name, books in results.items():
            print(f"{category_name}: {len(books)} books")
            total_books += len(books)
        
        print(f"Total books across all categories: {total_books}")

async def example_data_processing():
    """Example of processing scraped data"""
    print("\n=== Data Processing Example ===")
    
    async with DataScraper(PERIPLUS_CONFIG, DEFAULT_CONFIG) as scraper:
        result = await scraper.run_scraper(
            category_name="new_releases",
            max_pages=1
        )
        
        # Process the data
        books_with_authors = [book for book in result.books if book.author]
        books_with_prices = [book for book in result.books if book.price]
        
        print(f"Total books: {len(result.books)}")
        print(f"Books with authors: {len(books_with_authors)}")
        print(f"Books with prices: {len(books_with_prices)}")
        
        # Find books with specific keywords
        programming_books = [
            book for book in result.books 
            if book.title and any(keyword.lower() in book.title.lower() 
                                for keyword in ['python', 'programming', 'code', 'software'])
        ]
        
        if programming_books:
            print(f"\nProgramming-related books found: {len(programming_books)}")
            for book in programming_books:
                print(f"  - {book.title}")

async def main():
    """Run all examples"""
    print("Scalable Data Scraper - Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_basic_scraping()
        await example_custom_config()
        await example_multiple_categories()
        await example_data_processing()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("Check the 'output' and 'custom_output' directories for results.")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("This might be due to network issues or changes in the website structure.")
        print("Try running with a smaller number of pages or check your internet connection.")

if __name__ == "__main__":
    asyncio.run(main())