"""
Spider principal pour extraire les consultations du portail PMMP
"""
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import logging
import re
from scraper.items import ConsultationItem, LotItem
from scraper.selectors import ConsultationsSelectors, DetailConsultationSelectors, URLs


class ConsultationsSpider(scrapy.Spider):
    """
    Spider pour extraire les consultations (appels d'offres)
    Utilise Playwright pour gérer les formulaires dynamiques
    """
    name = 'consultations_spider'
    allowed_domains = ['marchespublics.gov.ma']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
    }
    
    def __init__(self, statut='en_cours', periode='3ans', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statut = statut
        self.periode = periode
        self.stats = {
            'pages_crawled': 0,
            'consultations_extracted': 0,
            'errors': 0
        }
        self.logger.info(f"Initialisation du spider - Statut: {statut}, Période: {periode}")
    
    def start_requests(self):
        """Point d'entrée du spider"""
        url = URLs.CONSULTATIONS_EN_COURS if self.statut == 'en_cours' else URLs.CONSULTATIONS_SEARCH
        
        yield scrapy.Request(
            url=url,
            callback=self.parse_list_page,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_load_state', 'networkidle'),
                    PageMethod('wait_for_timeout', 2000),
                ],
            },
            errback=self.errback_close_page,
        )
    
    async def parse_list_page(self, response):
        """Parse la page listant les consultations"""
        page = response.meta.get('playwright_page')
        self.stats['pages_crawled'] += 1
        
        try:
            # Attendre que le tableau soit chargé
            await page.wait_for_selector(ConsultationsSelectors.TABLE, timeout=10000)
            
            # Extraire le contenu HTML mis à jour
            html = await page.content()
            await page.close()
            
            # Parser avec Scrapy Selector
            from scrapy.http import HtmlResponse
            response = HtmlResponse(url=response.url, body=html, encoding='utf-8')
            
            # Extraire les lignes du tableau
            table = response.css(ConsultationsSelectors.TABLE).get()
            if not table:
                self.logger.warning(f"Aucun tableau trouvé sur {response.url}")
                return
            
            rows = response.css(ConsultationsSelectors.ROWS)
            self.logger.info(f"Trouvé {len(rows)} consultations sur la page")
            
            for row in rows:
                # Extraire les données de la ligne
                item = self.parse_consultation_row(row, response)
                
                if item and item.get('ref_consultation'):
                    self.stats['consultations_extracted'] += 1
                    
                    # Si un lien vers le détail existe, le suivre
                    detail_url = row.css(ConsultationsSelectors.DETAIL_LINK + '::attr(href)').get()
                    if detail_url:
                        detail_url = response.urljoin(detail_url)
                        yield scrapy.Request(
                            url=detail_url,
                            callback=self.parse_detail_page,
                            meta={
                                'playwright': True,
                                'playwright_include_page': True,
                                'playwright_context': 'default',
                                'consultation_item': item,
                            },
                            errback=self.errback_close_page,
                        )
                    else:
                        yield item
            
            # Gestion de la pagination
            next_page = response.css(ConsultationsSelectors.NEXT_PAGE + '::attr(href)').get()
            if not next_page:
                # Fallback XPath pour trouver un lien "Suivant"/"Next"
                next_page = response.xpath("//a[contains(., 'Suivant') or contains(., 'Next')]/@href").get()

            if next_page:
                # Certains liens de pagination sont en javascript: on déclenche alors un clic via Playwright
                if next_page.lower().startswith('javascript') or next_page.strip() in ('#', ''):
                    self.logger.info("Pagination via clic Playwright sur 'Suivant'")
                    yield scrapy.Request(
                        url=response.url,
                        callback=self.parse_list_page,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_context': 'default',
                            'playwright_page_methods': [
                                PageMethod('wait_for_selector', ConsultationsSelectors.TABLE),
                                PageMethod('click', "text=Suivant"),
                                PageMethod('wait_for_load_state', 'networkidle'),
                                PageMethod('wait_for_timeout', 1500),
                            ],
                        },
                        errback=self.errback_close_page,
                    )
                else:
                    next_url = response.urljoin(next_page)
                    self.logger.info(f"Navigation vers page suivante: {next_url}")
                    yield scrapy.Request(
                        url=next_url,
                        callback=self.parse_list_page,
                        meta={'playwright': True, 'playwright_include_page': True, 'playwright_context': 'default'},
                        errback=self.errback_close_page,
                    )
        
        except Exception as e:
            self.logger.error(f"Erreur lors du parsing de {response.url}: {e}")
            self.stats['errors'] += 1
            if page:
                await page.close()
    
    def parse_consultation_row(self, row, response):
        """Extrait les données d'une ligne du tableau"""
        try:
            item = ConsultationItem()
            
            # Extraction des champs
            item['ref_consultation'] = self.clean_text(
                row.css(ConsultationsSelectors.REF_CONSULTATION + '::text').get()
            )
            item['titre'] = self.clean_text(
                row.css(ConsultationsSelectors.TITRE + '::text').get()
            )
            item['organisme_acronyme'] = self.clean_text(
                row.css(ConsultationsSelectors.ORGANISME + '::text').get()
            )
            item['type_marche'] = self.normalize_type_marche(
                row.css(ConsultationsSelectors.TYPE_MARCHE + '::text').get()
            )
            item['date_publication'] = self.parse_date(
                row.css(ConsultationsSelectors.DATE_PUBLICATION + '::text').get()
            )
            item['date_limite'] = self.parse_date(
                row.css(ConsultationsSelectors.DATE_LIMITE + '::text').get()
            )
            item['statut'] = self.normalize_statut(
                row.css(ConsultationsSelectors.STATUT + '::text').get()
            )
            
            # URL de détail - IMPORTANT: Ce champ est essentiel pour accéder aux documents
            # On essaie plusieurs sélecteurs pour maximiser les chances de trouver le lien
            detail_url = None
            
            # Tentative 1: Sélecteur spécifique
            detail_url = row.css(ConsultationsSelectors.DETAIL_LINK + '::attr(href)').get()
            
            # Tentative 2: Chercher tout lien dans la ligne
            if not detail_url:
                detail_url = row.css('a::attr(href)').get()
            
            # Tentative 3: Chercher un lien contenant "detail" ou "consultation"
            if not detail_url:
                all_links = row.css('a::attr(href)').getall()
                for link in all_links:
                    if link and ('detail' in link.lower() or 'consultation' in link.lower()):
                        detail_url = link
                        break
            
            # Construire l'URL complète
            if detail_url:
                item['url_detail'] = response.urljoin(detail_url)
                self.logger.debug(f"✓ URL détail trouvée: {item['url_detail']}")
            else:
                # Si aucun lien n'est trouvé, construire l'URL à partir de la référence
                # (adapter selon le format réel des URLs du site)
                if item.get('ref_consultation') and item.get('organisme_acronyme'):
                    item['url_detail'] = f"{URLs.DETAIL_CONSULTATION}&refConsultation={item['ref_consultation']}&orgAcronyme={item['organisme_acronyme']}"
                    self.logger.warning(f"⚠ URL détail construite: {item['url_detail']}")
                else:
                    item['url_detail'] = ''
                    self.logger.warning(f"✗ Aucune URL détail trouvée pour {item.get('ref_consultation', 'REF_INCONNUE')}")
            
            # Métadonnées
            item['date_extraction'] = datetime.now()
            
            return item
        
        except Exception as e:
            self.logger.error(f"Erreur extraction ligne: {e}")
            return None
    
    async def parse_detail_page(self, response):
        """Parse la page de détail d'une consultation"""
        page = response.meta.get('playwright_page')
        item = response.meta.get('consultation_item', ConsultationItem())
        
        try:
            # Attendre le chargement
            await page.wait_for_load_state('networkidle')
            
            html = await page.content()
            await page.close()
            
            from scrapy.http import HtmlResponse
            detail_response = HtmlResponse(url=response.url, body=html, encoding='utf-8')
            
            # Enrichir l'item avec les détails
            item['objet'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.OBJET + '::text').get()
            )
            item['organisme_nom_complet'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.ORGANISME_NOM + '::text').get()
            )
            item['organisme_ville'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.ORGANISME_VILLE + '::text').get()
            )
            item['organisme_telephone'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.ORGANISME_TEL + '::text').get()
            )
            item['organisme_email'] = detail_response.css(
                DetailConsultationSelectors.ORGANISME_EMAIL + '::attr(href)'
            ).get()
            if item.get('organisme_email'):
                item['organisme_email'] = item['organisme_email'].replace('mailto:', '')
            
            # Montants
            item['montant_estime'] = self.parse_amount(
                detail_response.css(DetailConsultationSelectors.MONTANT_ESTIME + '::text').get()
            )
            item['cautionnement_provisoire'] = self.parse_amount(
                detail_response.css(DetailConsultationSelectors.CAUTIONNEMENT + '::text').get()
            )
            
            # Classification
            item['secteur'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.SECTEUR + '::text').get()
            )
            item['code_cpv'] = self.clean_text(
                detail_response.css(DetailConsultationSelectors.CODE_CPV + '::text').get()
            )
            
            # URLs documents (avec fallback XPath sur le texte)
            avis_href = detail_response.css(DetailConsultationSelectors.URL_AVIS + '::attr(href)').get()
            if not avis_href:
                avis_href = detail_response.xpath("//a[contains(., 'Avis') or contains(., 'avis')]/@href").get()
            item['url_avis'] = detail_response.urljoin(avis_href or '')

            dce_href = detail_response.css(DetailConsultationSelectors.URL_DCE + '::attr(href)').get()
            if not dce_href:
                dce_href = detail_response.xpath("//a[contains(., 'DCE') or contains(., 'dce')]/@href").get()
            item['url_dce'] = detail_response.urljoin(dce_href or '')

            # Enregistrer l'URL de détail au cas où elle n'aurait pas été posée côté liste
            if not item.get('url_detail'):
                item['url_detail'] = response.url

            # Archiver la page HTML
            item['page_html'] = html
            
            yield item
            
            # Extraire les lots s'il y en a
            lots_rows = detail_response.css(DetailConsultationSelectors.LOT_ROW)
            for lot_row in lots_rows:
                lot_item = self.parse_lot(lot_row, item['ref_consultation'])
                if lot_item:
                    yield lot_item
        
        except Exception as e:
            self.logger.error(f"Erreur parsing détail {response.url}: {e}")
            self.stats['errors'] += 1
            if page:
                await page.close()
            # Retourner l'item de base même en cas d'erreur
            yield item
    
    def parse_lot(self, row, ref_consultation):
        """Extrait les informations d'un lot"""
        try:
            lot = LotItem()
            lot['ref_consultation'] = ref_consultation
            lot['numero_lot'] = self.clean_text(row.css('td:nth-child(1)::text').get())
            lot['designation'] = self.clean_text(row.css('td:nth-child(2)::text').get())
            lot['montant_estime'] = self.parse_amount(row.css('td:nth-child(3)::text').get())
            lot['date_extraction'] = datetime.now()
            return lot
        except Exception as e:
            self.logger.error(f"Erreur extraction lot: {e}")
            return None
    
    # Méthodes utilitaires
    def clean_text(self, text):
        """Nettoie et normalise le texte"""
        if not text:
            return None
        return ' '.join(text.strip().split())
    
    def parse_date(self, date_str):
        """Parse une date au format du site"""
        if not date_str:
            return None
        try:
            # Adapter selon le format réel (ex: "23/10/2025" ou "2025-10-23")
            date_str = self.clean_text(date_str)
            # Essayer différents formats
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y %H:%M']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            self.logger.warning(f"Impossible de parser la date '{date_str}': {e}")
            return None
    
    def parse_amount(self, amount_str):
        """Parse un montant (ex: '1 234 567,89 DH')"""
        if not amount_str:
            return None
        try:
            # Retirer les espaces, symboles monétaires
            amount_str = re.sub(r'[^\d,.]', '', amount_str)
            amount_str = amount_str.replace(',', '.')
            return float(amount_str) if amount_str else None
        except Exception:
            return None
    
    def normalize_type_marche(self, type_str):
        """Normalise le type de marché"""
        if not type_str:
            return None
        type_str = type_str.lower()
        if 'travaux' in type_str:
            return 'travaux'
        elif 'fourniture' in type_str:
            return 'fournitures'
        elif 'service' in type_str:
            return 'services'
        elif 'etude' in type_str or 'étude' in type_str:
            return 'etudes'
        return type_str
    
    def normalize_statut(self, statut_str):
        """Normalise le statut"""
        if not statut_str:
            return 'en_cours'
        statut_str = statut_str.lower()
        if 'cours' in statut_str:
            return 'en_cours'
        elif 'clôtur' in statut_str or 'clotur' in statut_str:
            return 'cloture'
        elif 'annul' in statut_str:
            return 'annule'
        return statut_str
    
    async def errback_close_page(self, failure):
        """Gestion des erreurs avec fermeture de la page Playwright"""
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()
        self.logger.error(f"Erreur de requête: {failure}")
        self.stats['errors'] += 1
    
    def closed(self, reason):
        """Appelé à la fin du spider"""
        self.logger.info(f"Spider fermé: {reason}")
        self.logger.info(f"Statistiques finales: {self.stats}")
