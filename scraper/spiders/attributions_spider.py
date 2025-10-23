"""
Spider pour extraire les attributions
"""
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from scraper.items import AttributionItem
from scraper.selectors import AttributionSelectors, URLs
import re


class AttributionsSpider(scrapy.Spider):
    """Spider pour extraire les résultats d'attribution"""
    name = 'attributions_spider'
    allowed_domains = ['marchespublics.gov.ma']
    
    def start_requests(self):
        yield scrapy.Request(
            url=URLs.ATTRIBUTIONS,
            callback=self.parse,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_load_state', 'networkidle'),
                ],
            },
        )
    
    async def parse(self, response):
        page = response.meta.get('playwright_page')
        
        try:
            await page.wait_for_selector(AttributionSelectors.TABLE, timeout=10000)
            html = await page.content()
            await page.close()
            
            from scrapy.http import HtmlResponse
            response = HtmlResponse(url=response.url, body=html, encoding='utf-8')
            
            rows = response.css(AttributionSelectors.ROWS)
            self.logger.info(f"Trouvé {len(rows)} attributions")
            
            for row in rows:
                item = AttributionItem()
                item['ref_consultation'] = row.css(AttributionSelectors.REF_CONSULTATION + '::text').get()
                item['organisme_acronyme'] = row.css(AttributionSelectors.ORGANISME + '::text').get()
                item['entreprise_nom'] = row.css(AttributionSelectors.ENTREPRISE + '::text').get()
                item['montant_ttc'] = self.parse_amount(row.css(AttributionSelectors.MONTANT + '::text').get())
                item['date_attribution'] = self.parse_date(row.css(AttributionSelectors.DATE_ATTRIBUTION + '::text').get())
                item['url_resultat'] = response.urljoin(row.css(AttributionSelectors.DETAIL_LINK + '::attr(href)').get() or '')
                item['date_extraction'] = datetime.now()
                item['page_html'] = html
                
                yield item
        
        except Exception as e:
            self.logger.error(f"Erreur: {e}")
            if page:
                await page.close()
    
    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            for fmt in ['%d/%m/%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
        except:
            return None
    
    def parse_amount(self, amount_str):
        if not amount_str:
            return None
        try:
            amount_str = re.sub(r'[^\d,.]', '', amount_str)
            amount_str = amount_str.replace(',', '.')
            return float(amount_str) if amount_str else None
        except:
            return None
