# -*- coding: utf-8 -*-
"""Préparer les exercices antérieurs sans toucher aux périodes existantes."""
from datetime import date, timedelta


def periodes_a_preparer(annee_debut: int, premier_exercice=None, annee_courante=None):
    """Retourne des triplets (année de clôture, début, fin), chronologiques.

    Un premier exercice décalé (01/07/2026–30/06/2027) laisse la possibilité
    d'ajouter un exercice court 01/01/2026–30/06/2026. Aucune période déjà
    enregistrée n'est réécrite.
    """
    annee = int(annee_debut)
    if not 1900 <= annee <= 2200:
        raise ValueError("L’année de début doit être comprise entre 1900 et 2200.")
    if premier_exercice and annee > premier_exercice.date_debut.year:
        raise ValueError(
            f"L’exercice {premier_exercice.annee} existe déjà. Impossible d’avancer "
            "l’année de début sans supprimer des données historiques."
        )
    borne = premier_exercice.annee if premier_exercice else int(annee_courante or date.today().year) + 1
    if borne - annee > 40:
        raise ValueError("Préparation limitée à 40 exercices par opération.")

    periodes = []
    for ref in range(annee, borne):
        debut, fin = date(ref, 1, 1), date(ref, 12, 31)
        if premier_exercice and premier_exercice.date_debut.year == ref:
            fin = premier_exercice.date_debut - timedelta(days=1)
        if fin >= debut:
            periodes.append((ref, debut, fin))
    return periodes
