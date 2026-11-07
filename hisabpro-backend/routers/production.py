from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from auth import requiert_admin
from services.production_audit_service import controler_production

router = APIRouter(prefix="/api/production", tags=["production"])


@router.get("/controle")
def controle_production(
    exercice: int | None = Query(default=None),
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Audit de cohérence lecture seule avant mise en production."""
    return controler_production(db, current_user["societe_id"], exercice)


@router.get("/audit-actions")
def audit_actions(
    limit: int = Query(default=200, ge=1, le=1000),
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Journal applicatif append-only des opérations modifiantes."""
    rows = db.execute(text("""
        SELECT id, societe_id, acteur_id, acteur_nom, acteur_email, acteur_role, methode, chemin,
               statut_http, succes, ip, request_id, created_at
          FROM audit_actions
         WHERE societe_id = :sid
         ORDER BY created_at DESC, id DESC
         LIMIT :lim
    """), {"sid": current_user["societe_id"], "lim": limit}).mappings().all()
    return [dict(r) for r in rows]
