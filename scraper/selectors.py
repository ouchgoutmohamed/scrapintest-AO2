"""
Sélecteurs CSS/XPath pour extraire les données du portail PMMP
Centralise tous les sélecteurs pour faciliter la maintenance
"""

class ConsultationsSelectors:
    """Sélecteurs pour la page de consultations"""
    
    # Tableau des résultats
    TABLE = "table.data-table, table.consultation-table, table[id*='result']"
    ROWS = "tr[class*='row'], tbody tr"
    
    # Colonnes du tableau (à adapter selon la structure réelle)
    REF_CONSULTATION = "td:nth-child(1), td.ref"
    TITRE = "td:nth-child(2), td.titre, td.objet"
    ORGANISME = "td:nth-child(3), td.organisme"
    TYPE_MARCHE = "td:nth-child(4), td.type"
    DATE_PUBLICATION = "td:nth-child(5), td.date-pub"
    DATE_LIMITE = "td:nth-child(6), td.date-limite"
    STATUT = "td:nth-child(7), td.statut"
    
    # Lien vers détail
    DETAIL_LINK = "a[href*='DetailsConsultation'], a.detail-link"
    
    # Pagination
    PAGINATION = "div.pagination, ul.pagination"
    NEXT_PAGE = "a.next, a[rel='next']"
    PAGE_NUMBERS = "a.page-number"
    
    # Formulaire de recherche
    FORM = "form[name='search'], form#search-form"
    PERIODE_SELECT = "select[name='periode']"
    STATUT_SELECT = "select[name='statut']"
    SUBMIT_BUTTON = "input[type='submit'], button[type='submit']"
    
    # Token PRADO
    PRADO_PAGESTATE = "input[name='PRADO_PAGESTATE']"


class DetailConsultationSelectors:
    """Sélecteurs pour la page de détail d'une consultation"""
    
    # Informations générales
    REF_CONSULTATION = "span.ref-consultation, div.reference"
    TITRE = "h1.titre, h2.titre-consultation"
    OBJET = "div.objet, p.description"
    TYPE_MARCHE = "span.type-marche"
    
    # Dates
    DATE_PUBLICATION = "span.date-publication"
    DATE_LIMITE = "span.date-limite"
    DATE_SEANCE = "span.date-seance"
    
    # Organisme
    ORGANISME_NOM = "div.organisme-nom"
    ORGANISME_VILLE = "span.organisme-ville"
    ORGANISME_TEL = "span.organisme-tel"
    ORGANISME_EMAIL = "a[href^='mailto:']"
    
    # Financier
    MONTANT_ESTIME = "span.montant-estime"
    CAUTIONNEMENT = "span.cautionnement"
    
    # Secteur
    SECTEUR = "span.secteur"
    CODE_CPV = "span.code-cpv"
    
    # Documents
    URL_AVIS = "a[href*='avis']"
    URL_DCE = "a[href*='dce']"
    
    # Lots
    LOTS_TABLE = "table.lots, table[id*='lot']"
    LOT_ROW = "tr.lot, tbody tr"


class PVSelectors:
    """Sélecteurs pour les procès-verbaux"""
    
    TABLE = "table.pv-table, table.data-table, table"
    ROWS = "tbody tr"
    
    REF_CONSULTATION = "td:nth-child(1)"
    ORGANISME = "td:nth-child(2)"
    TYPE_PV = "td:nth-child(3)"
    DATE_SEANCE = "td:nth-child(4)"
    DATE_PUBLICATION = "td:nth-child(5)"
    PV_LINK = "a[href*='pv'], a.pv-link, a[href*='telecharger'], a[href*='download']"


class AttributionSelectors:
    """Sélecteurs pour les attributions"""
    
    TABLE = "table.attribution-table"
    ROWS = "tbody tr"
    
    REF_CONSULTATION = "td:nth-child(1)"
    ORGANISME = "td:nth-child(2)"
    ENTREPRISE = "td:nth-child(3)"
    MONTANT = "td:nth-child(4)"
    DATE_ATTRIBUTION = "td:nth-child(5)"
    DETAIL_LINK = "a[href*='attribution']"


class CommonSelectors:
    """Sélecteurs communs à plusieurs pages"""
    
    # Messages d'erreur
    ERROR_MESSAGE = "div.error, div.alert-danger, span.error-message"
    EMPTY_RESULTS = "div.no-results, p:contains('Aucun résultat')"
    
    # Loading/AJAX
    LOADING_SPINNER = "div.loading, div.spinner"
    
    # Captcha (si présent)
    CAPTCHA = "div.captcha, img[alt*='captcha']"


# URLs de base
class URLs:
    """URLs du portail PMMP"""
    BASE = "https://www.marchespublics.gov.ma"
    
    # Consultations
    CONSULTATIONS_EN_COURS = f"{BASE}/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&EnCours&searchAnnCons"
    CONSULTATIONS_SEARCH = f"{BASE}/index.php?page=entreprise.EntrepriseAdvancedSearch"
    
    # PV
    PV_EXTRAITS = f"{BASE}/index.php?page=entreprise.EntrepriseAdvancedSearch&AvisExtraitPV"
    
    # Résultats
    ATTRIBUTIONS = f"{BASE}/index.php?page=entreprise.EntrepriseAdvancedSearch&ResultatDefinitif"
    
    # Détails
    DETAIL_CONSULTATION = f"{BASE}/index.php?page=entreprise.EntrepriseDetailsConsultation"
    LISTE_PPS = f"{BASE}/index.php?page=entreprise.ListePPs"
