"""
Middlewares personnalisés pour le scraper PMMP
"""
import random
import time
import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured


class CustomUserAgentMiddleware:
    """Middleware pour gérer le User-Agent"""
    
    def __init__(self, user_agent):
        self.user_agent = user_agent
    
    @classmethod
    def from_crawler(cls, crawler):
        user_agent = crawler.settings.get('USER_AGENT')
        if not user_agent:
            raise NotConfigured
        
        middleware = cls(user_agent)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.user_agent
    
    def spider_opened(self, spider):
        spider.logger.info(f'User-Agent configuré: {self.user_agent}')


class DelayMiddleware:
    """
    Middleware pour introduire des délais aléatoires entre les requêtes
    Respect du serveur et prévention du blocage
    """
    
    def __init__(self, delay, random_delay):
        self.delay = delay
        self.random_delay = random_delay
        self.last_request_time = None
    
    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat('SCRAPER_DELAY', 2.5)
        random_delay = crawler.settings.getfloat('SCRAPER_RANDOM_DELAY', 2.0)
        
        middleware = cls(delay, random_delay)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def process_request(self, request, spider):
        if self.last_request_time is not None:
            # Calculer le délai depuis la dernière requête
            elapsed = time.time() - self.last_request_time
            wait_time = self.delay + random.uniform(0, self.random_delay)
            
            if elapsed < wait_time:
                sleep_time = wait_time - elapsed
                spider.logger.debug(f"Pause de {sleep_time:.2f}s avant la prochaine requête")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def spider_opened(self, spider):
        spider.logger.info(f'Délai configuré: {self.delay}s + random(0, {self.random_delay}s)')


class CustomSpiderMiddleware:
    """Middleware personnalisé pour le spider"""
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def process_spider_input(self, response, spider):
        """Traitement avant que la response n'atteigne le spider"""
        return None
    
    def process_spider_output(self, response, result, spider):
        """Traitement des items retournés par le spider"""
        for item in result:
            yield item
    
    def process_spider_exception(self, response, exception, spider):
        """Gestion des exceptions du spider"""
        spider.logger.error(f"Exception dans le spider: {exception}")
    
    def spider_opened(self, spider):
        spider.logger.info('Spider middleware activé')


class RetryWithDelayMiddleware:
    """
    Middleware de retry avec délai exponentiel
    En cas d'erreur 429 (Too Many Requests), attend plus longtemps
    """
    
    def __init__(self):
        self.retry_count = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        return middleware
    
    def process_response(self, request, response, spider):
        if response.status == 429:
            retry_times = self.retry_count.get(request.url, 0)
            
            if retry_times < 3:
                # Attendre de plus en plus longtemps
                wait_time = (2 ** retry_times) * 5  # 5s, 10s, 20s
                spider.logger.warning(
                    f"Code 429 reçu. Attente de {wait_time}s avant retry #{retry_times + 1}"
                )
                time.sleep(wait_time)
                
                self.retry_count[request.url] = retry_times + 1
                return request
            else:
                spider.logger.error(f"Échec après 3 retries pour {request.url}")
        
        return response
