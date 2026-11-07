from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from database import get_db
from auth import get_current_user
from datetime import datetime

router_ref = APIRouter(prefix="/api/references", tags=["references"])

JOURNAUX_AUTORISES = {
    "AC", "VT", "BQ", "CA", "OD", "AN", "EN", "AE", "AV", "AM", "TV", "PR", "SA"
}


def _journal_valide(journal: str) -> str:
    code = (journal or "").strip().upper()
    if code not in JOURNAUX_AUTORISES:
        raise HTTPException(422, f"Journal inconnu : {journal!r}")
    return code


@router_ref.get("/prochain-numero")
def prochain_numero(
    journal: str = Query(..., description="Code du journal comptable"),
    exercice: Optional[int] = Query(None, description="Année de l'exercice sélectionné"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Prévisualise le prochain numéro *interne* d'écriture.

    Ce numéro n'est pas une référence de pièce. Depuis 07C.2, il s'agit d'une
    prévision non réservée : le numéro réel n'est attribué par PostgreSQL qu'au
    moment de la validation définitive. Deux brouillons peuvent donc afficher la
    même prévision sans conflit.

    Exemple indicatif : BQ-2027-0001.
    """
    code = _journal_valide(journal)
    annee = int(exercice or datetime.now().year)

    dernier = db.execute(text("""
        SELECT dernier_numero
          FROM ecriture_sequences
         WHERE societe_id = :sid
           AND exercice = :exercice
           AND journal = :journal
    """), {
        "sid": current_user["societe_id"],
        "exercice": annee,
        "journal": code,
    }).scalar()

    prochain = int(dernier or 0) + 1
    numero = f"{code}-{annee}-{prochain:04d}"
    return {
        "numero": numero,
        "journal": code,
        "exercice": annee,
        "prochain": prochain,
        "reserve": False,
        "attribue_a": "validation",
        "nature": "numero_ecriture_interne_prevision",
    }


@router_ref.get("/verifier-doublon")
def verifier_doublon(
    reference: str = Query(...),
    journal: str = Query(...),
    exercice: Optional[int] = Query(None),
    exclude_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Vérifie un doublon de *référence de pièce*.

    La référence de pièce est un identifiant externe (n° facture fournisseur,
    relevé, chèque, contrat...). Elle reste distincte du numéro interne
    d'écriture attribué automatiquement.
    """
    ref = (reference or "").strip()
    if not ref:
        return {"doublon": False}

    code = _journal_valide(journal)
    conditions = [
        "e.societe_id = :sid",
        "e.journal::text = :journal",
        "LOWER(COALESCE(e.reference, '')) = LOWER(:reference)",
    ]
    params = {
        "sid": current_user["societe_id"],
        "journal": code,
        "reference": ref,
    }
    if exercice is not None:
        conditions.append("e.exercice = :exercice")
        params["exercice"] = int(exercice)
    if exclude_id is not None:
        conditions.append("e.id <> :exclude_id")
        params["exclude_id"] = int(exclude_id)

    result = db.execute(text(f"""
        SELECT e.id, e.numero_ecriture, e.date, e.libelle, e.reference
          FROM ecritures e
         WHERE {' AND '.join(conditions)}
         ORDER BY e.id
         LIMIT 1
    """), params).fetchone()

    if result:
        return {
            "doublon": True,
            "ecriture": {
                "id": result[0],
                "numero_ecriture": result[1],
                "date": str(result[2]),
                "libelle": result[3],
                "reference": result[4],
            },
        }
    return {"doublon": False}
