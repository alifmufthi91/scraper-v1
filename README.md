# Scalable Data Scraper

A flexible and scalable web scraper built in Python for extracting data from e-commerce websites. Currently configured for the Periplus bookstore website but designed to be easily extensible to other sites.

## Features

- **Scalable Architecture**: Async/await pattern for high-performance concurrent scraping
- **Configurable**: Easy configuration for different websites and categories
- **Robust Error Handling**: Automatic retries, rate limiting, and comprehensive error logging
- **Multiple Output Formats**: JSON, CSV, or both
- **Pagination Support**: Automatic pagination handling
- **CLI Interface**: Easy-to-use command-line interface
- **Extensible**: Easy to add new websites and categories

## Installation

1. Clone or download the project files
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Copy `.env.example` to `.env` and customize settings:

```bash
cp .env.example .env
```

## Quick Start

### Basic Usage

Scrape new releases with default settings (5 pages max):
```bash
python main.py
```

Scrape up to 10 pages:
```bash
python main.py --max-pages 10
```

### Advanced Usage

Scrape with custom configuration:
```bash
python main.py --max-pages 5 --delay 2.0 --output-format both --output-dir ./data
```

Scrape multiple categories:
```bash
python main.py --multiple --categories "new_releases,bestsellers"
```

Custom category parameters:
```bash
python main.py --category-param 104 --category bestsellers --max-pages 3
```

Debug mode:
```bash
python main.py --log-level DEBUG --max-pages 2
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

- `MAX_PAGES`: Maximum pages to scrape (default: 5)
- `DELAY`: Delay between requests in seconds (default: 1.0)
- `MAX_RETRIES`: Maximum retries per request (default: 3)
- `TIMEOUT`: Request timeout in seconds (default: 30)
- `OUTPUT_FORMAT`: Output format - json, csv, or both (default: json)
- `OUTPUT_DIR`: Output directory (default: output)
- `CONCURRENT_REQUESTS`: Number of concurrent requests (default: 5)

### Site Configuration

The scraper uses site-specific configurations defined in `config.py`. For Periplus:

```python
PERIPLUS_CONFIG = SiteConfig(
    name="periplus",
    base_url="https://www.periplus.com/index.php",
    selectors={
        "product_container": "div.product-thumb",
        "title": "h4 a",
        "author": "p.author a",
        "price": "p.price",
        "image": "img",
        "link": "h4 a",
        "availability": "p.stock"
    },
    pagination_selector="ul.pagination li a[rel='next']",
    category_params={
        "new_releases": "103",
        "bestsellers": "104",  # Example
        "featured": "105"      # Example
    }
)
```

## Command Line Options

```
usage: main.py [-h] [--category CATEGORY] [--category-param CATEGORY_PARAM]
               [--max-pages MAX_PAGES] [--multiple] [--categories CATEGORIES]
               [--delay DELAY] [--retries RETRIES] [--timeout TIMEOUT]
               [--concurrent CONCURRENT] [--output-format {json,csv,both}]
               [--output-dir OUTPUT_DIR] [--log-level {DEBUG,INFO,WARNING,ERROR}]

Scalable Data Scraper for E-commerce Sites

optional arguments:
  -h, --help            show this help message and exit
  --category CATEGORY   Category name to scrape (default: new_releases)
  --category-param CATEGORY_PARAM
                        Category parameter for URL (e.g., 103 for new releases)
  --max-pages MAX_PAGES
                        Maximum number of pages to scrape (default: 5)
  --multiple            Scrape multiple categories
  --categories CATEGORIES
                        Comma-separated categories (name:param or just name for predefined)
  --delay DELAY         Delay between requests in seconds (default: 1.0)
  --retries RETRIES     Maximum number of retries per request (default: 3)
  --timeout TIMEOUT     Request timeout in seconds (default: 30)
  --concurrent CONCURRENT
                        Number of concurrent requests (default: 5)
  --output-format {json,csv,both}
                        Output format (default: json)
  --output-dir OUTPUT_DIR
                        Output directory (default: output)
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Logging level (default: INFO)
```

## Output

The scraper generates timestamped files in the specified output directory:

### JSON Format
```json
{
  "site_name": "periplus",
  "category": "new_releases",
  "total_books": 25,
  "pages_scraped": 2,
  "books": [
    {
      "title": "Book Title",
      "author": "Author Name",
      "price": "$19.99",
      "image_url": "https://...",
      "product_url": "https://...",
      "availability": "In Stock",
      "category": "new_releases",
      "scraped_at": "2024-01-15T10:30:00"
    }
  ],
  "scraping_started": "2024-01-15T10:29:45",
  "scraping_completed": "2024-01-15T10:30:15",
  "success": true,
  "errors": []
}
```

### CSV Format
Standard CSV with columns: title, author, price, image_url, product_url, availability, category, scraped_at

## Programmatic Usage

You can also use the scraper programmatically:

```python
import asyncio
from scraper import DataScraper
from config import PERIPLUS_CONFIG, DEFAULT_CONFIG

async def main():
    async with DataScraper(PERIPLUS_CONFIG, DEFAULT_CONFIG) as scraper:
        result = await scraper.run_scraper(
            category_name="new_releases",
            max_pages=3
        )
        print(f"Scraped {result.total_books} books")

asyncio.run(main())
```

## Adding New Websites

To add support for a new website:

1. Create a new `SiteConfig` in `config.py`:

```python
NEW_SITE_CONFIG = SiteConfig(
    name="new_site",
    base_url="https://example.com",
    selectors={
        "product_container": "div.product",
        "title": "h3.title",
        "author": "span.author",
        "price": "div.price",
        "image": "img.product-image",
        "link": "a.product-link",
        "availability": "span.stock"
    },
    pagination_selector="a.next-page",
    category_params={
        "category1": "param1",
        "category2": "param2"
    }
)
```

2. Update the main script to use the new configuration
3. Test with a small number of pages first

## Best Practices

1. **Respect robots.txt**: Always check the target website's robots.txt file
2. **Rate Limiting**: Use appropriate delays between requests (1-2 seconds recommended)
3. **Error Handling**: Monitor logs for errors and adjust selectors if needed
4. **Legal Compliance**: Ensure your scraping activities comply with the website's terms of service
5. **Start Small**: Test with 1-2 pages before running large scraping jobs

## Troubleshooting

### Common Issues

1. **No data scraped**: Check if CSS selectors in config match the website structure
2. **Rate limiting**: Increase delay between requests
3. **Timeout errors**: Increase timeout value or reduce concurrent requests
4. **Import errors**: Ensure all dependencies are installed

### Debugging

Enable debug logging to see detailed information:
```bash
python main.py --log-level DEBUG --max-pages 1
```

Check the `scraper.log` file for detailed logs.

## License

This project is for educational purposes. Please ensure compliance with website terms of service and applicable laws when using this scraper.

## Contributing

To contribute:
1. Test your changes thoroughly
2. Update documentation if needed
3. Follow the existing code style
4. Add appropriate error handling

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify CSS selectors match the target website
3. Test with smaller page limits first
4. Ensure proper rate limiting
