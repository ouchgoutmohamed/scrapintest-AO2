"""
Run a Scrapy spider programmatically with safe settings overrides.

Usage:
  python scripts/run_spider.py <spider_name> <output_json_path>

This disables DB/metrics pipelines and writes items to the given JSON file.
It keeps Playwright and project settings intact.
"""
import sys
import os
from datetime import datetime

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/run_spider.py <spider_name> <output_json_path>")
        sys.exit(1)

    spider_name = sys.argv[1]
    output_path = sys.argv[2]

    # Ensure directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load base project settings
    settings = get_project_settings()

    # Disable pipelines/extensions that require DB or metrics
    settings.set('ITEM_PIPELINES', {}, priority='cmdline')
    settings.set('EXTENSIONS', {}, priority='cmdline')
    # Disable custom downloader middlewares to avoid missing modules (we keep default Scrapy ones)
    settings.set('DOWNLOADER_MIDDLEWARES', {}, priority='cmdline')

    # Keep Scrapy-Playwright download handlers and middlewares from project
    # Ensure Twisted asyncio reactor remains set for Playwright
    settings.set('TWISTED_REACTOR', 'twisted.internet.asyncioreactor.AsyncioSelectorReactor', priority='cmdline')

    # Write to JSON file
    settings.set('FEEDS', {
        output_path: {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': True,
            'indent': 2,
            'overwrite': True,
        }
    }, priority='cmdline')

    # Be gentle
    settings.set('CONCURRENT_REQUESTS', 1, priority='cmdline')
    settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', 1, priority='cmdline')
    settings.set('DOWNLOAD_DELAY', 2.5, priority='cmdline')
    # Logging
    settings.set('LOG_LEVEL', 'INFO', priority='cmdline')
    settings.set('LOG_STDOUT', True, priority='cmdline')
    settings.set('LOG_FILE', 'logs/run_spider.log', priority='cmdline')

    print(f"Running spider '{spider_name}' -> {output_path}")
    process = CrawlerProcess(settings)
    process.crawl(spider_name)
    process.start()  # blocks until finished

    print(f"Done. Output saved to: {output_path}")


if __name__ == '__main__':
    # Ensure project root is on sys.path
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    main()
