"""Contrôles de cohérence avant mise en production (FACT.11).

Ce module ne corrige jamais automatiquement les données. Il signale les écarts
qui nécessitent une décision métier/comptable afin d'éviter qu'un outil de
"réparation" silencieux altère une pièce définitive.
"""
from decimal import Decimal
import json
from sqlalchemy import text
from sqlalchemy.orm import joinedload

import models
from services.tva_service import ventilation_facture, total_ventilation
from services.identifiants_maroc_service import normaliser_ice, normaliser_if, normaliser_tp


def _item(code, libelle, niveau, count=0, details=None):
    count = int(count or 0)
    return {
        "code": code,
        "libelle": libelle,
        "niveau": niveau,
        "ok": count == 0,
        "nb": count,
        "details": details or [],
    }


def _count(db, sql, params):
    return int(db.execute(text(sql), params).scalar() or 0)


def controler_production(db, societe_id: int, exercice: int | None = None):
    p = {"sid": societe_id, "ex": exercice}
    ex_filter = " AND f.exercice = :ex" if exercice is not None else ""
    e_ex_filter = " AND e.exercice = :ex" if exercice is not None else ""

    checks = []
    checks.append(_item(
        "FACTURE_VALIDEE_INCOMPLETE", "Factures validées avec métadonnées obligatoires manquantes", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM factures f
             WHERE f.societe_id=:sid AND COALESCE(f.est_proforma,false)=false
               AND COALESCE(f.est_validee,false)=true {ex_filter}
               AND (NULLIF(BTRIM(COALESCE(f.numero,'')), '') IS NULL
                    OR f.date_echeance IS NULL
                    OR (f.type::text='achat' AND (f.tiers_id IS NULL OR NULLIF(BTRIM(COALESCE(f.reference,'')), '') IS NULL)))
        """, p)
    ))
    checks.append(_item(
        "FACTURE_VALIDEE_SANS_LIGNE", "Factures validées sans ligne", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM factures f
             WHERE f.societe_id=:sid AND COALESCE(f.est_proforma,false)=false
               AND COALESCE(f.est_validee,false)=true {ex_filter}
               AND NOT EXISTS (SELECT 1 FROM lignes_facture l WHERE l.facture_id=f.id)
        """, p)
    ))
    checks.append(_item(
        "NUMERO_FACTURE_DUPLIQUE", "Numéros internes de facture dupliqués", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM (
              SELECT f.numero FROM factures f
               WHERE f.societe_id=:sid AND f.numero IS NOT NULL {ex_filter}
               GROUP BY f.numero HAVING count(*) > 1
            ) x
        """, p)
    ))
    checks.append(_item(
        "REF_FOURNISSEUR_DUPLIQUE", "Références fournisseur validées dupliquées", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM (
              SELECT f.tiers_id, f.exercice, lower(btrim(f.reference)) ref
                FROM factures f
               WHERE f.societe_id=:sid AND f.type::text='achat'
                 AND COALESCE(f.est_proforma,false)=false AND COALESCE(f.est_validee,false)=true
                 AND f.tiers_id IS NOT NULL AND NULLIF(BTRIM(COALESCE(f.reference,'')), '') IS NOT NULL {ex_filter}
               GROUP BY f.tiers_id, f.exercice, lower(btrim(f.reference)) HAVING count(*) > 1
            ) x
        """, p)
    ))
    checks.append(_item(
        "FACTURE_VALIDEE_NON_COMPTABILISEE", "Factures définitives non comptabilisées", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM factures f
             WHERE f.societe_id=:sid AND COALESCE(f.est_proforma,false)=false
               AND COALESCE(f.est_validee,false)=true AND COALESCE(f.est_comptabilisee,false)=false {ex_filter}
        """, p)
    ))
    a_ex_filter = " AND a.exercice = :ex" if exercice is not None else ""
    ac_ex_filter = " AND ac.exercice = :ex" if exercice is not None else ""
    date_doc_filter_r = ""
    date_doc_filter_i = ""
    if exercice is not None:
        date_doc_filter_r = """ AND r.date BETWEEN
            (SELECT x.date_debut FROM exercices_comptables x WHERE x.societe_id=:sid AND x.annee=:ex) AND
            (SELECT x.date_fin FROM exercices_comptables x WHERE x.societe_id=:sid AND x.annee=:ex)"""
        date_doc_filter_i = """ AND i.date_imputation BETWEEN
            (SELECT x.date_debut FROM exercices_comptables x WHERE x.societe_id=:sid AND x.annee=:ex) AND
            (SELECT x.date_fin FROM exercices_comptables x WHERE x.societe_id=:sid AND x.annee=:ex)"""
    checks.append(_item(
        "AVOIR_NON_COMPTABILISE", "Avoirs définitifs non comptabilisés", "bloquant",
        _count(db, f"""SELECT count(*) FROM avoirs a WHERE a.societe_id=:sid
            AND COALESCE(a.statut::text,'emis') <> 'annule' AND COALESCE(a.est_comptabilisee,false)=false {a_ex_filter}""", p)
    ))
    checks.append(_item(
        "REGLEMENT_NON_COMPTABILISE", "Règlements non rejetés non comptabilisés", "bloquant",
        _count(db, f"""SELECT count(*) FROM reglements r WHERE r.societe_id=:sid
            AND COALESCE(r.statut,'') NOT IN ('rejete','annule') AND COALESCE(r.est_comptabilisee,false)=false {date_doc_filter_r}""", p)
    ))
    checks.append(_item(
        "ACOMPTE_NON_COMPTABILISE", "Acomptes non annulés non comptabilisés", "bloquant",
        _count(db, f"""SELECT count(*) FROM acomptes ac WHERE ac.societe_id=:sid
            AND COALESCE(ac.statut,'') <> 'annule' AND COALESCE(ac.est_comptabilisee,false)=false {ac_ex_filter}""", p)
    ))
    checks.append(_item(
        "IMPUTATION_ACOMPTE_NON_COMPTABILISEE", "Imputations d'acomptes non comptabilisées", "bloquant",
        _count(db, f"""SELECT count(*) FROM imputations_acomptes i WHERE i.societe_id=:sid
            AND COALESCE(i.est_comptabilisee,false)=false {date_doc_filter_i}""", p)
    ))

    checks.append(_item(
        "LIGNE_FACTURE_INVALIDE", "Lignes de facture avec quantité/prix/TVA/remise incohérents", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM lignes_facture l JOIN factures f ON f.id=l.facture_id
             WHERE f.societe_id=:sid {ex_filter}
               AND (COALESCE(l.quantite,0) <= 0 OR COALESCE(l.prix_unitaire,0) < 0
                    OR COALESCE(l.tva,0) < 0 OR COALESCE(l.tva,0) > 100
                    OR COALESCE(l.remise,0) < 0 OR COALESCE(l.remise,0) > 100
                    OR COALESCE(l.remise2,0) < 0 OR COALESCE(l.remise2,0) > 100
                    OR COALESCE(l.rabais,0) < 0)
        """, p)
    ))
    checks.append(_item(
        "LIEN_BC_AUTRE_SOCIETE", "Bons de commande liés à un devis/facture d'une autre société", "bloquant",
        _count(db, """
            SELECT count(*) FROM bons_commande bc
            LEFT JOIN devis d ON d.id=bc.devis_id
            LEFT JOIN factures f ON f.id=bc.facture_id
            WHERE bc.societe_id=:sid
              AND ((d.id IS NOT NULL AND d.societe_id<>bc.societe_id)
                OR (f.id IS NOT NULL AND f.societe_id<>bc.societe_id))
        """, p)
    ))
    checks.append(_item(
        "LIEN_BL_AUTRE_SOCIETE", "BL/BR liés à une commande/facture d'une autre société", "bloquant",
        _count(db, """
            SELECT count(*) FROM bons_livraison bl
            LEFT JOIN bons_commande bc ON bc.id=bl.bon_commande_id
            LEFT JOIN factures f ON f.id=bl.facture_id
            WHERE bl.societe_id=:sid
              AND ((bc.id IS NOT NULL AND bc.societe_id<>bl.societe_id)
                OR (f.id IS NOT NULL AND f.societe_id<>bl.societe_id))
        """, p)
    ))
    checks.append(_item(
        "LIEN_LIGNE_SOURCE_AUTRE_SOCIETE", "Lignes commerciales liées à des sources d'une autre société", "bloquant",
        _count(db, """
            SELECT count(*) FROM (
              SELECT lf.id FROM lignes_facture lf
              JOIN factures f ON f.id=lf.facture_id
              LEFT JOIN lignes_devis ld ON ld.id=lf.source_ligne_devis_id LEFT JOIN devis d ON d.id=ld.devis_id
              LEFT JOIN lignes_bon_commande lbc ON lbc.id=lf.source_ligne_bc_id LEFT JOIN bons_commande bc ON bc.id=lbc.bon_commande_id
              LEFT JOIN lignes_bon_livraison lbl ON lbl.id=lf.source_ligne_bl_id LEFT JOIN bons_livraison bl ON bl.id=lbl.bon_livraison_id
              WHERE f.societe_id=:sid AND ((d.id IS NOT NULL AND d.societe_id<>f.societe_id)
                OR (bc.id IS NOT NULL AND bc.societe_id<>f.societe_id) OR (bl.id IS NOT NULL AND bl.societe_id<>f.societe_id))
              UNION ALL
              SELECT lbc2.id FROM lignes_bon_commande lbc2 JOIN bons_commande bc2 ON bc2.id=lbc2.bon_commande_id
              LEFT JOIN lignes_devis ld2 ON ld2.id=lbc2.source_ligne_devis_id LEFT JOIN devis d2 ON d2.id=ld2.devis_id
              WHERE bc2.societe_id=:sid AND d2.id IS NOT NULL AND d2.societe_id<>bc2.societe_id
              UNION ALL
              SELECT lbl2.id FROM lignes_bon_livraison lbl2 JOIN bons_livraison bl2 ON bl2.id=lbl2.bon_livraison_id
              LEFT JOIN lignes_bon_commande lbc3 ON lbc3.id=lbl2.source_ligne_bc_id LEFT JOIN bons_commande bc3 ON bc3.id=lbc3.bon_commande_id
              WHERE bl2.societe_id=:sid AND bc3.id IS NOT NULL AND bc3.societe_id<>bl2.societe_id
            ) x
        """, p)
    ))

    checks.append(_item(
        "ECRITURE_VALIDEE_DESEQUILIBREE", "Écritures validées déséquilibrées", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM (
              SELECT e.id
                FROM ecritures e LEFT JOIN lignes_ecriture l ON l.ecriture_id=e.id
               WHERE e.societe_id=:sid AND COALESCE(e.est_validee,false)=true {e_ex_filter}
               GROUP BY e.id
              HAVING abs(COALESCE(sum(l.debit),0)-COALESCE(sum(l.credit),0)) > 0.01
            ) x
        """, p)
    ))
    checks.append(_item(
        "ECRITURE_VALIDEE_SANS_LIGNE", "Écritures validées sans ligne", "bloquant",
        _count(db, f"""
            SELECT count(*) FROM ecritures e
             WHERE e.societe_id=:sid AND COALESCE(e.est_validee,false)=true {e_ex_filter}
               AND NOT EXISTS (SELECT 1 FROM lignes_ecriture l WHERE l.ecriture_id=e.id)
        """, p)
    ))
    checks.append(_item(
        "LIEN_REGLEMENT_AUTRE_SOCIETE", "Règlements liés à une facture d'une autre société", "bloquant",
        _count(db, """
            SELECT count(*) FROM reglements r JOIN factures f ON f.id=r.facture_id
             WHERE r.societe_id=:sid AND f.societe_id<>r.societe_id
        """, p)
    ))
    checks.append(_item(
        "LIEN_AVOIR_AUTRE_SOCIETE", "Avoirs liés à une facture d'une autre société", "bloquant",
        _count(db, """
            SELECT count(*) FROM avoirs a JOIN factures f ON f.id=a.facture_id
             WHERE a.societe_id=:sid AND f.societe_id<>a.societe_id
        """, p)
    ))
    checks.append(_item(
        "LIEN_IMPUTATION_AUTRE_SOCIETE", "Imputations d'acomptes incohérentes entre sociétés", "bloquant",
        _count(db, """
            SELECT count(*) FROM imputations_acomptes i
              JOIN acomptes a ON a.id=i.acompte_id
              JOIN factures f ON f.id=i.facture_id
             WHERE i.societe_id=:sid
               AND (a.societe_id<>i.societe_id OR f.societe_id<>i.societe_id)
        """, p)
    ))
    checks.append(_item(
        "ACOMPTE_SURIMPUTE", "Acomptes imputés au-delà de leur montant", "bloquant",
        _count(db, """
            SELECT count(*) FROM (
              SELECT a.id, a.montant, COALESCE(sum(i.montant),0) impute
                FROM acomptes a LEFT JOIN imputations_acomptes i ON i.acompte_id=a.id
               WHERE a.societe_id=:sid
               GROUP BY a.id, a.montant
              HAVING COALESCE(sum(i.montant),0) > a.montant + 0.01
            ) x
        """, p)
    ))
    checks.append(_item(
        "STOCK_NEGATIF", "Articles stockables avec stock négatif", "avertissement",
        _count(db, """
            SELECT count(*) FROM articles a
             WHERE a.societe_id=:sid AND COALESCE(a.is_stockable,true)=true AND COALESCE(a.stock_actuel,0) < -0.0001
        """, p)
    ))
    if exercice is not None:
        checks.append(_item(
            "BROUILLON_EXERCICE_CLOTURE", "Pièces encore en brouillon dans un exercice clôturé", "avertissement",
            _count(db, """
                SELECT
                  (SELECT count(*) FROM factures f
                    WHERE f.societe_id=:sid AND f.exercice=:ex AND COALESCE(f.est_proforma,false)=false AND COALESCE(f.est_validee,false)=false)
                + (SELECT count(*) FROM ecritures e
                    WHERE e.societe_id=:sid AND e.exercice=:ex AND COALESCE(e.est_validee,false)=false)
                WHERE EXISTS (SELECT 1 FROM exercices_comptables x
                               WHERE x.societe_id=:sid AND x.annee=:ex AND x.statut='cloture')
            """, p)
        ))

    # FACT-E — contrôle historique des identités figées. Les validations futures
    # empêchent ces anomalies ; l'audit permet de repérer les données legacy.
    identite_vendeur_incomplete = []
    identite_client_b2b_incomplete = []
    q_identites = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.est_validee == True,
        models.Facture.est_proforma == False,
        models.Facture.type == "vente",
    )
    if exercice is not None:
        q_identites = q_identites.filter(models.Facture.exercice == exercice)
    for f in q_identites.all():
        try:
            vendeur = json.loads(f.societe_snapshot_json or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            vendeur = {}
        requis_vendeur = ("raison_sociale", "identifiant_fiscal", "ice", "patente", "adresse", "ville")
        vendeur_ok = all(str(vendeur.get(k) or "").strip() for k in requis_vendeur)
        if vendeur_ok:
            try:
                normaliser_ice(vendeur.get("ice")); normaliser_if(vendeur.get("identifiant_fiscal")); normaliser_tp(vendeur.get("patente"))
            except ValueError:
                vendeur_ok = False
        if not vendeur_ok:
            identite_vendeur_incomplete.append({"facture_id": f.id, "numero": f.numero})

        if (f.tiers_categorie_snapshot or "").lower() == "professionnel":
            client_ok = bool(str(f.tiers_adresse_snapshot or "").strip())
            try:
                normaliser_ice(f.tiers_ice_snapshot)
            except ValueError:
                client_ok = False
            if not client_ok:
                identite_client_b2b_incomplete.append({"facture_id": f.id, "numero": f.numero})

    checks.append(_item(
        "SNAPSHOT_VENDEUR_INCOMPLET", "Factures de vente avec identité vendeur historique incomplète/invalide", "bloquant",
        len(identite_vendeur_incomplete), identite_vendeur_incomplete[:50]
    ))
    checks.append(_item(
        "SNAPSHOT_CLIENT_B2B_INCOMPLET", "Factures B2B avec identité client historique incomplète/invalide", "bloquant",
        len(identite_client_b2b_incomplete), identite_client_b2b_incomplete[:50]
    ))

    # La fiche courante doit être exploitable pour les prochaines factures.
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    identite_courante_invalide = 0
    if societe:
        try:
            normaliser_ice(societe.ice)
            normaliser_if(societe.identifiant_fiscal)
            normaliser_tp(societe.patente)
        except ValueError:
            identite_courante_invalide = 1
    checks.append(_item(
        "IDENTIFIANTS_SOCIETE_INVALIDES", "Identifiants fiscaux de la société au format invalide", "avertissement",
        identite_courante_invalide
    ))

    # Contrôle Python des échéanciers : leur somme doit rester réconciliée au TTC
    # de la facture, y compris après les règles TVA/frais de CONFORM.1.
    q = db.query(models.Facture).options(
        joinedload(models.Facture.lignes), joinedload(models.Facture.echeances)
    ).filter(models.Facture.societe_id == societe_id, models.Facture.est_validee == True)
    if exercice is not None:
        q = q.filter(models.Facture.exercice == exercice)
    mismatches = []
    for f in q.all():
        if not f.echeances:
            continue
        ttc = Decimal(str(total_ventilation(ventilation_facture(f))["ttc"]))
        ech = sum((Decimal(str(e.montant or 0)) for e in f.echeances), Decimal("0"))
        if abs(ttc - ech) > Decimal("0.01"):
            mismatches.append({"facture_id": f.id, "numero": f.numero, "ttc": float(ttc), "echeancier": float(ech)})
    checks.append(_item(
        "ECHEANCIER_NON_RECONCILIE", "Échéanciers dont le total diffère du TTC", "bloquant",
        len(mismatches), mismatches[:50]
    ))

    bloquants = [x for x in checks if x["niveau"] == "bloquant" and not x["ok"]]
    avertissements = [x for x in checks if x["niveau"] == "avertissement" and not x["ok"]]
    return {
        "societe_id": societe_id,
        "exercice": exercice,
        "pret_production": not bloquants,
        "nb_bloquants": len(bloquants),
        "nb_avertissements": len(avertissements),
        "checks": checks,
    }
