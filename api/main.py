"""
API REST FastAPI pour accéder aux données du PMMP
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import csv
import io
import logging

from database.connection import get_db
from api.schemas import (
    ConsultationResponse, ConsultationDetail, PVResponse, 
    AttributionResponse, StatsResponse
)
from api.crud import (
    get_consultations, get_consultation_by_ref, get_pvs,
    get_attributions, get_stats, search_consultations
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'app FastAPI
app = FastAPI(
    title="API PMMP - Portail Marchés Publics Marocains",
    description="API pour accéder aux données des marchés publics marocains",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API PMMP - Marchés Publics Marocains",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Vérification de santé de l'API et de la connexion DB"""
    try:
        # Test de connexion DB
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# ============================================================================
# ENDPOINTS CONSULTATIONS
# ============================================================================

@app.get("/api/v1/consultations", response_model=List[ConsultationResponse], tags=["Consultations"])
async def list_consultations(
    statut: Optional[str] = Query(None, description="Filtrer par statut (en_cours, cloture, etc.)"),
    type_marche: Optional[str] = Query(None, description="Type de marché (travaux, fournitures, services)"),
    organisme: Optional[str] = Query(None, description="Acronyme de l'organisme"),
    date_debut: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_fin: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Offset pour pagination"),
    db: Session = Depends(get_db)
):
    """
    Liste les consultations avec filtres optionnels
    
    Exemples:
    - /api/v1/consultations?statut=en_cours&limit=50
    - /api/v1/consultations?type_marche=travaux&organisme=ONEE
    """
    try:
        consultations = get_consultations(
            db=db,
            statut=statut,
            type_marche=type_marche,
            organisme=organisme,
            date_debut=date_debut,
            date_fin=date_fin,
            limit=limit,
            offset=offset
        )
        return consultations
    except Exception as e:
        logger.error(f"Error fetching consultations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/consultations/{ref_consultation}", response_model=ConsultationDetail, tags=["Consultations"])
async def get_consultation_detail(
    ref_consultation: str,
    db: Session = Depends(get_db)
):
    """
    Récupère le détail complet d'une consultation avec ses lots, PV, attributions
    """
    consultation = get_consultation_by_ref(db, ref_consultation)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    return consultation


@app.get("/api/v1/consultations/search", tags=["Consultations"])
async def search_consultations_endpoint(
    q: str = Query(..., min_length=3, description="Recherche dans titre et objet"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Recherche full-text dans les consultations
    
    Exemple: /api/v1/consultations/search?q=construction route
    """
    results = search_consultations(db, q, limit)
    return results


# ============================================================================
# ENDPOINTS PV
# ============================================================================

@app.get("/api/v1/pv", response_model=List[PVResponse], tags=["Procès-Verbaux"])
async def list_pv(
    ref_consultation: Optional[str] = Query(None, description="Référence consultation"),
    organisme: Optional[str] = Query(None, description="Organisme"),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Liste les procès-verbaux avec filtres"""
    pvs = get_pvs(
        db=db,
        ref_consultation=ref_consultation,
        organisme=organisme,
        date_debut=date_debut,
        date_fin=date_fin,
        limit=limit,
        offset=offset
    )
    return pvs


# ============================================================================
# ENDPOINTS ATTRIBUTIONS
# ============================================================================

@app.get("/api/v1/attributions", response_model=List[AttributionResponse], tags=["Attributions"])
async def list_attributions(
    ref_consultation: Optional[str] = Query(None),
    entreprise: Optional[str] = Query(None, description="Nom de l'entreprise"),
    organisme: Optional[str] = Query(None),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    montant_min: Optional[float] = Query(None, description="Montant minimum"),
    montant_max: Optional[float] = Query(None, description="Montant maximum"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Liste les attributions avec filtres"""
    attributions = get_attributions(
        db=db,
        ref_consultation=ref_consultation,
        entreprise=entreprise,
        organisme=organisme,
        date_debut=date_debut,
        date_fin=date_fin,
        montant_min=montant_min,
        montant_max=montant_max,
        limit=limit,
        offset=offset
    )
    return attributions


# ============================================================================
# ENDPOINTS STATISTIQUES
# ============================================================================

@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Statistiques"])
async def get_statistics(db: Session = Depends(get_db)):
    """
    Statistiques globales sur les marchés publics
    """
    stats = get_stats(db)
    return stats


@app.get("/api/v1/stats/organismes", tags=["Statistiques"])
async def get_organismes_stats(
    limit: int = Query(20, description="Top N organismes"),
    db: Session = Depends(get_db)
):
    """Top des organismes par nombre de consultations"""
    from database.models import Consultation
    from sqlalchemy import func
    
    results = db.query(
        Consultation.organisme_acronyme,
        Consultation.organisme_nom_complet,
        func.count(Consultation.id_interne).label('count'),
        func.sum(Consultation.montant_estime).label('total_montant')
    ).group_by(
        Consultation.organisme_acronyme,
        Consultation.organisme_nom_complet
    ).order_by(func.count(Consultation.id_interne).desc()).limit(limit).all()
    
    return [
        {
            "acronyme": r.organisme_acronyme,
            "nom": r.organisme_nom_complet,
            "nombre_consultations": r.count,
            "montant_total": float(r.total_montant) if r.total_montant else 0
        }
        for r in results
    ]


# ============================================================================
# ENDPOINTS EXPORT
# ============================================================================

@app.get("/api/v1/export/csv", tags=["Export"])
async def export_consultations_csv(
    statut: Optional[str] = None,
    type_marche: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Export des consultations au format CSV"""
    
    consultations = get_consultations(
        db=db,
        statut=statut,
        type_marche=type_marche,
        date_debut=date_debut,
        date_fin=date_fin,
        limit=10000
    )
    
    # Créer le CSV en mémoire
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'ref_consultation', 'titre', 'organisme_acronyme', 'type_marche',
        'statut', 'date_publication', 'date_limite', 'montant_estime'
    ])
    
    writer.writeheader()
    for c in consultations:
        writer.writerow({
            'ref_consultation': c.ref_consultation,
            'titre': c.titre,
            'organisme_acronyme': c.organisme_acronyme,
            'type_marche': c.type_marche,
            'statut': c.statut,
            'date_publication': c.date_publication.isoformat() if c.date_publication else '',
            'date_limite': c.date_limite.isoformat() if c.date_limite else '',
            'montant_estime': c.montant_estime or ''
        })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=consultations_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


# ============================================================================
# GESTION DES ERREURS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
