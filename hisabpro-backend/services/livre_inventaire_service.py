# -*- coding: utf-8 -*-
"""Construction et archivage logique du Livre d'inventaire HisabPro.

Le service produit une photographie de fin d'exercice à partir des écritures
validées et des registres métiers (stocks, immobilisations, ajustements).
Les calculs monétaires restent en Decimal jusqu'à la sérialisation.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json

from sqlalchemy import or_
from sqlalchemy.orm import joinedload


CENT = Decimal("0.01")
CURRENT_LIVRE_VERSION = 2


def money(value) -> Decimal:
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value or 0))
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


def to_float(value) -> float:
    return float(money(value))


def sd(soldes: dict[str, Decimal], prefixes) -> Decimal:
    """Somme dans le sens débiteur (débit - crédit)."""
    return money(sum((v for c, v in soldes.items() if any(c.startswith(p) for p in prefixes)), Decimal("0")))


def sc(soldes: dict[str, Decimal], prefixes) -> Decimal:
    """Somme nette dans le sens créditeur (crédit - débit)."""
    return money(-sd(soldes, prefixes))


def debit_positions(soldes: dict[str, Decimal], prefixes) -> Decimal:
    """Additionne uniquement les soldes débiteurs des comptes ciblés.

    Contrairement à ``sd()``, cette fonction ne compense jamais un compte
    débiteur avec un autre compte créditeur du même préfixe. Elle sert aux
    postes du bilan pour lesquels la non-compensation doit être visible.
    """
    return money(sum((
        v for c, v in soldes.items()
        if any(c.startswith(p) for p in prefixes) and v > 0
    ), Decimal("0")))


def credit_positions(soldes: dict[str, Decimal], prefixes) -> Decimal:
    """Additionne uniquement les soldes créditeurs des comptes ciblés."""
    return money(sum((
        -v for c, v in soldes.items()
        if any(c.startswith(p) for p in prefixes) and v < 0
    ), Decimal("0")))


def calculer_cpc(soldes: dict[str, Decimal]):
    pe = {
        "Ventes de marchandises": sc(soldes, ("711",)),
        "Ventes de biens et services": sc(soldes, ("712",)),
        "Variation de stocks de produits": sc(soldes, ("713",)),
        "Immobilisations produites": sc(soldes, ("714",)),
        "Subventions d'exploitation": sc(soldes, ("716",)),
        "Autres produits d'exploitation": sc(soldes, ("718",)),
        "Reprises et transferts": sc(soldes, ("719",)),
    }
    ce = {
        "Achats revendus": sd(soldes, ("611",)),
        "Achats consommés": sd(soldes, ("612",)),
        "Autres charges externes": sd(soldes, ("613", "614")),
        "Impôts et taxes": sd(soldes, ("616",)),
        "Charges de personnel": sd(soldes, ("617",)),
        "Autres charges d'exploitation": sd(soldes, ("618",)),
        "Dotations d'exploitation": sd(soldes, ("619",)),
    }
    pf = {
        "Produits des titres": sc(soldes, ("732",)),
        "Gains de change": sc(soldes, ("733",)),
        "Intérêts et autres produits": sc(soldes, ("738",)),
        "Reprises financières": sc(soldes, ("739",)),
    }
    cf = {
        "Charges d'intérêts": sd(soldes, ("631",)),
        "Pertes de change": sd(soldes, ("633",)),
        "Autres charges financières": sd(soldes, ("638",)),
        "Dotations financières": sd(soldes, ("639",)),
    }
    pnc = {
        "Produits de cession d'immobilisations": sc(soldes, ("751",)),
        "Subventions d'équilibre": sc(soldes, ("756",)),
        "Reprises sur subventions": sc(soldes, ("757",)),
        "Autres produits non courants": sc(soldes, ("758",)),
        "Reprises non courantes": sc(soldes, ("759",)),
    }
    cnc = {
        "VNA des immobilisations cédées": sd(soldes, ("651",)),
        "Subventions accordées": sd(soldes, ("656",)),
        "Autres charges non courantes": sd(soldes, ("658",)),
        "Dotations non courantes": sd(soldes, ("659",)),
    }

    total_pe = money(sum(pe.values(), Decimal("0")))
    total_ce = money(sum(ce.values(), Decimal("0")))
    resultat_exploitation = money(total_pe - total_ce)
    total_pf = money(sum(pf.values(), Decimal("0")))
    total_cf = money(sum(cf.values(), Decimal("0")))
    resultat_financier = money(total_pf - total_cf)
    resultat_courant = money(resultat_exploitation + resultat_financier)
    total_pnc = money(sum(pnc.values(), Decimal("0")))
    total_cnc = money(sum(cnc.values(), Decimal("0")))
    resultat_non_courant = money(total_pnc - total_cnc)
    resultat_avant_impot = money(resultat_courant + resultat_non_courant)
    impot = sd(soldes, ("67",))
    resultat_net = money(resultat_avant_impot - impot)

    return {
        "produits_exploitation": pe,
        "total_produits_exploitation": total_pe,
        "charges_exploitation": ce,
        "total_charges_exploitation": total_ce,
        "resultat_exploitation": resultat_exploitation,
        "produits_financiers": pf,
        "total_produits_financiers": total_pf,
        "charges_financieres": cf,
        "total_charges_financieres": total_cf,
        "resultat_financier": resultat_financier,
        "resultat_courant": resultat_courant,
        "produits_non_courants": pnc,
        "total_produits_non_courants": total_pnc,
        "charges_non_courantes": cnc,
        "total_charges_non_courantes": total_cnc,
        "resultat_non_courant": resultat_non_courant,
        "resultat_avant_impot": resultat_avant_impot,
        "impot_resultat": impot,
        "resultat_net": resultat_net,
    }


def calculer_bilan(soldes: dict[str, Decimal], resultat_net: Decimal):
    def actif(label, brut, amort=Decimal("0")):
        brut, amort = money(brut), money(amort)
        return {"label": label, "brut": brut, "amort": amort, "net": money(brut - amort)}

    actif_immobilise = [
        actif("Immobilisations en non-valeurs", sd(soldes, ("21",)), sc(soldes, ("281",))),
        actif("Immobilisations incorporelles", sd(soldes, ("22",)), sc(soldes, ("282", "292"))),
        actif("Immobilisations corporelles", sd(soldes, ("23",)), sc(soldes, ("283", "293"))),
        actif("Immobilisations financières", sd(soldes, ("24", "25")), sc(soldes, ("294", "295"))),
        actif("Écarts de conversion — actif", sd(soldes, ("27",))),
    ]
    actif_circulant = [
        actif("Stocks", sd(soldes, ("31",)), sc(soldes, ("391",))),
        actif("Fournisseurs débiteurs, avances", sd(soldes, ("341",))),
        actif("Clients et comptes rattachés", sd(soldes, ("342",)), sc(soldes, ("3942",))),
        actif("Personnel — débiteur", sd(soldes, ("343",)), sc(soldes, ("3943",))),
        actif("État — débiteur", sd(soldes, ("345",))),
        actif("Comptes d'associés — débiteurs", sd(soldes, ("346",)), sc(soldes, ("3946",))),
        actif("Autres débiteurs", sd(soldes, ("348",)), sc(soldes, ("3948",))),
        actif("Comptes de régularisation — actif", sd(soldes, ("349",))),
        actif("Titres et valeurs de placement", sd(soldes, ("350",)), sc(soldes, ("395",))),
        actif("Écarts de conversion — actif circulant", sd(soldes, ("37",))),
    ]
    # La trésorerie est présentée sans compensation : un compte 514 débiteur
    # reste à l'actif, tandis qu'un autre 514 créditeur est isolé au passif.
    # Cela évite notamment un poste « Trésorerie-actif » négatif.
    tresorerie_actif = [
        actif("Chèques et valeurs à encaisser", debit_positions(soldes, ("511",))),
        actif("Banques, TG et CCP — soldes débiteurs", debit_positions(soldes, ("514",))),
        actif("Caisses, régies d'avances", debit_positions(soldes, ("516",)), credit_positions(soldes, ("59",))),
    ]

    def total_net(rows):
        return money(sum((r["net"] for r in rows), Decimal("0")))

    capitaux_propres = [
        {"label": "Capital social ou personnel", "montant": sc(soldes, ("111",))},
        {"label": "Primes d'émission, fusion, apport", "montant": sc(soldes, ("112", "113"))},
        {"label": "Réserves", "montant": sc(soldes, ("114", "115"))},
        {"label": "Report à nouveau", "montant": sc(soldes, ("116",))},
        {"label": "Résultats en instance d'affectation", "montant": sc(soldes, ("118",))},
        {"label": "Résultat antérieur en attente d'affectation (119)", "montant": sc(soldes, ("119",))},
        {"label": "Résultat net de l'exercice", "montant": money(resultat_net)},
    ]
    financement_permanent = [
        {"label": "Capitaux propres assimilés", "montant": sc(soldes, ("131", "135"))},
        {"label": "Dettes de financement", "montant": sc(soldes, ("141", "148"))},
        {"label": "Provisions durables pour risques et charges", "montant": sc(soldes, ("151", "155"))},
        {"label": "Écarts de conversion — passif", "montant": sc(soldes, ("17",))},
    ]
    passif_circulant = [
        {"label": "Fournisseurs et comptes rattachés", "montant": sc(soldes, ("441",))},
        {"label": "Clients créditeurs, avances et acomptes", "montant": sc(soldes, ("442",))},
        {"label": "Personnel — créditeur", "montant": sc(soldes, ("443",))},
        {"label": "Organismes sociaux", "montant": sc(soldes, ("444",))},
        {"label": "État — créditeur", "montant": sc(soldes, ("445",))},
        {"label": "Comptes d'associés — créditeurs", "montant": sc(soldes, ("446",))},
        {"label": "Autres créanciers", "montant": sc(soldes, ("448",))},
        {"label": "Comptes de régularisation — passif", "montant": sc(soldes, ("449",))},
        {"label": "Autres provisions pour risques et charges", "montant": sc(soldes, ("45",))},
        {"label": "Écarts de conversion — passif circulant", "montant": sc(soldes, ("47",))},
    ]
    tresorerie_passif = [
        {"label": "Crédits d'escompte et de trésorerie", "montant": credit_positions(soldes, ("552", "553"))},
        {"label": "Banques — soldes créditeurs", "montant": credit_positions(soldes, ("554",))},
        {
            "label": "Soldes créditeurs des comptes de trésorerie-actif à reclasser",
            "montant": credit_positions(soldes, ("511", "514", "516")),
        },
    ]

    total_actif = money(total_net(actif_immobilise) + total_net(actif_circulant) + total_net(tresorerie_actif))
    total_passif = money(
        sum((x["montant"] for x in capitaux_propres + financement_permanent + passif_circulant + tresorerie_passif), Decimal("0"))
    )
    return {
        "actif_immobilise": actif_immobilise,
        "actif_circulant": actif_circulant,
        "tresorerie_actif": tresorerie_actif,
        "capitaux_propres": capitaux_propres,
        "financement_permanent": financement_permanent,
        "passif_circulant": passif_circulant,
        "tresorerie_passif": tresorerie_passif,
        "total_actif": total_actif,
        "total_passif": total_passif,
        "ecart": money(total_actif - total_passif),
        "equilibre": abs(total_actif - total_passif) <= Decimal("0.01"),
    }


def _serialiser(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(type(obj).__name__)


def canonical_json(snapshot: dict) -> str:
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_serialiser)


def empreinte_snapshot(snapshot: dict) -> str:
    return sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()


def _soldes_valides(db, societe_id: int, exercice: int):
    import models
    soldes: dict[str, Decimal] = {}
    debit_total = Decimal("0")
    credit_total = Decimal("0")
    q = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes))
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
        )
        # Une référence de justificatif est facultative : NOT LIKE sur NULL
        # vaut UNKNOWN en SQL et excluait à tort ces écritures définitives.
        .filter(or_(
            models.Ecriture.reference.is_(None),
            ~models.Ecriture.reference.like(f"CLOTURE-{exercice}%"),
        ))
    )
    rows = q.all()
    for e in rows:
        for l in e.lignes:
            d, c = money(l.debit), money(l.credit)
            debit_total += d
            credit_total += c
            soldes[l.compte] = money(soldes.get(l.compte, Decimal("0")) + d - c)
    return soldes, money(debit_total), money(credit_total), len(rows)


def _detail_balance(soldes):
    rows = []
    for compte, solde in sorted(soldes.items()):
        if not compte or compte[0] not in "12345" or abs(solde) <= Decimal("0.005"):
            continue
        rows.append({
            "compte": compte,
            "debit": to_float(solde if solde > 0 else 0),
            "credit": to_float(-solde if solde < 0 else 0),
            "solde": to_float(solde),
            "sens": "D" if solde > 0 else "C",
        })
    return rows


def stock_apercu_historique_limite(inventaire_valide: bool, nb_articles: int) -> bool:
    """Signale un aperçu de stock non figé, sans présumer de mouvements futurs.

    Si aucun article stockable n'est présent, il n'y a pas de valeurs de stock
    courantes susceptibles d'être prises pour des valeurs historiques.
    """
    return not inventaire_valide and nb_articles > 0


def _stocks(db, societe_id: int, date_fin, soldes):
    """Stock de clôture : photographie physique validée + rapprochement brut.

    La valeur physique au CMUP correspond au stock brut. Les dépréciations 391x
    sont présentées séparément et ne doivent pas créer un faux écart de rapprochement.
    """
    import models
    from services.inventaire_nombres_service import (
        projection_article, projection_snapshot_ligne, diagnostics_lignes, somme, nombre,
    )

    ex = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_debut <= date_fin,
        models.ExerciceComptable.date_fin >= date_fin,
    ).first()
    exercice = ex.annee if ex else date_fin.year
    inv = (
        db.query(models.InventaireStock)
        .options(joinedload(models.InventaireStock.lignes))
        .filter(
            models.InventaireStock.societe_id == societe_id,
            models.InventaireStock.exercice == exercice,
            models.InventaireStock.date_inventaire == date_fin,
        )
        .order_by(models.InventaireStock.id.desc())
        .first()
    )

    lignes = []
    if inv:
        for l in inv.lignes:
            article = db.query(models.Article).filter_by(id=l.article_id).first()
            lignes.append({
                "article_id": l.article_id,
                "code": l.code,
                "designation": l.designation,
                "unite": article.unite if article else None,
                **projection_snapshot_ligne(l),
                "emplacement": article.emplacement if article else None,
                "compte_stock": l.compte_stock,
                "compte_variation": l.compte_variation,
            })
    else:
        # Aperçu de secours : tant qu'aucun comptage de clôture n'a été validé,
        # on montre l'état courant mais il ne peut pas être archivé définitivement.
        articles = db.query(models.Article).filter_by(
            societe_id=societe_id, actif=True, is_stockable=True
        ).order_by(models.Article.code).all()
        for a in articles:
            projection = projection_article(a)
            lignes.append({
                "article_id": a.id,
                "code": a.code,
                "designation": a.designation,
                "unite": a.unite,
                "quantite": projection["stock"],
                "cmup": projection["cmup"],
                "valeur": projection["valeur"],
                "nombres_diagnostics": projection["nombres_diagnostics"],
                "emplacement": a.emplacement,
            })

    brut = sd(soldes, ("31",))
    depreciation = sc(soldes, ("391",))
    net = money(brut - depreciation)
    diagnostics = diagnostics_lignes(lignes)
    diagnostics_total = {}
    if inv:
        nombre(inv.total_valeur, "total_valeur_inventaire", diagnostics_total, negatif=True, decimales=2)
    total = somme([l["valeur"] for l in lignes], "total_valeur", diagnostics_total)
    ecart_brut = somme([total, -to_float(brut)], "ecart_physique_comptable", diagnostics_total)
    diagnostics.extend({"article_id": None, "code": None, "champ": c, "message": m}
                       for c, m in diagnostics_total.items())
    complet = not diagnostics
    ecart_brut = ecart_brut if complet else None
    return {
        "lignes": lignes,
        "nb_articles": len(lignes),
        "inventaire_valide": bool(inv),
        "inventaire_reference": inv.reference if inv else None,
        "date_inventaire": inv.date_inventaire.isoformat() if inv else None,
        "valeur_physique": total if complet else None,
        "valeur_comptable_brute": to_float(brut),
        "depreciations": to_float(depreciation),
        "valeur_comptable_nette": to_float(net),
        "ecart_physique_comptable": ecart_brut,
        "valorisation_complete": complet,
        "diagnostics": diagnostics,
        "historique_stock_limite": stock_apercu_historique_limite(bool(inv), len(lignes)),
    }


def calculer_rapprochement_immobilisations(lignes: list[dict], soldes: dict[str, Decimal]):
    """Rapproche le registre des immobilisations avec les comptes configurés.

    Le contrôle est volontairement fait compte par compte. Une compensation
    entre un manque sur un compte d'immobilisation et un excédent sur un autre
    ne doit pas masquer l'écart. Même logique pour les amortissements cumulés.
    """
    module_brut: dict[str, Decimal] = {}
    module_amort: dict[str, Decimal] = {}

    for x in lignes:
        compte_immo = str(x.get("compte_immo") or "").strip()
        compte_amort = str(x.get("compte_amort") or "").strip()
        if compte_immo:
            module_brut[compte_immo] = money(
                module_brut.get(compte_immo, Decimal("0")) + money(x.get("valeur_brute", 0))
            )
        if compte_amort:
            module_amort[compte_amort] = money(
                module_amort.get(compte_amort, Decimal("0")) + money(x.get("amortissements_cumules", 0))
            )

    details = []
    brut_module = money(sum(module_brut.values(), Decimal("0")))
    amort_module = money(sum(module_amort.values(), Decimal("0")))
    brut_comptable = Decimal("0")
    amort_comptable = Decimal("0")

    for compte in sorted(module_brut):
        attendu = module_brut[compte]
        comptable = money(soldes.get(compte, Decimal("0")))
        brut_comptable += comptable
        details.append({
            "nature": "brut",
            "compte": compte,
            "module": to_float(attendu),
            "comptable": to_float(comptable),
            "ecart": to_float(money(attendu - comptable)),
        })

    for compte in sorted(module_amort):
        attendu = module_amort[compte]
        # Un amortissement cumulé normal porte un solde créditeur.
        comptable = money(-soldes.get(compte, Decimal("0")))
        amort_comptable += comptable
        details.append({
            "nature": "amortissement",
            "compte": compte,
            "module": to_float(attendu),
            "comptable": to_float(comptable),
            "ecart": to_float(money(attendu - comptable)),
        })

    brut_comptable = money(brut_comptable)
    amort_comptable = money(amort_comptable)
    vnc_module = money(brut_module - amort_module)
    vnc_comptable = money(brut_comptable - amort_comptable)
    ecart_brut = money(brut_module - brut_comptable)
    ecart_amort = money(amort_module - amort_comptable)
    ecart_vnc = money(vnc_module - vnc_comptable)

    # Le rapprochement exige que le brut ET les amortissements soient cohérents ;
    # un simple écart VNC nul pourrait résulter de deux erreurs qui se compensent.
    rapproche = abs(ecart_brut) <= CENT and abs(ecart_amort) <= CENT
    return {
        "brut_module": to_float(brut_module),
        "brut_comptable": to_float(brut_comptable),
        "ecart_brut": to_float(ecart_brut),
        "amortissements_module": to_float(amort_module),
        "amortissements_comptables": to_float(amort_comptable),
        "ecart_amortissements": to_float(ecart_amort),
        "vnc_module": to_float(vnc_module),
        "vnc_comptable": to_float(vnc_comptable),
        "ecart_vnc": to_float(ecart_vnc),
        "rapproche": rapproche,
        "details_comptes": details,
    }


def _immobilisations(db, societe_id: int, exercice: int, date_fin, soldes):
    import models
    from services.immobilisations_service import situation_a_date

    rows = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.date_acquisition <= date_fin,
    ).order_by(models.Immobilisation.date_acquisition, models.Immobilisation.id).all()

    lignes, brut_total, amort_total, vnc_total = [], Decimal("0"), Decimal("0"), Decimal("0")
    for immo in rows:
        if immo.date_sortie and immo.date_sortie <= date_fin:
            continue
        brut = money(immo.valeur_brute)
        cumul = Decimal("0")
        if immo.amortissable:
            try:
                cumul = money(situation_a_date(immo, date_fin)["cumul"])
            except Exception:
                cumul = Decimal("0")
        cumul = min(cumul, brut)
        vnc = money(brut - cumul)
        brut_total += brut; amort_total += cumul; vnc_total += vnc
        lignes.append({
            "id": immo.id,
            "reference": immo.reference,
            "designation": immo.designation,
            "categorie": immo.categorie,
            "date_acquisition": immo.date_acquisition.isoformat() if immo.date_acquisition else None,
            "date_mise_en_service": immo.date_mise_en_service.isoformat() if immo.date_mise_en_service else None,
            "compte_immo": immo.compte_immo,
            "compte_amort": immo.compte_amort,
            "valeur_brute": to_float(brut),
            "amortissements_cumules": to_float(cumul),
            "vnc": to_float(vnc),
        })
    rapprochement = calculer_rapprochement_immobilisations(lignes, soldes)
    return {
        "lignes": lignes,
        "nb": len(lignes),
        "valeur_brute": to_float(brut_total),
        "amortissements_cumules": to_float(amort_total),
        "vnc": to_float(vnc_total),
        "rapprochement": rapprochement,
    }


def etat_rapprochement_immobilisations(db, societe_id: int, exercice: int, date_fin, soldes=None):
    """Retourne le rapprochement registre immobilisations / comptabilité.

    ``soldes`` peut être fourni par le moteur de clôture pour éviter une seconde
    lecture de la balance. Sans soldes fournis, seuls les mouvements validés sont
    pris en compte, hors écritures techniques de clôture.
    """
    if soldes is None:
        soldes, _, _, _ = _soldes_valides(db, societe_id, exercice)
    return _immobilisations(db, societe_id, exercice, date_fin, soldes).get("rapprochement", {})


def construire_snapshot(db, societe_id: int, exercice: int):
    import models
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if not ex:
        raise ValueError(f"Exercice {exercice} introuvable.")

    cloture = db.query(models.ClotureExercice).filter_by(societe_id=societe_id, exercice=exercice).first()
    brouillons = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice, est_validee=False
    ).count()
    soldes, total_debit, total_credit, nb_ecritures = _soldes_valides(db, societe_id, exercice)
    cpc = calculer_cpc(soldes)
    bilan = calculer_bilan(soldes, cpc["resultat_net"])
    stocks = _stocks(db, societe_id, ex.date_fin, soldes)
    immos = _immobilisations(db, societe_id, exercice, ex.date_fin, soldes)

    ajustements = db.query(models.AjustementInventaire).filter_by(
        societe_id=societe_id, exercice=exercice
    ).order_by(models.AjustementInventaire.type, models.AjustementInventaire.id).all()

    snap = {
        "version": CURRENT_LIVRE_VERSION,
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "exercice": {
            "annee": exercice,
            "date_debut": ex.date_debut.isoformat(),
            "date_fin": ex.date_fin.isoformat(),
            "statut": ex.statut,
            "cloture": bool(cloture),
            "date_cloture": cloture.date_cloture.isoformat() if cloture and cloture.date_cloture else None,
        },
        "comptabilite": {
            "nb_ecritures_validees": nb_ecritures,
            "nb_brouillons": brouillons,
            "total_debit": to_float(total_debit),
            "total_credit": to_float(total_credit),
            "balance_equilibree": abs(total_debit - total_credit) <= Decimal("0.01"),
            "balance_comptes_bilan": _detail_balance(soldes),
        },
        "bilan": bilan,
        "cpc": cpc,
        "stocks": stocks,
        "immobilisations": immos,
        "ajustements_inventaire": [{
            "id": a.id,
            "type": a.type,
            "libelle": a.libelle,
            "montant": to_float(a.montant),
            "compte_activite": a.compte_activite,
            "compte_contrepartie": a.compte_contrepartie,
        } for a in ajustements],
    }
    snap["controles"] = {
        "exercice_cloture": bool(cloture),
        "aucun_brouillon": brouillons == 0,
        "balance_equilibree": snap["comptabilite"]["balance_equilibree"],
        "bilan_equilibre": bool(bilan["equilibre"]),
        "inventaire_stock_valide": bool(stocks.get("inventaire_valide")) or stocks.get("nb_articles", 0) == 0,
        "stock_rapproche": stocks.get("valorisation_complete", True) and ((stocks.get("nb_articles", 0) == 0 and abs(Decimal(str(stocks["valeur_comptable_brute"]))) <= Decimal("0.01")) or (bool(stocks.get("inventaire_valide")) and abs(Decimal(str(stocks["ecart_physique_comptable"]))) <= Decimal("0.01"))),
        "valorisation_stock_complete": stocks.get("valorisation_complete", True),
        "immobilisations_rapprochees": bool(immos.get("rapprochement", {}).get("rapproche")),
        "historique_stock_limite": stocks["historique_stock_limite"],
    }
    # Une archive définitive ne doit figer qu'un exercice dont les contrôles
    # de cohérence sont tous satisfaits. Le contrôle backend est volontairement
    # plus strict qu'un simple équilibre débit/crédit.
    snap["controles"]["archivable"] = (
        snap["controles"]["exercice_cloture"]
        and snap["controles"]["aucun_brouillon"]
        and snap["controles"]["balance_equilibree"]
        and snap["controles"]["bilan_equilibre"]
        and snap["controles"]["stock_rapproche"]
        and snap["controles"]["immobilisations_rapprochees"]
    )
    return snap
