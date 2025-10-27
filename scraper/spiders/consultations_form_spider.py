"""
Spider Playwright (desktop-only) pour soumettre le formulaire PRADO
et extraire les consultations avec pagination côté serveur.
"""
import scrapy
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urlunsplit
from scraper.selectors import ConsultationsSelectors

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


DESKTOP_URL = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"


def to_desktop(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.replace("/mobile/", "/")
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


class ConsultationsFormSpider(scrapy.Spider):
    name = "consultations_form_spider"
    allowed_domains = ["marchespublics.gov.ma"]

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 3.0,
        "ROBOTSTXT_OBEY": True,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_CONTEXT": "default",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats_summary = {"pages_crawled": 0, "consultations_extracted": 0, "errors": 0}

    def start_requests(self):
        yield scrapy.Request(
            to_desktop(DESKTOP_URL),
            meta={"playwright": True, "playwright_include_page": True, "playwright_context": "default"},
            callback=self.fill_and_submit,
            errback=self.errback_close_page,
        )

    async def fill_and_submit(self, response):
        page = response.meta["playwright_page"]

        # Dates en Africa/Casablanca pour éviter les bords de journée
        tz = None
        if ZoneInfo:
            try:
                tz = ZoneInfo("Africa/Casablanca")
            except Exception:
                tz = None
        today = datetime.now(tz).date() if tz else datetime.now().date()
        mise_en_ligne_du = (today - timedelta(days=180)).strftime("%d/%m/%Y")
        mise_en_ligne_au = today.strftime("%d/%m/%Y")
        plis_du = today.strftime("%d/%m/%Y")
        plis_au = (today + timedelta(days=183)).strftime("%d/%m/%Y")

        # Remplissage robuste des dates (observé: ids PRADO AdvancedSearch_dateMiseEnLigneCalcule*)
        try:
            # Effacer puis remplir explicitement les champs connus
            for selector, value in [
                ("#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneCalculeStart", mise_en_ligne_du),
                ("#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneCalculeEnd", mise_en_ligne_au),
            ]:
                if await page.locator(selector).count():
                    await page.fill(selector, "")
                    await page.fill(selector, value)
        except Exception:
            pass

        # Fallback par name/placeholder si structure différente
        try:
            await page.fill("input[name*='dateLimiteDu'], input[placeholder*='jj/mm/aaaa'] >> nth=0", plis_du)
            await page.fill("input[name*='dateLimiteAu'], input[placeholder*='jj/mm/aaaa'] >> nth=1", plis_au)
            await page.fill("input[name*='datePublicationDu'], input[placeholder*='jj/mm/aaaa'] >> nth=2", mise_en_ligne_du)
            await page.fill("input[name*='datePublicationAu'], input[placeholder*='jj/mm/aaaa'] >> nth=3", mise_en_ligne_au)
        except Exception:
            pass

        # Soumission
        try:
            if await page.locator("#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche").count():
                await page.click("#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche")
            else:
                await page.click("text='Lancer la recherche', input[type=submit], button[type=submit]")
        except Exception:
            # Dernier recours: appuyer sur Entrée dans un champ
            try:
                await page.keyboard.press("Enter")
            except Exception:
                pass
        # Attendre stabilisation réseau
        try:
            await page.wait_for_load_state('networkidle', timeout=30000)
        except Exception:
            pass
        # Attendre un tableau de résultats (utilise les sélecteurs centraux)
        html = None
        try:
            await page.wait_for_selector(ConsultationsSelectors.TABLE, timeout=60000)
        except Exception:
            # Fallback générique
            try:
                await page.wait_for_selector("a[href*='EntrepriseDetailsConsultation'], a[href*='DetailsConsultation']", timeout=30000)
            except Exception:
                try:
                    await page.wait_for_selector("table, div.resultats, ul.consultations-list", timeout=30000)
                except Exception:
                    # Ignorer: on prendra le HTML courant
                    pass
        finally:
            html = await page.content()
            await page.close()

        # Remettre dans le pipeline Scrapy (sans Playwright)
        yield response.replace(body=html, meta={"playwright": False}, callback=self.parse_results)

    def parse_results(self, response):
        self.stats_summary["pages_crawled"] += 1

        # Chercher un tableau pertinent (priorité aux sélecteurs centraux)
        table_sel = f"{ConsultationsSelectors.TABLE}"
        table = response.css(table_sel).get()
        rows = []
        if table:
            rows = response.css(f"{ConsultationsSelectors.TABLE} tbody tr")
        if not rows:
            # Fallback: premier tableau avec des lignes
            rows = response.css("table tbody tr")

        for r in rows:
            href = r.css("a::attr(href)").get() or ""
            # Ignorer les liens javascript:
            if href.startswith("javascript:"):
                href = ""
            url_detail = response.urljoin(href) if href else None

            tds = r.css("td")
            get_td_text = lambda i: (tds[i].css("::text").getall() if i < len(tds) else [])
            td_text = lambda i: " ".join([t.strip() for t in get_td_text(i) if t.strip()])

            ref = td_text(0)
            objet = td_text(1)
            acheteur = td_text(2)
            # Essayer de récupérer une date dans les colonnes suivantes
            date_limite_raw = ""
            for i in range(3, min(7, len(tds))):
                txt = td_text(i)
                if any(ch in txt for ch in ["/", "-", ":"]) and any(m in txt for m in ["202", "20/"]):
                    date_limite_raw = txt
                    break

            # Normalisation de date au format ISO si possible
            date_iso = None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y %H:%M"):
                try:
                    date_iso = datetime.strptime(date_limite_raw.strip(), fmt).date().isoformat()
                    break
                except Exception:
                    continue

            item = {
                "ref": ref,
                "objet": objet,
                "acheteur": acheteur,
                "date_limite": date_iso or date_limite_raw,
                "url_detail": url_detail,
                "source_list_url": response.url,
            }
            # Ne garder que les lignes avec au moins un champ non vide ou un lien
            if any([ref, objet, acheteur, url_detail]):
                self.stats_summary["consultations_extracted"] += 1
                yield item

        # Fallback liste/cartes
        if not rows:
            cards = response.css("div.consultation, li.consultation-item, div.card-consultation")
            for c in cards:
                href = c.css("a::attr(href)").get()
                url_detail = response.urljoin(href) if href else None
                objet = (c.css(".objet::text, .title::text, h3::text").get("") or "").strip()
                ref = (c.css(".ref::text, .reference::text").get("") or "").strip()
                acheteur = (c.css(".acheteur::text, .ministry::text").get("") or "").strip()
                date_limite_raw = (c.css(".date::text, .deadline::text").get("") or "").strip()

                date_iso = None
                for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                    try:
                        date_iso = datetime.strptime(date_limite_raw, fmt).date().isoformat()
                        break
                    except Exception:
                        continue

                item = {
                    "ref": ref,
                    "objet": objet,
                    "acheteur": acheteur,
                    "date_limite": date_iso or date_limite_raw,
                    "url_detail": url_detail,
                    "source_list_url": response.url,
                }
                self.stats_summary["consultations_extracted"] += 1
                yield item

        # Dump HTML si aucune consultation
        if not rows and not response.css("div.consultation, li.consultation-item, div.card-consultation"):
            try:
                import os
                os.makedirs("logs", exist_ok=True)
                path = f"logs/empty_consultations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                self.logger.warning(f"Aucun item extrait. HTML dumpé dans {path}")
            except Exception as e:
                self.logger.error(f"Impossible de sauvegarder le dump HTML: {e}")

        # Pagination (desktop)
        # Pagination: rel=next ou lien contenant 'Suivant'
        next_href = response.css("a[rel='next']::attr(href)").get()
        if not next_href:
            # Utiliser XPath pour rechercher par texte
            next_href = response.xpath("//a[contains(normalize-space(.), 'Suivant')]/@href").get()
        if next_href:
            yield response.follow(to_desktop(next_href), callback=self.parse_results, meta={"playwright": False})

    async def errback_close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Erreur: {failure}")
        self.stats_summary["errors"] += 1

    def closed(self, reason):
        self.logger.info(f"Spider fermé: {reason}")
        self.logger.info(f"Stats: {self.stats_summary}")

