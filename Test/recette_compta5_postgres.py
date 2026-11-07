# -*- coding: utf-8 -*-
"""COMPTA.5 — recette E2E comptable sur PostgreSQL réel, sans données persistées.

Cette recette utilise la DATABASE_URL du backend et exécute tout dans une seule
transaction. Les ``commit()`` applicatifs sont transformés en ``flush()`` pendant
la recette, puis un ROLLBACK final supprime intégralement la société, les pièces,
les écritures, les numéros et les traces créés par le scénario.

Par sécurité, une base distante est refusée sauf si
HISABPRO_ALLOW_REMOTE_PG_TESTS=1 est explicitement défini.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _fail(message: str):
    print(f"[ECHEC] {message}")
    raise SystemExit(1)


def _check(label: str, condition: bool, detail: str = ""):
    if not condition:
        _fail(f"{label}" + (f" — {detail}" if detail else ""))
    print(f"[OK] {label}")


def _guard_local_database(database_url: str):
    parsed = urlparse(database_url)
    host = (parsed.hostname or "").lower()
    if host not in {"localhost", "127.0.0.1", "::1", ""} and os.getenv("HISABPRO_ALLOW_REMOTE_PG_TESTS") != "1":
        _fail(
            "Recette PostgreSQL refusée sur une base distante. "
            "Utilisez une base locale/test ou définissez explicitement HISABPRO_ALLOW_REMOTE_PG_TESTS=1."
        )


def _preflight(db):
    """Vérifie que les migrations structurantes utilisées par COMPTA.5 sont installées."""
    from sqlalchemy import text

    checks = {
        "ecriture_justificatifs": "SELECT to_regclass('public.ecriture_justificatifs') IS NOT NULL",
        "ecriture_sequences": "SELECT to_regclass('public.ecriture_sequences') IS NOT NULL",
        "periodes_comptables": "SELECT to_regclass('public.periodes_comptables') IS NOT NULL",
        "fonction_numero": "SELECT to_regprocedure('public.hisabpro_numero_a_la_validation()') IS NOT NULL",
    }
    for label, sql in checks.items():
        ok = bool(db.execute(text(sql)).scalar())
        _check(f"Préflight migration : {label}", ok)


def _valider_brouillon(db, cu, reference: str, source: str):
    import models
    from routers import ecritures

    ec = (
        db.query(models.Ecriture)
        .filter_by(societe_id=cu["societe_id"], reference=reference, source=source, est_validee=False)
        .order_by(models.Ecriture.id.desc())
        .first()
    )
    _check(f"Brouillon comptable généré ({source} / {reference})", ec is not None)
    out = ecritures.valider_ecriture(ec.id, cu, db)
    db.refresh(ec)
    _check(f"Écriture validée et numérotée ({reference})", bool(out.get("numero_ecriture")) and ec.est_validee)
    return ec


def _avancer_jusqua_decembre(db, cu, annee: int):
    """Fait progresser les périodes sans jamais rouvrir une période fermée."""
    import models
    from routers import exercices

    ex = db.query(models.ExerciceComptable).filter_by(societe_id=cu["societe_id"], annee=annee).first()
    if not ex:
        _fail(f"Exercice {annee} introuvable")

    for _ in range(24):
        rows = (
            db.query(models.PeriodeComptable)
            .filter_by(exercice_id=ex.id)
            .order_by(models.PeriodeComptable.numero.asc())
            .all()
        )
        dec = next((p for p in rows if p.numero == 12), None)
        if dec and dec.statut == "ouverte":
            return
        futures = [p for p in rows if p.statut == "a_venir"]
        if not futures:
            _fail("Impossible d'ouvrir décembre : aucune période future disponible")
        ouvertes = [p for p in rows if p.statut == "ouverte"]
        if len(ouvertes) >= 2:
            cible = sorted(ouvertes, key=lambda p: p.numero)[0]
            exercices.changer_statut_periode(
                annee, cible.numero, exercices.PeriodeStatutIn(statut="fermee"), cu, db
            )
        cible = sorted(futures, key=lambda p: p.numero)[0]
        exercices.changer_statut_periode(
            annee, cible.numero, exercices.PeriodeStatutIn(statut="ouverte"), cu, db
        )
    _fail("Boucle de progression des périodes interrompue par garde-fou")


def run() -> int:
    try:
        import psycopg2  # noqa: F401
    except Exception:
        _fail("psycopg2-binary absent. Activez le venv backend puis installez requirements.txt.")

    from database import DATABASE_URL, SessionLocal
    import models, schemas
    from routers import factures, commercial, cloture, fec
    from services.exercices_service import ensure_exercice
    from services.fec_service import lignes_fec

    _guard_local_database(DATABASE_URL)
    db = SessionLocal()
    real_commit = db.commit
    real_rollback = db.rollback
    # Tous les endpoints partagent la même transaction de recette. Aucun commit
    # ne doit rendre les données de test persistantes.
    db.commit = db.flush  # type: ignore[method-assign]

    token = uuid.uuid4().hex[:10]
    annee = date.today().year
    d = date.today()

    try:
        _preflight(db)

        societe = models.Societe(
            raison_sociale=f"RECETTE COMPTA5 {token}",
            ice=f"T{token[:18]}",
            regime_tva="encaissement",
            stock_declencheur_vente="facture",
            stock_declencheur_achat="facture",
        )
        db.add(societe); db.flush()
        user = models.Utilisateur(
            societe_id=societe.id,
            nom="Recette COMPTA5",
            email=f"recette-compta5-{token}@hisabpro.test",
            hashed_password="recette-non-utilisable",
            role="admin",
            actif=True,
        )
        db.add(user)
        db.add(models.ModuleActif(societe_id=societe.id, module="comptabilite", actif=True))
        db.flush()
        cu = {"societe_id": societe.id, "id": user.id, "role": "admin"}

        ensure_exercice(db, societe.id, annee)
        db.flush()

        client = models.Tiers(
            societe_id=societe.id, type="client", nom=f"CLIENT {token}",
            compte_client="3421", plafond_credit=0, actif=True,
        )
        fournisseur = models.Tiers(
            societe_id=societe.id, type="fournisseur", nom=f"FOURNISSEUR {token}",
            compte_fournisseur="4411", actif=True,
        )
        db.add_all([client, fournisseur]); db.flush()
        famille = models.FamilleArticle(
            societe_id=societe.id, code=f"SERV-{token[:5]}", libelle="Services recette",
            compte_vente="7124", compte_achat="6126", tva_defaut=20, actif=True,
        )
        db.add(famille); db.flush()
        article = models.Article(
            societe_id=societe.id, famille_id=famille.id, code=f"S-{token[:6]}",
            designation="Service recette COMPTA.5", prix_vente_ht=100, prix_achat_ht=50,
            tva=20, is_stockable=False, actif=True,
        )
        db.add(article); db.flush()

        # Vente -> comptabilisation -> validation écriture -> règlement -> validation écriture.
        vente = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=d, tiers=client.nom, tiers_id=client.id,
            lignes=[schemas.LigneFactureCreate(
                article_id=article.id, description=article.designation,
                quantite=1, prix_unitaire=100, tva=20,
            )],
        ), cu, db)
        vf = db.query(models.Facture).filter_by(id=vente["id"]).first()
        factures.valider_facture(vf.id, cu, db); db.refresh(vf)
        factures.comptabiliser_facture(vf.id, cu, db)
        ec_vente = _valider_brouillon(db, cu, vf.numero, "facture")
        _check("Vente : Ref_Piece = numéro facture client", ec_vente.reference == vf.numero)

        commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=vf.id, date=d, tiers=vf.tiers, montant=120,
            mode="virement", reference=f"VIR-CLIENT-{token}", comptabiliser=True,
        ), cu, db)
        ec_enc = _valider_brouillon(db, cu, f"VIR-CLIENT-{token}", "reglement")
        _check("Encaissement : source et pièce automatiques", ec_enc.date_piece == d)

        # Achat -> la Ref_Piece FEC doit être le numéro fournisseur.
        ref_fournisseur = f"FF-{token}"
        achat = factures.creer_facture(schemas.FactureCreate(
            type="achat", date=d, tiers=fournisseur.nom, tiers_id=fournisseur.id,
            reference=ref_fournisseur,
            lignes=[schemas.LigneFactureCreate(
                article_id=article.id, description=article.designation,
                quantite=1, prix_unitaire=50, tva=20,
            )],
        ), cu, db)
        af = db.query(models.Facture).filter_by(id=achat["id"]).first()
        factures.valider_facture(af.id, cu, db); db.refresh(af)
        factures.comptabiliser_facture(af.id, cu, db)
        ec_achat = _valider_brouillon(db, cu, ref_fournisseur, "facture")
        _check("Achat : Ref_Piece = numéro facture fournisseur", ec_achat.reference == ref_fournisseur)

        commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=af.id, date=d, tiers=af.tiers, montant=60,
            mode="virement", reference=f"VIR-FOURN-{token}", comptabiliser=True,
        ), cu, db)
        _valider_brouillon(db, cu, f"VIR-FOURN-{token}", "reglement")

        # Périodes : progression irréversible jusqu'à la période de clôture.
        _avancer_jusqua_decembre(db, cu, annee)
        resultat_cloture = cloture.cloturer_exercice(annee, False, cu, db)
        _check("Clôture définitive réalisée", "clôturé" in resultat_cloture["message"])
        _check("Résultat attendu = bénéfice 50 MAD", abs(resultat_cloture["resultat_net"] - 50.0) < 0.01)

        ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe.id, annee=annee).first()
        _check("Exercice marqué clôturé", ex.statut == "cloture")
        an = db.query(models.Ecriture).filter_by(
            societe_id=societe.id, exercice=annee + 1, journal="AN", source="cloture"
        ).first()
        _check("À-nouveaux N+1 générés et validés", an is not None and an.est_validee and bool(an.numero_ecriture))

        controle = fec.apercu_fec(annee, cu, db)
        _check("FEC conforme après clôture", controle["conforme_export"], str(controle["bloquants"]))
        _, cloture_obj, ecritures = fec._charger_exercice(db, societe.id, annee)
        rows = list(lignes_fec(ecritures, annee, cloture_obj))
        _check("Toutes les lignes FEC ont 18 colonnes", bool(rows) and all(len(row) == 18 for row in rows))
        _check("Référence fournisseur présente dans le FEC", any(row[8] == ref_fournisseur for row in rows))
        _check("Référence règlement client présente dans le FEC", any(row[8] == f"VIR-CLIENT-{token}" for row in rows))

        print("=" * 72)
        print("COMPTA.5 — recette PostgreSQL E2E réussie. ROLLBACK intégral en cours.")
        return 0
    except Exception as exc:
        print(f"[ECHEC] {type(exc).__name__}: {exc}")
        return 1
    finally:
        # Appel de la vraie méthode sauvegardée, pas du commit neutralisé.
        real_rollback()
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
