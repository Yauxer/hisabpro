"""Lot 977 : une caisse (comptes 516) ne peut jamais être créditrice.

Une sortie d'espèces est refusée si, à sa date ou à une date postérieure déjà
enregistrée, la caisse deviendrait créditrice. Une entrée d'argent est toujours
acceptée, même si une ancienne anomalie existe : elle la résorbe.
"""
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import text

ZERO = Decimal('0.00')


def est_caisse(compte):
    return str(compte or '').strip().startswith('516')


def _dh(v):
    return f"{Decimal(v):,.2f}".replace(',', ' ').replace('.', ',')


def disponible(db, sid, compte, jour, *, valides_seulement, exclure=None):
    """Plus petit solde de la caisse à partir de `jour` : les sorties postérieures déjà saisies comptent."""
    r = db.execute(text('''
        WITH m AS (
            SELECT e.date, sum(l.debit - l.credit) AS mvt
            FROM lignes_ecriture l JOIN ecritures e ON e.id = l.ecriture_id
            WHERE e.societe_id = :s AND l.compte = :c AND (NOT CAST(:v AS boolean) OR e.est_validee)
              AND (CAST(:x AS integer) IS NULL OR e.id <> CAST(:x AS integer))
            GROUP BY e.date),
        c AS (SELECT date, sum(mvt) OVER (ORDER BY date) AS cumul FROM m)
        SELECT coalesce((SELECT cumul FROM c WHERE date <= :j ORDER BY date DESC LIMIT 1), 0) AS a_date,
               (SELECT min(cumul) FROM c WHERE date > :j) AS min_apres'''),
        {'s': sid, 'c': str(compte).strip(), 'v': valides_seulement, 'x': exclure, 'j': jour}).one()
    a_date = Decimal(str(r.a_date or 0))
    return a_date if r.min_apres is None else min(a_date, Decimal(str(r.min_apres)))


def verifier_sortie(db, sid, compte, montant, jour: date, *, valides_seulement=False, exclure=None):
    """Refuse (409) une sortie d'espèces qui rendrait la caisse créditrice."""
    montant = Decimal(str(montant or 0))
    if not est_caisse(compte) or montant <= 0:
        return
    solde = disponible(db, sid, compte, jour, valides_seulement=valides_seulement, exclure=exclure)
    if solde - montant < 0:
        raise HTTPException(409, (
            f"Caisse insuffisante ({compte}) au {jour:%d/%m/%Y} : solde disponible {_dh(max(solde, ZERO))} DH, "
            f"sortie de {_dh(montant)} DH. Une caisse ne peut pas être créditrice : enregistrez d'abord "
            "l'alimentation de la caisse (solde d'ouverture, apport ou retrait de la banque)."))


def verifier_ecriture(db, ecriture):
    """Avant validation : chaque caisse créditée par l'écriture doit rester débitrice ou nulle."""
    sorties = {}
    for l in ecriture.lignes or []:
        if est_caisse(l.compte):
            sorties[l.compte] = sorties.get(l.compte, ZERO) + Decimal(str(l.credit or 0)) - Decimal(str(l.debit or 0))
    for compte, net in sorties.items():
        if net > 0:
            verifier_sortie(db, ecriture.societe_id, compte, net, ecriture.date, valides_seulement=True, exclure=ecriture.id)
