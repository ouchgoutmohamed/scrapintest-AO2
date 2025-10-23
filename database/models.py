"""
Modèles de base de données pour le système PMMP
Définit les tables: consultations, lots, pv_extraits, attributions, achevements
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, 
    Numeric, Boolean, ForeignKey, Enum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TypeMarche(str, enum.Enum):
    """Types de marchés publics"""
    TRAVAUX = "travaux"
    FOURNITURES = "fournitures"
    SERVICES = "services"
    ETUDES = "etudes"


class StatutConsultation(str, enum.Enum):
    """Statuts possibles d'une consultation"""
    EN_COURS = "en_cours"
    CLOTURE = "cloture"
    ANNULE = "annule"
    REPORTE = "reporte"
    INFRUCTUEUX = "infructueux"


class Consultation(Base):
    """Table principale des consultations (appels d'offres)"""
    __tablename__ = 'consultations'
    
    # Clé primaire
    id_interne = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiants officiels
    ref_consultation = Column(String(100), unique=True, nullable=False, index=True)
    organisme_acronyme = Column(String(50), nullable=False, index=True)
    
    # Informations principales
    titre = Column(Text, nullable=False)
    objet = Column(Text)
    type_marche = Column(Enum(TypeMarche), nullable=False)
    
    # Dates
    date_publication = Column(DateTime, nullable=False, index=True)
    date_limite = Column(DateTime)
    date_seance = Column(DateTime)
    
    # Statut
    statut = Column(Enum(StatutConsultation), nullable=False, default=StatutConsultation.EN_COURS)
    
    # Détails financiers
    montant_estime = Column(Numeric(15, 2))
    cautionnement_provisoire = Column(Numeric(15, 2))
    
    # Informations de contact
    organisme_nom_complet = Column(String(255))
    organisme_ville = Column(String(100))
    organisme_telephone = Column(String(50))
    organisme_email = Column(String(100))
    
    # Classification
    secteur = Column(String(100))
    code_cpv = Column(String(50))
    
    # URLs et sources
    url_detail = Column(String(500))
    url_avis = Column(String(500))
    url_dce = Column(String(500))  # Dossier de consultation
    
    # Métadonnées d'extraction
    date_extraction = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_derniere_maj = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    page_html_archivee = Column(Text)  # Path vers fichier HTML archivé
    
    # Relations
    lots = relationship("Lot", back_populates="consultation", cascade="all, delete-orphan")
    pv_extraits = relationship("PVExtrait", back_populates="consultation", cascade="all, delete-orphan")
    attributions = relationship("Attribution", back_populates="consultation", cascade="all, delete-orphan")
    achevements = relationship("Achevement", back_populates="consultation", cascade="all, delete-orphan")
    
    # Index composites
    __table_args__ = (
        Index('idx_consultation_organisme_date', 'organisme_acronyme', 'date_publication'),
        Index('idx_consultation_statut_date', 'statut', 'date_publication'),
        Index('idx_consultation_type_date', 'type_marche', 'date_publication'),
    )
    
    def __repr__(self):
        return f"<Consultation(ref={self.ref_consultation}, titre={self.titre[:50]})>"


class Lot(Base):
    """Table des lots pour les marchés subdivisés"""
    __tablename__ = 'lots'
    
    id_lot = Column(Integer, primary_key=True, autoincrement=True)
    ref_consultation = Column(String(100), ForeignKey('consultations.ref_consultation', ondelete='CASCADE'), nullable=False)
    
    # Informations du lot
    numero_lot = Column(String(20), nullable=False)
    designation = Column(Text, nullable=False)
    description = Column(Text)
    
    # Détails financiers
    montant_estime = Column(Numeric(15, 2))
    cautionnement_provisoire = Column(Numeric(15, 2))
    cautionnement_definitif = Column(Numeric(15, 2))
    
    # Délais
    delai_execution = Column(String(100))
    
    # Métadonnées
    date_extraction = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    consultation = relationship("Consultation", back_populates="lots")
    
    __table_args__ = (
        Index('idx_lot_consultation', 'ref_consultation'),
    )
    
    def __repr__(self):
        return f"<Lot(ref={self.ref_consultation}, numero={self.numero_lot})>"


class PVExtrait(Base):
    """Table des extraits de procès-verbaux"""
    __tablename__ = 'pv_extraits'
    
    id_pv = Column(Integer, primary_key=True, autoincrement=True)
    ref_consultation = Column(String(100), ForeignKey('consultations.ref_consultation', ondelete='CASCADE'), nullable=False)
    organisme_acronyme = Column(String(50), nullable=False)
    
    # Informations du PV
    type_pv = Column(String(50))  # ex: "Ouverture des plis", "Jugement des offres"
    date_seance = Column(DateTime)
    date_publication_pv = Column(DateTime, nullable=False, index=True)
    
    # Contenu
    contenu = Column(Text)
    nombre_soumissionnaires = Column(Integer)
    
    # URLs
    url_pv = Column(String(500))
    
    # Métadonnées
    date_extraction = Column(DateTime, default=datetime.utcnow, nullable=False)
    page_html_archivee = Column(Text)
    
    # Relations
    consultation = relationship("Consultation", back_populates="pv_extraits")
    
    __table_args__ = (
        Index('idx_pv_consultation', 'ref_consultation'),
        Index('idx_pv_date', 'date_publication_pv'),
    )
    
    def __repr__(self):
        return f"<PVExtrait(ref={self.ref_consultation}, type={self.type_pv})>"


class Attribution(Base):
    """Table des résultats définitifs (attributions)"""
    __tablename__ = 'attributions'
    
    id_attribution = Column(Integer, primary_key=True, autoincrement=True)
    ref_consultation = Column(String(100), ForeignKey('consultations.ref_consultation', ondelete='CASCADE'), nullable=False)
    organisme_acronyme = Column(String(50), nullable=False)
    
    # Informations de l'attribution
    date_attribution = Column(Date, nullable=False, index=True)
    date_publication = Column(DateTime, index=True)
    
    # Entreprise attributaire
    entreprise_nom = Column(String(255), nullable=False)
    entreprise_ice = Column(String(50))  # Identifiant Commun de l'Entreprise
    entreprise_ville = Column(String(100))
    
    # Détails financiers
    montant_ht = Column(Numeric(15, 2))
    montant_ttc = Column(Numeric(15, 2))
    taux_rabais = Column(Numeric(5, 2))
    
    # Lot concerné (si applicable)
    numero_lot = Column(String(20))
    designation_lot = Column(Text)
    
    # Délai
    delai_execution = Column(String(100))
    
    # URLs
    url_resultat = Column(String(500))
    
    # Métadonnées
    date_extraction = Column(DateTime, default=datetime.utcnow, nullable=False)
    page_html_archivee = Column(Text)
    
    # Relations
    consultation = relationship("Consultation", back_populates="attributions")
    
    __table_args__ = (
        Index('idx_attribution_consultation', 'ref_consultation'),
        Index('idx_attribution_entreprise', 'entreprise_nom'),
        Index('idx_attribution_date', 'date_attribution'),
    )
    
    def __repr__(self):
        return f"<Attribution(ref={self.ref_consultation}, entreprise={self.entreprise_nom})>"


class Achevement(Base):
    """Table des rapports d'achèvement"""
    __tablename__ = 'achevements'
    
    id_achevement = Column(Integer, primary_key=True, autoincrement=True)
    ref_consultation = Column(String(100), ForeignKey('consultations.ref_consultation', ondelete='CASCADE'), nullable=False)
    organisme_acronyme = Column(String(50), nullable=False)
    
    # Informations de l'achèvement
    date_achevement = Column(Date, nullable=False, index=True)
    date_publication = Column(DateTime)
    
    # Détails
    entreprise_nom = Column(String(255))
    montant_definitif = Column(Numeric(15, 2))
    observations = Column(Text)
    
    # URLs
    url_rapport = Column(String(500))
    
    # Métadonnées
    date_extraction = Column(DateTime, default=datetime.utcnow, nullable=False)
    page_html_archivee = Column(Text)
    
    # Relations
    consultation = relationship("Consultation", back_populates="achevements")
    
    __table_args__ = (
        Index('idx_achevement_consultation', 'ref_consultation'),
        Index('idx_achevement_date', 'date_achevement'),
    )
    
    def __repr__(self):
        return f"<Achevement(ref={self.ref_consultation}, date={self.date_achevement})>"


class ExtractionLog(Base):
    """Table pour logger les exécutions du scraper"""
    __tablename__ = 'extraction_logs'
    
    id_log = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informations de l'extraction
    date_execution = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    spider_name = Column(String(100), nullable=False)
    statut = Column(String(20), nullable=False)  # success, failed, partial
    
    # Statistiques
    pages_parcourues = Column(Integer, default=0)
    items_extraits = Column(Integer, default=0)
    items_inseres = Column(Integer, default=0)
    items_mis_a_jour = Column(Integer, default=0)
    erreurs = Column(Integer, default=0)
    
    # Détails
    duree_secondes = Column(Integer)
    message = Column(Text)
    erreur_details = Column(Text)
    
    def __repr__(self):
        return f"<ExtractionLog(spider={self.spider_name}, date={self.date_execution}, statut={self.statut})>"
