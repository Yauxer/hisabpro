# -*- coding: utf-8 -*-
"""Analyse assistée des retraitements fiscaux — Patch 08.2.

Le but n'est pas de transformer un numéro de compte en décision fiscale aveugle.
Le moteur sépare donc :
- les retraitements *automatiques* lorsque la règle et la qualification comptable
  permettent un traitement suffisamment déterministe ;
- les éléments *à confirmer* lorsqu'une information extra-comptable est requise
  (bénéficiaire d'un don, pièce justificative, conditions d'une provision, etc.).

Référentiel fonctionnel principal : CGI 2026, notamment art. 10 et 11.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")

CATEGORIES_RETRAITEMENT = {
    "amendes_penalites": "Amendes, pénalités et majorations",
    "liberalites": "Libéralités",
    "cadeaux_publicitaires": "Cadeaux publicitaires",
    "dons": "Dons",
    "charges_non_justifiees": "Charges non justifiées",
    "paiements_especes": "Paiements en espèces au-delà des limites",
    "amortissement_vehicule": "Amortissement / location de véhicule de tourisme",
    "amortissements_non_deductibles": "Amortissements non déductibles",
    "provisions_non_deductibles": "Provisions à contrôler",
    "interets_comptes_courants_associes": "Intérêts de comptes courants d'associés",
    "produits_participation_abattement": "Produits de participation — abattement de 100%",
    "reprises_provisions_taxees": "Reprises de provisions antérieurement taxées",
    "produits_exoneres": "Produits exonérés / non imposables",
    "charges_liees_produits_exoneres": "Charges liées à des produits exonérés",
    "autre": "Autre retraitement",
}

# Comptes dont la qualification permet une réintégration automatique.
AUTOMATIQUES_REINTEGRATION = (
    ("6583", "amendes_penalites", "Amendes, pénalités et majorations non déductibles", "CGI 2026 art. 11-I"),
    ("65862", "liberalites", "Libéralités comptabilisées", "CGI 2026 art. 11-IV"),
)

# Les familles ci-dessous nécessitent une confirmation métier/fiscale.
PROVISIONS_CHARGES_PREFIXES = ("6194", "6195", "6196", "6392", "6393", "6394", "6396", "6594", "6595", "6596")
REPRISES_PROVISIONS_PREFIXES = ("7194", "7195", "7196", "7198", "7392", "7393", "7394", "7396", "7594", "7595", "7596")
PRODUITS_PARTICIPATION_PREFIXES = ("7321", "7328")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _somme_prefixes(mouvements: dict[str, Decimal], prefixes: tuple[str, ...]) -> Decimal:
    total = ZERO
    for compte, montant in mouvements.items():
        if any(str(compte).startswith(p) for p in prefixes):
            total += money(montant)
    return money(max(ZERO, total))


def _comptes_prefixes(mouvements: dict[str, Decimal], prefixes: tuple[str, ...]) -> list[str]:
    return sorted({str(c) for c, m in mouvements.items() if money(m) > 0 and any(str(c).startswith(p) for p in prefixes)})


def _comptes_concernes_compacts(mouvements: dict[str, Decimal] | None, *, max_chars: int = 110) -> str:
    """Retourne une liste courte et traçable des comptes réellement concernés.

    Le champ ``compte_source`` est destiné à l'affichage et à l'audit du
    retraitement. On conserve donc les numéros de comptes réels plutôt qu'un
    libellé générique, tout en bornant la chaîne pour rester compatible avec
    la taille maximale persistée en base.
    """
    comptes = sorted({str(c).strip() for c, m in (mouvements or {}).items() if str(c).strip() and money(m) != ZERO})
    if not comptes:
        return ""

    retenus: list[str] = []
    for compte in comptes:
        restant = len(comptes) - len(retenus) - 1
        suffixe = f" +{restant}" if restant > 0 else ""
        candidat = ", ".join([*retenus, compte]) + suffixe
        if len(candidat) > max_chars:
            break
        retenus.append(compte)

    if not retenus:
        return comptes[0][:max_chars]

    restant = len(comptes) - len(retenus)
    resultat = ", ".join(retenus)
    if restant > 0:
        resultat += f" +{restant}"
    return resultat[:max_chars]


def _auto(*, identifiant: str, type_: str, categorie: str, libelle: str, montant, compte_source: str, reference: str, commentaire: str):
    return {
        "id": identifiant,
        "niveau": "automatique",
        "type": type_,
        "type_suggere": type_,
        "categorie": categorie,
        "libelle": libelle,
        "montant": money(montant),
        "montant_detecte": money(montant),
        "compte_source": compte_source,
        "reference": reference,
        "commentaire": commentaire,
        "automatique": True,
        "impacte_calcul": True,
    }


def _candidat(*, identifiant: str, type_suggere: str, categorie: str, libelle: str, montant_detecte, compte_source: str, reference: str, commentaire: str, questions: list[str] | None = None):
    return {
        "id": identifiant,
        "niveau": "a_confirmer",
        "type": type_suggere,
        "type_suggere": type_suggere,
        "categorie": categorie,
        "libelle": libelle,
        "montant": None,
        "montant_detecte": None if montant_detecte is None else money(montant_detecte),
        "compte_source": compte_source,
        "reference": reference,
        "commentaire": commentaire,
        "questions": questions or [],
        "automatique": False,
        "impacte_calcul": False,
    }


def analyser_retraitements(*, charges_par_compte: dict[str, Decimal], produits_par_compte: dict[str, Decimal],
                            charges_sans_reference: Decimal = ZERO,
                            charges_sans_reference_par_compte: dict[str, Decimal] | None = None,
                            vehicules_tourisme_superieurs_plafond: list[dict] | None = None):
    """Construit l'analyse fiscale sans modifier le calcul tant qu'un candidat n'est pas confirmé."""
    automatiques = []
    candidats = []

    # Automatique : amendes / pénalités.
    penalites = _somme_prefixes(charges_par_compte, ("6583",))
    if penalites > 0:
        automatiques.append(_auto(
            identifiant="auto:amendes_penalites",
            type_="reintegration",
            categorie="amendes_penalites",
            libelle="Amendes, pénalités et majorations non déductibles détectées",
            montant=penalites,
            compte_source="6583*",
            reference="CGI 2026 art. 11-I",
            commentaire="Réintégration automatique des charges enregistrées dans la famille 6583.",
        ))

    liberalites = _somme_prefixes(charges_par_compte, ("65862",))
    if liberalites > 0:
        automatiques.append(_auto(
            identifiant="auto:liberalites",
            type_="reintegration",
            categorie="liberalites",
            libelle="Libéralités comptabilisées",
            montant=liberalites,
            compte_source="65862*",
            reference="CGI 2026 art. 11-IV",
            commentaire="La qualification comptable en libéralité justifie une réintégration automatique ; à reclasser si l'opération relève en réalité d'un don déductible.",
        ))

    cadeaux = _somme_prefixes(charges_par_compte, ("61447",))
    if cadeaux > 0:
        candidats.append(_candidat(
            identifiant="check:cadeaux",
            type_suggere="reintegration",
            categorie="cadeaux_publicitaires",
            libelle="Cadeaux à la clientèle : vérifier les conditions de déductibilité",
            montant_detecte=cadeaux,
            compte_source="61447*",
            reference="CGI 2026 art. 10-I-B-1°",
            commentaire="Le compte seul ne permet pas de savoir si chaque cadeau respecte la valeur unitaire maximale et porte l'identification commerciale requise.",
            questions=["Valeur unitaire ≤ 100 MAD ?", "Raison sociale, nom/sigle ou marque apposé(e) sur le cadeau ?"],
        ))

    dons = _somme_prefixes(charges_par_compte, ("61462", "65861"))
    if dons > 0:
        candidats.append(_candidat(
            identifiant="check:dons",
            type_suggere="reintegration",
            categorie="dons",
            libelle="Dons : vérifier le bénéficiaire et les plafonds applicables",
            montant_detecte=dons,
            compte_source="61462* / 65861*",
            reference="CGI 2026 art. 10-I-B-2°",
            commentaire="Certains dons sont déductibles, d'autres non ou seulement dans une limite. HisabPro ne réintègre rien sans confirmation.",
            questions=["Le bénéficiaire figure-t-il parmi les organismes admis ?", "Une limite spécifique s'applique-t-elle ?", "La pièce justificative est-elle conservée ?"],
        ))

    provisions = _somme_prefixes(charges_par_compte, PROVISIONS_CHARGES_PREFIXES)
    if provisions > 0:
        candidats.append(_candidat(
            identifiant="check:provisions",
            type_suggere="reintegration",
            categorie="provisions_non_deductibles",
            libelle="Dotations aux provisions : contrôler les conditions fiscales",
            montant_detecte=provisions,
            compte_source=", ".join(_comptes_prefixes(charges_par_compte, PROVISIONS_CHARGES_PREFIXES)[:6]) or "Provisions",
            reference="CGI 2026 art. 10-I-F-2°",
            commentaire="Une provision n'est pas automatiquement non déductible : sa nature, son évaluation et, pour certaines créances douteuses, les diligences requises doivent être vérifiées.",
            questions=["Risque/charge nettement précisé(e) et probable ?", "Montant évalué de façon suffisamment précise ?", "Conditions particulières respectées (ex. créance douteuse) ?"],
        ))

    interets_associes = _somme_prefixes(charges_par_compte, ("63114",))
    if interets_associes > 0:
        candidats.append(_candidat(
            identifiant="check:interets_associes",
            type_suggere="reintegration",
            categorie="interets_comptes_courants_associes",
            libelle="Intérêts de comptes courants d'associés : contrôler le plafond fiscal",
            montant_detecte=interets_associes,
            compte_source="63114*",
            reference="CGI 2026 art. 10-II-A-2°",
            commentaire="Le montant déductible dépend notamment de la libération du capital, du montant des avances et du taux fiscal annuel.",
            questions=["Capital social entièrement libéré ?", "Avances rémunérées dans la limite du capital ?", "Taux servi ≤ taux fiscal annuel admis ?"],
        ))

    participation = _somme_prefixes(produits_par_compte, PRODUITS_PARTICIPATION_PREFIXES)
    if participation > 0:
        candidats.append(_candidat(
            identifiant="check:participations",
            type_suggere="deduction",
            categorie="produits_participation_abattement",
            libelle="Produits de participation : vérifier l'abattement fiscal de 100%",
            montant_detecte=participation,
            compte_source="7321* / 7328*",
            reference="CGI 2026 art. 6-I-C-1°",
            commentaire="L'abattement de 100% dépend des conditions légales, notamment de la nature du produit et des justificatifs requis.",
            questions=["Produit éligible à l'abattement de 100% ?", "Attestation / justificatif de détention disponible lorsque requis ?"],
        ))

    reprises = _somme_prefixes(produits_par_compte, REPRISES_PROVISIONS_PREFIXES)
    if reprises > 0:
        candidats.append(_candidat(
            identifiant="check:reprises_provisions",
            type_suggere="deduction",
            categorie="reprises_provisions_taxees",
            libelle="Reprises sur provisions : vérifier si elles ont déjà été taxées antérieurement",
            montant_detecte=reprises,
            compte_source=", ".join(_comptes_prefixes(produits_par_compte, REPRISES_PROVISIONS_PREFIXES)[:6]) or "Reprises",
            reference="CGI 2026 — cohérence des provisions et reprises",
            commentaire="Seule la part correspondant à une provision antérieurement réintégrée peut justifier une déduction extra-comptable.",
            questions=["La provision d'origine avait-elle été réintégrée fiscalement ?", "Quel montant de la reprise correspond exactement à cette provision ?"],
        ))

    if money(charges_sans_reference) > 0:
        comptes_sans_reference = _comptes_concernes_compacts(charges_sans_reference_par_compte)
        candidats.append(_candidat(
            identifiant="check:pieces",
            type_suggere="reintegration",
            categorie="charges_non_justifiees",
            libelle="Charges portées par des écritures sans référence de justificatif",
            montant_detecte=charges_sans_reference,
            compte_source=comptes_sans_reference or "Comptes de charges concernés",
            reference="CGI 2026 art. 11-III",
            commentaire="L'absence de référence dans HisabPro ne prouve pas l'absence de facture, mais signale un dossier à vérifier.",
            questions=["Facture régulière ou pièce probante disponible ?", "La pièce est-elle établie au nom de la société et suffisamment renseignée ?"],
        ))

    vehicules = vehicules_tourisme_superieurs_plafond or []
    if vehicules:
        candidats.append(_candidat(
            identifiant="check:vehicules_tourisme",
            type_suggere="reintegration",
            categorie="amortissement_vehicule",
            libelle=f"{len(vehicules)} véhicule(s) de tourisme avec une valeur brute > 400 000 MAD",
            montant_detecte=None,
            compte_source="Immobilisations",
            reference="CGI 2026 art. 10-I-F-1°-b",
            commentaire="Le plafond porte sur la valeur fiscalement amortissable ; le montant exact à réintégrer dépend de la dotation de l'exercice et, le cas échéant, du prorata.",
            questions=["Véhicule soumis au plafond (hors exceptions légales) ?", "Dotation comptable de l'exercice identifiée ?", "Part fiscalement non admise calculée ?"],
        ))

    checklist = [
        {
            "code": "paiements_especes",
            "libelle": "Paiements en espèces",
            "reference": "CGI 2026 art. 11-II",
            "regle": "Contrôler les dépenses réglées hors moyens admis au-delà de 5 000 MAD/jour/fournisseur et 50 000 MAD/mois/fournisseur.",
            "automatisable": False,
        },
        {
            "code": "pieces_justificatives",
            "libelle": "Factures et pièces probantes",
            "reference": "CGI 2026 art. 11-III",
            "regle": "Vérifier la régularité des factures/pièces et les mentions exigées ; une référence HisabPro ne remplace pas la pièce elle-même.",
            "automatisable": False,
        },
        {
            "code": "vehicules",
            "libelle": "Véhicules de tourisme",
            "reference": "CGI 2026 art. 10-I-F-1°-b",
            "regle": "Plafond fiscal de 400 000 MAD TTC par véhicule pour les véhicules concernés, avec règles spécifiques de location/crédit-bail.",
            "automatisable": False,
        },
        {
            "code": "charges_produits_exoneres",
            "libelle": "Charges rattachées à des produits exonérés",
            "reference": "CGI / régime fiscal applicable",
            "regle": "Vérifier les règles de rattachement propres aux exonérations ou régimes particuliers de la société.",
            "automatisable": False,
        },
    ]

    return {
        "automatiques": automatiques,
        "a_confirmer": candidats,
        "checklist": checklist,
        "total_automatique_reintegrations": money(sum((r["montant"] for r in automatiques if r["type"] == "reintegration"), ZERO)),
        "total_automatique_deductions": money(sum((r["montant"] for r in automatiques if r["type"] == "deduction"), ZERO)),
        "nb_a_confirmer": len(candidats),
    }
