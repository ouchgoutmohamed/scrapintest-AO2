"""
Spider pour extraire les procès-verbaux
"""
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from scraper.items import PVExtraitItem
from scraper.selectors import PVSelectors, URLs


class PVSpider(scrapy.Spider):
    """Spider pour extraire les extraits de procès-verbaux"""
    name = 'pv_spider'
    allowed_domains = ['marchespublics.gov.ma']
    
    def start_requests(self):
        yield scrapy.Request(
            url=URLs.PV_EXTRAITS,
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
            await page.wait_for_selector(PVSelectors.TABLE, timeout=10000)
            html = await page.content()
            await page.close()
            
            from scrapy.http import HtmlResponse
            response = HtmlResponse(url=response.url, body=html, encoding='utf-8')
            
            rows = response.css(PVSelectors.ROWS)
            self.logger.info(f"Trouvé {len(rows)} PV")
            
            for row in rows:
                item = PVExtraitItem()
                item['ref_consultation'] = row.css(PVSelectors.REF_CONSULTATION + '::text').get()
                item['organisme_acronyme'] = row.css(PVSelectors.ORGANISME + '::text').get()
                item['type_pv'] = row.css(PVSelectors.TYPE_PV + '::text').get()
                item['date_seance'] = self.parse_date(row.css(PVSelectors.DATE_SEANCE + '::text').get())
                item['date_publication_pv'] = self.parse_date(row.css(PVSelectors.DATE_PUBLICATION + '::text').get())
                item['url_pv'] = response.urljoin(row.css(PVSelectors.PV_LINK + '::attr(href)').get() or '')
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
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y %H:%M']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
        except:
            return None
