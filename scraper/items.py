"""
Définition des items Scrapy (structures de données extraites)
"""
import scrapy
from scrapy.item import Item, Field
from datetime import datetime


class ConsultationItem(scrapy.Item):
    """Item pour les consultations (appels d'offres)"""
    # Identifiants
    ref_consultation = Field()
    organisme_acronyme = Field()
    
    # Informations principales
    titre = Field()
    objet = Field()
    type_marche = Field()
    
    # Dates
    date_publication = Field()
    date_limite = Field()
    date_seance = Field()
    
    # Statut
    statut = Field()
    
    # Détails financiers
    montant_estime = Field()
    cautionnement_provisoire = Field()
    
    # Informations organisme
    organisme_nom_complet = Field()
    organisme_ville = Field()
    organisme_telephone = Field()
    organisme_email = Field()
    
    # Classification
    secteur = Field()
    code_cpv = Field()
    
    # URLs
    url_detail = Field()
    url_avis = Field()
    url_dce = Field()
    
    # Métadonnées
    date_extraction = Field()
    page_html = Field()  # HTML brut pour archivage


class LotItem(scrapy.Item):
    """Item pour les lots d'un marché"""
    ref_consultation = Field()
    numero_lot = Field()
    designation = Field()
    description = Field()
    montant_estime = Field()
    cautionnement_provisoire = Field()
    cautionnement_definitif = Field()
    delai_execution = Field()
    date_extraction = Field()


class PVExtraitItem(scrapy.Item):
    """Item pour les extraits de procès-verbaux"""
    ref_consultation = Field()
    organisme_acronyme = Field()
    type_pv = Field()
    date_seance = Field()
    date_publication_pv = Field()
    contenu = Field()
    nombre_soumissionnaires = Field()
    url_pv = Field()
    date_extraction = Field()
    page_html = Field()


class AttributionItem(scrapy.Item):
    """Item pour les attributions de marchés"""
    ref_consultation = Field()
    organisme_acronyme = Field()
    date_attribution = Field()
    date_publication = Field()
    entreprise_nom = Field()
    entreprise_ice = Field()
    entreprise_ville = Field()
    montant_ht = Field()
    montant_ttc = Field()
    taux_rabais = Field()
    numero_lot = Field()
    designation_lot = Field()
    delai_execution = Field()
    url_resultat = Field()
    date_extraction = Field()
    page_html = Field()


class AchevementItem(scrapy.Item):
    """Item pour les rapports d'achèvement"""
    ref_consultation = Field()
    organisme_acronyme = Field()
    date_achevement = Field()
    date_publication = Field()
    entreprise_nom = Field()
    montant_definitif = Field()
    observations = Field()
    url_rapport = Field()
    date_extraction = Field()
    page_html = Field()
