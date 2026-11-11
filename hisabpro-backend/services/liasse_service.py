# -*- coding: utf-8 -*-
"""Dossier de liasse fiscale HisabPro - Patch 09.3.

Ce service consolide la source comptable 09.1, l'ETIC 09.2 et le moteur fiscal
Patch 08. Il produit une structure stable utilisée par l'écran de contrôle,
l'archive finale et les exports PDF/Excel.

Important : le dossier HisabPro n'est pas présenté comme un dépôt EDI DGI.
L'EDI SIMPL-IS fait l'objet d'un format XML spécifique qui devra être certifié
séparément avant activation d'un envoi direct.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Dict, Iterable

from sqlalchemy.orm import Session

import models
from services.etats_synthese_service import source_etats_synthese
from services.fec_exercice_service import controler_fec_exercice
from services.etic_service import construire_etic
from services.plan_comptable import libelle_compte
from services.bilan_presentation import lignes_bilan_detaille

MONEY = Decimal("0.01")
ZERO = Decimal("0.00")


def money(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def num(v) -> float:
    return float(money(v))


def _sd(soldes: Dict[str, Any], prefixes: Iterable[str]) -> Decimal:
    ps = tuple(prefixes)
    total = ZERO
    for c, v in (soldes or {}).items():
        if c.startswith(ps):
            total += money(v.get("debit")) - money(v.get("credit"))
    return money(total)


def _sc(soldes: Dict[str, Any], prefixes: Iterable[str]) -> Decimal:
    ps = tuple(prefixes)
    total = ZERO
    for c, v in (soldes or {}).items():
        if c.startswith(ps):
            total += money(v.get("credit")) - money(v.get("debit"))
    return money(total)


def _sd_positifs(soldes: Dict[str, Any], prefixes: Iterable[str]) -> Decimal:
    """Lot 977 : somme des seuls comptes à solde débiteur (présentation actif)."""
    ps = tuple(prefixes)
    return money(sum((max(ZERO, money(v.get("debit")) - money(v.get("credit"))) for c, v in (soldes or {}).items() if c.startswith(ps)), ZERO))


def _sc_positifs(soldes: Dict[str, Any], prefixes: Iterable[str]) -> Decimal:
    """Lot 977 : somme des seuls comptes à solde créditeur (présentation passif)."""
    ps = tuple(prefixes)
    return money(sum((max(ZERO, money(v.get("credit")) - money(v.get("debit"))) for c, v in (soldes or {}).items() if c.startswith(ps)), ZERO))


def caisses_creditrices(soldes: Dict[str, Any]) -> Dict[str, Decimal]:
    """Lot 977 : une caisse ne peut jamais être créditrice ; anomalie à corriger, jamais reclassée."""
    return {c: money(money(v.get("credit")) - money(v.get("debit"))) for c, v in (soldes or {}).items()
            if c.startswith("516") and money(v.get("credit")) - money(v.get("debit")) > ZERO}


def calculer_cpc(soldes: Dict[str, Any]) -> Dict[str, Any]:
    pexpl = {
        "Ventes de marchandises": _sc(soldes, ("711",)),
        "Ventes de biens et services produits": _sc(soldes, ("712",)),
        "Variation des stocks de produits": _sc(soldes, ("713",)),
        "Immobilisations produites par l'entreprise": _sc(soldes, ("714",)),
        "Subventions d'exploitation": _sc(soldes, ("716",)),
        "Autres produits d'exploitation": _sc(soldes, ("718",)),
        "Reprises d'exploitation / transferts": _sc(soldes, ("719",)),
    }
    cexpl = {
        "Achats revendus de marchandises": _sd(soldes, ("611",)),
        "Achats consommés de matières et fournitures": _sd(soldes, ("612",)),
        "Autres charges externes": _sd(soldes, ("613", "614")),
        "Impôts et taxes": _sd(soldes, ("616",)),
        "Charges de personnel": _sd(soldes, ("617",)),
        "Autres charges d'exploitation": _sd(soldes, ("618",)),
        "Dotations d'exploitation": _sd(soldes, ("619",)),
    }
    pfin = {
        "Produits des titres": _sc(soldes, ("732",)),
        "Gains de change": _sc(soldes, ("733",)),
        "Intérêts et autres produits financiers": _sc(soldes, ("738",)),
        "Reprises financières": _sc(soldes, ("739",)),
    }
    cfin = {
        "Charges d'intérêts": _sd(soldes, ("631",)),
        "Pertes de change": _sd(soldes, ("633",)),
        "Autres charges financières": _sd(soldes, ("638",)),
        "Dotations financières": _sd(soldes, ("639",)),
    }
    pnc = {
        "Produits de cession d'immobilisations": _sc(soldes, ("751",)),
        "Subventions d'équilibre": _sc(soldes, ("756",)),
        "Reprises sur subventions d'investissement": _sc(soldes, ("757",)),
        "Autres produits non courants": _sc(soldes, ("758",)),
        "Reprises non courantes": _sc(soldes, ("759",)),
    }
    cnc = {
        "VNA des immobilisations cédées": _sd(soldes, ("651",)),
        "Subventions accordées": _sd(soldes, ("656",)),
        "Autres charges non courantes": _sd(soldes, ("658",)),
        "Dotations non courantes": _sd(soldes, ("659",)),
    }
    I = money(sum(pexpl.values(), ZERO)); II = money(sum(cexpl.values(), ZERO)); III = money(I-II)
    IV = money(sum(pfin.values(), ZERO)); V = money(sum(cfin.values(), ZERO)); VI = money(IV-V); VII = money(III+VI)
    VIII = money(sum(pnc.values(), ZERO)); IX = money(sum(cnc.values(), ZERO)); X = money(VIII-IX); XI = money(VII+X)
    XII = _sd(soldes, ("67",)); net = money(XI-XII)
    lignes = []
    def section(code, libelle, detail, total):
        lignes.append({"type":"titre","code":code,"libelle":libelle,"montant":None})
        for k,v in detail.items(): lignes.append({"type":"ligne","code":"","libelle":k,"montant":num(v)})
        lignes.append({"type":"total","code":code,"libelle":f"Total {libelle}","montant":num(total)})
    section("I", "Produits d'exploitation", pexpl, I)
    section("II", "Charges d'exploitation", cexpl, II)
    lignes.append({"type":"total","code":"III","libelle":"Résultat d'exploitation","montant":num(III)})
    section("IV", "Produits financiers", pfin, IV)
    section("V", "Charges financières", cfin, V)
    lignes += [
        {"type":"total","code":"VI","libelle":"Résultat financier","montant":num(VI)},
        {"type":"total","code":"VII","libelle":"Résultat courant","montant":num(VII)},
    ]
    section("VIII", "Produits non courants", pnc, VIII)
    section("IX", "Charges non courantes", cnc, IX)
    lignes += [
        {"type":"total","code":"X","libelle":"Résultat non courant","montant":num(X)},
        {"type":"total","code":"XI","libelle":"Résultat avant impôts","montant":num(XI)},
        {"type":"ligne","code":"XII","libelle":"Impôts sur les résultats","montant":num(XII)},
        {"type":"total","code":"XV","libelle":"Résultat net de l'exercice","montant":num(net)},
    ]
    return {"I":num(I),"II":num(II),"III":num(III),"IV":num(IV),"V":num(V),"VI":num(VI),"VII":num(VII),
            "VIII":num(VIII),"IX":num(IX),"X":num(X),"XI":num(XI),"XII":num(XII),"resultat_net":num(net),"lignes":lignes}


def calculer_bilan(soldes: Dict[str, Any], resultat_net) -> Dict[str, Any]:
    def aligne(code, label, brut, amort=ZERO):
        b=money(brut); a=money(amort); return {"code":code,"libelle":label,"brut":num(b),"amort_prov":num(a),"net":num(b-a)}
    actif_immo=[
        aligne("21","Immobilisations en non-valeurs",_sd(soldes,("21",)),_sc(soldes,("281",))),
        aligne("22","Immobilisations incorporelles",_sd(soldes,("22",)),_sc(soldes,("282","292"))),
        aligne("23","Immobilisations corporelles",_sd(soldes,("23",)),_sc(soldes,("283","293"))),
        aligne("24/25","Immobilisations financières",_sd(soldes,("24","25")),_sc(soldes,("294","295"))),
        aligne("27","Écarts de conversion - actif",_sd(soldes,("27",))),
    ]
    actif_circ=[
        aligne("31","Stocks",_sd(soldes,("31",)),_sc(soldes,("391",))),
        aligne("341","Fournisseurs débiteurs, avances",_sd(soldes,("341",))),
        aligne("342","Clients et comptes rattachés",_sd(soldes,("342",)),_sc(soldes,("3942",))),
        aligne("343","Personnel - débiteur",_sd(soldes,("343",)),_sc(soldes,("3943",))),
        aligne("345","État - débiteur",_sd(soldes,("345",))),
        aligne("346","Comptes d'associés - débiteurs",_sd(soldes,("346",)),_sc(soldes,("3946",))),
        aligne("348","Autres débiteurs",_sd(soldes,("348",)),_sc(soldes,("3948",))),
        aligne("349","Comptes de régularisation - actif",_sd(soldes,("349",))),
        aligne("350","Titres et valeurs de placement",_sd(soldes,("350",)),_sc(soldes,("395",))),
        aligne("37","Écarts de conversion - actif circulant",_sd(soldes,("37",))),
    ]
    treso=[
        aligne("511","Chèques et valeurs à encaisser",_sd(soldes,("511",))),
        aligne("514","Banques, TG et CCP",_sd_positifs(soldes,("514",))),
        aligne("516","Caisses, régies d'avances",_sd(soldes,("516",)),_sc(soldes,("59",))),
    ]
    def total_actif(rows):
        return {"brut":num(sum((money(x["brut"]) for x in rows),ZERO)),"amort_prov":num(sum((money(x["amort_prov"]) for x in rows),ZERO)),"net":num(sum((money(x["net"]) for x in rows),ZERO))}
    ta1=total_actif(actif_immo); ta2=total_actif(actif_circ); ta3=total_actif(treso)
    total_actif={k:num(money(ta1[k])+money(ta2[k])+money(ta3[k])) for k in ("brut","amort_prov","net")}
    def pligne(code,label,m): return {"code":code,"libelle":label,"montant":num(m)}
    cp=[
        pligne("111","Capital social ou personnel",_sc(soldes,("111",))),
        pligne("112/113","Primes d'émission, fusion et apport",_sc(soldes,("112","113"))),
        pligne("114/115","Réserves",_sc(soldes,("114","115"))),
        pligne("116","Report à nouveau (+/-)",_sc(soldes,("116",))),
        pligne("118","Résultats nets en instance d'affectation (+/-)",_sc(soldes,("118",))),
        pligne("119_ANT","Résultat antérieur en attente d'affectation (+/-)",_sc(soldes,("119",))),
        pligne("RESULTAT","Résultat net de l'exercice (+/-)",money(resultat_net)),
    ]
    fp=[
        pligne("131/135","Capitaux propres assimilés",_sc(soldes,("131","135"))),
        pligne("141/148","Dettes de financement",_sc(soldes,("141","148"))),
        pligne("151/155","Provisions durables pour risques et charges",_sc(soldes,("151","155"))),
        pligne("17","Écarts de conversion - passif",_sc(soldes,("17",))),
    ]
    pc=[
        pligne("441","Fournisseurs et comptes rattachés",_sc(soldes,("441",))),
        pligne("442","Clients créditeurs, avances et acomptes",_sc(soldes,("442",))),
        pligne("443","Personnel - créditeur",_sc(soldes,("443",))),
        pligne("444","Organismes sociaux",_sc(soldes,("444",))),
        pligne("445","État - créditeur",_sc(soldes,("445",))),
        pligne("446","Comptes d'associés - créditeurs",_sc(soldes,("446",))),
        pligne("448","Autres créanciers",_sc(soldes,("448",))),
        pligne("449","Comptes de régularisation - passif",_sc(soldes,("449",))),
        pligne("45","Autres provisions pour risques et charges",_sc(soldes,("45",))),
        pligne("47","Écarts de conversion - passif circulant",_sc(soldes,("47",))),
    ]
    tp=[pligne("552/553","Crédits d'escompte et de trésorerie",_sc(soldes,("552","553"))),pligne("554","Banques (soldes créditeurs)",_sc(soldes,("554",))+_sc_positifs(soldes,("514",)))]
    total_cp=money(sum((money(x["montant"]) for x in cp),ZERO)); total_fp=money(total_cp+sum((money(x["montant"]) for x in fp),ZERO))
    total_pc=money(sum((money(x["montant"]) for x in pc),ZERO)); total_tp=money(sum((money(x["montant"]) for x in tp),ZERO)); total_passif=money(total_fp+total_pc+total_tp)
    ecart=money(total_actif["net"])-total_passif
    return {"actif":{"immobilise":actif_immo,"circulant":actif_circ,"tresorerie":treso,"total":total_actif},
            "passif":{"capitaux_propres":cp,"financement_permanent":fp,"passif_circulant":pc,"tresorerie":tp,"total":num(total_passif)},
            "equilibre":abs(ecart)<=MONEY,"ecart":num(ecart)}


def calculer_esg(soldes: Dict[str, Any]) -> Dict[str, Any]:
    vm=_sc(soldes,("711",)); ar=_sd(soldes,("611",)); marge=money(vm-ar)
    vbs=_sc(soldes,("712",)); var=_sc(soldes,("713",)); ip=_sc(soldes,("714",)); prod=money(vbs+var+ip)
    ac=_sd(soldes,("612",)); ace=_sd(soldes,("613","614")); conso=money(ac+ace); va=money(marge+prod-conso)
    sub=_sc(soldes,("716",)); it=_sd(soldes,("616",)); pers=_sd(soldes,("617",)); ebe=money(va+sub-it-pers)
    ape=_sc(soldes,("718",)); acex=_sd(soldes,("618",)); rep=_sc(soldes,("719",)); dot=_sd(soldes,("619",)); re=money(ebe+ape-acex+rep-dot)
    rf=money(_sc(soldes,("73",))-_sd(soldes,("63",))); rc=money(re+rf); rnc=money(_sc(soldes,("75",))-_sd(soldes,("65",))); imp=_sd(soldes,("67",)); net=money(rc+rnc-imp)
    dotdur=_sd(soldes,("6191","6192","6193","6194","61955"))+_sd(soldes,("6391","6392","6393"))+_sd(soldes,("6591","6594","65955","65962"))
    repdur=_sc(soldes,("7191","7192","7193","7194","71955"))+_sc(soldes,("7391","7392","7393"))+_sc(soldes,("7591","7594","75955","75962"))+_sc(soldes,("757",))
    ces=_sc(soldes,("751",)); vna=_sd(soldes,("651",)); caf=money(net+dotdur-repdur-ces+vna)
    rows=[
        ("I","Marge brute",marge),("II","Production de l'exercice",prod),("III","Consommation de l'exercice",conso),("IV","Valeur ajoutée",va),
        ("V","Excédent brut d'exploitation",ebe),("VI","Résultat d'exploitation",re),("VII","Résultat financier",rf),("VIII","Résultat courant",rc),
        ("IX","Résultat non courant",rnc),("X","Résultat net",net),("CAF","Capacité d'autofinancement",caf)]
    return {"lignes":[{"code":c,"libelle":l,"montant":num(m)} for c,l,m in rows],"resultat_net":num(net),"caf":num(caf)}


def calculer_tableau_financement(soldes, soldes_n1, cpc, cpc_n1, flux_financement=None, flux_financement_n1=None, n1_disponible=True):
    """Tableau de financement — modèle normal CGNC, rubriques A à H.

    Les masses N/N-1 servent à la partie I. La partie II repose uniquement sur
    les flux réels ventilés par nature. Les distributions sont déduites de la
    CAF pour former l'autofinancement, conformément à la présentation CGNC ;
    elles ne sont plus présentées comme un emploi stable autonome.
    """
    def masses(s, resultat_courant):
        fp = money(_sc(s, ("11", "13", "14", "15", "16", "17")) + money(resultat_courant))
        ai = _sd(s, ("21", "22", "23", "24", "25", "26", "27", "28"))
        fr = money(fp - ai)
        ac = _sd(s, ("31", "34", "35", "37", "39"))
        pc = _sc(s, ("44", "45", "46", "47", "49"))
        bfg = money(ac - pc)
        ta = _sd(s, ("51",))
        tp = _sc(s, ("55",))
        tn = money(ta - tp)
        return {
            "financement_permanent": fp, "actif_immobilise": ai,
            "fonds_roulement": fr, "actif_circulant": ac,
            "passif_circulant": pc, "bfg": bfg,
            "tresorerie_actif": ta, "tresorerie_passif": tp,
            "tresorerie_nette": tn,
        }

    N = masses(soldes, cpc.get("resultat_net", 0))
    P = masses(soldes_n1, cpc_n1.get("resultat_net", 0))

    def row(label, key, inverse=False, total=False):
        n = N[key]
        if not n1_disponible:
            return {"libelle": label, "n": num(n), "n1": None,
                    "emploi": None, "ressource": None, "total": total}
        p = P[key]; d = money(n - p)
        emploi = max((-d if inverse else d), ZERO)
        ressource = max((d if inverse else -d), ZERO)
        return {"libelle": label, "n": num(n), "n1": num(p),
                "emploi": num(emploi), "ressource": num(ressource), "total": total}

    synth = [
        row("Financement permanent", "financement_permanent", True),
        row("Moins actif immobilisé", "actif_immobilise", False),
        row("Fonds de roulement fonctionnel (A)", "fonds_roulement", True, True),
        row("Actif circulant hors trésorerie", "actif_circulant", False),
        row("Moins passif circulant hors trésorerie", "passif_circulant", True),
        row("Besoin de financement global (B)", "bfg", False, True),
        row("Trésorerie nette (A - B)", "tresorerie_nette", False, True),
    ]

    def fval(flux, key, fallback=0):
        return money((flux or {}).get(key, fallback))

    def presentation_flux(s, flux):
        caf = money(calculer_esg(s)["caf"])
        distributions = fval(flux, "distributions_benefices")
        autofinancement = money(caf - distributions)

        c_inc = fval(flux, "cessions_immobilisations_incorporelles")
        c_cor = fval(flux, "cessions_immobilisations_corporelles")
        c_fin = fval(flux, "cessions_immobilisations_financieres")
        c_nv = fval(flux, "cessions_immobilisations_non_ventilees")
        rec_creances = fval(flux, "recuperations_creances_immobilisees")
        cessions_reductions = money(c_inc + c_cor + c_fin + c_nv + rec_creances)

        aug_cap = fval(flux, "augmentations_capitaux_propres")
        subv = fval(flux, "subventions_investissement_recues")
        aug_cp_assim = money(aug_cap + subv)
        aug_det = fval(flux, "augmentations_dettes_financement")

        a_inc = fval(flux, "acquisitions_immobilisations_incorporelles")
        a_cor = fval(flux, "acquisitions_immobilisations_corporelles")
        a_fin = fval(flux, "acquisitions_immobilisations_financieres")
        aug_creances = fval(flux, "augmentations_creances_immobilisees")
        # Compatibilité avec 051 : si seule l'ancienne clé agrégée est fournie,
        # elle est présentée comme acquisition non ventilée dans le corporel.
        ancien_acq = fval(flux, "acquisitions_immobilisations")
        if a_inc + a_cor + a_fin + aug_creances == ZERO and ancien_acq > ZERO:
            a_cor = ancien_acq
        acquisitions = money(a_inc + a_cor + a_fin + aug_creances)

        remb_cap = fval(flux, "reductions_capitaux_propres")
        remb_det = fval(flux, "remboursements_dettes_financement")
        non_valeurs = fval(flux, "emplois_non_valeurs")

        total_ressources = money(autofinancement + cessions_reductions + aug_cp_assim + aug_det)
        total_emplois = money(acquisitions + remb_cap + remb_det + non_valeurs)
        return {
            "caf": caf, "distributions": distributions, "autofinancement": autofinancement,
            "cession_incorporelle": c_inc, "cession_corporelle": c_cor,
            "cession_financiere": c_fin, "cession_non_ventilee": c_nv,
            "recuperations_creances": rec_creances, "cessions_reductions": cessions_reductions,
            "augmentation_capital": aug_cap, "subventions": subv,
            "augmentation_cp_assimiles": aug_cp_assim, "augmentation_dettes": aug_det,
            "acquisition_incorporelle": a_inc, "acquisition_corporelle": a_cor,
            "acquisition_financiere": a_fin, "augmentation_creances": aug_creances,
            "acquisitions": acquisitions, "remboursement_capitaux": remb_cap,
            "remboursement_dettes": remb_det, "emplois_non_valeurs": non_valeurs,
            "total_ressources": total_ressources, "total_emplois": total_emplois,
        }

    F = presentation_flux(soldes, flux_financement or {})
    F1 = presentation_flux(soldes_n1, flux_financement_n1 or {})

    def rr(code, libelle, key, total=False, niveau=0, signe=None):
        return {"code": code, "libelle": libelle, "montant": num(F[key]),
                "n1": num(F1[key]) if n1_disponible else None,
                "total": total, "niveau": niveau, "signe": signe}

    ressources = [
        rr("A", "AUTOFINANCEMENT (A)", "autofinancement", True),
        rr("A1", "+ Capacité d'autofinancement", "caf", False, 1, "+"),
        rr("A2", "- Distributions de bénéfices", "distributions", False, 1, "-"),
        rr("B", "CESSIONS ET RÉDUCTIONS D'IMMOBILISATIONS (B)", "cessions_reductions", True),
        rr("B1", "+ Cessions d'immobilisations incorporelles", "cession_incorporelle", False, 1, "+"),
        rr("B2", "+ Cessions d'immobilisations corporelles", "cession_corporelle", False, 1, "+"),
        rr("B3", "+ Cessions d'immobilisations financières", "cession_financiere", False, 1, "+"),
        rr("B4", "+ Récupérations sur créances immobilisées", "recuperations_creances", False, 1, "+"),
        rr("C", "AUGMENTATION DES CAPITAUX PROPRES ET ASSIMILÉS (C)", "augmentation_cp_assimiles", True),
        rr("C1", "+ Augmentation du capital, apports", "augmentation_capital", False, 1, "+"),
        rr("C2", "+ Subventions d'investissement", "subventions", False, 1, "+"),
        rr("D", "AUGMENTATION DES DETTES DE FINANCEMENT (D)", "augmentation_dettes", True),
    ]
    if F["cession_non_ventilee"] or F1["cession_non_ventilee"]:
        ressources.insert(8, rr("B?", "Cessions d'immobilisations non ventilées (7518) — à reclasser", "cession_non_ventilee", False, 1, "+"))

    emplois = [
        rr("E", "ACQUISITIONS ET AUGMENTATIONS D'IMMOBILISATIONS (E)", "acquisitions", True),
        rr("E1", "+ Acquisitions d'immobilisations incorporelles", "acquisition_incorporelle", False, 1, "+"),
        rr("E2", "+ Acquisitions d'immobilisations corporelles", "acquisition_corporelle", False, 1, "+"),
        rr("E3", "+ Acquisitions d'immobilisations financières", "acquisition_financiere", False, 1, "+"),
        rr("E4", "+ Augmentation des créances immobilisées", "augmentation_creances", False, 1, "+"),
        rr("F", "REMBOURSEMENT DES CAPITAUX PROPRES (F)", "remboursement_capitaux", True),
        rr("G", "REMBOURSEMENT DES DETTES DE FINANCEMENT (G)", "remboursement_dettes", True),
        rr("H", "EMPLOIS EN NON-VALEURS (H)", "emplois_non_valeurs", True),
    ]

    tr = F["total_ressources"]
    te = F["total_emplois"]
    if n1_disponible:
        varfr = money(N["fonds_roulement"] - P["fonds_roulement"])
        varbfg = money(N["bfg"] - P["bfg"])
        vartn = money(N["tresorerie_nette"] - P["tresorerie_nette"])
        ec = money((tr - te) - varfr)
        total_general_ressources = money(tr + max(-varbfg, ZERO) + max(-vartn, ZERO))
        total_general_emplois = money(te + max(varbfg, ZERO) + max(vartn, ZERO))
        ec_general = money(total_general_ressources - total_general_emplois)
    else:
        varfr = varbfg = vartn = None
        ec = ec_general = None
        total_general_ressources = total_general_emplois = None
    avertissements = []
    if F["cession_non_ventilee"] > ZERO:
        avertissements.append(
            f"{F['cession_non_ventilee']:.2f} MAD de cessions 7518 ne peuvent pas être ventilés par nature automatiquement."
        )

    return {
        "applicable": bool(n1_disponible),
        "motif_non_applicable": (None if n1_disponible else
            "Aucune donnée N-1 : le tableau de financement comparatif ne peut pas être établi pour un premier exercice ou une reprise sans balance d'ouverture/comparatif."),
        "synthese": synth, "ressources": ressources, "emplois": emplois,
        "total_ressources": num(tr), "total_emplois": num(te),
        "total_general_ressources": num(total_general_ressources) if total_general_ressources is not None else None,
        "total_general_emplois": num(total_general_emplois) if total_general_emplois is not None else None,
        "variation_fonds_roulement": num(varfr) if varfr is not None else None,
        "variation_bfg": num(varbfg) if varbfg is not None else None,
        "variation_tresorerie": num(vartn) if vartn is not None else None,
        "controle": (abs(ec) <= Decimal("1.00") and abs(ec_general) <= Decimal("1.00")) if n1_disponible else None,
        "ecart_controle": num(ec) if ec is not None else None,
        "ecart_total_general": num(ec_general) if ec_general is not None else None,
        "masses_n": {k: num(v) for k, v in N.items()},
        "masses_n1": ({k: num(v) for k, v in P.items()} if n1_disponible else None),
        "source_flux": "mouvements_valides_ventiles_cgnc_hors_an_cloture",
        "avertissements": avertissements,
    }


def detail_cpc(soldes, db=None, societe_id=None):
    rows=[]
    for c in sorted(soldes or {}):
        if c.startswith("6"):
            m=_sd({c:soldes[c]},(c,)); nature="Charge"
        elif c.startswith("7"):
            m=_sc({c:soldes[c]},(c,)); nature="Produit"
        else: continue
        if m:
            rows.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=societe_id) or "Compte mouvementé","nature":nature,"montant":num(m)})
    return rows


def _merge_lignes_n_n1(rows_n, rows_n1, key="libelle", n1_disponible=True):
    p={r.get(key):r for r in rows_n1}
    out=[]
    for r in rows_n:
        x=dict(r); q=p.get(r.get(key),{})
        if "montant" in r: x["n1"]=(q.get("montant",0) if n1_disponible else None)
        elif "net" in r: x["net_n1"]=(q.get("net",0) if n1_disponible else None)
        out.append(x)
    return out


def _controle(code, libelle, ok, details="", bloquant=True):
    return {"code":code,"libelle":libelle,"ok":bool(ok),"details":details or "","bloquant":bool(bloquant)}


def construire_liasse(db: Session, societe_id: int, exercice: int) -> Dict[str, Any]:
    soc=db.query(models.Societe).filter_by(id=societe_id).first()
    if not soc: raise ValueError("Société introuvable")
    ex=db.query(models.ExerciceComptable).filter_by(societe_id=societe_id,annee=exercice).first()
    src=source_etats_synthese(db,societe_id,exercice); src1=source_etats_synthese(db,societe_id,exercice-1)
    s=src["soldes"]; s1=src1["soldes"]
    cpc=calculer_cpc(s); cpc1=calculer_cpc(s1); bilan=calculer_bilan(s,cpc["resultat_net"]); bilan1=calculer_bilan(s1,cpc1["resultat_net"])
    esg=calculer_esg(s); esg1=calculer_esg(s1)
    n1_disponible = bool(src1.get("disponible"))
    tf=calculer_tableau_financement(
        s, s1, cpc, cpc1, src.get("flux_financement"), src1.get("flux_financement"),
        n1_disponible=n1_disponible,
    )
    fec=controler_fec_exercice(db,societe_id,exercice)
    etic=construire_etic(db,societe_id,exercice)
    try:
        from routers.fiscalite import situation_is
        fiscal=situation_is(exercice,current_user={"societe_id":societe_id,"id":0,"role":"comptable"},db=db)
        fiscal_error=None
    except Exception as exc:
        fiscal={}; fiscal_error=str(exc)

    passage=[]
    calc=fiscal.get("calcul",{}) if fiscal else {}
    source_f=fiscal.get("source_comptable",{}) if fiscal else {}
    if calc:
        is_comp=money(source_f.get("is_deja_comptabilise")); resultat_net_f=money(calc.get("resultat_comptable_avant_is"))-is_comp
        passage=[
            {"rubrique":"Résultat net comptable","montant":num(resultat_net_f)},
            {"rubrique":"Réintégrations fiscales (dont IS comptabilisé)","montant":num(money(calc.get("reintegrations"))+is_comp)},
            {"rubrique":"Déductions fiscales","montant":num(calc.get("deductions"))},
            {"rubrique":"Résultat fiscal avant déficits","montant":num(calc.get("resultat_fiscal_avant_deficit"))},
            {"rubrique":"Déficits imputés","montant":num(calc.get("deficit_impute"))},
            {"rubrique":"Bénéfice fiscal imposable","montant":num(calc.get("benefice_fiscal_imposable"))},
        ]

    checks=[]
    checks.append(_controle("IDENTITE_IF","Identifiant fiscal renseigné",bool((soc.identifiant_fiscal or "").strip()),"Renseignez l'IF dans les paramètres société."))
    checks.append(_controle("IDENTITE_ICE","ICE renseigné",bool((soc.ice or "").strip()),"Renseignez l'ICE dans les paramètres société."))
    checks.append(_controle("SOURCE_BALANCE","Balance générale équilibrée",src["controle"]["balance_equilibree"],f"Écart : {src['controle']['ecart_balance']:.2f} MAD"))
    creditrices=caisses_creditrices(s)
    checks.append(_controle("CAISSE_CREDITRICE","Aucune caisse créditrice",not creditrices,
        ("Caisse créditrice : "+", ".join(f"{c} ({m:.2f} MAD)" for c,m in creditrices.items())+
         ". Une caisse ne peut pas être créditrice : enregistrez l'alimentation manquante (solde d'ouverture, apport, retrait bancaire) ou corrigez la sortie par contrepassation.") if creditrices else ""))
    checks.append(_controle("BROUILLONS","Aucun brouillon dans l'exercice",src["source"]["brouillons_exclus"]==0,f"{src['source']['brouillons_exclus']} brouillon(s) exclu(s)."))
    clos=bool(src["source"].get("exercice_clos")) or bool(ex and ex.statut=="cloture")
    checks.append(_controle("EXERCICE_CLOTURE","Exercice comptable clôturé",clos,"La liasse peut être prévisualisée avant clôture, mais pas finalisée."))
    checks.append(_controle("BILAN_EQUI","Bilan actif/passif équilibré",bilan["equilibre"],f"Écart : {bilan['ecart']:.2f} MAD"))
    checks.append(_controle(
        "FEC_CONFORME", "FEC conforme aux contrôles Avis n°24",
        bool(fec.get("conforme_export")),
        f"{fec.get('nb_bloquants', 0)} anomalie(s) bloquante(s), {fec.get('nb_avertissements', 0)} avertissement(s)."
    ))
    etic_ok=etic.get("progression",{}).get("completes",0)==etic.get("progression",{}).get("total",0)
    checks.append(_controle("ETIC_COMPLETE","ETIC complète",etic_ok,f"{etic.get('progression',{}).get('completes',0)}/{etic.get('progression',{}).get('total',0)} sections complètes."))
    if fiscal_error:
        checks.append(_controle("MOTEUR_FISCAL","Moteur fiscal disponible",False,fiscal_error))
    else:
        if (soc.regime_fiscal or "is")=="is":
            checks.append(_controle("LIQUIDATION_IS","Liquidation IS confirmée",bool(fiscal.get("liquidation",{}).get("confirmee")),"Confirmez la liquidation fiscale avant finalisation."))
        rc_ok=abs(money(cpc["XI"])-money(source_f.get("resultat_comptable_avant_is")))<=MONEY
        checks.append(_controle("RESULTAT_COMPTABLE_FISCAL","Résultat avant IS cohérent entre CPC et fiscalité",rc_ok,f"CPC {money(cpc['XI']):.2f} / Fiscal {money(source_f.get('resultat_comptable_avant_is')):.2f} MAD"))
    if src1.get("disponible"):
        checks.append(_controle("COMPARATIF_N1","Comparatif N-1 disponible",True,"",False))
    else:
        checks.append(_controle("COMPARATIF_N1","Comparatif N-1 disponible",False,"Aucune donnée N-1 ; acceptable pour un premier exercice ou une reprise.",False))
    tf_applicable = bool(src1.get("disponible"))
    checks.append(_controle(
        "TABLEAU_FINANCEMENT", "Contrôle du tableau de financement",
        tf["controle"] if tf_applicable else True,
        (f"Écart de contrôle : {tf['ecart_controle']:.2f} MAD" if tf_applicable
         else "Premier exercice / reprise sans comparatif N-1 : contrôle de variation non applicable."),
        True,
    ))
    bloq=[c for c in checks if c["bloquant"] and not c["ok"]]; warns=[c for c in checks if (not c["bloquant"]) and not c["ok"]]

    archive=db.query(models.LiasseFiscaleArchive).filter_by(societe_id=societe_id,exercice=exercice).order_by(models.LiasseFiscaleArchive.version.desc()).first() if hasattr(models,"LiasseFiscaleArchive") else None
    statut="finalisee" if archive else ("prete" if not bloq else "brouillon")
    date_debut=(ex.date_debut if ex else date(exercice,1,1)); date_fin=(ex.date_fin if ex else date(exercice,12,31))

    # Ajoute N-1 aux présentations principales.
    actif={}
    for sec in ("immobilise","circulant","tresorerie"):
        actif[sec]=_merge_lignes_n_n1(bilan["actif"][sec],bilan1["actif"][sec], n1_disponible=n1_disponible)
    passif={}
    for sec in ("capitaux_propres","financement_permanent","passif_circulant","tresorerie"):
        passif[sec]=_merge_lignes_n_n1(bilan["passif"][sec],bilan1["passif"][sec], n1_disponible=n1_disponible)
    cpc1_by={(x["type"],x["code"],x["libelle"]):x for x in cpc1["lignes"]}
    cpc_rows=[]
    for r in cpc["lignes"]:
        x=dict(r); q=cpc1_by.get((r["type"],r["code"],r["libelle"]),{}); x["n1"]=(q.get("montant") if n1_disponible and r.get("montant") is not None else None); cpc_rows.append(x)
    esg1_by={x["code"]:x for x in esg1["lignes"]}; esg_rows=[]
    for r in esg["lignes"]:
        x=dict(r); x["n1"]=(esg1_by.get(r["code"],{}).get("montant",0) if n1_disponible else None); esg_rows.append(x)

    return {
        "exercice":int(exercice),"statut":statut,"comparatif_n1_disponible":n1_disponible,
        "societe":{"raison_sociale":soc.raison_sociale,"identifiant_fiscal":soc.identifiant_fiscal,"ice":soc.ice,"rc":soc.rc,"patente":soc.patente,"forme_juridique":soc.forme_juridique,"capital_social":num(soc.capital_social),"adresse":soc.adresse,"ville":soc.ville,"regime_fiscal":soc.regime_fiscal,"devise":soc.devise or "MAD","logo_url":getattr(soc,"logo_url",None)},
        "exercice_comptable":{"date_debut":date_debut,"date_fin":date_fin,"statut":ex.statut if ex else None},
        "source":{"n":src,"n1":src1},
        "etats":{
            "bilan":{"actif":{**actif,"total":bilan["actif"]["total"],"total_n1":bilan1["actif"]["total"] if n1_disponible else None},"passif":{**passif,"total":bilan["passif"]["total"],"total_n1":bilan1["passif"]["total"] if n1_disponible else None},"equilibre":bilan["equilibre"],"ecart":bilan["ecart"],
                     "detail":{cote:lignes_bilan_detaille(bilan,s,bilan1,s1,cote,n1_disponible) for cote in ("actif","passif")}},
            "cpc":{"lignes":cpc_rows,"resultat_net":cpc["resultat_net"],"resultat_net_n1":cpc1["resultat_net"] if n1_disponible else None},
            "esg":{"lignes":esg_rows,"caf":esg["caf"],"caf_n1":esg1["caf"] if n1_disponible else None},
            "tableau_financement":tf,
            "detail_cpc":detail_cpc(s, db=db, societe_id=societe_id),
        },
        "fiscal":{"passage_resultat_fiscal":passage,"situation":fiscal,"erreur":fiscal_error},
        "fec":fec,
        "etic":etic,
        "controles":{"pret_a_finaliser":len(bloq)==0,"nb_bloquants":len(bloq),"nb_avertissements":len(warns),"items":checks,"bloquants":bloq,"avertissements":warns},
        "archive":({"id":archive.id,"version":archive.version,"empreinte_sha256":archive.empreinte_sha256,"date_finalisation":archive.date_finalisation,"finalisee_par":archive.finalisee_par} if archive else None),
        "referentiel":{"comptable":"CGNC / loi n° 9-88","fiscal":"CGI 2026 et moteur fiscal HisabPro Patch 08","etic":"ETIC modèle normal","depot":"Télédéclaration électronique via SIMPL-IS ; export EDI direct non activé tant que le format courant n'est pas certifié."},
    }


def _json_default(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, (date,datetime)): return obj.isoformat()
    if hasattr(obj,"value"): return obj.value
    raise TypeError(type(obj).__name__)


def contenu_canonique(liasse: Dict[str,Any]) -> str:
    clean=deepcopy(liasse); clean["archive"]=None; clean["statut"]="finalisee"
    return json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=_json_default)


def empreinte_liasse(liasse: Dict[str,Any]) -> str:
    return hashlib.sha256(contenu_canonique(liasse).encode("utf-8")).hexdigest()
