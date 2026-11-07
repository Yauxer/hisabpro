# -*- coding: utf-8 -*-
import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

import models
from auth import get_current_user, requiert_ecriture
from database import get_db
from services.delais_paiement_service import construire_rapport

router = APIRouter(prefix="/api/delais-paiement", tags=["delais-paiement"])


class MetaDelaisPaiement(BaseModel):
    date_livraison_service: Optional[date] = None
    litige_judiciaire: Optional[bool] = None
    reference_litige: Optional[str] = Field(default=None, max_length=200)
    hors_champ: Optional[bool] = None
    motif_hors_champ: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def valider_coherence(self):
        if self.litige_judiciaire and not (self.reference_litige or "").strip():
            raise ValueError("Précisez la référence du litige judiciaire.")
        if self.hors_champ and not (self.motif_hors_champ or "").strip():
            raise ValueError("Précisez le motif de l'exclusion du champ de la loi 69-21.")
        return self


@router.get("")
def rapport_delais_paiement(
    annee: int = Query(..., ge=2023, le=2100),
    trimestre: int = Query(..., ge=1, le=4),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return construire_rapport(db, current_user["societe_id"], annee, trimestre)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.patch("/factures/{facture_id}", dependencies=[Depends(requiert_ecriture)])
def completer_facture_delais(
    facture_id: int,
    data: MetaDelaisPaiement,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    facture = db.query(models.Facture).filter_by(
        id=facture_id,
        societe_id=current_user["societe_id"],
    ).first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if getattr(getattr(facture, "type", None), "value", getattr(facture, "type", None)) != "achat":
        raise HTTPException(422, "Le reporting des délais de paiement concerne les factures fournisseurs.")

    payload = data.model_dump(exclude_unset=True)
    mapping = {
        "hors_champ": "delais_paiement_hors_champ",
        "motif_hors_champ": "delais_paiement_motif_hors_champ",
    }
    for cle, valeur in payload.items():
        setattr(facture, mapping.get(cle, cle), valeur)
    db.commit()
    return {"message": "Informations délais de paiement enregistrées", "facture_id": facture.id}


@router.get("/export.csv")
def exporter_delais_paiement(
    annee: int = Query(..., ge=2023, le=2100),
    trimestre: int = Query(..., ge=1, le=4),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = construire_rapport(db, current_user["societe_id"], annee, trimestre)
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Reference facture", "Date facture", "Date livraison/service", "Fournisseur",
        "Adresse fournisseur", "RC fournisseur", "IF fournisseur", "ICE fournisseur",
        "Nature marchandises/travaux/services", "Montant TTC", "Date echeance",
        "Montant non paye fin periode", "Montant paye hors delai periode",
        "Dates paiements hors delai", "Modes paiement", "References paiement",
        "Mois retard max", "Amende indicative MAD", "Litige judiciaire", "Reference litige",
        "Completude", "Informations manquantes",
    ])
    for r in rapport["factures"]:
        writer.writerow([
            r["reference_facture"], r["date_facture"], r["date_livraison_service"], r["fournisseur"],
            r["fournisseur_adresse"], r["fournisseur_rc"], r["fournisseur_if"], r["fournisseur_ice"],
            r["nature_operation"], f'{r["montant_ttc"]:.2f}', r["date_echeance"],
            f'{r["montant_non_paye_fin_periode"]:.2f}', f'{r["montant_paye_hors_delai_periode"]:.2f}',
            " | ".join(r["dates_paiements_hors_delai"]), " | ".join(r["modes_paiement"]),
            " | ".join(r["references_paiement"]), r["mois_retard_max"],
            "" if r["amende_indicative"] is None else f'{r["amende_indicative"]:.2f}',
            "Oui" if r["litige_judiciaire"] else "Non", r["reference_litige"],
            "OK" if r["completude"]["complete"] else "A completer",
            " | ".join(r["completude"]["manquants"]),
        ])

    headers = {"Content-Disposition": f'attachment; filename="delais_paiement_{annee}_T{trimestre}.csv"'}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers=headers)
