"""
Configuration centrale du scraper Scrapy + Playwright
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Scrapy settings for pmmp_scraper project
BOT_NAME = 'pmmp_scraper'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# User-Agent desktop explicite pour éviter la redirection mobile
USER_AGENT = os.getenv(
    'SCRAPER_USER_AGENT',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
)

# Respect du robots.txt
ROBOTSTXT_OBEY = True

# Configuration des requêtes concurrentes (limitation pour respecter le serveur)
CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 1))
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Délais entre les requêtes (en secondes)
DOWNLOAD_DELAY = float(os.getenv('SCRAPER_DELAY', 2.5))
RANDOMIZE_DOWNLOAD_DELAY = True  # Ajoute une variation aléatoire
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Timeout des téléchargements
DOWNLOAD_TIMEOUT = int(os.getenv('DOWNLOAD_TIMEOUT', 30))

# Retry sur erreurs
RETRY_ENABLED = True
RETRY_TIMES = int(os.getenv('RETRY_TIMES', 3))
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Configuration Playwright pour le rendu JavaScript
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 45000

# Contexts Playwright (pour gérer les sessions)
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1366, "height": 900},
        "user_agent": USER_AGENT,
        "is_mobile": False,
        "has_touch": False,
        "locale": "fr-FR",
        "extra_http_headers": {
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        },
        "ignore_https_errors": True,
    },
}

# Middlewares activés
# Garder une configuration minimale et éviter les références à des modules inexistants
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    # Scrapy-Playwright n'exige pas de middleware dédié; le download handler suffit
    # 'scrapy_playwright.middleware.ScrapyPlaywrightMiddleware': 585,
    # Middlewares custom (désactivés par défaut, activables selon besoin)
    # 'scraper.middlewares.RetryWithDelayMiddleware': 560,
    # 'scraper.middlewares.CustomUserAgentMiddleware': 400,
    # 'scraper.middlewares.DelayMiddleware': 543,
}

SPIDER_MIDDLEWARES = {
    'scraper.middlewares.CustomSpiderMiddleware': 543,
}

# Pipelines de traitement des items
ITEM_PIPELINES = {
    'scraper.pipelines.ValidationPipeline': 100,
    'scraper.pipelines.CleaningPipeline': 200,
    'scraper.pipelines.DeduplicationPipeline': 300,
    'scraper.pipelines.ArchivePipeline': 400,
    'scraper.pipelines.DatabasePipeline': 500,
    'scraper.pipelines.MetricsPipeline': 600,
}

# Extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.logstats.LogStats': 500,
    'scraper.extensions.MetricsExtension': 500,
}

# Configuration des logs
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_FILE = 'logs/scraper.log'
LOG_ENCODING = 'utf-8'

# Désactiver les cookies (pas nécessaire pour ce site)
COOKIES_ENABLED = False

# Cache HTTP (optionnel, pour dev)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Feed exports
FEEDS = {
    'data/exports/consultations_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'overwrite': False,
        'indent': 2,
    },
}

# Configuration personnalisée
CUSTOM_SETTINGS = {
    'ARCHIVE_STORAGE_PATH': os.getenv('ARCHIVE_STORAGE_PATH', './data/archives'),
    'ENABLE_ARCHIVING': os.getenv('ENABLE_ARCHIVING', 'True') == 'True',
    'DATABASE_URL': os.getenv('DATABASE_URL'),
    'PMMP_BASE_URL': os.getenv('PMMP_BASE_URL', 'https://www.marchespublics.gov.ma'),
}

# Twisted Reactor (pour compatibilité avec Playwright)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
