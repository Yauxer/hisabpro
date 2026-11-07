# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import date, timedelta

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def date_fin_max_douze_mois(date_debut: date) -> date:
    """Retourne la dernière date incluse dans un exercice de douze mois maximum.

    La durée est appréciée en mois calendaires et non en nombre fixe de jours.
    Ainsi 01/01/2023 -> 31/12/2023 et 01/03/2023 -> 29/02/2024
    sont valides, alors que 01/01/2023 -> 01/01/2024 dépasse douze mois.
    Le 29 février est traité explicitement : 29/02/2024 -> 28/02/2025
    constitue bien une période maximale de douze mois.
    """
    try:
        anniversaire = date_debut.replace(year=date_debut.year + 1)
    except ValueError:  # 29 février -> borne exclusive au 1er mars suivant
        anniversaire = date(date_debut.year + 1, 3, 1)
    return anniversaire - timedelta(days=1)


def valider_duree_exercice(date_debut: date, date_fin: date) -> None:
    if date_fin < date_debut:
        raise ValueError("La date de fin doit être postérieure à la date de début.")
    if date_fin > date_fin_max_douze_mois(date_debut):
        raise ValueError("Un exercice comptable ne peut pas dépasser 12 mois.")


def generer_periodes_dates(date_debut: date, date_fin: date):
    valider_duree_exercice(date_debut, date_fin)

    periodes = []
    courant = date_debut
    numero = 1
    while courant <= date_fin:
        dernier_jour = monthrange(courant.year, courant.month)[1]
        fin_mois = date(courant.year, courant.month, dernier_jour)
        fin = min(fin_mois, date_fin)
        periodes.append({
            "numero": numero,
            "libelle": f"{MOIS_FR[courant.month - 1]} {courant.year}",
            "date_debut": courant,
            "date_fin": fin,
        })
        numero += 1
        courant = fin + timedelta(days=1)
    return periodes


def statut_exercice_par_defaut(date_debut: date, date_fin: date, clos: bool = False):
    if clos:
        return "cloture"
    if date_debut > date.today():
        return "a_venir"
    return "ouvert"
