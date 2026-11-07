# -*- coding: utf-8 -*-
"""Recette des MODIFICATIONS et SUPPRESSIONS : couvre les 37 endpoints PATCH/PUT/DELETE
que la recette fonctionnelle (creation) ne touchait jamais."""
import sys, types, os
os.environ.setdefault('SECRET_KEY','x'*40); sys.path.insert(0,'.')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
fdb=types.ModuleType('database'); fdb.engine=create_engine('sqlite://')
fdb.SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=fdb.engine)
fdb.Base=declarative_base(); fdb.get_db=lambda:None
sys.modules['database']=fdb
fa=types.ModuleType('auth')
for n in ['get_current_user','requiert_ecriture','requiert_admin']: setattr(fa,n,lambda:{"societe_id":1})
fa.hash_password=lambda p:'h'+p; fa.verify_password=lambda a,b:True; fa.create_access_token=lambda **k:'t'
sys.modules['auth']=fa
import models
fdb.Base.metadata.create_all(fdb.engine)
from routers import (factures, commercial, ecritures, articles as R_art, tiers as R_tiers,
                     banque as R_banque, employes as R_emp, immobilisations as R_immo,
                     utilisateurs as R_users, inventaire, societe as R_soc, rapprochement as R_rap)
import schemas, valorisation, acomptes as R_acpt, avoirs as R_avoir
from datetime import date, timedelta
from fastapi import HTTPException

db=fdb.SessionLocal(); CU={"societe_id":1,"id":1,"role":"admin"}; R=[]

def t(nom, fn, attendu_erreur=False):
    """Execute fn ; verifie qu'elle passe (ou qu'elle leve une erreur si attendu)."""
    try:
        fn()
        ok = not attendu_erreur
        detail = "execute" if ok else "AURAIT DU ETRE REFUSE"
    except HTTPException as e:
        ok = attendu_erreur
        detail = f"refuse ({e.status_code})" if ok else f"HTTP {e.status_code}: {str(e.detail)[:60]}"
    except Exception as e:
        ok = False; detail = f"{type(e).__name__}: {str(e)[:70]}"
    R.append((nom, ok, detail))
    print(f"   [{'OK ' if ok else 'ECHEC'}] {nom} -> {detail}")

# ── Socle ──
db.add(models.Societe(id=1, raison_sociale="T", ice="001", prefixe_facture="FA", prefixe_devis="DV",
    prefixe_bc="BC", prefixe_bl="BL", prefixe_avoir="AV", stock_declencheur_vente="facture",
    stock_declencheur_achat="facture"))
db.add(models.ModuleActif(societe_id=1, module="comptabilite", actif=True))
db.add(models.Utilisateur(id=1, societe_id=1, nom="Admin", email="a@a.ma",
                          hashed_password="h", role="admin", actif=True))
art = models.Article(societe_id=1, code="A1", designation="Produit A", prix_vente_ht=1000,
    prix_achat_ht=600, tva=20, stock_actuel=100, cmup=600, stock_min=5, actif=True, is_stockable=True, unite="u")
db.add(art)
fam = models.FamilleArticle(societe_id=1, code="F1", libelle="Famille 1", tva_defaut=20,
    compte_vente="7111", compte_achat="6111", actif=True)
db.add(fam)
db.add(models.Tiers(societe_id=1, type="client", nom="Client A", delai_paiement=30, plafond_credit=0, actif=True))
db.commit()
print("="*74); print("RECETTE DES MODIFICATIONS ET SUPPRESSIONS"); print("="*74)

print("\n--- Articles et familles ---")
t("PATCH article (prix, designation)",
  lambda: R_art.modifier_article(art.id, schemas.ArticleUpdate(prix_vente_ht=1200,
      description="fiche revue"), CU, db))
t("PATCH ajustement de stock",
  lambda: R_art.ajuster_stock(art.id, {"stock_actuel": 110, "motif": "test"}, CU, db))
t("DELETE famille", lambda: R_art.supprimer_famille(fam.id, CU, db))

print("\n--- Tiers ---")
tr = db.query(models.Tiers).first()
t("PUT tiers", lambda: R_tiers.modifier_tiers(tr.id, R_tiers.TiersUpdate(
    nom="Client A modifie", plafond_credit=25000), CU, db))
t("DELETE tiers", lambda: R_tiers.supprimer_tiers(tr.id, CU, db))

print("\n--- Comptes bancaires ---")
cb = models.CompteBancaire(societe_id=1, banque="BMCE", rib="123", compte_comptable="5141", actif=True)
db.add(cb); db.commit()
t("PATCH compte bancaire", lambda: R_banque.modifier_compte(cb.id,
    schemas.CompteBancaireUpdate(agence="Agence Centre"), CU, db))
t("DELETE compte bancaire", lambda: R_banque.supprimer_compte(cb.id, CU, db))

print("\n--- Employes ---")
emp = models.Employe(societe_id=1, nom="Salarie 1", poste="Comptable", salaire_brut=8000,
                     situation_familiale="celiba", nb_enfants=0, actif=True)
db.add(emp); db.commit()
t("PUT employe", lambda: R_emp.modifier_employe(emp.id,
    schemas.EmployeCreate(nom="Salarie 1", poste="Chef comptable", salaire_brut=12000), CU, db))
t("DELETE employe", lambda: R_emp.supprimer_employe(emp.id, CU, db))

print("\n--- Immobilisations ---")
im = models.Immobilisation(societe_id=1, designation="Ordinateur", date_acquisition=date(2026,1,1),
    valeur_brute=12000, duree_amort=5, methode="lineaire", compte_immo="2340",
    compte_amort="2834", compte_dotation="6193", actif=True)
db.add(im); db.commit()
t("PATCH immobilisation", lambda: R_immo.modifier(im.id,
    schemas.ImmobilisationUpdate(designation="Ordinateur portable", duree_amort=4), CU, db))
t("DELETE immobilisation", lambda: R_immo.supprimer(im.id, CU, db))

print("\n--- Utilisateurs ---")
u2 = R_users.creer(R_users.UtilisateurCreate(nom="Comptable", email="c@c.ma",
    mot_de_passe="motdepasse1", role="comptable"), CU, db)
t("PATCH utilisateur (role)", lambda: R_users.modifier(u2["id"],
    R_users.UtilisateurUpdate(role="lecture"), CU, db))
t("DELETE utilisateur", lambda: R_users.supprimer(u2["id"], CU, db))

print("\n--- Societe et modules ---")
t("PATCH societe", lambda: R_soc.modifier_ma_societe(
    R_soc.SocieteUpdate(ville="Casablanca", prefixe_facture="FAC"), CU, db))

print("\n--- Cycle commercial : devis, BC, BL ---")
dv = models.Devis(societe_id=1, numero="DV-1", date=date(2026,7,1), exercice=2026,
                  tiers="Client A", statut="brouillon")
dv.lignes=[models.LigneDevis(description="Produit A", quantite=2, prix_unitaire=1000, tva=20)]
db.add(dv); db.commit()
t("PATCH devis", lambda: commercial.modifier_devis(dv.id,
    schemas.DevisUpdate(tiers="Client A bis", notes="revu"), CU, db))
t("DELETE devis", lambda: commercial.supprimer_devis(dv.id, CU, db))

bc = models.BonCommande(societe_id=1, numero="BC-1", type="vente", date=date(2026,7,2),
                        exercice=2026, tiers="Client A", statut="en_attente")
bc.lignes=[models.LigneBonCommande(description="Produit A", quantite=3, prix_unitaire=1000)]
db.add(bc); db.commit()
t("PATCH bon de commande", lambda: commercial.modifier_bc(bc.id,
    schemas.BonCommandeUpdate(notes="urgent"), CU, db))

commercial.convertir_bc_en_bl(bc.id, schemas.ConvertirBLIn(date="2026-07-03"), CU, db)
bl = db.query(models.BonLivraison).filter_by(bon_commande_id=bc.id).first()
t("PATCH bon de livraison (statut)", lambda: commercial.modifier_bl(bl.id,
    schemas.BonLivraisonUpdate(transporteur="CTM"), CU, db))
t("DELETE bon de livraison", lambda: commercial.supprimer_bl(bl.id, CU, db))
t("DELETE bon de commande", lambda: commercial.supprimer_bc(bc.id, CU, db))

print("\n--- Factures : modification, garde-fous, suppression ---")
db.refresh(art); stock_avant_fact = art.stock_actuel    # etat AVANT la facture testee
factures.creer_facture(schemas.FactureCreate(numero="FA-M1", type="vente", date=date(2026,7,5),
    tiers="Client A", lignes=[schemas.LigneFactureCreate(description="Produit A",
        quantite=2, prix_unitaire=1000, tva=20)]), CU, db)
f = db.query(models.Facture).filter_by(numero="FA-M1").first()
stock_ref = stock_avant_fact
t("PATCH facture (entete seule)", lambda: factures.mettre_a_jour_facture(f.id,
    schemas.FactureUpdate(tiers="Client A bis", notes="note"), CU, db))
t("PATCH facture (remplacement des lignes)", lambda: factures.mettre_a_jour_facture(f.id,
    schemas.FactureUpdate(lignes=[schemas.LigneFactureCreate(description="Produit A",
        quantite=5, prix_unitaire=1200, tva=20, remise=10)]), CU, db))
db.refresh(f); art2 = db.query(models.Article).first()
ht,_,_,_,_ = factures._calc_totaux(f)
R.append(("Recalcul HT apres modification", abs(ht-5400)<0.05, f"HT={ht:g} (attendu 5400)"))
print(f"   [{'OK ' if abs(ht-5400)<0.05 else 'ECHEC'}] Recalcul HT apres modification -> HT={ht:g} (attendu 5400)")
R.append(("Stock recalcule apres modification", abs(art2.stock_actuel-(stock_ref-5))<0.01,
          f"stock={art2.stock_actuel:g} (attendu {stock_ref-5:g})"))
print(f"   [{'OK ' if abs(art2.stock_actuel-(stock_ref-5))<0.01 else 'ECHEC'}] Stock recalcule -> {art2.stock_actuel:g} (attendu {stock_ref-5:g})")

factures.comptabiliser_facture(f.id, CU, db)
t("PATCH montants d'une facture comptabilisee (doit etre refuse)",
  lambda: factures.mettre_a_jour_facture(f.id, schemas.FactureUpdate(
      lignes=[schemas.LigneFactureCreate(description="Produit A", quantite=99,
          prix_unitaire=1, tva=20)]), CU, db), attendu_erreur=True)
t("DELETE facture comptabilisee (doit etre refuse)",
  lambda: factures.supprimer_facture(f.id, CU, db), attendu_erreur=True)

print("\n--- Reglements ---")
factures.creer_facture(schemas.FactureCreate(numero="FA-M2", type="vente", date=date(2026,7,6),
    tiers="Client A", lignes=[schemas.LigneFactureCreate(description="Produit A",
        quantite=1, prix_unitaire=1000, tva=20)]), CU, db)
f2 = db.query(models.Facture).filter_by(numero="FA-M2").first()
commercial.creer_reglement(schemas.ReglementCreate(facture_id=f2.id, date=date(2026,7,7),
    tiers="Client A", montant=600, mode="virement", comptabiliser=False), CU, db)
rg = db.query(models.Reglement).first()
t("PATCH reglement (montant, mode)", lambda: commercial.modifier_reglement(rg.id,
    schemas.ReglementUpdate(montant=800, mode="cheque", reference="CHQ-1"), CU, db))
t("PATCH reglement vers effet SANS echeance (doit etre refuse)",
  lambda: commercial.modifier_reglement(rg.id, schemas.ReglementUpdate(mode="effet"), CU, db),
  attendu_erreur=True)
t("PATCH reglement vers effet AVEC echeance", lambda: commercial.modifier_reglement(rg.id,
    schemas.ReglementUpdate(mode="effet",
        date_echeance=str(date.today()+timedelta(days=30))), CU, db))
t("DELETE reglement", lambda: commercial.supprimer_reglement(rg.id, CU, db))

print("\n--- Ecritures ---")
ec = ecritures.creer_ecriture(schemas.EcritureCreate(date=date(2026,7,10), journal="OD",
    libelle="Test", reference="T1",
    lignes=[schemas.LigneEcritureCreate(compte="6111", libelle="x", debit=500, credit=0),
            schemas.LigneEcritureCreate(compte="5141", libelle="y", debit=0, credit=500)]), CU, db)
eid = db.query(models.Ecriture).filter_by(reference="T1").first().id
t("PATCH ecriture (libelle, date, lignes)", lambda: ecritures.modifier_ecriture(eid,
    schemas.EcritureUpdate(libelle="Test corrige", date="2026-07-12",
        lignes=[schemas.LigneEcritureCreate(compte="6111", libelle="x", debit=900, credit=0),
                schemas.LigneEcritureCreate(compte="5141", libelle="y", debit=0, credit=900)]), CU, db))
t("PATCH ecriture desequilibree (doit etre refuse)", lambda: ecritures.modifier_ecriture(eid,
    schemas.EcritureUpdate(lignes=[
        schemas.LigneEcritureCreate(compte="6111", libelle="x", debit=100, credit=0),
        schemas.LigneEcritureCreate(compte="5141", libelle="y", debit=0, credit=50)]), CU, db),
  attendu_erreur=True)
t("DELETE ecriture", lambda: ecritures.supprimer_ecriture(eid, CU, db))

print("\n--- Acomptes et avoirs ---")
ac = R_acpt.creer_acompte(R_acpt.AcompteCreate(type="client", tiers="Client A",
    date="2026-07-15", montant=500, mode="virement", comptabiliser=False), CU, db)
acid = db.query(models.Acompte).first().id
t("PATCH acompte", lambda: R_acpt.modifier_acompte(acid, {"montant": 700, "notes": "revu"}, CU, db))
t("DELETE acompte", lambda: R_acpt.supprimer_acompte(acid, CU, db))

av = models.Avoir(societe_id=1, facture_id=f2.id, numero="AV-M1", type="vente",
    date=date(2026,7,16), exercice=2026, tiers="Client A", statut="emis")
av.lignes=[models.LigneAvoir(description="Produit A", quantite=1, prix_unitaire=1000, tva=20)]
db.add(av); db.commit()
t("PATCH avoir", lambda: R_avoir.modifier_avoir(av.id, schemas.AvoirUpdate(motif="Retour"), CU, db))
t("DELETE avoir", lambda: R_avoir.supprimer_avoir(av.id, CU, db))

print("\n" + "="*74)
ok = sum(1 for _,o,_ in R if o)
print(f"TOTAL : {ok}/{len(R)} controles reussis")
ech = [(n,d) for n,o,d in R if not o]
if ech:
    print("\nEchecs :")
    for n,d in ech: print(f"  - {n} : {d}")
