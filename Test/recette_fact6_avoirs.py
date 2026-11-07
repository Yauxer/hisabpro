# -*- coding: utf-8 -*-
"""FACT.6 — recette avoirs / retours / annulations.

Exécutable sans PostgreSQL : la concurrence SQL reste couverte par les migrations,
les règles métier sont exercées ici sur SQLite.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "Test"
if str(TEST) not in sys.path:
    sys.path.insert(0, str(TEST))

from recette_fact5_e2e import Recette, CU, _installer_numerotation_test  # noqa: E402
import models  # noqa: E402
import schemas  # noqa: E402
from routers import factures  # noqa: E402
import avoirs  # noqa: E402


def _installer_numero_avoir():
    compteur = {"n": 0}
    def reserver(db, societe_id, exercice, type_doc, prefixe):
        compteur["n"] += 1
        return f"{prefixe}-{exercice}-{compteur['n']:04d}"
    avoirs.reserver_numero_commercial = reserver


class RecetteFact6(Recette):
    def expect_http6(self, libelle, status, fn):
        return self.expect_http(libelle, status, fn)

    def _facture_vente_remisee(self):
        res = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=date(2026, 9, 9), tiers=self.client.nom, tiers_id=self.client.id,
            remise_globale=5, ristourne=2, escompte=1,
            lignes=[
                schemas.LigneFactureCreate(
                    article_id=self.article.id, description="Même libellé", quantite=1,
                    prix_unitaire=100, tva=20, remise=10, remise2=5, rabais=2,
                ),
                schemas.LigneFactureCreate(
                    article_id=self.article.id, description="Même libellé", quantite=1,
                    prix_unitaire=100, tva=20, remise=10, remise2=5, rabais=2,
                ),
            ],
        ), CU, self.db)
        f = self.db.query(models.Facture).filter_by(id=res["id"]).first()
        factures.valider_facture(f.id, CU, self.db)
        factures.comptabiliser_facture(f.id, CU, self.db)
        self.db.refresh(f)
        return f

    def recette_lignes_et_tarifs_figes(self):
        db = self.db
        f = self._facture_vente_remisee()
        lignes = sorted(f.lignes, key=lambda x: x.id)
        stock_apres_facture = float(self.article.stock_actuel)
        self.check("facture vente validée: stock sorti", stock_apres_facture == 18)

        av = avoirs.creer_avoir(schemas.AvoirCreate(
            facture_id=f.id, date=date(2026, 9, 9), motif="Retour partiel", retour_stock=True,
            lignes=[schemas.LigneAvoirCreate(
                facture_ligne_id=lignes[0].id, quantite=1,
                # Valeurs volontairement falsifiées : elles doivent être ignorées.
                prix_unitaire=1, tva=0, remise=99,
            )],
        ), CU, db)
        a = db.query(models.Avoir).filter_by(id=av.id if hasattr(av, "id") else av["id"]).first()
        la = a.lignes[0]
        self.check("avoir lié par ID à la ligne source", la.facture_ligne_id == lignes[0].id)
        self.check("prix navigateur ignoré", float(la.prix_unitaire) == 100)
        self.check("TVA navigateur ignorée", float(la.tva) == 20)
        self.check("remises 1/2 et rabais repris de la facture",
                   float(la.remise) == 10 and float(la.remise2) == 5 and float(la.rabais) == 2)

        total_facture = factures._calc_totaux(f)[2]
        total_avoir = avoirs._totaux_avoir(a)[2]
        self.check("avoir d'une ligne identique = moitié exacte du TTC facture",
                   abs(total_avoir * 2 - total_facture) < 0.02,
                   f"avoir={total_avoir}, facture={total_facture}")

        self.expect_http6("sur-avoir d'une même ligne bloqué", 409, lambda: avoirs.creer_avoir(
            schemas.AvoirCreate(
                facture_id=f.id, date=date(2026, 9, 9),
                lignes=[schemas.LigneAvoirCreate(facture_ligne_id=lignes[0].id, quantite=0.01)],
            ), CU, db
        ))

        # Même description mais seconde ligne : autorisée grâce à l'ID technique.
        av2 = avoirs.creer_avoir(schemas.AvoirCreate(
            facture_id=f.id, date=date(2026, 9, 9), motif="Solde avoir",
            lignes=[schemas.LigneAvoirCreate(facture_ligne_id=lignes[1].id, quantite=1)],
        ), CU, db)
        a2 = db.query(models.Avoir).filter_by(id=av2.id if hasattr(av2, "id") else av2["id"]).first()
        self.check("deux lignes homonymes restent distinguées", a2.lignes[0].facture_ligne_id == lignes[1].id)

        listed = factures.lister_factures(
            exercice=2026, type=None, statut=None, recherche=None, skip=0, limit=100,
            current_user=CU, db=db,
        )
        lf = next(x for x in listed if x["id"] == f.id)
        self.check("facture totalement créditée détectée", lf["statut_credit"] == "totalement_creditee")

        # Le stock ne revient qu'à la comptabilisation de l'avoir marqué retour physique.
        db.refresh(self.article)
        self.check("avoir non comptabilisé: stock inchangé", self.article.stock_actuel == 18)
        avoirs.comptabiliser_avoir(a.id, CU, db)
        db.refresh(self.article)
        self.check("retour client comptabilisé: stock réintégré", self.article.stock_actuel == 19)

        e = db.query(models.Ecriture).filter_by(societe_id=1, journal="AV", reference=a.numero).first()
        debit = sum(float(l.debit or 0) for l in e.lignes)
        credit = sum(float(l.credit or 0) for l in e.lignes)
        self.check("écriture avoir équilibrée", abs(debit - credit) < 0.01)

        situation = factures.reglements_facture(f.id, CU, db)
        self.check("avoirs actifs déduits du solde facture", situation["total_avoirs"] > 0)

        # Annulation : écriture inverse + compensation stock + réouverture du reliquat.
        rep = avoirs.annuler_avoir(a.id, date(2026, 9, 9), CU, db)
        db.refresh(a); db.refresh(self.article)
        self.check("avoir comptabilisé annulé avec écriture inverse",
                   getattr(a.statut, "value", a.statut) == "annule" and bool(rep["ecriture_annulation_id"]))
        self.check("annulation retour client restaure le stock", self.article.stock_actuel == 18)
        nb_ann = db.query(models.Ecriture).filter_by(id=rep["ecriture_annulation_id"]).count()
        self.check("une seule écriture d'annulation créée", nb_ann == 1)
        rep2 = avoirs.annuler_avoir(a.id, date(2026, 9, 9), CU, db)
        self.check("annulation répétée idempotente", rep2["ecriture_annulation_id"] == rep["ecriture_annulation_id"])

        listed = factures.lister_factures(
            exercice=2026, type=None, statut=None, recherche=None, skip=0, limit=100,
            current_user=CU, db=db,
        )
        lf = next(x for x in listed if x["id"] == f.id)
        self.check("annulation réouvre le statut crédit partiel", lf["statut_credit"] == "partiellement_creditee")

    def recette_achat_retour_et_tva(self):
        db = self.db
        stock0 = float(self.article.stock_actuel)
        res = factures.creer_facture(schemas.FactureCreate(
            type="achat", date=date(2026, 9, 9), tiers=self.fournisseur.nom,
            tiers_id=self.fournisseur.id, reference="FF-FACT6-001",
            nature_tva_achat="non_deductible", tva_deductible_pct=0,
            lignes=[schemas.LigneFactureCreate(
                article_id=self.article.id, description=self.article.designation,
                quantite=2, prix_unitaire=60, tva=20,
            )],
        ), CU, db)
        f = db.query(models.Facture).filter_by(id=res["id"]).first()
        factures.valider_facture(f.id, CU, db)
        factures.comptabiliser_facture(f.id, CU, db)
        db.refresh(self.article)
        self.check("facture achat: entrée stock", self.article.stock_actuel == stock0 + 2)

        ligne = f.lignes[0]
        av = avoirs.creer_avoir(schemas.AvoirCreate(
            facture_id=f.id, date=date(2026, 9, 9), motif="Retour fournisseur",
            retour_stock=True,
            lignes=[schemas.LigneAvoirCreate(facture_ligne_id=ligne.id, quantite=1)],
        ), CU, db)
        a = db.query(models.Avoir).filter_by(id=av.id if hasattr(av, "id") else av["id"]).first()
        avoirs.comptabiliser_avoir(a.id, CU, db)
        db.refresh(self.article)
        self.check("retour fournisseur: sortie stock", self.article.stock_actuel == stock0 + 1)

        e = db.query(models.Ecriture).filter_by(journal="AV", reference=a.numero).first()
        comptes = [(l.compte, float(l.debit or 0), float(l.credit or 0)) for l in e.lignes]
        self.check("TVA non déductible n'est pas recréditée en 34552",
                   not any(c == "34552" and cr > 0 for c, d, cr in comptes))
        self.check("TVA non déductible reprise dans le compte d'achat",
                   sum(cr for c, d, cr in comptes if c == "6111") > avoirs._totaux_avoir(a)[0])

    def recette_garde_fous(self):
        db = self.db
        # Avoir sur facture validée mais non comptabilisée : création possible,
        # comptabilisation de l'avoir interdite tant que la source n'est pas en compta.
        res = factures.creer_facture(schemas.FactureCreate(
            type="vente", date=date(2026, 9, 9), tiers=self.client.nom, tiers_id=self.client.id,
            lignes=[schemas.LigneFactureCreate(
                article_id=self.article.id, description="Garde-fou", quantite=1,
                prix_unitaire=50, tva=20,
            )],
        ), CU, db)
        f = db.query(models.Facture).filter_by(id=res["id"]).first()
        factures.valider_facture(f.id, CU, db)
        av = avoirs.creer_avoir(schemas.AvoirCreate(
            facture_id=f.id, date=date(2026, 9, 9),
            lignes=[schemas.LigneAvoirCreate(facture_ligne_id=f.lignes[0].id, quantite=1)],
        ), CU, db)
        aid = av.id if hasattr(av, "id") else av["id"]
        self.expect_http6("avoir non comptabilisé tant que facture source non comptabilisée", 409,
                          lambda: avoirs.comptabiliser_avoir(aid, CU, db))
        self.expect_http6("PATCH annule interdit au profit de l'action dédiée", 409,
                          lambda: avoirs.modifier_avoir(aid, schemas.AvoirUpdate(statut="annule"), CU, db))

    def run(self):
        _installer_numerotation_test()
        _installer_numero_avoir()
        self.setup()
        self.recette_lignes_et_tarifs_figes()
        self.recette_achat_retour_et_tva()
        self.recette_garde_fous()
        total = self.ok + len(self.ko)
        print("=" * 72)
        print(f"FACT.6 — {self.ok}/{total} contrôles réussis")
        if self.ko:
            for libelle, detail in self.ko:
                print(f" - {libelle}: {detail}")
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(RecetteFact6().run())
