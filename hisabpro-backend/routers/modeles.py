from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/modeles", tags=["modeles"])


class LigneModeleOut(BaseModel):
    ordre:         int
    compte:        str
    libelle:       Optional[str] = None
    sens:          Optional[str] = None
    est_principal: Optional[bool] = False
    est_tva:       Optional[bool] = False
    taux_tva:      Optional[float] = None


class ModeleOut(BaseModel):
    id:                 int
    code:               str
    libelle:            str
    journal:            Optional[str] = None
    compte_declencheur: Optional[str] = None
    libelle_auto:       Optional[str] = None
    lignes:             List[LigneModeleOut] = []


@router.get("/par-compte/{compte}", response_model=List[ModeleOut])
def modeles_par_compte(
    compte: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne les modèles d'écritures correspondant à un compte donné."""
    resultats = []

    for longueur in [4, 3, 2]:
        if len(compte) < longueur:
            continue
        prefixe = compte[:longueur]

        rows = db.execute(text("""
            SELECT id, code, libelle, journal, compte_declencheur, libelle_auto
            FROM modeles_ecritures
            WHERE actif = true
              AND compte_declencheur LIKE :prefixe
              AND (SELECT COUNT(*) FROM lignes_modele lm WHERE lm.modele_id = modeles_ecritures.id) >= 2
            ORDER BY code
        """), {"prefixe": f"{prefixe}%"}).fetchall()

        for row in rows:
            if any(r["id"] == row[0] for r in resultats):
                continue

            lignes = db.execute(text("""
                SELECT ordre, compte, libelle, sens, est_principal, est_tva, taux_tva
                FROM lignes_modele
                WHERE modele_id = :mid
                ORDER BY ordre
            """), {"mid": row[0]}).fetchall()

            resultats.append({
                "id":                 row[0],
                "code":               row[1],
                "libelle":            row[2],
                "journal":            row[3],
                "compte_declencheur": row[4],
                "libelle_auto":       row[5],
                "lignes": [{
                    "ordre":         l[0],
                    "compte":        l[1],
                    "libelle":       l[2],
                    "sens":          l[3],
                    "est_principal": l[4],
                    "est_tva":       l[5],
                    "taux_tva":      l[6],
                } for l in lignes],
            })

        if resultats:
            break

    return resultats


@router.get("", response_model=List[ModeleOut])
def lister_modeles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT id, code, libelle, journal, compte_declencheur, libelle_auto
        FROM modeles_ecritures
        WHERE actif = true
          AND (SELECT COUNT(*) FROM lignes_modele lm WHERE lm.modele_id = modeles_ecritures.id) >= 2
        ORDER BY code
    """)).fetchall()

    resultats = []
    for row in rows:
        lignes = db.execute(text("""
            SELECT ordre, compte, libelle, sens, est_principal, est_tva, taux_tva
            FROM lignes_modele
            WHERE modele_id = :mid
            ORDER BY ordre
        """), {"mid": row[0]}).fetchall()

        resultats.append({
            "id":                 row[0],
            "code":               row[1],
            "libelle":            row[2],
            "journal":            row[3],
            "compte_declencheur": row[4],
            "libelle_auto":       row[5],
            "lignes": [{
                "ordre":         l[0],
                "compte":        l[1],
                "libelle":       l[2],
                "sens":          l[3],
                "est_principal": l[4],
                "est_tva":       l[5],
                "taux_tva":      l[6],
            } for l in lignes],
        })

    return resultats
