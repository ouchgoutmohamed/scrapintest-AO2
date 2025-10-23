"""
Extension Scrapy pour collecter des métriques
"""
from scrapy import signals
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import logging

logger = logging.getLogger(__name__)

# Métriques Prometheus
spider_started = Counter('pmmp_spider_started_total', 'Number of spider starts', ['spider'])
spider_closed = Counter('pmmp_spider_closed_total', 'Number of spider closures', ['spider', 'reason'])
requests_total = Counter('pmmp_requests_total', 'Total requests made', ['spider'])
responses_total = Counter('pmmp_responses_total', 'Total responses received', ['spider', 'status'])
items_scraped = Counter('pmmp_items_scraped_total', 'Total items scraped', ['spider', 'type'])
spider_errors = Counter('pmmp_spider_errors_total', 'Total spider errors', ['spider'])
active_spiders = Gauge('pmmp_active_spiders', 'Number of active spiders')


class MetricsExtension:
    """Extension pour exposer les métriques Prometheus"""
    
    def __init__(self, stats):
        self.stats = stats
        self.prometheus_started = False
    
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.stats)
        
        # Démarrer le serveur Prometheus (port 9100)
        if not ext.prometheus_started:
            try:
                start_http_server(9100)
                ext.prometheus_started = True
                logger.info("Serveur Prometheus démarré sur le port 9100")
            except Exception as e:
                logger.warning(f"Impossible de démarrer le serveur Prometheus: {e}")
        
        # Connecter les signaux
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        
        return ext
    
    def spider_opened(self, spider):
        spider_started.labels(spider=spider.name).inc()
        active_spiders.inc()
        logger.info(f"Spider {spider.name} démarré")
    
    def spider_closed(self, spider, reason):
        spider_closed.labels(spider=spider.name, reason=reason).inc()
        active_spiders.dec()
        logger.info(f"Spider {spider.name} fermé: {reason}")
    
    def request_scheduled(self, request, spider):
        requests_total.labels(spider=spider.name).inc()
    
    def response_received(self, response, request, spider):
        responses_total.labels(spider=spider.name, status=response.status).inc()
    
    def item_scraped(self, item, spider):
        item_type = item.__class__.__name__
        items_scraped.labels(spider=spider.name, type=item_type).inc()
