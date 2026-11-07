# -*- coding: utf-8 -*-
"""Moteur TVA marocain — fonctions pures.

Patch 02B :
- ventilation structurée factures / avoirs ;
- règlements partiels ;
- acomptes TTC ;
- déductibilité et prorata ;
- calculs en Decimal.

Le routeur ``routers/tva.py`` porte la chronologie fiscale (cumul avant/après
période) afin que les avoirs et reports de crédit produisent un delta correct.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

from services.tva_regles_service import qualification_valide

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
HUNDRED = Decimal("100")

# Clés internes négatives : montants inclus dans le TTC de la pièce mais exclus
# des bases/taux de la déclaration TVA. Elles évitent de confondre « 0 % » avec
# exonération, hors champ, suspension ou consignation.
QUALIF_CLE_INTERNE = {
    "exonere_droit_deduction": Decimal("-10"),
    "exonere_sans_deduction": Decimal("-11"),
    "hors_champ": Decimal("-12"),
    "suspension": Decimal("-13"),
}
CLE_CONSIGNE = Decimal("-20")

def _cle_tva(taux, qualification="taxable") -> Decimal:
    qualif = qualification_valide(qualification)
    if qualif != "taxable":
        return QUALIF_CLE_INTERNE[qualif]
    return D(taux)

def _taux_depuis_cle(cle: Decimal) -> Decimal:
    return cle if cle >= ZERO else ZERO

def _repartir_accessoire(montant: Decimal, lignes_par_cle: dict) -> dict:
    """Répartit un frais accessoire au prorata des bases de lignes.

    Un accessoire de vente suit le traitement TVA des biens/services auxquels il
    se rattache. Sur une facture mixte, on évite donc un taux unique arbitraire.
    """
    montant = max(D(montant), ZERO)
    poids = {k: max(D(v), ZERO) for k, v in lignes_par_cle.items() if D(v) > ZERO}
    total = sum(poids.values(), ZERO)
    if montant <= ZERO:
        return {}
    if total <= ZERO:
        return {Decimal("20"): montant}
    out = {}
    cumul = ZERO
    keys = list(sorted(poids.keys()))
    for i, k in enumerate(keys):
        if i == len(keys) - 1:
            part = montant - cumul
        else:
            part = montant * poids[k] / total
            cumul += part
        out[k] = part
    return out


def D(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value) -> Decimal:
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def pct(value, default=100) -> Decimal:
    """Pourcentage borné entre 0 et 100."""
    raw = D(default if value is None else value)
    return max(ZERO, min(raw, HUNDRED))


def taux_key(value) -> str:
    return format(D(value).normalize(), "f")


def _net_ligne(ligne) -> Decimal:
    qte = D(getattr(ligne, "quantite", 0))
    pu = D(getattr(ligne, "prix_unitaire", 0))
    remise1 = D(getattr(ligne, "remise", 0)) / HUNDRED
    remise2 = D(getattr(ligne, "remise2", 0)) / HUNDRED
    rabais_unitaire = D(getattr(ligne, "rabais", 0))

    ht = qte * pu
    ht *= (D(1) - remise1)
    ht *= (D(1) - remise2)
    ht -= rabais_unitaire * qte
    return max(ht, ZERO)


def ventilation_facture(facture, appliquer_escompte: bool = True) -> Dict[Decimal, dict]:
    """Ventile une facture par traitement TVA, y compris les frais accessoires.

    Les clés négatives sont internes et représentent des montants hors base de
    déclaration (exonération/hors champ/suspension/consigne) tout en conservant
    leur valeur dans le total TTC de la pièce.
    """
    lignes_par_cle = defaultdict(lambda: ZERO)
    accessoires_par_cle = defaultdict(lambda: ZERO)

    for ligne in getattr(facture, "lignes", []) or []:
        cle = _cle_tva(getattr(ligne, "tva", 0), getattr(ligne, "qualification_tva", "taxable"))
        lignes_par_cle[cle] += _net_ligne(ligne)

    transport = D(getattr(facture, "frais_transport_ht", 0))
    mode_transport = (getattr(facture, "frais_transport_mode", None) or "accessoire").lower()
    if transport:
        if mode_transport == "accessoire":
            for cle, montant in _repartir_accessoire(transport, lignes_par_cle).items():
                accessoires_par_cle[cle] += montant
        else:
            cle = _cle_tva(
                getattr(facture, "frais_transport_tva", 0),
                getattr(facture, "frais_transport_qualification_tva", "taxable"),
            )
            accessoires_par_cle[cle] += transport

    emballage = D(getattr(facture, "frais_emballage_ht", 0))
    mode_emballage = (getattr(facture, "frais_emballage_mode", None) or "perdu").lower()
    if emballage:
        if mode_emballage == "perdu":
            for cle, montant in _repartir_accessoire(emballage, lignes_par_cle).items():
                accessoires_par_cle[cle] += montant
        elif mode_emballage == "consigne":
            accessoires_par_cle[CLE_CONSIGNE] += emballage
        else:
            cle = _cle_tva(
                getattr(facture, "frais_emballage_tva", 0),
                getattr(facture, "frais_emballage_qualification_tva", "taxable"),
            )
            accessoires_par_cle[cle] += emballage

    remise_g = D(getattr(facture, "remise_globale", 0)) / HUNDRED
    ristourne = D(getattr(facture, "ristourne", 0)) / HUNDRED
    escompte = D(getattr(facture, "escompte", 0)) / HUNDRED
    coef_commercial = (D(1) - remise_g) * (D(1) - ristourne)
    coef_escompte = (D(1) - escompte) if appliquer_escompte else D(1)

    result = {}
    toutes_cles = set(lignes_par_cle) | set(accessoires_par_cle)
    for cle in toutes_cles:
        base_lignes = lignes_par_cle[cle] * coef_commercial
        base_accessoires = accessoires_par_cle[cle]
        # La consignation est une dette/créance remboursable, pas une réduction
        # financière : l'escompte ne s'applique pas à ce dépôt.
        coef = D(1) if cle == CLE_CONSIGNE else coef_escompte
        base = max((base_lignes + base_accessoires) * coef, ZERO)
        taux = _taux_depuis_cle(cle)
        tva = base * taux / HUNDRED
        # Le TTC est la somme des montants arrondis : l'écriture (tiers = HT + TVA)
        # reste équilibrée au centime.
        result[cle] = {"base": money(base), "tva": money(tva), "ttc": money(base) + money(tva)}
    return result


def ventilation_avoir(avoir, appliquer_escompte: bool = True) -> Dict[Decimal, dict]:
    """Ventile un avoir en reprenant les réductions figées de la facture source.

    FACT.6 : un avoir partiel doit annuler exactement la fraction économique de
    la ligne facturée. Les remises de pied, ristournes et escompte sont donc
    repris depuis les snapshots de l'avoir, et non depuis le paramétrage courant.
    """
    remise_g = D(getattr(avoir, "remise_globale_snapshot", 0)) / HUNDRED
    ristourne = D(getattr(avoir, "ristourne_snapshot", 0)) / HUNDRED
    escompte = D(getattr(avoir, "escompte_snapshot", 0)) / HUNDRED
    coef = (D(1) - remise_g) * (D(1) - ristourne)
    if appliquer_escompte:
        coef *= (D(1) - escompte)

    result = defaultdict(lambda: {"base": ZERO, "tva": ZERO, "ttc": ZERO})
    for ligne in getattr(avoir, "lignes", []) or []:
        cle = _cle_tva(getattr(ligne, "tva", 0), getattr(ligne, "qualification_tva", "taxable"))
        # FACT-G : pour un RRR/correctif de prix saisi en montant,
        # ``montant_ht_force`` représente déjà la base HT finale à créditer
        # (après les réductions de la facture source). On ne réapplique donc
        # pas les coefficients historiques une seconde fois.
        montant_force = getattr(ligne, "montant_ht_force", None)
        base = max(D(montant_force), ZERO) if montant_force is not None else max(_net_ligne(ligne) * coef, ZERO)
        taux = _taux_depuis_cle(cle)
        tva = base * taux / HUNDRED
        result[cle]["base"] += base
        result[cle]["tva"] += tva
    out = {}
    for taux, vals in result.items():
        base, tva = money(vals["base"]), money(vals["tva"])
        out[taux] = {"base": base, "tva": tva, "ttc": base + tva}
    return out


def total_ventilation(ventilation: Dict[Decimal, dict]) -> dict:
    return {
        "base": money(sum((D(v.get("base")) for v in ventilation.values()), ZERO)),
        "tva": money(sum((D(v.get("tva")) for v in ventilation.values()), ZERO)),
        "ttc": money(sum((D(v.get("ttc")) for v in ventilation.values()), ZERO)),
    }


def soustraire_ventilation(base: Dict[Decimal, dict], moins: Dict[Decimal, dict]) -> Dict[Decimal, dict]:
    """Soustrait un avoir d'une facture sans produire de montant négatif par taux."""
    out = {}
    for taux in set(base) | set(moins):
        b = base.get(taux, {"base": ZERO, "tva": ZERO, "ttc": ZERO})
        m = moins.get(taux, {"base": ZERO, "tva": ZERO, "ttc": ZERO})
        out[taux] = {
            "base": money(max(D(b.get("base")) - D(m.get("base")), ZERO)),
            "tva": money(max(D(b.get("tva")) - D(m.get("tva")), ZERO)),
            "ttc": money(max(D(b.get("ttc")) - D(m.get("ttc")), ZERO)),
        }
    return {t: v for t, v in out.items() if v["base"] or v["tva"] or v["ttc"]}


def appliquer_pourcentage(ventilation: Dict[Decimal, dict], pourcentage) -> Dict[Decimal, dict]:
    """Applique un taux de déductibilité/prorata à la base et à la TVA."""
    coef = pct(pourcentage) / HUNDRED
    return {
        taux: {
            "base": money(D(vals.get("base")) * coef),
            "tva": money(D(vals.get("tva")) * coef),
            "ttc": money(D(vals.get("ttc")) * coef),
        }
        for taux, vals in ventilation.items()
    }


def acompte_ttc_ventilation(montant_ttc, taux) -> Dict[Decimal, dict]:
    """Décompose un acompte TTC en base + TVA pour un taux donné."""
    montant = max(money(montant_ttc), ZERO)
    taux_d = max(D(taux), ZERO)
    if montant <= ZERO:
        return {}
    if taux_d == ZERO:
        return {taux_d: {"base": montant, "tva": ZERO, "ttc": montant}}
    base = money(montant / (D(1) + taux_d / HUNDRED))
    tva = money(montant - base)
    return {taux_d: {"base": base, "tva": tva, "ttc": montant}}


def date_encaissement_acompte(acompte) -> Optional[date]:
    """Date déclarée du paiement, jamais la remise d'un chèque encore en attente."""
    if getattr(acompte, "statut_paiement", "encaisse") != "encaisse":
        return None
    effective = getattr(acompte, "date_encaissement", None)
    if effective is not None:
        return effective
    # Anciennes avances immédiates : leur date reste la source existante.
    # Un chèque/effet sans date effective doit rester à qualifier.
    if getattr(acompte, "mode", "") in {"cheque", "effet"}:
        return None
    return getattr(acompte, "date", None)


def date_paiement_effective(reglement) -> Optional[date]:
    statut = str(getattr(reglement, "statut", "") or "").lower()
    if statut in {"rejete", "annule"} or statut.endswith("rejete"):
        return None

    date_enc = getattr(reglement, "date_encaissement", None)
    if date_enc:
        return date_enc

    mode = str(getattr(reglement, "mode", "") or "").lower()
    if mode in {"cheque", "effet"}:
        return None
    return getattr(reglement, "date", None)


def allouer_paiement(ventilation: Dict[Decimal, dict], montant_reconnu: Decimal) -> Dict[Decimal, dict]:
    """Répartit un paiement au prorata du TTC entre les taux de la facture."""
    total = total_ventilation(ventilation)
    total_ttc = total["ttc"]
    montant_reconnu = max(min(money(montant_reconnu), total_ttc), ZERO)
    if total_ttc <= ZERO or montant_reconnu <= ZERO:
        return {}

    ratio = montant_reconnu / total_ttc
    out = {}
    taux_tries = sorted(ventilation.keys())
    tva_cible = money(total["tva"] * ratio)
    base_cible = money(total["base"] * ratio)
    tva_cum = ZERO
    base_cum = ZERO
    for idx, taux in enumerate(taux_tries):
        vals = ventilation[taux]
        if idx == len(taux_tries) - 1:
            tva = money(tva_cible - tva_cum)
            base = money(base_cible - base_cum)
        else:
            tva = money(D(vals.get("tva")) * ratio)
            base = money(D(vals.get("base")) * ratio)
            tva_cum += tva
            base_cum += base
        out[taux] = {"base": base, "tva": tva, "ttc": money(base + tva)}
    return out


def ajouter_ventilation(cible: dict, ventilation: Dict[Decimal, dict], signe: Decimal = D(1)):
    for taux, vals in ventilation.items():
        # Les clés négatives sont des montants hors base de déclaration TVA.
        if D(taux) < ZERO:
            continue
        cle = taux_key(taux)
        if cle not in cible:
            cible[cle] = {"base": ZERO, "tva": ZERO}
        cible[cle]["base"] += D(vals.get("base")) * signe
        cible[cle]["tva"] += D(vals.get("tva")) * signe


def delta_ventilation(fin: Dict[Decimal, dict], avant: Dict[Decimal, dict]) -> Dict[Decimal, dict]:
    """Delta de deux situations cumulées, positif ou négatif."""
    out = {}
    for taux in set(fin) | set(avant):
        f = fin.get(taux, {"base": ZERO, "tva": ZERO})
        a = avant.get(taux, {"base": ZERO, "tva": ZERO})
        base = money(D(f.get("base")) - D(a.get("base")))
        tva = money(D(f.get("tva")) - D(a.get("tva")))
        if base or tva:
            out[taux] = {"base": base, "tva": tva, "ttc": money(base + tva)}
    return out


def appliquer_credit_periode(credit_anterieur, tva_collectee, tva_recuperable) -> dict:
    """Applique le crédit reportable à une période et retourne due/crédit final."""
    credit = max(money(credit_anterieur), ZERO)
    # Les avoirs retenus en amont peuvent rendre les totaux nets négatifs.
    # Seuls le montant à verser et le crédit final sont bornés à zéro.
    collectee = money(tva_collectee)
    recuperable = money(tva_recuperable)
    solde = money(collectee - recuperable - credit)
    return {
        "tva_due": max(solde, ZERO),
        "credit_fin": max(-solde, ZERO),
    }


def finaliser_bloc(par_taux: dict) -> dict:
    propre = {}
    total_tva = ZERO
    total_base = ZERO
    for taux in sorted(par_taux, key=lambda x: D(x)):
        base = money(par_taux[taux]["base"])
        tva = money(par_taux[taux]["tva"])
        if base == ZERO and tva == ZERO:
            continue
        propre[taux] = {"base": float(base), "tva": float(tva)}
        total_base += base
        total_tva += tva
    return {
        "total": float(money(total_tva)),
        "base_total": float(money(total_base)),
        "par_taux": propre,
    }
