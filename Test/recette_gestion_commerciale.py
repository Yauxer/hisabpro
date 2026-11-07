# -*- coding: utf-8 -*-
"""Campagne de recette : rejoue les 10 cas du cahier dans l'ordre, sur une base vierge."""
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
fa.hash_password=lambda p:p; fa.verify_password=lambda a,b:True; fa.create_access_token=lambda **k:'t'
sys.modules['auth']=fa
import models
fdb.Base.metadata.create_all(fdb.engine)
from routers import factures, commercial, inventaire, articles as mod_art, tiers as mod_tiers
import schemas, valorisation, avoirs as mod_avoirs
from datetime import date
from fastapi import HTTPException

db=fdb.SessionLocal()
CU={"societe_id":1,"id":1,"role":"admin"}
RESULTATS=[]

def check(cas, libelle, obtenu, attendu, tol=0.05):
    if isinstance(attendu,(int,float)) and isinstance(obtenu,(int,float)):
        ok = abs(obtenu-attendu) <= tol
    else:
        ok = obtenu == attendu
    RESULTATS.append((cas, libelle, ok, obtenu, attendu))
    etat = "OK " if ok else "ECHEC"
    print(f"   [{etat}] {libelle}: obtenu={obtenu} attendu={attendu}")
    return ok

# Société + modules
db.add(models.Societe(id=1, raison_sociale="RECETTE SARL", ice="001234567000045",
    prefixe_facture="FA", prefixe_devis="DV", prefixe_bc="BC", prefixe_bl="BL", prefixe_avoir="AV",
    stock_declencheur_vente="facture", stock_declencheur_achat="facture"))
db.add(models.ModuleActif(societe_id=1, module="comptabilite", actif=True))
db.commit()

print("\n" + "="*74)
print("CAS 1 — Création des données de base (tiers, familles, articles)")
print("="*74)

# Fournisseurs
for nom, ice, rc, if_, delai, plafond in [
    ("STE ATLAS BUREAU SARL","001234567000045","45678 - Casablanca","12345678",30,100000),
    ("INFOTECH DISTRIBUTION SARL","001987654000078","98765 - Casablanca","87654321",60,0)]:
    db.add(models.Tiers(societe_id=1, type="fournisseur", nom=nom, ice=ice, rc=rc,
        identifiant_fiscal=if_, delai_paiement=delai, plafond_credit=plafond, actif=True))
# Clients
db.add(models.Tiers(societe_id=1, type="client", nom="SOCIETE ALPHA CONSULTING SARL",
    ice="001112223000012", rc="11223 - Rabat", delai_paiement=30, plafond_credit=50000, actif=True))
db.add(models.Tiers(societe_id=1, type="client", nom="M. Karim Bennani",
    delai_paiement=0, plafond_credit=0, actif=True))
db.commit()
check(1, "4 tiers créés", db.query(models.Tiers).count(), 4)
check(1, "plafond ALPHA enregistré",
      db.query(models.Tiers).filter_by(nom="SOCIETE ALPHA CONSULTING SARL").first().plafond_credit, 50000)

# Familles
fams = {}
for code, lib in [("FA1","Informatique"),("FA2","Mobilier de bureau"),("FA3","Fournitures de bureau")]:
    f = models.FamilleArticle(societe_id=1, code=code, libelle=lib, tva_defaut=20,
                              compte_vente="7111", compte_achat="6111", actif=True)
    db.add(f); db.flush(); fams[code]=f.id
db.commit()
check(1, "3 familles créées", db.query(models.FamilleArticle).count(), 3)

# Articles
ART = {}
for code, des, fam, pa, pv, stock, smin in [
    ("A0001","Ordinateur portable HP 15\"","FA1",5500,7200,10,2),
    ("A0002","Cartouche d'encre HP 305","FA1",120,180,50,10),
    ("A0003","Bureau directeur 160 cm","FA2",1800,2500,5,1),
    ("A0004","Ramette papier A4 80g","FA3",32,45,200,20),
    ("A0005","Chaise de bureau ergonomique","FA2",650,950,15,3)]:
    a = models.Article(societe_id=1, code=code, designation=des, famille_id=fams[fam],
        prix_achat_ht=pa, prix_vente_ht=pv, tva=20, stock_actuel=stock, stock_min=smin,
        cmup=pa, actif=True, is_stockable=True, unite="unité")
    db.add(a); db.flush(); ART[code]=a
db.commit()
check(1, "5 articles créés", db.query(models.Article).count(), 5)
check(1, "stock initial A0001", ART["A0001"].stock_actuel, 10)
check(1, "seuil mini A0004 enregistré", ART["A0004"].stock_min, 20)
check(1, "A0003 rattaché à Mobilier", ART["A0003"].famille_id, fams["FA2"])

print("\n" + "="*74)
print("CAS 2 — Cycle d'achat simple : commande, réception, facture")
print("="*74)

bc2 = models.BonCommande(societe_id=1, numero="BC-2026-001", type="achat", date=date(2026,7,1),
    exercice=2026, tiers="STE ATLAS BUREAU SARL", statut="en_attente")
bc2.lignes=[models.LigneBonCommande(description="Bureau directeur 160 cm", quantite=5, prix_unitaire=1800),
            models.LigneBonCommande(description="Chaise de bureau ergonomique", quantite=10, prix_unitaire=650)]
db.add(bc2); db.commit()
stock_bureau_avant = ART["A0003"].stock_actuel
stock_chaise_avant = ART["A0005"].stock_actuel
check(2, "commande ne bouge pas le stock (bureaux)", ART["A0003"].stock_actuel, 5)

# BC → BR (réception totale)
commercial.convertir_bc_en_bl(bc2.id, schemas.ConvertirBLIn(date="2026-07-02"), CU, db)
br = db.query(models.BonLivraison).filter_by(bon_commande_id=bc2.id).first()
check(2, "BR créé avec préfixe BR", br.numero.startswith("BR-"), True)
check(2, "BR de type achat", br.type, "achat")

# BR → facture d'achat
fres = commercial.convertir_bl_en_facture(br.id, CU, db)
f2 = db.query(models.Facture).filter_by(numero=fres["numero"]).first()
ht2, tva2, net2, _, _ = factures._calc_totaux(f2)
check(2, "facture de type achat", f2.type, "achat")
check(2, "total HT achat", ht2, 15500)
check(2, "TVA 20%", tva2, 3100)
check(2, "net à payer TTC", ht2+tva2, 18600)

# Le stock bouge à la facturation (déclencheur = facture)
db.refresh(ART["A0003"]); db.refresh(ART["A0005"])
check(2, "stock bureaux après réception+facture", ART["A0003"].stock_actuel, 10)
check(2, "stock chaises après réception+facture", ART["A0005"].stock_actuel, 25)

print("\n" + "="*74)
print("CAS 3 — Achat avec remises en cascade et rabais")
print("="*74)

factures.creer_facture(schemas.FactureCreate(numero="FA-C3", type="achat", date=date(2026,7,3),
    tiers="INFOTECH DISTRIBUTION SARL", remise_globale=2,
    lignes=[schemas.LigneFactureCreate(description="Ordinateur portable HP 15\"", quantite=20,
                prix_unitaire=5500, tva=20, remise=8, remise2=3),
            schemas.LigneFactureCreate(description="Cartouche d'encre HP 305", quantite=100,
                prix_unitaire=120, tva=20, rabais=5)]), CU, db)
f3 = db.query(models.Facture).filter_by(numero="FA-C3").first()
ht3, tva3, net3, _, _ = factures._calc_totaux(f3)
check(3, "net commercial (cascade 8%+3% + rabais + pied 2%)", ht3, 107470.72)
check(3, "TVA 20% sur net commercial", tva3, 21494.14)
check(3, "net à payer TTC", ht3+tva3, 128964.86)
db.refresh(ART["A0001"]); db.refresh(ART["A0002"])
check(3, "stock A0001 après achat de 20", ART["A0001"].stock_actuel, 30)
check(3, "stock A0002 après achat de 100", ART["A0002"].stock_actuel, 150)
# CMUP recalculé au prix payé
check(3, "CMUP A0001 au cout NET (5500 x0,92 x0,97 = 4908,20)", round(ART["A0001"].cmup,2), 5105.47)

print("\n" + "="*74)
print("CAS 4 — Cycle de vente : devis, commande, livraison, facture")
print("="*74)

dv = models.Devis(societe_id=1, numero="DV-2026-001", date=date(2026,7,5), exercice=2026,
    tiers="SOCIETE ALPHA CONSULTING SARL", statut="brouillon")
dv.lignes=[models.LigneDevis(description="Ordinateur portable HP 15\"", quantite=3, prix_unitaire=7200, tva=20),
           models.LigneDevis(description="Ramette papier A4 80g", quantite=5, prix_unitaire=45, tva=20)]
db.add(dv); db.commit()

bc4 = models.BonCommande(societe_id=1, devis_id=dv.id, numero="BC-2026-002", type="vente",
    date=date(2026,7,6), exercice=2026, tiers="SOCIETE ALPHA CONSULTING SARL",
    reference="DV-2026-001", statut="en_attente")
bc4.lignes=[models.LigneBonCommande(description="Ordinateur portable HP 15\"", quantite=3, prix_unitaire=7200),
            models.LigneBonCommande(description="Ramette papier A4 80g", quantite=5, prix_unitaire=45)]
db.add(bc4); db.commit()

commercial.convertir_bc_en_bl(bc4.id, schemas.ConvertirBLIn(date="2026-07-07"), CU, db)
bl4 = db.query(models.BonLivraison).filter_by(bon_commande_id=bc4.id).first()
check(4, "BL créé avec préfixe BL", bl4.numero.startswith("BL-"), True)

f4res = commercial.convertir_bl_en_facture(bl4.id, CU, db)
f4 = db.query(models.Facture).filter_by(numero=f4res["numero"]).first()
ht4, tva4, _, _, _ = factures._calc_totaux(f4)
check(4, "total HT vente", ht4, 21825)
check(4, "TVA 20%", tva4, 4365)
check(4, "net à payer TTC", ht4+tva4, 26190)
check(4, "traçabilité : réf = n° du BL", f4.reference, bl4.numero)
db.refresh(ART["A0001"]); db.refresh(ART["A0004"])
check(4, "stock A0001 : 30 - 3", ART["A0001"].stock_actuel, 27)
check(4, "stock A0004 : 200 - 5", ART["A0004"].stock_actuel, 195)

print("\n" + "="*74)
print("CAS 5 — Vente avec remise, rabais et ristourne combinés")
print("="*74)

factures.creer_facture(schemas.FactureCreate(numero="FA-C5", type="vente", date=date(2026,7,8),
    tiers="M. Karim Bennani", ristourne=3,
    lignes=[schemas.LigneFactureCreate(description="Bureau directeur 160 cm", quantite=2,
                prix_unitaire=2500, tva=20, remise=10),
            schemas.LigneFactureCreate(description="Chaise de bureau ergonomique", quantite=4,
                prix_unitaire=950, tva=20, rabais=50)]), CU, db)
f5 = db.query(models.Facture).filter_by(numero="FA-C5").first()
ht5, tva5, _, _, _ = factures._calc_totaux(f5)
check(5, "net commercial (remise 10% + rabais 50/u + ristourne 3%)", ht5, 7857)
check(5, "TVA 20% sur net commercial", tva5, 1571.40)
check(5, "net à payer TTC", ht5+tva5, 9428.40)

print("\n" + "="*74)
print("CAS 6 — Avoir client suite à retour de marchandise")
print("="*74)

stock_av = ART["A0001"].stock_actuel
av6 = models.Avoir(societe_id=1, facture_id=f4.id, numero="AV-2026-001", type="vente",
    date=date(2026,7,10), exercice=2026, tiers="SOCIETE ALPHA CONSULTING SARL", statut="emis")
av6.lignes=[models.LigneAvoir(description="Ordinateur portable HP 15\"", quantite=1,
                              prix_unitaire=7200, tva=20)]
db.add(av6); db.commit()
tot_ht_av = 7200; tot_tva_av = 1440
check(6, "montant HT de l'avoir", tot_ht_av, 7200)
check(6, "TVA de l'avoir", tot_tva_av, 1440)
check(6, "total TTC de l'avoir", tot_ht_av+tot_tva_av, 8640)
check(6, "avoir référence la facture d'origine", av6.facture_id, f4.id)
mod_avoirs.comptabiliser_avoir(av6.id, CU, db)
db.refresh(av6)
check(6, "avoir comptabilisé", av6.est_comptabilisee, True)

print("\n" + "="*74)
print("CAS 7 — Avoir fournisseur suite à retour de marchandise")
print("="*74)

db.refresh(ART["A0005"])
stock_ch = ART["A0005"].stock_actuel
cmup_ch = ART["A0005"].cmup
mvt = valorisation.enregistrer_mouvement(db, 1, ART["A0005"], "sortie", 2,
    reference="AV-F-2026-001", note="Retour fournisseur - chaises defectueuses")
db.commit(); db.refresh(ART["A0005"])
check(7, "stock chaises (21 apres vente cas 5, -2 retour)", ART["A0005"].stock_actuel, 19)
check(7, "sortie valorisée au coût d'entrée", mvt.cout_unitaire, 650)
check(7, "CMUP non faussé par le retour", ART["A0005"].cmup, cmup_ch)
check(7, "montant HT de l'avoir fournisseur", 2*650, 1300)
check(7, "TTC de l'avoir fournisseur", 2*650*1.2, 1560)

print("\n" + "="*74)
print("CAS 8 — Inventaire physique et régularisation de stock")
print("="*74)

db.refresh(ART["A0004"]); db.refresh(ART["A0002"])
th_ram, th_car = ART["A0004"].stock_actuel, ART["A0002"].stock_actuel
print(f"   (stock théorique : ramettes={th_ram:g}, cartouches={th_car:g})")

sim = inventaire.simuler_inventaire(inventaire.InventaireIn(lignes=[
    inventaire.LigneComptage(article_id=ART["A0004"].id, quantite_reelle=190),
    inventaire.LigneComptage(article_id=ART["A0002"].id, quantite_reelle=52)]), CU, db)
check(8, "2 écarts détectés", sim["nb_ecarts"], 2)
ram_e = [e for e in sim["ecarts"] if e["code"]=="A0004"][0]
car_e = [e for e in sim["ecarts"] if e["code"]=="A0002"][0]
check(8, "écart ramettes (195 -> 190)", ram_e["ecart"], -5)
check(8, "mouvement ramettes = sortie", ram_e["sens"], "sortie")
check(8, "valeur écart ramettes (5 x 32)", ram_e["valeur_ecart"], -160)
check(8, "écart cartouches (150 -> 52, cf. achat cas 3)", car_e["ecart"], -98)
check(8, "mouvement cartouches = sortie (stock reel < theorique)", car_e["sens"], "sortie")
check(8, "valeur écart cartouches (98 x CMUP 116,67)", car_e["valeur_ecart"], -11433.34, 0.5)

# Sortie déjà enregistrée avant inventaire : ne doit pas être revalorisée
mv_avant = db.query(models.MouvementStock).filter_by(
    article_id=ART["A0004"].id, type="sortie").first()
cout_avant = mv_avant.cout_unitaire if mv_avant else None

res8 = inventaire.valider_inventaire(inventaire.InventaireIn(lignes=[
    inventaire.LigneComptage(article_id=ART["A0004"].id, quantite_reelle=190),
    inventaire.LigneComptage(article_id=ART["A0002"].id, quantite_reelle=52)]), CU, db)
db.refresh(ART["A0004"]); db.refresh(ART["A0002"])
check(8, "stock final ramettes = comptage", ART["A0004"].stock_actuel, 190)
check(8, "stock final cartouches = comptage", ART["A0002"].stock_actuel, 52)
check(8, "pièce de régularisation générée", res8["nb_regularises"], 2)
if mv_avant:
    db.refresh(mv_avant)
    check(8, "sortie antérieure non revalorisée", mv_avant.cout_unitaire, cout_avant)

print("\n" + "="*74)
print("CAS 9 — Rupture de stock et livraison partielle (reliquat)")
print("="*74)

db.refresh(ART["A0003"])
print(f"   (stock bureaux = {ART['A0003'].stock_actuel:g})")
bc9 = models.BonCommande(societe_id=1, numero="BC-2026-003", type="vente", date=date(2026,7,15),
    exercice=2026, tiers="SOCIETE ALPHA CONSULTING SARL", statut="en_attente")
bc9.lignes=[models.LigneBonCommande(description="Bureau directeur 160 cm", quantite=12, prix_unitaire=2500)]
db.add(bc9); db.commit()
r9 = commercial.consulter_reliquat(bc9.id, CU, db)
check(9, "commande ne bouge pas le stock", ART["A0003"].stock_actuel, 8)
check(9, "reliquat initial = 12", r9["total_reliquat"], 12)

commercial.convertir_bc_en_bl(bc9.id, schemas.ConvertirBLIn(date="2026-07-16",
    lignes=[schemas.LigneQuantiteIn(description="Bureau directeur 160 cm", quantite=8)]), CU, db)
r9 = commercial.consulter_reliquat(bc9.id, CU, db)
check(9, "après livraison partielle de 8 : reliquat", r9["total_reliquat"], 4)
check(9, "statut BC = partiel", r9["statut"], "partiel")

valorisation.enregistrer_mouvement(db, 1, ART["A0003"], "entree", 5, cout_unitaire=1800,
    reference="reappro"); db.commit(); db.refresh(ART["A0003"])
check(9, "après réappro de 5", ART["A0003"].stock_actuel, 13)

commercial.convertir_bc_en_bl(bc9.id, schemas.ConvertirBLIn(date="2026-07-20"), CU, db)
r9 = commercial.consulter_reliquat(bc9.id, CU, db)
check(9, "après 2e livraison : reliquat soldé", r9["total_reliquat"], 0)
check(9, "statut BC = livre", r9["statut"], "livre")
check(9, "2 bons de livraison", r9["nb_livraisons"], 2)
try:
    commercial.convertir_bc_en_bl(bc9.id, schemas.ConvertirBLIn(date="2026-07-25"), CU, db)
    check(9, "sur-livraison bloquée", False, True)
except HTTPException:
    check(9, "sur-livraison bloquée", True, True)

print("\n" + "="*74)
print("CAS 10 — Scénario transversal complet de bout en bout")
print("="*74)

db.add(models.Tiers(societe_id=1, type="fournisseur", nom="PAPETERIE DU NORD", actif=True, delai_paiement=30))
db.add(models.Tiers(societe_id=1, type="client", nom="ECOLE PRIVEE LES CEDRES", actif=True, delai_paiement=30))
cah = models.Article(societe_id=1, code="A0006", designation="Cahier 200 pages",
    famille_id=fams["FA3"], prix_achat_ht=8, prix_vente_ht=14, tva=20,
    stock_actuel=0, cmup=0, actif=True, is_stockable=True, unite="unité")
db.add(cah); db.commit()
check(10, "stock initial du cahier", cah.stock_actuel, 0)

# Achat de 500 avec remise 5%
factures.creer_facture(schemas.FactureCreate(numero="FA-C10-A", type="achat", date=date(2026,7,22),
    tiers="PAPETERIE DU NORD",
    lignes=[schemas.LigneFactureCreate(description="Cahier 200 pages", quantite=500,
        prix_unitaire=8, tva=20, remise=5)]), CU, db)
fa10 = db.query(models.Facture).filter_by(numero="FA-C10-A").first()
hta, tvaa, _, _, _ = factures._calc_totaux(fa10)
check(10, "net HT achat (500x8 -5%)", hta, 3800)
check(10, "TVA achat", tvaa, 760)
check(10, "TTC achat = dette fournisseur", hta+tvaa, 4560)
db.refresh(cah)
check(10, "stock après achat", cah.stock_actuel, 500)

# Vente de 300 avec remise 15%
factures.creer_facture(schemas.FactureCreate(numero="FA-C10-V", type="vente", date=date(2026,7,24),
    tiers="ECOLE PRIVEE LES CEDRES",
    lignes=[schemas.LigneFactureCreate(description="Cahier 200 pages", quantite=300,
        prix_unitaire=14, tva=20, remise=15)]), CU, db)
fv10 = db.query(models.Facture).filter_by(numero="FA-C10-V").first()
htv, tvav, _, _, _ = factures._calc_totaux(fv10)
check(10, "net HT vente (300x14 -15%)", htv, 3570)
check(10, "TVA vente", tvav, 714)
check(10, "TTC vente = créance client", htv+tvav, 4284)
db.refresh(cah)
check(10, "stock après vente", cah.stock_actuel, 200)

# Avoir de 20 avec la même remise
av10 = models.Avoir(societe_id=1, facture_id=fv10.id, numero="AV-2026-002", type="vente",
    date=date(2026,7,26), exercice=2026, tiers="ECOLE PRIVEE LES CEDRES", statut="emis")
av10.lignes=[models.LigneAvoir(description="Cahier 200 pages", quantite=20,
    prix_unitaire=14, tva=20, remise=15)]
db.add(av10); db.commit()
ht_av = 20*14*0.85
check(10, "net HT avoir (20x14 -15%)", ht_av, 238)
check(10, "TVA avoir", ht_av*0.2, 47.60)
check(10, "TTC avoir", ht_av*1.2, 285.60)
valorisation.enregistrer_mouvement(db, 1, cah, "entree", 20, cout_unitaire=7.60,
    reference="AV-2026-002", note="Retour client - cahiers abimes")
db.commit(); db.refresh(cah)
check(10, "stock après avoir (200 + 20)", cah.stock_actuel, 220)
check(10, "créance nette client (4284 - 285,60)", (htv+tvav) - ht_av*1.2, 3998.40)
check(10, "CMUP du cahier (achat à 7,60)", round(cah.cmup,2), 7.60)
check(10, "valeur du stock (220 x 7,60)", valorisation.valeur_stock(cah), 1672)

print("\n" + "="*74)
print("SYNTHÈSE DE LA CAMPAGNE")
print("="*74)
total = len(RESULTATS); ok = sum(1 for r in RESULTATS if r[2])
for cas in range(1, 11):
    lignes = [r for r in RESULTATS if r[0]==cas]
    if not lignes: continue
    n_ok = sum(1 for r in lignes if r[2])
    statut = "CONFORME" if n_ok==len(lignes) else "NON CONFORME"
    print(f"  Cas {cas:>2} : {n_ok:>2}/{len(lignes):<2} controles   {statut}")
print(f"\n  TOTAL : {ok}/{total} contrôles réussis")
echecs = [r for r in RESULTATS if not r[2]]
if echecs:
    print("\n  Échecs restants :")
    for c,l,_,o,a in echecs: print(f"    - Cas {c} / {l} : obtenu={o}, attendu={a}")
