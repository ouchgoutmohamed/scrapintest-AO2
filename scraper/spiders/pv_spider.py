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
            try:
                # Essayer la table prévue par les sélecteurs centraux
                await page.wait_for_selector(PVSelectors.TABLE, timeout=45000)
            except Exception:
                # Fallback: toute table présente sur la page
                try:
                    await page.wait_for_load_state('networkidle', timeout=20000)
                except Exception:
                    pass
                try:
                    await page.wait_for_selector("table", timeout=30000)
                except Exception:
                    pass
            html = await page.content()
            await page.close()
            
            from scrapy.http import HtmlResponse
            response = HtmlResponse(url=response.url, body=html, encoding='utf-8')
            
            # Chercher des lignes dans une table plausible
            rows = response.css(f"{PVSelectors.TABLE} {PVSelectors.ROWS}")
            if not rows:
                # Fallback: première table avec tbody tr
                rows = response.css("table tbody tr")
            self.logger.info(f"Trouvé {len(rows)} PV")
            
            for row in rows:
                item = PVExtraitItem()
                item['ref_consultation'] = row.css(PVSelectors.REF_CONSULTATION + '::text').get()
                item['organisme_acronyme'] = row.css(PVSelectors.ORGANISME + '::text').get()
                item['type_pv'] = row.css(PVSelectors.TYPE_PV + '::text').get()
                item['date_seance'] = self.parse_date(row.css(PVSelectors.DATE_SEANCE + '::text').get())
                item['date_publication_pv'] = self.parse_date(row.css(PVSelectors.DATE_PUBLICATION + '::text').get())
                href = row.css(PVSelectors.PV_LINK + '::attr(href)').get() or ''
                # Éviter les liens javascript:
                if href.startswith('javascript:'):
                    href = ''
                item['url_pv'] = response.urljoin(href) if href else ''
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
