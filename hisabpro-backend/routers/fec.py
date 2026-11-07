# -*- coding: utf-8 -*-
"""Fichier des Écritures Comptables — Avis n°24 du CNC (Maroc).

L'annexe 3 de l'Avis n°24 fixe 18 informations minimales. L'export est refusé
lorsqu'un contrôle bloquant rendrait le fichier incomplet ou incohérent.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.fec_service import ENTETES_FEC_AVIS24, controler_fec, lignes_fec, nettoyer
from services.fec_exercice_service import charger_fec_exercice
from services.fec_source_recovery_service import recuperer_depuis_factures

# Le chargeur central précharge notamment :
# joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.lettrages)
# afin que le FEC expose le lettrage sans requêtes N+1.

router = APIRouter(prefix="/api/fec", tags=["fec"])




@router.post("/reparer-sources-factures")
def reparer_sources_factures_fec(
    exercice: int = Query(..., description="Année de référence de l'exercice"),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Récupère les auxiliaires/références historiques depuis les factures exactes.

    Patch 099 : le rapprochement exige une facture source non ambiguë sur le
    journal, la date et le TTC ; en cas de doute, aucune donnée n'est ajoutée.
    Les écritures définitives restent inchangées.
    """
    return recuperer_depuis_factures(
        db, current_user["societe_id"], exercice, created_by=current_user.get("id")
    )


@router.get("/apercu")
def apercu_fec(
    exercice: int = Query(..., description="Année de référence de l'exercice"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Contrôle réglementaire avant export.

    La réponse distingue les anomalies bloquantes des avertissements. Le frontend
    ne doit pas proposer de « forcer » un FEC qui échoue à un contrôle bloquant.
    """
    societe_id = current_user["societe_id"]
    ex, cloture, ecritures = charger_fec_exercice(db, societe_id, exercice)
    return controler_fec(ecritures, exercice, ex, cloture, db=db, societe_id=societe_id)


@router.get("/export")
def exporter_fec(
    exercice: int = Query(..., description="Année de référence de l'exercice à exporter"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")

    ex, cloture, ecritures = charger_fec_exercice(db, societe_id, exercice)
    controle = controler_fec(ecritures, exercice, ex, cloture, db=db, societe_id=societe_id)
    if not controle["conforme_export"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Export FEC bloqué : les contrôles Avis n°24 ont détecté des anomalies.",
                "controle": controle,
            },
        )

    lignes = ["\t".join(ENTETES_FEC_AVIS24)]
    for champs in lignes_fec(ecritures, exercice, cloture, db=db, societe_id=societe_id):
        # Garde-fou : l'annexe 3 prescrit exactement 18 informations minimales.
        if len(champs) != len(ENTETES_FEC_AVIS24):
            raise HTTPException(500, "Erreur interne : ligne FEC de longueur invalide.")
        lignes.append("\t".join(nettoyer(v) for v in champs))

    contenu = "\r\n".join(lignes)
    data = ("\ufeff" + contenu).encode("utf-8")

    ice = nettoyer(getattr(societe, "ice", "")) or str(societe_id)
    nom = f"{ice}_FEC_{exercice}.txt"
    return Response(
        content=data,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nom}"',
            "X-HisabPro-FEC-Standard": "CNC-Avis-24",
        },
    )
