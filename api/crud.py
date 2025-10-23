"""
Fonctions CRUD pour l'accès aux données
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import date, datetime

from database.models import (
    Consultation, Lot, PVExtrait, Attribution, Achevement, StatutConsultation
)


# ============================================================================
# CONSULTATIONS
# ============================================================================

def get_consultations(
    db: Session,
    statut: Optional[str] = None,
    type_marche: Optional[str] = None,
    organisme: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Consultation]:
    """Récupère les consultations avec filtres"""
    
    query = db.query(Consultation)
    
    # Filtres
    if statut:
        query = query.filter(Consultation.statut == statut)
    
    if type_marche:
        query = query.filter(Consultation.type_marche == type_marche)
    
    if organisme:
        query = query.filter(Consultation.organisme_acronyme.ilike(f"%{organisme}%"))
    
    if date_debut:
        query = query.filter(Consultation.date_publication >= date_debut)
    
    if date_fin:
        query = query.filter(Consultation.date_publication <= date_fin)
    
    # Tri et pagination
    query = query.order_by(Consultation.date_publication.desc())
    query = query.offset(offset).limit(limit)
    
    return query.all()


def get_consultation_by_ref(db: Session, ref: str) -> Optional[Consultation]:
    """Récupère une consultation par sa référence"""
    return db.query(Consultation).filter(
        Consultation.ref_consultation == ref
    ).first()


def search_consultations(db: Session, search_term: str, limit: int = 100) -> List[Consultation]:
    """Recherche full-text dans les consultations"""
    search = f"%{search_term}%"
    
    query = db.query(Consultation).filter(
        or_(
            Consultation.titre.ilike(search),
            Consultation.objet.ilike(search),
            Consultation.ref_consultation.ilike(search)
        )
    ).order_by(Consultation.date_publication.desc()).limit(limit)
    
    return query.all()


# ============================================================================
# PV
# ============================================================================

def get_pvs(
    db: Session,
    ref_consultation: Optional[str] = None,
    organisme: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> List[PVExtrait]:
    """Récupère les PV avec filtres"""
    
    query = db.query(PVExtrait)
    
    if ref_consultation:
        query = query.filter(PVExtrait.ref_consultation == ref_consultation)
    
    if organisme:
        query = query.filter(PVExtrait.organisme_acronyme.ilike(f"%{organisme}%"))
    
    if date_debut:
        query = query.filter(PVExtrait.date_publication_pv >= date_debut)
    
    if date_fin:
        query = query.filter(PVExtrait.date_publication_pv <= date_fin)
    
    query = query.order_by(PVExtrait.date_publication_pv.desc())
    query = query.offset(offset).limit(limit)
    
    return query.all()


# ============================================================================
# ATTRIBUTIONS
# ============================================================================

def get_attributions(
    db: Session,
    ref_consultation: Optional[str] = None,
    entreprise: Optional[str] = None,
    organisme: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    montant_min: Optional[float] = None,
    montant_max: Optional[float] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Attribution]:
    """Récupère les attributions avec filtres"""
    
    query = db.query(Attribution)
    
    if ref_consultation:
        query = query.filter(Attribution.ref_consultation == ref_consultation)
    
    if entreprise:
        query = query.filter(Attribution.entreprise_nom.ilike(f"%{entreprise}%"))
    
    if organisme:
        query = query.filter(Attribution.organisme_acronyme.ilike(f"%{organisme}%"))
    
    if date_debut:
        query = query.filter(Attribution.date_attribution >= date_debut)
    
    if date_fin:
        query = query.filter(Attribution.date_attribution <= date_fin)
    
    if montant_min:
        query = query.filter(Attribution.montant_ttc >= montant_min)
    
    if montant_max:
        query = query.filter(Attribution.montant_ttc <= montant_max)
    
    query = query.order_by(Attribution.date_attribution.desc())
    query = query.offset(offset).limit(limit)
    
    return query.all()


# ============================================================================
# STATISTIQUES
# ============================================================================

def get_stats(db: Session) -> dict:
    """Calcule les statistiques globales"""
    
    total_consultations = db.query(func.count(Consultation.id_interne)).scalar()
    
    consultations_en_cours = db.query(func.count(Consultation.id_interne)).filter(
        Consultation.statut == 'en_cours'
    ).scalar()
    
    total_attributions = db.query(func.count(Attribution.id_attribution)).scalar()
    
    montant_total_estime = db.query(
        func.sum(Consultation.montant_estime)
    ).scalar() or 0
    
    montant_total_attribue = db.query(
        func.sum(Attribution.montant_ttc)
    ).scalar() or 0
    
    nombre_organismes = db.query(
        func.count(func.distinct(Consultation.organisme_acronyme))
    ).scalar()
    
    nombre_entreprises = db.query(
        func.count(func.distinct(Attribution.entreprise_nom))
    ).scalar()
    
    derniere_extraction = db.query(
        func.max(Consultation.date_extraction)
    ).scalar()
    
    return {
        "total_consultations": total_consultations,
        "consultations_en_cours": consultations_en_cours,
        "total_attributions": total_attributions,
        "montant_total_estime": float(montant_total_estime),
        "montant_total_attribue": float(montant_total_attribue),
        "nombre_organismes": nombre_organismes,
        "nombre_entreprises": nombre_entreprises,
        "derniere_extraction": derniere_extraction
    }
