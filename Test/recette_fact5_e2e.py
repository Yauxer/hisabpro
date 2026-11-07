# -*- coding: utf-8 -*-
"""FACT.5 — recette E2E du cycle commercial HisabPro.

Cette recette est volontairement exécutable sans PostgreSQL afin de valider la
logique applicative dans la CI. Les fonctions de réservation atomique de numéros,
qui sont couvertes séparément par les tests SQL FACT.4B, sont remplacées ici par
un compteur déterministe. La vraie migration PostgreSQL 030 reste la source de
vérité pour la concurrence en production.
"""
from __future__ import annotations

import os
import sys
import types
from datetime import date
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Isoler la recette de la base PostgreSQL configurée par défaut.
os.environ.setdefault("SECRET_KEY", "x" * 40)
fdb = types.ModuleType("database")
fdb.engine = create_engine("sqlite:///:memory:")
fdb.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=fdb.engine)
fdb.Base = declarative_base()
fdb.get_db = lambda: None
sys.modules["database"] = fdb

fauth = types.ModuleType("auth")
fauth.get_current_user = lambda: {"societe_id": 1, "id": 1, "role": "admin"}
fauth.requiert_ecriture = fauth.get_current_user
fauth.requiert_admin = fauth.get_current_user
fauth.hash_password = lambda p: p
fauth.verify_password = lambda a, b: True
fauth.create_access_token = lambda **kwargs: "token"
sys.modules["auth"] = fauth

import models  # noqa: E402
import schemas  # noqa: E402
from routers import commercial, factures  # noqa: E402

# Deux tables contiennent des CHECK PostgreSQL non compilables sous SQLite.
# Elles ne sont pas nécessaires à cette recette ; la clôture est testée via
# clotures_exercice, utilisée par exercice_est_clos().
_tables = [
    t for t in fdb.Base.metadata.sorted_tables
    if t.name not in {"exercices_comptables", "periodes_comptables"}
]
fdb.Base.metadata.create_all(fdb.engine, tables=_tables)
# Versions SQLite minimales des deux tables exclues ci-dessus : le moteur de stock
# les consulte pour vérifier qu'une date appartient à une période ouverte.
with fdb.engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE exercices_comptables (
            id INTEGER PRIMARY KEY, societe_id INTEGER NOT NULL, annee INTEGER NOT NULL,
            date_debut DATE NOT NULL, date_fin DATE NOT NULL, statut VARCHAR(20) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(societe_id, annee)
        )
    """))
    conn.execute(text("""
        CREATE TABLE periodes_comptables (
            id INTEGER PRIMARY KEY, exercice_id INTEGER NOT NULL, numero INTEGER NOT NULL,
            libelle VARCHAR(40) NOT NULL, date_debut DATE NOT NULL, date_fin DATE NOT NULL,
            statut VARCHAR(20) NOT NULL DEFAULT 'ouverte', date_fermeture DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(exercice_id, numero)
        )
    """))

CU = {"societe_id": 1, "id": 1, "role": "admin"}


def _installer_numerotation_test():
    compteurs = {}

    def reserver(db, societe_id, exercice, type_doc, prefixe):
        cle = (societe_id, exercice, type_doc)
        compteurs[cle] = compteurs.get(cle, 0) + 1
        return f"{prefixe}-{exercice}-{compteurs[cle]:04d}"

    factures.reserver_numero = reserver
    factures.reserver_numero_commercial = reserver
    commercial.reserver_numero_commercial = reserver


class Recette:
    def __init__(self):
        self.db = fdb.SessionLocal()
        self.ok = 0
        self.ko = []

    def check(self, libelle, condition, detail=""):
        if condition:
            self.ok += 1
            print(f"[OK] {libelle}")
        else:
            self.ko.append((libelle, detail))
            print(f"[ECHEC] {libelle} {detail}")

    def expect_http(self, libelle, status, fn):
        try:
            fn()
        except HTTPException as exc:
            self.check(libelle, exc.status_code == status,
                       f"status={exc.status_code}, attendu={status}, detail={exc.detail}")
            self.db.rollback()
            return exc
        except Exception as exc:  # pragma: no cover - diagnostic de recette
            self.check(libelle, False, f"exception inattendue: {type(exc).__name__}: {exc}")
            self.db.rollback()
            return None
        self.check(libelle, False, "aucune erreur levée")
        return None

    def setup(self):
        db = self.db
        db.add(models.Societe(
            id=1, raison_sociale="RECETTE FACT5 SARL", ice="001234567000045",
            identifiant_fiscal="12345678", patente="87654321", adresse="1 rue Test", ville="Casablanca",
            prefixe_facture="FA", prefixe_devis="DV", prefixe_bc="BC",
            prefixe_bl="BL", prefixe_avoir="AV", regime_tva="encaissement",
            stock_declencheur_vente="facture", stock_declencheur_achat="facture",
        ))
        db.add(models.ModuleActif(societe_id=1, module="comptabilite", actif=True))
        db.add(models.ExerciceComptable(
            societe_id=1, annee=2026, date_debut=date(2026, 1, 1),
            date_fin=date(2026, 12, 31), statut="ouvert",
        ))
        self.client = models.Tiers(
            societe_id=1, type="client", nom="ALPHA CLIENT SARL", ice="001111111000011",
            categorie_fiscale="professionnel", adresse="10 avenue Client", ville="Casablanca",
            delai_paiement=30, plafond_credit=100000, actif=True,
        )
        self.fournisseur = models.Tiers(
            societe_id=1, type="fournisseur", nom="ATLAS FOURNISSEUR SARL", ice="002222222000022",
            categorie_fiscale="professionnel", adresse="20 avenue Fournisseur", ville="Casablanca",
            delai_paiement=30, plafond_credit=0, actif=True,
        )
        db.add_all([self.client, self.fournisseur])
        fam = models.FamilleArticle(
            societe_id=1, code="MARCH", libelle="Marchandises", tva_defaut=20,
            compte_vente="7111", compte_achat="6111", actif=True,
        )
        db.add(fam); db.flush()
        self.article = models.Article(
            societe_id=1, famille_id=fam.id, code="A-001", designation="Produit test",
            prix_achat_ht=60, prix_vente_ht=100, tva=20, stock_actuel=20,
            stock_min=2, cmup=60, actif=True, is_stockable=True, unite="unité",
        )
        db.add(self.article)
        db.commit()

    def recette_brouillon_stock(self):
        db = self.db
        stock0 = float(self.article.stock_actuel)
        res = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=date(2026, 9, 1), tiers=self.client.nom, tiers_id=self.client.id,
            lignes=[schemas.LigneFactureCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=2, prix_unitaire=100, tva=20,
            )],
        ), CU, db)
        f = db.query(models.Facture).filter_by(id=res["id"]).first()
        db.refresh(self.article)
        self.check("création brouillon: aucun mouvement de stock", self.article.stock_actuel == stock0)

        factures.mettre_a_jour_facture(f.id, schemas.FactureUpdate(lignes=[
            schemas.LigneFactureCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=3, prix_unitaire=100, tva=20,
            )
        ]), CU, db)
        db.refresh(self.article)
        self.check("édition lignes brouillon: stock toujours inchangé", self.article.stock_actuel == stock0)

        factures.supprimer_facture(f.id, CU, db)
        db.refresh(self.article)
        self.check("suppression brouillon: stock inchangé", self.article.stock_actuel == stock0)

    def recette_vente_complete(self):
        db = self.db
        devis = commercial.creer_devis(schemas.DevisCreate(
            numero="DV-2026-0001", date=date(2026, 9, 2), tiers=self.client.nom,
            tiers_id=self.client.id,
            lignes=[schemas.LigneDevisCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=4, prix_unitaire=100, tva=20,
            )],
        ), CU, db)
        commercial.modifier_devis(
            devis["id"], schemas.DevisUpdate(statut="accepte"), CU, db
        )
        bc = commercial.convertir_devis_en_bc(devis["id"], CU, db)
        self.check("Devis → BC avec numéro réservé", bc["numero"].startswith("BC-2026-"))

        ligne_bc = db.query(models.LigneBonCommande).filter_by(bon_commande_id=bc["id"]).first()
        bl = commercial.convertir_bc_en_bl(bc["id"], schemas.ConvertirBLIn(
            date="2026-09-03",
            lignes=[schemas.LigneQuantiteIn(
                ligne_bc_id=ligne_bc.id, description=ligne_bc.description, quantite=2,
            )],
        ), CU, db)
        self.check("livraison partielle de 2/4", len(bl.lignes) == 1 and bl.lignes[0].quantite_livree == 2)
        db.refresh(self.article)
        self.check("BL sans déclencheur logistique: stock inchangé", self.article.stock_actuel == 20)

        ligne_bl = db.query(models.LigneBonLivraison).filter_by(bon_livraison_id=bl.id).first()
        draft = commercial.convertir_bl_en_facture(bl.id, schemas.ConvertirBLFactureIn(
            date=date(2026, 9, 3),
            lignes=[schemas.LigneQuantiteFactureIn(ligne_bl_id=ligne_bl.id, quantite=1)]
        ), CU, db)
        f1 = db.query(models.Facture).filter_by(id=draft["id"]).first()
        self.check("BL → facture crée un brouillon sans numéro", f1.numero is None and not f1.est_validee)
        db.refresh(self.article)
        self.check("facture brouillon issue du BL: stock inchangé", self.article.stock_actuel == 20)

        # Le reliquat d'1 unité du BL peut encore être réservé dans un second brouillon.
        draft2 = commercial.convertir_bl_en_facture(bl.id, schemas.ConvertirBLFactureIn(
            date=date(2026, 9, 3),
            lignes=[schemas.LigneQuantiteFactureIn(ligne_bl_id=ligne_bl.id, quantite=1)]
        ), CU, db)
        f2 = db.query(models.Facture).filter_by(id=draft2["id"]).first()
        self.expect_http("surfacturation du BL bloquée même avec brouillons", 409,
            lambda: commercial.convertir_bl_en_facture(bl.id, schemas.ConvertirBLFactureIn(
                date=date(2026, 9, 3),
                lignes=[schemas.LigneQuantiteFactureIn(ligne_bl_id=ligne_bl.id, quantite=0.5)]
            ), CU, db))

        # On supprime le second brouillon afin de poursuivre la recette sur une facture unique.
        factures.supprimer_facture(f2.id, CU, db)
        factures.valider_facture(f1.id, CU, db)
        db.refresh(f1); db.refresh(self.article)
        self.check("validation attribue un numéro définitif", bool(f1.numero) and f1.est_validee)
        self.check("stock vente décrémenté uniquement à validation", self.article.stock_actuel == 19)

        factures.comptabiliser_facture(f1.id, CU, db)
        db.refresh(f1)
        nb_ecritures = db.query(models.Ecriture).filter_by(
            societe_id=1, reference=f1.numero, journal="VT").count()
        self.check("facture vente comptabilisée une fois", f1.est_comptabilisee and nb_ecritures == 1)
        self.expect_http("double comptabilisation facture bloquée", 409,
                         lambda: factures.comptabiliser_facture(f1.id, CU, db))
        nb_apres = db.query(models.Ecriture).filter_by(
            societe_id=1, reference=f1.numero, journal="VT").count()
        self.check("aucune écriture doublon après seconde tentative", nb_apres == 1)

        _, _, total_ttc, _, _ = factures._calc_totaux(f1)
        r1 = commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=f1.id, date=date(2026, 9, 4), tiers=f1.tiers,
            montant=float(total_ttc) / 2, mode="virement", comptabiliser=True,
        ), CU, db)
        db.refresh(f1)
        self.check("règlement partiel → facture partiellement payée",
                   getattr(f1.statut, "value", f1.statut) == "partiellement_payee")

        situation = factures.reglements_facture(f1.id, CU, db)
        reste = float(situation["solde_restant"])
        self.expect_http("sur-règlement à la création bloqué", 409,
            lambda: commercial.creer_reglement(schemas.ReglementCreate(
                facture_id=f1.id, date=date(2026, 9, 4), tiers=f1.tiers,
                montant=reste + 1, mode="virement", comptabiliser=False,
            ), CU, db))

        commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=f1.id, date=date(2026, 9, 5), tiers=f1.tiers,
            montant=reste, mode="virement", comptabiliser=True,
        ), CU, db)
        db.refresh(f1)
        self.check("règlement exact du reliquat → facture soldée",
                   getattr(f1.statut, "value", f1.statut) == "payee")
        self.expect_http("règlement supplémentaire sur facture soldée bloqué", 409,
            lambda: commercial.creer_reglement(schemas.ReglementCreate(
                facture_id=f1.id, date=date(2026, 9, 5), tiers=f1.tiers,
                montant=1, mode="virement", comptabiliser=False,
            ), CU, db))
        return f1

    def recette_modification_reglement(self):
        db = self.db
        res = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=date(2026, 9, 6), tiers=self.client.nom, tiers_id=self.client.id,
            lignes=[schemas.LigneFactureCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=1, prix_unitaire=100, tva=20,
            )],
        ), CU, db)
        f = db.query(models.Facture).filter_by(id=res["id"]).first()
        factures.valider_facture(f.id, CU, db)
        r1 = commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=f.id, date=date(2026, 9, 6), tiers=f.tiers,
            montant=40, mode="virement", comptabiliser=False,
        ), CU, db)
        commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=f.id, date=date(2026, 9, 6), tiers=f.tiers,
            montant=30, mode="virement", comptabiliser=False,
        ), CU, db)
        self.expect_http("sur-règlement via modification bloqué", 409,
            lambda: commercial.modifier_reglement(
                r1.id, schemas.ReglementUpdate(montant=100), CU, db
            ))

    def recette_achat_complete(self):
        db = self.db
        stock_avant = float(self.article.stock_actuel)
        bc = commercial.creer_bc(schemas.BonCommandeCreate(
            numero="BC-A-2026-0001", type="achat", date=date(2026, 9, 7),
            tiers=self.fournisseur.nom, tiers_id=self.fournisseur.id,
            lignes=[schemas.LigneBCCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=3, prix_unitaire=60, tva=20,
            )],
        ), CU, db)
        br = commercial.convertir_bc_en_bl(bc["id"], schemas.ConvertirBLIn(date="2026-09-07"), CU, db)
        self.check("BC achat → BR", br.type == "achat" and br.numero.startswith("BR-2026-"))
        db.refresh(self.article)
        self.check("BR avec déclencheur facture: stock inchangé", self.article.stock_actuel == stock_avant)

        draft = commercial.convertir_bl_en_facture(br.id, schemas.ConvertirBLFactureIn(date=date(2026, 9, 7)), CU, db)
        f = db.query(models.Facture).filter_by(id=draft["id"]).first()
        self.expect_http("facture fournisseur sans référence refusée à validation", 422,
                         lambda: factures.valider_facture(f.id, CU, db))
        factures.mettre_a_jour_facture(
            f.id, schemas.FactureUpdate(reference="FF-ATLAS-2026-001"), CU, db
        )
        factures.valider_facture(f.id, CU, db)
        db.refresh(f); db.refresh(self.article)
        self.check("validation facture achat augmente le stock",
                   self.article.stock_actuel == stock_avant + 3)
        factures.comptabiliser_facture(f.id, CU, db)
        # COMPTA.5 : pour un achat, la pièce FEC est le numéro fournisseur,
        # pas le numéro interne HisabPro de la facture.
        self.check("écriture achat créée avec référence fournisseur", db.query(models.Ecriture).filter_by(
            societe_id=1, reference=f.reference, journal="AC", source="facture").count() == 1)

        # Le doublon fournisseur est détecté avant même la validation du nouveau brouillon.
        self.expect_http("doublon numéro facture fournisseur bloqué", 409,
            lambda: factures.creer_facture(schemas.FactureCreate(
                type="achat", date=date(2026, 9, 8), tiers=self.fournisseur.nom,
                tiers_id=self.fournisseur.id, reference="FF-ATLAS-2026-001",
                lignes=[schemas.LigneFactureCreate(
                    article_id=self.article.id, description=self.article.designation,
                    quantite=1, prix_unitaire=60, tva=20,
                )],
            ), CU, db))

        situation = factures.reglements_facture(f.id, CU, db)
        commercial.creer_reglement(schemas.ReglementCreate(
            facture_id=f.id, date=date(2026, 9, 8), tiers=f.tiers,
            montant=situation["solde_restant"], mode="virement", comptabiliser=True,
        ), CU, db)
        db.refresh(f)
        self.check("facture fournisseur soldée",
                   getattr(f.statut, "value", f.statut) == "payee")

    def recette_exercice_clos(self):
        db = self.db
        db.add(models.ClotureExercice(societe_id=1, exercice=2025, resultat_net=0))
        db.commit()
        res = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=date(2025, 12, 20), tiers=self.client.nom, tiers_id=self.client.id,
            lignes=[schemas.LigneFactureCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=1, prix_unitaire=100, tva=20,
            )],
        ), CU, db)
        f = db.query(models.Facture).filter_by(id=res["id"]).first()
        self.expect_http("validation facture sur exercice clôturé bloquée", 423,
                         lambda: factures.valider_facture(f.id, CU, db))

    def run(self):
        _installer_numerotation_test()
        self.setup()
        self.recette_brouillon_stock()
        self.recette_vente_complete()
        self.recette_modification_reglement()
        self.recette_achat_complete()
        self.recette_exercice_clos()
        total = self.ok + len(self.ko)
        print("=" * 72)
        print(f"FACT.5 — {self.ok}/{total} contrôles réussis")
        if self.ko:
            for libelle, detail in self.ko:
                print(f" - {libelle}: {detail}")
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(Recette().run())
