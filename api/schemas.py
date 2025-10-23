"""
Schémas Pydantic pour validation et sérialisation des réponses API
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TypeMarche(str, Enum):
    TRAVAUX = "travaux"
    FOURNITURES = "fournitures"
    SERVICES = "services"
    ETUDES = "etudes"


class StatutConsultation(str, Enum):
    EN_COURS = "en_cours"
    CLOTURE = "cloture"
    ANNULE = "annule"
    REPORTE = "reporte"


# ============================================================================
# SCHEMAS CONSULTATIONS
# ============================================================================

class ConsultationBase(BaseModel):
    ref_consultation: str
    organisme_acronyme: str
    titre: str
    type_marche: Optional[str] = None
    statut: Optional[str] = None
    date_publication: Optional[datetime] = None
    date_limite: Optional[datetime] = None
    montant_estime: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConsultationResponse(ConsultationBase):
    """Réponse API pour une consultation (vue liste)"""
    organisme_nom_complet: Optional[str] = None
    organisme_ville: Optional[str] = None
    secteur: Optional[str] = None
    url_detail: Optional[str] = None


class LotResponse(BaseModel):
    """Réponse pour un lot"""
    numero_lot: str
    designation: str
    montant_estime: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConsultationDetail(ConsultationResponse):
    """Réponse détaillée avec relations"""
    objet: Optional[str] = None
    organisme_telephone: Optional[str] = None
    organisme_email: Optional[str] = None
    cautionnement_provisoire: Optional[float] = None
    code_cpv: Optional[str] = None
    url_avis: Optional[str] = None
    url_dce: Optional[str] = None
    date_extraction: Optional[datetime] = None
    
    # Relations
    lots: List[LotResponse] = []


# ============================================================================
# SCHEMAS PV
# ============================================================================

class PVResponse(BaseModel):
    """Réponse pour un procès-verbal"""
    ref_consultation: str
    organisme_acronyme: str
    type_pv: Optional[str] = None
    date_seance: Optional[datetime] = None
    date_publication_pv: Optional[datetime] = None
    contenu: Optional[str] = None
    nombre_soumissionnaires: Optional[int] = None
    url_pv: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS ATTRIBUTIONS
# ============================================================================

class AttributionResponse(BaseModel):
    """Réponse pour une attribution"""
    ref_consultation: str
    organisme_acronyme: str
    date_attribution: Optional[date] = None
    entreprise_nom: str
    entreprise_ice: Optional[str] = None
    entreprise_ville: Optional[str] = None
    montant_ht: Optional[float] = None
    montant_ttc: Optional[float] = None
    taux_rabais: Optional[float] = None
    numero_lot: Optional[str] = None
    url_resultat: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEMAS STATISTIQUES
# ============================================================================

class StatsResponse(BaseModel):
    """Statistiques globales"""
    total_consultations: int
    consultations_en_cours: int
    total_attributions: int
    montant_total_estime: float
    montant_total_attribue: float
    nombre_organismes: int
    nombre_entreprises: int
    derniere_extraction: Optional[datetime] = None
