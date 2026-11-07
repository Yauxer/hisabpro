# -*- coding: utf-8 -*-
"""Diagnostic et reclassements sûrs des immobilisations historiques.

Patch 05C : ce service ne fabrique jamais une acquisition ou une TVA manquante.
Il sait uniquement :
- diagnostiquer les écarts registre / écritures liées à une immobilisation ;
- proposer une catégorie cible prudente ;
- générer des OD de reclassement de comptes, à montant constant.

Les écarts de montants restent à traiter séparément après vérification de leur origine.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def D(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v in (None, ""):
        return ZERO
    return Decimal(str(v))


def money(v) -> Decimal:
    return D(v).quantize(CENT, rounding=ROUND_HALF_UP)


CATEGORY_ACCOUNTS = {
    "Matériel de bureau": {"compte_immo": "2352", "compte_amort": "28352", "compte_dotation": "61935"},
    "Matériel informatique": {"compte_immo": "2355", "compte_amort": "28355", "compte_dotation": "61935"},
    "Véhicule": {"compte_immo": "2340", "compte_amort": "2834", "compte_dotation": "61934"},
    "Mobilier": {"compte_immo": "2351", "compte_amort": "28351", "compte_dotation": "61935"},
    "Logiciel": {"compte_immo": "2220", "compte_amort": "2822", "compte_dotation": "61922"},
    "Bâtiment": {"compte_immo": "2321", "compte_amort": "2832", "compte_dotation": "61932"},
    "Terrain": {"compte_immo": "2311", "compte_amort": "2831", "compte_dotation": "61931"},
    "Outillage": {"compte_immo": "2332", "compte_amort": "28332", "compte_dotation": "61933"},
    "Autre": {"compte_immo": "2380", "compte_amort": "2838", "compte_dotation": "61938"},
}


_STRONG_HINTS = (
    ("Matériel informatique", ("ordinateur", "serveur", "laptop", "portable", "unité centrale", "unite centrale", "pc ", "pc-")),
    ("Véhicule", ("voiture", "véhicule", "vehicule", "camion", "fourgon", "moto")),
    ("Logiciel", ("logiciel", "software", "licence", "license")),
)


def comptes_recommandes(categorie: str | None) -> dict[str, str]:
    return dict(CATEGORY_ACCOUNTS.get((categorie or "").strip(), CATEGORY_ACCOUNTS["Autre"]))


def suggerer_categorie(designation: str | None, categorie_actuelle: str | None) -> tuple[str, bool]:
    """Retourne (catégorie suggérée, suggestion forte).

    Une suggestion forte n'est jamais appliquée automatiquement : elle est seulement
    présentée à l'utilisateur pour confirmation.
    """
    txt = f" {(designation or '').strip().lower()} "
    for categorie, mots in _STRONG_HINTS:
        if any(m in txt for m in mots):
            return categorie, categorie != (categorie_actuelle or "").strip()
    actuelle = (categorie_actuelle or "").strip()
    return (actuelle if actuelle in CATEGORY_ACCOUNTS else "Autre"), False


def _ecriture_acquisition(db, models, immo, societe_id: int):
    ecriture = None
    if getattr(immo, "ecriture_acquisition_id", None):
        ecriture = db.query(models.Ecriture).filter_by(
            id=immo.ecriture_acquisition_id, societe_id=societe_id
        ).first()
    if ecriture is None:
        ecriture = db.query(models.Ecriture).filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.reference.like(f"ACQ-%-{immo.id}"),
        ).order_by(models.Ecriture.id.asc()).first()
    return ecriture


def _references_amortissement_patterns(immo_id: int) -> tuple[str, str]:
    """Références qui participent au cumul d'amortissement d'une immobilisation.

    Les écritures AM historiques portent ``AM-...-{id}``. Les corrections 05D
    portent ``RECON-AMORT-...-{id}``. Le diagnostic doit intégrer les deux ;
    sinon une correction validée ne modifie jamais le rapprochement affiché.
    """
    return (f"AM-%-{immo_id}", f"RECON-AMORT-%-{immo_id}")


def _ecritures_amortissement(db, models, immo, societe_id: int, exercice: int):
    from sqlalchemy import or_

    p_am, p_recon = _references_amortissement_patterns(immo.id)
    return db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        or_(
            models.Ecriture.reference.like(p_am),
            models.Ecriture.reference.like(p_recon),
        ),
        models.Ecriture.exercice <= exercice,
    ).order_by(models.Ecriture.date, models.Ecriture.id).all()


def _montants_par_compte(lignes: Iterable, prefix: str, sens: str) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for l in lignes:
        compte = str(getattr(l, "compte", "") or "")
        if not compte.startswith(prefix):
            continue
        valeur = money((D(l.debit) - D(l.credit)) if sens == "debit" else (D(l.credit) - D(l.debit)))
        if abs(valeur) <= CENT:
            continue
        out[compte] = money(out.get(compte, ZERO) + valeur)
    return out


def _plan_attendu(db, models, immo, societe_id: int, exercice: int):
    from services.immobilisations_service import dotation_sur_periode

    if not immo.amortissable:
        return ZERO, ZERO
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    if not ex:
        return ZERO, ZERO
    try:
        calc = dotation_sur_periode(immo, ex.date_debut, ex.date_fin)
        return money(calc["cumul_fin"]), money(calc["dotation"])
    except Exception:
        return ZERO, ZERO



def construire_lignes_acquisition_reconstituee(
    valeur_brute, tva_recuperable, ttc,
    compte_immo: str, compte_tva: str, compte_contrepartie: str,
):
    """Construit une acquisition manquante de l'exercice courant.

    La valeur brute inclut déjà la TVA non récupérable. La TVA récupérable est
    donc débitée séparément ; la contrepartie porte le TTC. Aucun compte n'est
    choisi implicitement par ce helper.
    """
    brut = money(valeur_brute)
    tva = money(tva_recuperable)
    total = money(ttc)
    if brut <= ZERO or total <= ZERO:
        raise ValueError("Montants d'acquisition invalides")
    if abs((brut + tva) - total) > CENT:
        raise ValueError("La ventilation HT/TVA du registre n'est pas équilibrée")
    lignes = [(str(compte_immo), brut, ZERO, "Reconstitution valeur brute immobilisation")]
    if tva > CENT:
        lignes.append((str(compte_tva), tva, ZERO, "Reconstitution TVA récupérable immobilisation"))
    lignes.append((str(compte_contrepartie), ZERO, total, "Contrepartie acquisition historique"))
    return lignes


def construire_lignes_reprise_ouverture(
    valeur_brute, amortissement_ouverture,
    compte_immo: str, compte_amort: str, compte_contrepartie: str,
):
    """Reconstitue un actif antérieur à l'ouverture sans toucher au résultat N.

    La contrepartie d'ouverture est volontairement fournie par l'utilisateur :
    HisabPro ne devine jamais un report à nouveau, une dette ou un apport.
    """
    brut = money(valeur_brute)
    amort = money(amortissement_ouverture)
    if brut <= ZERO or amort < ZERO or amort > brut:
        raise ValueError("Valeurs de reprise d'ouverture invalides")
    vnc = money(brut - amort)
    lignes = [(str(compte_immo), brut, ZERO, "Reprise d'ouverture — valeur brute immobilisation")]
    if amort > CENT:
        lignes.append((str(compte_amort), ZERO, amort, "Reprise d'ouverture — amortissements antérieurs"))
    if vnc > CENT:
        lignes.append((str(compte_contrepartie), ZERO, vnc, "Contrepartie de reprise d'ouverture"))
    return lignes


def construire_lignes_correction_dotation(
    ecart_dotation, compte_amort: str, compte_dotation: str,
):
    """Corrige uniquement la dotation de l'exercice courant.

    ecart > 0  : dotation insuffisante => charge au débit / amortissement au crédit.
    ecart < 0  : dotation excessive    => reprise technique de l'excès.
    """
    ecart = money(ecart_dotation)
    if abs(ecart) <= CENT:
        return []
    montant = money(abs(ecart))
    if ecart > ZERO:
        return [
            (str(compte_dotation), montant, ZERO, "Complément de dotation historique"),
            (str(compte_amort), ZERO, montant, "Complément amortissement cumulé"),
        ]
    return [
        (str(compte_amort), montant, ZERO, "Correction amortissement cumulé excessif"),
        (str(compte_dotation), ZERO, montant, "Correction dotation historique excessive"),
    ]

def analyser_immo(db, models, immo, societe_id: int, exercice: int) -> dict:
    cible_cat, suggestion_forte = suggerer_categorie(immo.designation, immo.categorie)
    cible = comptes_recommandes(cible_cat)
    actuels = {
        "compte_immo": str(immo.compte_immo or ""),
        "compte_amort": str(immo.compte_amort or ""),
        "compte_dotation": str(immo.compte_dotation or ""),
    }

    acq = _ecriture_acquisition(db, models, immo, societe_id)
    acquisition_par_compte: dict[str, Decimal] = {}
    tva_par_compte: dict[str, Decimal] = {}
    amort_ouverture_par_compte: dict[str, Decimal] = {}
    if acq:
        acquisition_par_compte = _montants_par_compte(acq.lignes or [], "2", "debit")
        # Exclure les 28x du brut. Une reprise d'ouverture 05D peut toutefois
        # contenir les amortissements antérieurs : ils sont comptés séparément.
        acquisition_par_compte = {k: v for k, v in acquisition_par_compte.items() if not k.startswith("28")}
        tva_par_compte = _montants_par_compte(acq.lignes or [], "345", "debit")
        amort_ouverture_par_compte = _montants_par_compte(acq.lignes or [], "28", "credit")

    am_ecritures = _ecritures_amortissement(db, models, immo, societe_id, exercice)
    amort_par_compte: dict[str, Decimal] = dict(amort_ouverture_par_compte)
    dotation_exercice_par_compte: dict[str, Decimal] = {}
    for e in am_ecritures:
        for k, v in _montants_par_compte(e.lignes or [], "28", "credit").items():
            amort_par_compte[k] = money(amort_par_compte.get(k, ZERO) + v)
        if e.exercice == exercice:
            for k, v in _montants_par_compte(e.lignes or [], "6", "debit").items():
                dotation_exercice_par_compte[k] = money(dotation_exercice_par_compte.get(k, ZERO) + v)

    attendu_cumul, attendu_dotation = _plan_attendu(db, models, immo, societe_id, exercice)
    # Le plan courant calcule déjà la différence de cumul entre l'ouverture
    # réelle et la clôture. N-1 peut être absent ou ne pas être contigu : sa
    # seule date de fin ne détermine donc pas le solde à reprendre à l'ouverture.
    attendu_ouverture = money(attendu_cumul - attendu_dotation)
    compta_cumul = money(sum(amort_par_compte.values(), ZERO))
    compta_dotation = money(sum(dotation_exercice_par_compte.values(), ZERO))
    brut_compta = money(sum(acquisition_par_compte.values(), ZERO))
    tva_compta = money(sum(tva_par_compte.values(), ZERO))
    try:
        from services.immobilisations_service import ventilation_acquisition
        vent = ventilation_acquisition(immo.prix_acquisition_ht, immo.taux_tva, immo.tva_recuperable_pct)
    except Exception:
        vent = {
            "prix_ht": money(immo.prix_acquisition_ht), "tva_totale": ZERO,
            "tva_recuperable": ZERO, "tva_non_recuperable": ZERO,
            "cout_entree": money(immo.valeur_brute), "ttc": money(immo.valeur_brute),
        }

    ex_courant = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    if acq:
        acquisition_statut = "comptabilisee"
    elif ex_courant and ex_courant.date_debut <= immo.date_acquisition <= ex_courant.date_fin:
        acquisition_statut = "manquante_exercice"
    elif ex_courant and immo.date_acquisition < ex_courant.date_debut:
        acquisition_statut = "manquante_anterieure"
    else:
        acquisition_statut = "future"

    comptes_a_reclasser = (
        actuels["compte_immo"] != cible["compte_immo"]
        or actuels["compte_amort"] != cible["compte_amort"]
        or actuels["compte_dotation"] != cible["compte_dotation"]
        or any(k != cible["compte_immo"] for k in acquisition_par_compte)
        or any(k != cible["compte_amort"] for k in amort_par_compte)
        or any(k != cible["compte_dotation"] for k in dotation_exercice_par_compte)
    )

    tva_incoherente = bool(acq and tva_compta > CENT and money(immo.taux_tva) <= ZERO)
    ecart_amort = money(attendu_cumul - compta_cumul)
    ecart_brut = money(money(immo.valeur_brute) - brut_compta) if acq else money(immo.valeur_brute)

    return {
        "id": immo.id,
        "designation": immo.designation,
        "date_acquisition": immo.date_acquisition.isoformat(),
        "categorie_actuelle": immo.categorie,
        "categorie_suggeree": cible_cat,
        "suggestion_categorie_forte": suggestion_forte,
        "comptes_actuels": actuels,
        "comptes_cibles": cible,
        "comptes_a_reclasser": comptes_a_reclasser,
        "acquisition": {
            "statut": acquisition_statut,
            "ecriture_id": acq.id if acq else None,
            "exercice": acq.exercice if acq else None,
            "comptes_detectes": {k: float(v) for k, v in acquisition_par_compte.items()},
            "brut_comptabilise": float(brut_compta),
            "brut_registre": float(money(immo.valeur_brute)),
            "ecart_brut": float(ecart_brut),
            "prix_ht": float(money(vent.get("prix_ht", 0))),
            "tva_totale_registre": float(money(vent.get("tva_totale", 0))),
            "tva_recuperable_registre": float(money(vent.get("tva_recuperable", 0))),
            "tva_non_recuperable_registre": float(money(vent.get("tva_non_recuperable", 0))),
            "ttc_registre": float(money(vent.get("ttc", 0))),
            "compte_tva": str(immo.compte_tva or "34551"),
            "compte_fournisseur": str(immo.compte_fournisseur or "4481"),
            "compte_reglement": str(immo.compte_reglement or "5141"),
            "fournisseur": immo.fournisseur,
            "date_paiement": immo.date_paiement.isoformat() if immo.date_paiement else None,
            "amortissement_ouverture_suggere": float(money(attendu_ouverture)),
            "vnc_ouverture_suggeree": float(money(money(immo.valeur_brute) - attendu_ouverture)),
        },
        "amortissement": {
            "attendu_cumule": float(attendu_cumul),
            "comptabilise_cumule": float(compta_cumul),
            "ecart_cumule": float(ecart_amort),
            "attendu_exercice": float(attendu_dotation),
            "comptabilise_exercice": float(compta_dotation),
            "comptes_detectes": {k: float(v) for k, v in amort_par_compte.items()},
            "dotations_exercice_detectees": {k: float(v) for k, v in dotation_exercice_par_compte.items()},
            "ecritures_ids": [e.id for e in am_ecritures],
        },
        "tva": {
            "taux_registre": float(money(immo.taux_tva)),
            "tva_comptabilisee": float(tva_compta),
            "incoherente": tva_incoherente,
        },
        "correction_montants_automatique": False,
    }


def analyser_reconciliation(db, models, societe_id: int, exercice: int, date_fin: date) -> dict:
    immos = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.date_acquisition <= date_fin,
    ).filter(
        (models.Immobilisation.date_sortie == None) | (models.Immobilisation.date_sortie > date_fin)  # noqa: E711
    ).order_by(models.Immobilisation.date_acquisition, models.Immobilisation.id).all()

    items = [analyser_immo(db, models, i, societe_id, exercice) for i in immos]
    return {
        "exercice": exercice,
        "nb_immobilisations": len(items),
        "nb_categories_suspectes": sum(1 for x in items if x["suggestion_categorie_forte"]),
        "nb_acquisitions_manquantes": sum(1 for x in items if x["acquisition"]["statut"].startswith("manquante")),
        "nb_ecarts_amortissement": sum(1 for x in items if abs(Decimal(str(x["amortissement"]["ecart_cumule"]))) > CENT),
        "nb_tva_incoherentes": sum(1 for x in items if x["tva"]["incoherente"]),
        "items": items,
    }


def construire_lignes_reclassement(item: dict, comptes_cibles: dict[str, str], exercice: int):
    """Pure helper : construit des transferts à montant constant.

    Retourne une liste de tuples (compte, debit, credit, libelle). Aucun montant
    manquant n'est créé. Les transferts ne changent donc ni le total du bilan ni
    le résultat net ; ils corrigent uniquement l'imputation des comptes.
    """
    lignes = []
    acq = item["acquisition"]
    for compte_old, montant_raw in (acq.get("comptes_detectes") or {}).items():
        montant = money(montant_raw)
        compte_new = comptes_cibles["compte_immo"]
        if montant > ZERO and compte_old != compte_new:
            lignes.extend([
                (compte_new, montant, ZERO, "Reclassement valeur brute immobilisation"),
                (compte_old, ZERO, montant, "Reclassement valeur brute immobilisation"),
            ])

    amort = item["amortissement"]
    for compte_old, montant_raw in (amort.get("comptes_detectes") or {}).items():
        montant = money(montant_raw)
        compte_new = comptes_cibles["compte_amort"]
        if montant > ZERO and compte_old != compte_new:
            # Un amortissement cumulé porte normalement un crédit : on solde
            # l'ancien compte au débit puis on crédite le nouveau.
            lignes.extend([
                (compte_old, montant, ZERO, "Reclassement amortissement cumulé"),
                (compte_new, ZERO, montant, "Reclassement amortissement cumulé"),
            ])

    for compte_old, montant_raw in (amort.get("dotations_exercice_detectees") or {}).items():
        montant = money(montant_raw)
        compte_new = comptes_cibles["compte_dotation"]
        if montant > ZERO and compte_old != compte_new:
            # Reclassement entre comptes de charges : total charges inchangé.
            lignes.extend([
                (compte_new, montant, ZERO, f"Reclassement dotation {exercice}"),
                (compte_old, ZERO, montant, f"Reclassement dotation {exercice}"),
            ])
    return lignes
