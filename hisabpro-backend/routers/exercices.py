# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth import get_current_user, requiert_admin, requiert_ecriture
from database import get_db
import models
from services.exercices_utils import generer_periodes_dates, statut_exercice_par_defaut, valider_duree_exercice
from services.exercices_service import (
    ensure_exercice,
    _creer_periodes_si_absentes,
    marquer_exercice_cloture,
    preparer_exercice_suivant,
    synchroniser_exercices,
    verifier_chevauchement,
)

router = APIRouter(prefix="/api/exercices", tags=["exercices"])


def _set_audit_periode(db: Session, current_user: dict, motif: str):
    db.execute(text("SELECT set_config('hisabpro.audit_actor_id', :v, true)"),
               {"v": str(current_user.get("id") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_motif', :v, true)"),
               {"v": motif})



class ExerciceCreate(BaseModel):
    annee: int
    date_debut: date
    date_fin: date

    @field_validator("annee")
    @classmethod
    def annee_valide(cls, v):
        if v < 1900 or v > 2200:
            raise ValueError("Année d'exercice invalide.")
        return v


class ExerciceUpdate(BaseModel):
    date_debut: date
    date_fin: date


class PeriodeStatutIn(BaseModel):
    statut: str

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v not in {"ouverte", "fermee"}:
            raise ValueError("Statut attendu : ouverte ou fermee.")
        return v


def _valider_dates(debut: date, fin: date, annee: int):
    try:
        valider_duree_exercice(debut, fin)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if fin.year != annee:
        raise HTTPException(400,
            "L'année de référence doit correspondre à l'année de clôture de l'exercice. "
            "La date de début peut appartenir à l'année civile précédente.")


def _out(ex):
    libelle = str(ex.annee) if ex.date_debut.year == ex.date_fin.year else f"{ex.date_debut.year}/{ex.date_fin.year}"
    return {
        "id": ex.id,
        "annee": ex.annee,
        "libelle": libelle,
        "date_debut": ex.date_debut.isoformat(),
        "date_fin": ex.date_fin.isoformat(),
        "statut": ex.statut,
        "nb_periodes": len(ex.periodes or []),
    }


@router.get("")
def lister_exercices(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # La consultation ne prépare ni ne modifie aucun calendrier, notamment
    # avec un profil lecture ou sur une connexion PostgreSQL en lecture seule.
    rows = db.query(models.ExerciceComptable).filter_by(
        societe_id=current_user["societe_id"]
    ).order_by(models.ExerciceComptable.date_debut.asc()).all()
    return [_out(x) for x in rows]


@router.post("/synchroniser")
def synchroniser_calendrier(
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Prépare explicitement le calendrier existant, avec droits administrateur."""
    rows = synchroniser_exercices(db, current_user["societe_id"])
    return [_out(x) for x in rows]


@router.post("", status_code=201)
def creer_exercice(
    data: ExerciceCreate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _valider_dates(data.date_debut, data.date_fin, data.annee)
    if db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=data.annee).first():
        raise HTTPException(409, f"L'exercice {data.annee} existe déjà.")
    chevauche = verifier_chevauchement(db, societe_id, data.date_debut, data.date_fin)
    if chevauche:
        raise HTTPException(409, f"Les dates chevauchent l'exercice {chevauche.annee}.")
    ex = ensure_exercice(db, societe_id, data.annee, data.date_debut, data.date_fin)
    ex.statut = statut_exercice_par_defaut(data.date_debut, data.date_fin)
    db.commit()
    db.refresh(ex)
    return _out(ex)


@router.patch("/{annee}")
def modifier_exercice(
    annee: int,
    data: ExerciceUpdate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _valider_dates(data.date_debut, data.date_fin, annee)
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=annee).first()
    if not ex:
        raise HTTPException(404, "Exercice introuvable.")
    if ex.statut == "cloture":
        raise HTTPException(423, "Un exercice clôturé est définitif et ses dates ne peuvent plus être modifiées.")

    hors_plage = db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        models.Ecriture.exercice == annee,
        ((models.Ecriture.date < data.date_debut) | (models.Ecriture.date > data.date_fin)),
    ).count()
    if hors_plage:
        raise HTTPException(409, f"{hors_plage} écriture(s) sortiraient de la nouvelle période.")
    chevauche = verifier_chevauchement(db, societe_id, data.date_debut, data.date_fin, ex.id)
    if chevauche:
        raise HTTPException(409, f"Les dates chevauchent l'exercice {chevauche.annee}.")

    # Les dates ne peuvent plus être déplacées après fermeture définitive d'une
    # sous-période : on évite ainsi de réécrire rétroactivement le calendrier.
    fermees = db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id, statut="fermee").count()
    if fermees:
        raise HTTPException(409, "Des périodes sont déjà définitivement fermées : les dates de l'exercice ne sont plus modifiables.")

    ex.date_debut, ex.date_fin = data.date_debut, data.date_fin
    ex.statut = statut_exercice_par_defaut(data.date_debut, data.date_fin)
    db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id).delete(synchronize_session=False)
    db.flush()
    _creer_periodes_si_absentes(db, ex)
    db.commit()
    db.refresh(ex)
    return _out(ex)


@router.post("/{annee}/preparer-suivant")
def preparer_suivant(
    annee: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    ex = ensure_exercice(db, societe_id, annee)
    try:
        suivant = preparer_exercice_suivant(db, societe_id, ex)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    db.commit()
    db.refresh(suivant)
    return _out(suivant)


@router.get("/{annee}/periodes")
def lister_periodes(
    annee: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=current_user["societe_id"], annee=annee
    ).first()
    if not ex:
        raise HTTPException(404, "Exercice introuvable. Préparez d'abord l'exercice depuis le module Exercices.")
    rows = db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id).order_by(
        models.PeriodeComptable.numero.asc()).all()
    return [{
        "id": p.id,
        "numero": p.numero,
        "libelle": p.libelle,
        "date_debut": p.date_debut.isoformat(),
        "date_fin": p.date_fin.isoformat(),
        "statut": p.statut,
        "date_fermeture": p.date_fermeture.isoformat() if p.date_fermeture else None,
    } for p in rows]


@router.patch("/{annee}/periodes/{numero}")
def changer_statut_periode(
    annee: int,
    numero: int,
    data: PeriodeStatutIn,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=annee
    ).with_for_update().first()
    if not ex:
        raise HTTPException(404, "Exercice introuvable.")
    if ex.statut == "cloture" or db.query(models.ClotureExercice.id).filter_by(
        societe_id=societe_id, exercice=annee
    ).first():
        raise HTTPException(423, "Exercice définitivement clôturé : ses périodes restent verrouillées.")
    p = db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id, numero=numero).first()
    if not p:
        raise HTTPException(404, "Période introuvable.")

    if data.statut == p.statut:
        return {"numero": p.numero, "libelle": p.libelle, "statut": p.statut}

    if data.statut == "fermee":
        if p.statut == "a_venir":
            raise HTTPException(409, f"{p.libelle} n'est pas encore ouverte.")
        brouillons = db.query(models.Ecriture).filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == annee,
            models.Ecriture.date >= p.date_debut,
            models.Ecriture.date <= p.date_fin,
            models.Ecriture.est_validee == False,  # noqa: E712
        ).count()
        if brouillons:
            raise HTTPException(409,
                f"{brouillons} écriture(s) en brouillon sur {p.libelle}. Validez-les avant fermeture.")
        _set_audit_periode(db, current_user, f"Fermeture de {p.libelle} (réouverture administrative possible)")
        p.statut = "fermee"
        p.date_fermeture = datetime.now()
    else:
        _set_audit_periode(db, current_user, f"Réouverture administrative de {p.libelle}")
        p.statut = "ouverte"
        p.date_fermeture = None

    db.commit()
    return {"numero": p.numero, "libelle": p.libelle, "statut": p.statut}


@router.post("/{annee}/periodes/ouvrir-toutes")
def ouvrir_toutes_periodes(
    annee: int,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Rouvre les douze périodes, y compris celles fermées manuellement.

    Exclusivement sur la société active et un exercice non clôturé. Chaque
    changement reste consigné par le trigger d'audit append-only.
    """
    societe_id = current_user["societe_id"]
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=annee
    ).with_for_update().first()
    if not ex:
        raise HTTPException(404, "Exercice introuvable.")
    if ex.statut == "cloture" or db.query(models.ClotureExercice.id).filter_by(
        societe_id=societe_id, exercice=annee
    ).first():
        raise HTTPException(423, "Exercice définitivement clôturé : ses périodes restent verrouillées.")

    periodes = db.query(models.PeriodeComptable).filter_by(
        exercice_id=ex.id
    ).order_by(models.PeriodeComptable.numero.asc()).all()
    _set_audit_periode(db, current_user, f"Réouverture globale des périodes de l'exercice {annee}")
    nb_modifiees = 0
    for periode in periodes:
        if periode.statut != "ouverte":
            periode.statut = "ouverte"
            periode.date_fermeture = None
            nb_modifiees += 1
    db.commit()
    return {"exercice": annee, "nb_ouvertes": len(periodes), "nb_modifiees": nb_modifiees}
