# -*- coding: utf-8 -*-
"""Chargement et contrôle FEC d'un exercice depuis PostgreSQL.

Centralise la source utilisée par l'aperçu/export FEC, la clôture et la liasse
afin qu'aucun de ces parcours ne puisse appliquer un jeu de contrôles différent.
"""
from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

import models
from services.fec_service import controler_fec


def charger_fec_exercice(db: Session, societe_id: int, exercice: int):
    exercice_obj = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    cloture = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    ecritures = (
        db.query(models.Ecriture)
        .options(
            joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.lettrages),
            joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.auxiliaire_complements),
            joinedload(models.Ecriture.justificatifs),
        )
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
        )
        .order_by(models.Ecriture.date, models.Ecriture.id)
        .all()
    )
    return exercice_obj, cloture, ecritures


def controler_fec_exercice(db: Session, societe_id: int, exercice: int) -> dict:
    exercice_obj, cloture, ecritures = charger_fec_exercice(
        db, societe_id, exercice
    )
    return controler_fec(ecritures, exercice, exercice_obj, cloture, db=db, societe_id=societe_id)
