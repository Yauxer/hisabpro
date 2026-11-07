# -*- coding: utf-8 -*-
"""Règles de construction des écritures d'inventaire de fin d'exercice.

Les fonctions de ce module sont volontairement indépendantes de SQLAlchemy afin de
pouvoir être testées sans base de données.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

CENT = Decimal("0.01")


def money(value) -> Decimal:
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value or 0))
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


TYPES_AJUSTEMENT = {
    "cca": {
        "label": "Charge constatée d'avance (CCA)",
        "auto_reverse": True,
        "compte_contrepartie": "3491",
        "classe_activite": "6",
        "sens": "cca",
    },
    "pca": {
        "label": "Produit constaté d'avance (PCA)",
        "auto_reverse": True,
        "compte_contrepartie": "4491",
        "classe_activite": "7",
        "sens": "pca",
    },
    "fnp": {
        "label": "Fournisseur - facture non parvenue (FNP)",
        "auto_reverse": True,
        "compte_contrepartie": "4417",
        "classe_activite": "6",
        "sens": "fnp",
    },
    "fae": {
        "label": "Client - facture à établir (FAE)",
        "auto_reverse": True,
        "compte_contrepartie": "3427",
        "classe_activite": "7",
        "sens": "fae",
    },
    "provision_risque": {
        "label": "Provision pour risques et charges",
        "auto_reverse": False,
        "compte_activite_defaut": "6195",
        "compte_contrepartie": "1518",
        "sens": "provision",
        "prefixes_contrepartie": ("15", "45"),
    },
    "depreciation_client": {
        "label": "Dépréciation d'une créance client",
        "auto_reverse": False,
        "compte_activite_defaut": "61964",
        "compte_contrepartie": "3942",
        "sens": "provision",
        "prefixes_contrepartie": ("3942",),
    },
    "depreciation_stock": {
        "label": "Dépréciation de stock",
        "auto_reverse": False,
        "compte_activite_defaut": "61961",
        "compte_contrepartie": "3911",
        "sens": "provision",
        "prefixes_contrepartie": ("391",),
    },
}


def _valider_compte(compte: str, prefixes, libelle: str):
    compte = (compte or "").strip()
    if not compte:
        raise ValueError(f"{libelle} obligatoire.")
    if not re.fullmatch(r"[0-9]{1,10}", compte):
        raise ValueError(f"{libelle} : numéro attendu sur 1 à 10 chiffres.")
    if prefixes and not any(compte.startswith(p) for p in prefixes):
        attendu = " ou ".join(prefixes)
        raise ValueError(f"{libelle} doit commencer par {attendu}.")
    return compte


def construire_ajustement(type_ajustement: str, montant, compte_activite: str | None = None,
                           compte_contrepartie: str | None = None):
    """Retourne (lignes, auto_reverse, comptes_effectifs).

    Chaque ligne est un dictionnaire ``compte/libelle/debit/credit`` avec Decimal.
    Les écritures CCA/PCA/FNP/FAE sont automatiquement contre-passables au 01/01/N+1.
    Les provisions/dépréciations ne le sont pas : elles doivent être réexaminées et
    faire l'objet d'une reprise explicite lorsque le risque disparaît.
    """
    cfg = TYPES_AJUSTEMENT.get(type_ajustement)
    if not cfg:
        raise ValueError("Type d'ajustement d'inventaire inconnu.")

    try:
        if isinstance(montant, bool):
            raise ValueError
        brut = Decimal(str(montant))
        if not brut.is_finite() or abs(brut) >= Decimal("10000000000000000"):
            raise ValueError
        m = money(brut)
        if m >= Decimal("10000000000000000"):
            raise ValueError
    except (ValueError, InvalidOperation, TypeError, OverflowError):
        raise ValueError("Le montant doit être un nombre fini compatible avec 16 chiffres et 2 décimales.") from None
    if m <= 0:
        raise ValueError("Le montant doit être strictement positif.")

    sens = cfg["sens"]
    if sens in {"cca", "fnp"}:
        activite = _valider_compte(compte_activite, ("6",), "Compte de charge")
    elif sens in {"pca", "fae"}:
        activite = _valider_compte(compte_activite, ("7",), "Compte de produit")
    else:
        activite = _valider_compte(
            compte_activite or cfg.get("compte_activite_defaut"), ("6",), "Compte de dotation"
        )

    contrepartie = _valider_compte(
        compte_contrepartie or cfg["compte_contrepartie"],
        None if sens == "provision" else (cfg["compte_contrepartie"],),
        "Compte de contrepartie",
    )
    if sens == "provision":
        # La famille suit le type déclaré ; conserver ses subdivisions.
        # Le même référentiel est exposé par /types-ajustements pour l'interface.
        _valider_compte(contrepartie, cfg["prefixes_contrepartie"], "Compte de provision/dépréciation")

    label = cfg["label"]
    if sens == "cca":
        lignes = [
            {"compte": contrepartie, "libelle": label, "debit": m, "credit": money(0)},
            {"compte": activite, "libelle": label, "debit": money(0), "credit": m},
        ]
    elif sens == "pca":
        lignes = [
            {"compte": activite, "libelle": label, "debit": m, "credit": money(0)},
            {"compte": contrepartie, "libelle": label, "debit": money(0), "credit": m},
        ]
    elif sens == "fnp":
        lignes = [
            {"compte": activite, "libelle": label, "debit": m, "credit": money(0)},
            {"compte": contrepartie, "libelle": label, "debit": money(0), "credit": m},
        ]
    elif sens == "fae":
        lignes = [
            {"compte": contrepartie, "libelle": label, "debit": m, "credit": money(0)},
            {"compte": activite, "libelle": label, "debit": money(0), "credit": m},
        ]
    else:
        lignes = [
            {"compte": activite, "libelle": label, "debit": m, "credit": money(0)},
            {"compte": contrepartie, "libelle": label, "debit": money(0), "credit": m},
        ]

    return lignes, bool(cfg["auto_reverse"]), {
        "compte_activite": activite,
        "compte_contrepartie": contrepartie,
    }


def contrepasser(lignes):
    """Inverse le débit et le crédit d'une écriture d'inventaire."""
    return [
        {
            **l,
            "libelle": f"Contrepassation — {l.get('libelle') or ''}".strip(),
            "debit": money(l.get("credit", 0)),
            "credit": money(l.get("debit", 0)),
        }
        for l in lignes
    ]


def construire_ligne_soldage(compte: str, solde, libelle: str = "Solde de clôture"):
    """Construit la ligne qui annule un solde signé ``débit - crédit``.

    Cette fonction ne suppose jamais le sens « normal » du compte. C'est
    indispensable en clôture : une CCA peut, par exemple, laisser un compte de
    charge temporairement créditeur. Le mouvement de soldage reste alors un
    débit positif, jamais un crédit négatif.
    """
    s = money(solde)
    if abs(s) <= Decimal("0.005"):
        return None
    if s > 0:
        return {"compte": compte, "libelle": libelle, "debit": money(0), "credit": s}
    return {"compte": compte, "libelle": libelle, "debit": -s, "credit": money(0)}


def _ligne_depuis_solde_cible(compte: str, solde, libelle: str):
    """Crée une ligne portant un solde signé débit-crédit sur ``compte``."""
    s = money(solde)
    if abs(s) <= Decimal("0.005"):
        return None
    if s > 0:
        return {"compte": compte, "libelle": libelle, "debit": s, "credit": money(0)}
    return {"compte": compte, "libelle": libelle, "debit": money(0), "credit": -s}


def construire_cascade_resultat(soldes: dict):
    """Construit la détermination du résultat via les comptes CGNC de classe 8.

    Convention des soldes reçus : ``débit - crédit``.
    La cascade appliquée est :
      61/71 -> 8100
      63/73 -> 8300
      8100 + 8300 -> 8400
      65/75 -> 8500
      8400 + 8500 -> 8600
      8600 + 67 -> 8800
      8800 -> 1191 (bénéfice) ou 1199 (perte)

    La fonction est pure et indépendante de SQLAlchemy afin d'être testable.
    """
    lignes = []

    def solde_groupe(prefixes, compte_cible, libelle_cible):
        total = Decimal("0.00")
        for compte, solde in sorted(soldes.items()):
            if not any(compte.startswith(p) for p in prefixes):
                continue
            s = money(solde)
            if abs(s) <= Decimal("0.005"):
                continue
            ligne = construire_ligne_soldage(compte, s, f"Solde de clôture {compte}")
            if ligne:
                lignes.append(ligne)
            total += s
        total = money(total)
        cible = _ligne_depuis_solde_cible(compte_cible, total, libelle_cible)
        if cible:
            lignes.append(cible)
        return total

    exploitation = solde_groupe(("61", "71"), "8100", "Résultat d'exploitation")
    financier = solde_groupe(("63", "73"), "8300", "Résultat financier")

    # 8100 + 8300 -> 8400
    for compte, solde in (("8100", exploitation), ("8300", financier)):
        ligne = construire_ligne_soldage(compte, solde, f"Solde de {compte}")
        if ligne:
            lignes.append(ligne)
    courant = money(exploitation + financier)
    ligne = _ligne_depuis_solde_cible("8400", courant, "Résultat courant")
    if ligne:
        lignes.append(ligne)

    non_courant = solde_groupe(("65", "75"), "8500", "Résultat non courant")

    # 8400 + 8500 -> 8600
    for compte, solde in (("8400", courant), ("8500", non_courant)):
        ligne = construire_ligne_soldage(compte, solde, f"Solde de {compte}")
        if ligne:
            lignes.append(ligne)
    avant_impots = money(courant + non_courant)
    ligne = _ligne_depuis_solde_cible("8600", avant_impots, "Résultat avant impôts")
    if ligne:
        lignes.append(ligne)

    # Impôts sur les résultats (67*) + résultat avant impôts -> 8800.
    impots = Decimal("0.00")
    for compte, solde in sorted(soldes.items()):
        if not compte.startswith("67"):
            continue
        s = money(solde)
        if abs(s) <= Decimal("0.005"):
            continue
        ligne = construire_ligne_soldage(compte, s, f"Solde de clôture {compte}")
        if ligne:
            lignes.append(ligne)
        impots += s
    impots = money(impots)

    ligne = construire_ligne_soldage("8600", avant_impots, "Solde du résultat avant impôts")
    if ligne:
        lignes.append(ligne)
    apres_impots = money(avant_impots + impots)
    ligne = _ligne_depuis_solde_cible("8800", apres_impots, "Résultat après impôts")
    if ligne:
        lignes.append(ligne)

    # Le résultat économique est l'opposé du solde signé final :
    # solde créditeur => bénéfice positif ; solde débiteur => perte négative.
    resultat = money(-apres_impots)

    ligne = construire_ligne_soldage("8800", apres_impots, "Solde du résultat après impôts")
    if ligne:
        lignes.append(ligne)

    compte_resultat = None
    if resultat > Decimal("0.005"):
        compte_resultat = "1191"
        lignes.append({
            "compte": "1191",
            "libelle": "Résultat net de l'exercice (bénéfice)",
            "debit": money(0),
            "credit": resultat,
        })
    elif resultat < Decimal("-0.005"):
        compte_resultat = "1199"
        lignes.append({
            "compte": "1199",
            "libelle": "Résultat net de l'exercice (perte)",
            "debit": -resultat,
            "credit": money(0),
        })

    # Contrôle de construction : la cascade complète doit être équilibrée.
    total_d = sum((money(l.get("debit", 0)) for l in lignes), Decimal("0.00"))
    total_c = sum((money(l.get("credit", 0)) for l in lignes), Decimal("0.00"))
    if abs(total_d - total_c) > Decimal("0.01"):
        raise ValueError(
            f"Cascade de résultat déséquilibrée : {total_d - total_c:+.2f}"
        )

    return lignes, resultat, compte_resultat
