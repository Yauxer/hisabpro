"""Cahier humain633/635 et oracle indépendant en centimes ; aucune connexion DB."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.sax.saxutils import escape
import importlib.util,json,re
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from openpyxl.workbook.properties import CalcProperties
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image
from generer_annexe_reprises619 import CHAMPS,argent

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/recette'
NOM='ANNEXE_RECETTE_SOCIETES_LIEES_20261019';JSON_NOM='donnees_recette_societes_liees_20261019.json'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
DOMAINES=['Préparation','Facturation liée','Règlements et lettrage','Contrôles','Négatifs','Technique']


def lisible(texte):
    mots='capital|social|pièce|pièces|ligne|lignes|compte|comptes|débit|crédit|banque|résultat|bilan|prorata|TVA|TTC|HT|prix|délai|exercice|Exercices|déduction|correspondantes|liées|Annexe|Virement|registre|quatorze|auxiliaires|facture|saisir|sélectionner|date|acheteur|vendeur|fournisseur|client'
    texte=re.sub(r'\b('+mots+r')(?=\d)',r'\1 ',texte,flags=re.I)
    texte=re.sub(r'(\d)(MAD|jours|pièces|lignes)\b',r'\1 \2',texte)
    texte=re.sub(r'\b(chez|dans|vers|de|à|avec|société|facture|encaissement|règlement|acheteur|vendeur|fournisseur|client)([AB])\b',r'\1 \2',texte)
    texte=re.sub(r'\b([AB])(?=\d)',r'\1 ',texte)
    return texte.replace('A→B','A → B').replace('àREC639','à REC639').replace('versREC639','vers REC639').replace('àRIF-','à RIF-').replace('référenceVIR-','référence VIR-').replace('codeAAA','code AAA').replace('casGRP-','cas GRP-')


def oracle():
    pieces=[]
    def piece(s,ref,d,j,ls):
        assert sum(x[1] for x in ls)==sum(x[2] for x in ls)
        pieces.append({'societe':s,'reference':ref,'date':d,'journal':j,'lignes':[{'compte':c,'debit_cents':dr,'credit_cents':cr} for c,dr,cr in ls]})
    ht=2*10000+3*10000;tva=ht*20//100;ttc=ht+tva;capital=1000000
    for s in ('A','B'):piece(s,'CAP-'+s+'-639','2026-01-02','BQ',[('5141',capital,0),('1111',0,capital)])
    piece('A','ATLAS-2026-001','2026-10-19','VT',[('3421',ttc,0),('71243',0,ht),('4455',0,tva)])
    piece('B','ATLAS-2026-001','2026-10-19','AC',[('6111',ht,0),('34552',tva,0),('4411',0,ttc)])
    piece('A','VIR-A-639','2026-10-19','BQ',[('5141',ttc,0),('3421',0,ttc)])
    piece('B','VIR-B-639','2026-10-19','BQ',[('4411',ttc,0),('5141',0,ttc)])
    result={}
    for s in ('A','B'):
        ps=[p for p in pieces if p['societe']==s];soldes={}
        for p in ps:
            for l in p['lignes']:soldes[l['compte']]=soldes.get(l['compte'],0)+l['debit_cents']-l['credit_cents']
        resultat=ht if s=='A' else -ht
        actif=capital+ttc if s=='A' else capital-ttc+tva
        passif=capital+resultat+(tva if s=='A' else 0)
        assert actif==passif and sum(soldes.values())==0
        result[s]={'pieces':len(ps),'lignes':sum(len(p['lignes']) for p in ps),
            'debit':argent(sum(l['debit_cents'] for p in ps for l in p['lignes'])),
            'credit':argent(sum(l['credit_cents'] for p in ps for l in p['lignes'])),
            'soldes_cents':soldes,'banque':argent(soldes['5141']),'resultat_avant_impot':argent(resultat),
            'actif':argent(actif),'passif':argent(passif),'solde_tiers':'0.00'}
    return {'ht':argent(ht),'tva':argent(tva),'ttc':argent(ttc),'pieces':pieces,'societes':result,
        'variation_prix_101':{'ht':'502.00','tva':'100.40','ttc':'602.40'}}


def jeu():
    return {'version':'639-20261019','perimetre':'Annexe sociétés liées633/635 ; ne remplace pas le cahier annuel général.',
        'administrateur':{'email':'groupe639@example.com','mot_de_passe':'RecetteGroupe639!'},
        'lecteur':{'email':'lecteur639@example.com','mot_de_passe':'RecetteLecture639!'},
        'societes':{'A':{'nom':'ATLAS SERVICES RECETTE639 SARL','prefixe':'ATLAS'},'B':{'nom':'RIF CONSEIL RECETTE639 SARL','prefixe':'RIF'}},
        'parametres':{'exercice':2026,'debut':'2026-01-01','fin':'2026-12-31','devise':'MAD','forme_juridique':'SARL','regime_fiscal':'is','regime_tva':'encaissement','prorata_laboratoire':'100.00','capital_social':'10000.00','mentions':'ICE/IF/RC laissés vides volontairement dans ce laboratoire ; conserver les avertissements, jamais déposer ces documents.'},
        'tiers':{'client_A':'RIF CONSEIL RECETTE639 SARL','fournisseur_B':'ATLAS SERVICES RECETTE639 SARL','compte_client':'3421','compte_fournisseur':'4411'},
        'articles':{'A':{'code':'REC639-V','designation':'Prestation étude recette639','is_stockable':False,'compte_vente':'71243'},'B':{'code':'REC639-A','designation':'Étude achetée recette639','is_stockable':False,'compte_achat':'6111'}},
        'facture':{'date':'2026-10-19','delai_paiement':60,'date_echeance':'2026-12-18','lignes':[{'description':'Lot A recette639','quantite':2,'prix_unitaire':'100.00','tva':'20.00'},{'description':'Lot B recette639','quantite':3,'prix_unitaire':'100.00','tva':'20.00'}],'nature_tva_achat':'charge','tva_deductible_pct':'100.00','remises':'0','frais':'0','ras':'0'},
        'justification_liaison':'Relation commerciale fictive de recette639 vérifiée dans les deux sociétés.',
        'logo':'images/LOGO_RECETTE_FICTIF.png','oracle':oracle(),
        'limites':[{'id':'LIM-639-01','statut':'Bloqué','objet':'Consolidation fiscale ou qualification réglementaire du groupe','action':'Hors de ce scénario ; nécessite dossier et textes applicables, aucun résultat déduit.'},
                   {'id':'LIM-639-02','statut':'Bloqué','objet':'Synchronisation automatique des règlements/avoirs/livraisons','action':'Non développée ; traiter séparément dans chaque société et conserver les alertes.'}]}


def cas():
    ts=[]
    def t(n,module,obj,pre,donnees,actions,attendu,ecritures='Aucune écriture créée par cette action.',fiscal='Aucune liquidation ou déclaration fiscale dans ce cas.',controles='Vérifier la société active, les montants et l’absence de doublon.',preuve='Capture de l’écran et référence des documents concernés.',observations='Sociétés fictives uniquement ; résultat humain à renseigner.'):
        ts.append(dict(zip([k for k,_ in CHAMPS],[f'GRP-{n:03}',module,obj,pre,donnees,actions,attendu,ecritures,fiscal,controles,'Non testé','','',preuve,'',observations])))
    t(1,'Préparation','Créer les deux sociétés depuis une installation isolée vierge','Technicien : installation102 préparée et sauvegarde de référence ; aucune base réelle.',
      'Admin groupe639@example.com / RecetteGroupe639! ; sociétés A et B : noms exacts dans le jeu de données.',
      'Sur l’inscription, créer A avec cet administrateur. Se connecter. Dans le sélecteur de société, Nouvelle société : créer B. Revenir à A puis vérifier que le sélecteur donne accès aux deux.',
      'Deux sociétés distinctes, administrateur dans chacune, aucune facture ni écriture. Ne pas réutiliser un dossier existant.')
    t(2,'Préparation','Configurer calendriers, préfixes et hypothèses du laboratoire','GRP-001 réussi.',
      '2026 : 01/01→31/12 ; MAD ; SARL ; capital social10000,00 chacune ; IS ; TVA encaissement ; prorata100% ; préfixes ATLAS et RIF ; logo de recette fourni.',
      'Dans chaque société : Paramètres → Fiche société, renseigner les valeurs et Préfixe Factures. Charger le logo fourni et enregistrer. Vérifier Exercices2026 et ses périodes ouvertes. Déclaration TVA : sélectionner2026, conserver Prorata annuel de déduction100% et enregistrer.',
      'Réglages séparés. Le capital social déclaré ne crée pas à lui seul une écriture. Numéros définitifs attribués à la validation.',
      fiscal='20% et100% sont des hypothèses de laboratoire ; ne pas les assimiler à un droit fiscal réel.',
      observations='ICE/IF/RC restent volontairement vides ; conserver les avertissements, ne pas inventer de mentions légales ni déposer ces documents.')
    t(3,'Préparation','Créer les tiers qui représentent chaque société','GRP-002 réussi.',
      'Chez A : client RIF CONSEIL RECETTE639 SARL, compte3421. Chez B : fournisseur ATLAS SERVICES RECETTE639 SARL, compte4411. Délai60jours, tiers actifs.',
      'Dans A, Clients/Fournisseurs : créer le client. Basculer B : créer le fournisseur. Conserver les comptes collectifs et les codes auxiliaires générés. Revenir A.',
      'Deux tiers propres à leurs sociétés ; aucun identifiant technique réutilisé de l’autre côté.')
    t(4,'Préparation','Créer les articles non stockables','GRP-003 réussi.',
      'A : REC639-V, Prestation étude recette639, vente71243. B : REC639-A, Étude achetée recette639, achat6111. Prix100, TVA20%, non stockables.',
      'Articles → Nouvel article dans chaque société : saisir code et désignation, désactiver le caractère stockable ; dans les comptes comptables, sélectionner le compte indiqué. Enregistrer puis relire les fiches.',
      'Les services sont disponibles sans stock initial ; aucune écriture de stock ou acquisition.')
    t(5,'Préparation','Enregistrer les deux apports bancaires','GRP-004 réussi.',
      'A : CAP-A-639 ; B : CAP-B-639 ; date02/01/2026 ; montant10000,00MAD chacune.',
      'Dans chaque société, Journal → Nouvelle écriture : journalBQ, date02/01/2026, référence et libellé Apport fictif de recette639. Saisir débit5141=10000 et crédit1111=10000, enregistrer puis valider.',
      'Une pièce définitive par société, deux lignes, débit=crédit10000 ; banque10000.',
      'Dans chacune : D5141 Banque10000 / C1111 Capital social10000.',preuve='Pièces BQ et balances initiales des deux sociétés.')
    t(6,'Facturation liée','Enregistrer la liaison commerciale explicite','GRP-005 réussi, société activeA.',
      'AcheteurB ; client chezA=RIF CONSEIL RECETTE639 SARL ; fournisseur chezB=ATLAS SERVICES RECETTE639 SARL ; justification du JSON.',
      'Paramètres → Sociétés liées : choisir B, puis les deux tiers. Saisir la justification exacte, cocher la vérification et Enregistrer la liaison. Relire la ligne active.',
      'Liaison active A→B et historique de création ; aucune facture, mouvement ou écriture créée.')
    t(7,'Facturation liée','Créer le brouillon de vente','GRP-006 réussi.',
      'A ; date19/10/2026 ; clientB ; deux lignes articleREC639-V : Lot A recette639, qté2×100 ; Lot B recette639, qté3×100 ; TVA20 ; remises/frais/RAS0 ; délai60jours.',
      'Facturation → Factures → Nouvelle facture de vente. Renseigner le client et les deux lignes ; choisir Enregistrer le brouillon. Vérifier les totaux et l’échéance18/12/2026.',
      'Brouillon sans numéro définitif : HT500,00, TVA100,00, TTC600,00 ; aucun Journal nouveau.')
    t(8,'Facturation liée','Valider et comptabiliser la vente chezA','GRP-007 réussi.',
      'Facture de600,00MAD ; numéro attendu ATLAS-2026-001.',
      'Dans la liste Factures, Valider définitivement le brouillon. Conserver les avertissements de mentions du laboratoire. Générer son écriture comptable, puis au Journal valider ce brouillon. Ouvrir le détail de la vente.',
      'Vente définitive et comptabilisée ; A possède deux pièces, banque10000 et client débiteur600. B ne possède encore que son capital.',
      'A : D3421=600 / C71243=500 / C4455=100 ; auxiliaire du client réel.',
      fiscal='TVA facturée100 dans le Journal ; le régime encaissement ne constitue pas à lui seul une déclaration déposée.')
    t(9,'Facturation liée','Préparer l’achat et vérifier l’aperçu','GRP-008 réussi, détail de la vente dans A.',
      'Liaison A→B ; chaque ligne source versREC639-A ; nature Charge ; pourcentage propre facture100%.',
      'Déplier Correspondance entre sociétés. Choisir B. Associer les deux lignes àREC639-A. Choisir Charge et saisir100. Cliquer Vérifier le brouillon d’achat sans confirmer la création.',
      'Aperçu HT500, TVA100, TTC600, date19/10/2026 et exercice acheteur2026 ; fournisseurA. B reste sans nouvelle pièce ni facture.')
    t(10,'Facturation liée','Créer le brouillon correspondant chezB','GRP-009 réussi, aperçu relu.',
      'Mêmes paramètres ; référence fournisseur ATLAS-2026-001.',
      'Cocher la vérification de la société, articles, montants et TVA ; Créer le brouillon chez l’acheteur. Noter son identifiant et actualiser la correspondance.',
      'Un seul achat lié, non validé et non comptabilisé, aucun numéro interne ; référence ATLAS-2026-001. Aucune écriture créée chezB et aucune modification de la venteA.')
    t(11,'Facturation liée','Valider et comptabiliser l’achat chezB','GRP-010 réussi.',
      'Achat B600,00MAD, numéro interne attendu RIF-2026-001 ; référence fournisseur ATLAS-2026-001.',
      'Fermer le détail, basculer B. Facturation → Factures → filtre Achats : ouvrir et vérifier le brouillon. Valider définitivement, générer son écriture puis la valider au Journal. Relire le panneau de correspondance.',
      'Deux pièces dansB ; achat et écriture propres àB, fournisseur créditeur600, banque10000. Suivi : deux factures comptabilisées, aucun écart documentaire.',
      'B : D6111=500 / D34552=100 / C4411=600 ; auxiliaire du fournisseur réel.',
      fiscal='TVA récupérable100 selon les hypothèses100% du laboratoire ; aucune qualification fiscale réelle ou déclaration validée.')
    t(12,'Règlements et lettrage','Payer le fournisseur chezB sans régler silencieusementA','GRP-011 réussi.',
      'B ; factureRIF-2026-001 ;19/10/2026 ;600,00 ; Virement ; référenceVIR-B-639 ; banque5141.',
      'Sur l’achat, Payer le fournisseur : saisir ces valeurs, choisir la comptabilisation et enregistrer. Valider l’écriture de règlement au Journal. Basculer A et consulter la vente sans y saisir de règlement.',
      'B : facture payée, dette0, banque9400. A : vente encore impayée600 tant que son encaissement n’a pas été saisi.',
      'B : D4411=600 / C5141=600. A : aucune nouvelle écriture.',
      fiscal='Consulter les impacts du règlement dans chaque dossier, sans transférer automatiquement une déclaration TVA.')
    t(13,'Règlements et lettrage','Enregistrer l’encaissement réel dans le dossierA','GRP-012 réussi.',
      'A ; venteATLAS-2026-001 ;19/10/2026 ;600,00 ; Virement ; référenceVIR-A-639 ; banque5141.',
      'Sur la vente, Encaisser le client : saisir ces valeurs, choisir la comptabilisation et enregistrer. Au Journal, valider l’écriture de règlement. Revenir dans chaque liste de factures et vérifier Payée.',
      'A : banque10600, client0. B : banque9400, fournisseur0. Trois pièces définitives par société.',
      'A : D5141=600 / C3421=600. Le règlementB n’est pas créé une seconde fois.')
    t(14,'Règlements et lettrage','Lettrer les deux auxiliaires séparément','GRP-013 réussi, toutes les écritures validées.',
      'A : compte3421 et clientB ; B : compte4411 et fournisseurA ; deux lignes équilibrées dans chaque sélection.',
      'Lettrage dans A : choisir3421, clientB, cocher la ligne facture600 au débit et celle du règlement600 au crédit, Lettrer2lignes. Noter le code généré d’au moins trois lettres. Répéter dans B sur4411 avec les sens opposés.',
      'Deux lettrages propres à leurs sociétés, solde0 chacun. Les lignes définitives gardent les mêmes comptes/montants/références.',
      'Aucune écriture supplémentaire ; lettrage enregistré hors réécriture des lignes définitives.')
    t(15,'Contrôles','Comparer balances, FEC, CPC, bilans et PDF','GRP-014 réussi.',
      'Résultats attendus de la feuille Oracle : A banque10600/résultat+500/bilan10600 ; B banque9400/TVA100/résultat−500/bilan9500 ; D=C11200 dans chaque Journal.',
      'Dans chaque société : exporter le FEC2026, la balance et la facture PDF ; ouvrir Liasse fiscale pour bilan/CPC. Comparer compte par compte à l’oracle et aux14lignes attendues. Relire les références et le logo de chaque PDF. Paramètres → Sociétés liées : déplier Factures de la liaison puis Actualiser les factures liées ; vérifier TTC600, reste0 et encaissé/payé600 dans chacun des deux dossiers.',
      'Trois pièces et sept lignes par société, six pièces/quatorze lignes au total de contrôle. Aucun écart documentaire. PDFA=ATLAS, PDFB=RIF avec référenceATLAS ; aucun logo d’une société tierce.',
      'Voir Journal attendu et soldes indépendants ; ne pas transformer le total de contrôle en consolidation fiscale.',
      fiscal='Résultats avant impôt seulement ; pas d’IS/CM/CSS calculé, pas de déclaration ou archivage définitif.',preuve='FEC/PDF/balances et captures CPC/bilan des deux sociétés.')
    t(16,'Négatifs','Vérifier un compte de consultation seule','GRP-015 réussi ; administrateur prépare un lecteur dansA puis l’invite dansB en lecture.',
      'lecteur639@example.com / RecetteLecture639! ; rôleLecture dans les deux sociétés.',
      'Paramètres → Utilisateurs : créer le lecteur dansA ; dansB, inviter son email avec rôleLecture. Se déconnecter et se connecter comme lecteur. Ouvrir Sociétés liées et les deux détails de facture.',
      'Suivi consultable, aucun formulaire d’association ou de création, aucune commande de retrait ou comptabilisation. Les pièces et soldes du scénario restent identiques.')
    t(17,'Négatifs','Vérifier qu’une vente ne crée pas un second achat','GRP-015 réussi ; se reconnecter administrateur.',
      'VenteATLAS-2026-001 déjà liée àRIF-2026-001.',
      'Dans A, rouvrir le détail de la vente puis Correspondance entre sociétés. Actualiser, fermer et rouvrir le panneau. Vérifier qu’il affiche l’achat existant sans proposer une nouvelle création. DansB, compter les achats correspondants.',
      'Un seul achat ; aucun nouveau numéro, stock ou Journal. Les répétitions réseau avec même clé sont couvertes par les tests techniques635.')
    t(18,'Négatifs','Afficher un écart de brouillon sans modifier une vente définitive','Utiliser deux AUTRES sociétés VAR-A639 et VAR-B639 ; répéterGRP-001→010 avec préfixesVARA/VARB et tiers aux noms correspondants. Ne pas toucher au scénario principal.',
      'Dans le brouillonVAR-B, prix du Lot A=101 au lieu100 ; quantité2 inchangée ; Lot B3×100 ; TVA20%.',
      'Dans VAR-B, modifier le brouillon d’achat et enregistrer. Rouvrir le détail puis Actualiser la correspondance. Basculer VAR-A et relire la vente d’origine.',
      'Achat modifié HT502, TVA100,40, TTC602,40 ; alerte Écarts à vérifier sur les lignes. Vente d’origineHT500/TTC600 intacte ; aucune écriture d’achat générée.',observations='Variante isolée seulement ; aucune facture définitive n’est réécrite pour faire disparaître le contrôle.')
    t(19,'Contrôles','Retirer la liaison en conservant les pièces','Scénario principal GRP-015 terminé, administrateur connectéA.',
      'Liaison A→B ; motif Fin de recette639 — liaison retirée.',
      'Paramètres → Sociétés liées : Retirer la liaison, saisir ce motif, confirmer. Rouvrir les détails des factures et comparer FEC/Journal/balances aux exportsGRP-015.',
      'Liaison retirée avec historique, correspondance conservée, mêmes pièces et montants. Ce retrait ne supprime pas les factures ni les écritures et n’autorise pas une nouvelle copie de la même vente.')
    t(20,'Technique','Vérifier le paquet et le banc d’installation isolé','Technicien, copie de travail isolée ; aucun paramètre de base réelle.',
      'Test/verifier_zip_session.py avec le ZIP cumulatif fourni ; Test/recette_installation_vierge_102.py --rapport .codex-tests/recette639-installation.md.',
      'Vérifier le manifeste embarqué du ZIP sans extraction. Lancer le CLI102 depuis la racine avec le Python du projet ; lire le rapport et vérifier que son cluster temporaire est supprimé. Ne jamais passer une URL de base ni lancer ces SQL sur le dossier réel pour cette recette.',
      'ZIP CRC/SHA/liste valides ;93SQL distincts et29rejeux,80tables, droits limités, cluster supprimé. Ce CLI ne migre pas l’installation active.',preuve='Sortie du vérificateur, rapport d’installation et résultat des tests techniques635/637.',observations='Cas technique distinct des actions métier ; aucune validation humaine globale ou production déduite.')
    for t in ts:
        for k,v in t.items():t[k]=lisible(v)
    return ts


def markdown(d,ts):
    o=d['oracle'];l=[f'# {TITRE}','Version 1 du 19 octobre 2026','Annexe — Sociétés liées et factures correspondantes633/635',
      'Recette utilisateur à effectuer. Tous les cas sont Non testé. Ce complément ne remplace pas le cahier annuel général.',
      'Sociétés, opérations et identifiants de recette fictifs. Aucun dépôt, conformité officielle ou mise en production validé.',
      '## Préparer le jeu de données',
      '| Objet | Société A | Société B | Valeur / consigne |','|---|---|---|---|',
      f'| Société | {d["societes"]["A"]["nom"]} | {d["societes"]["B"]["nom"]} | Dossiers vierges, créés pour la recette uniquement |',
      f'| Administrateur | {d["administrateur"]["email"]} | Même utilisateur, administrateur secondaire | Mot de passe fictif : {d["administrateur"]["mot_de_passe"]} |',
      '| Exercice | 2026 | 2026 | 01/01/2026 au31/12/2026, périodes ouvertes |',
      '| Société / comptabilité | SARL, MAD | SARL, MAD | Capital social10000MAD chacune ; régime fiscal IS |',
      '| Préfixe Factures | ATLAS | RIF | À paramétrer avant la première facture ; numéros attribués à validation |',
      f'| Tiers | Client : {d["tiers"]["client_A"]} | Fournisseur : {d["tiers"]["fournisseur_B"]} | Comptes collectifs3421 et4411 ; codes auxiliaires générés |',
      '| Article | REC639-V : Prestation étude recette639 | REC639-A : Étude achetée recette639 | Services non stockables ; prix100 ; vente71243 / achat6111 |',
      '| TVA de laboratoire | Encaissement, taux20% | Encaissement, achat Charge, déduction100% | Prorata annuel100% ; hypothèses du scénario, pas qualification fiscale |',
      '| Logo | LOGO_RECETTE_FICTIF.png | LOGO_RECETTE_FICTIF.png | Fichier fourni dans docs/recette/images |',
      'Liaison A → B : '+d['justification_liaison'],
      'Facture datée du19/10/2026, délai60jours et échéance18/12/2026. Deux lignes : Lot A recette639 (2×100MAD) et Lot B recette639 (3×100MAD), taux20%, aucune remise, frais ou RAS.',
      'Capitaux le02/01/2026 : CAP-A-639 etCAP-B-639. Deux virements séparés le19/10/2026 : VIR-A-639 etVIR-B-639, chacun600MAD. Lecteur : '+d['lecteur']['email']+' / '+d['lecteur']['mot_de_passe']+'.',
      'ICE/IF/RC laissés vides : conserver les avertissements de mentions incomplètes. Ne jamais inventer des mentions pour obtenir un document utilisable en production.',
      '## Calculs indépendants attendus','Calcul en centimes entiers, sans appel aux services comptables de l’application.',
      'Deux lots :2×100+3×100=500HT ; TVA20%=100 ; TTC600. Capital10000 par société. Aucun stock, remise, frais, RAS ou impôt dans le parcours principal.',
      '| Société | Banque finale MAD | Résultat avant impôt MAD | Actif = passif MAD |','|---|---|---|---|']
    for s,v in o['societes'].items():l.append(f'| {s} | {v["banque"]} | {v["resultat_avant_impot"]} | {v["actif"]} |')
    l+=['Dans chacune :3pièces,7lignes, débit=crédit11200.00MAD. A : TVA facturée100, client0. B : TVA récupérable100, fournisseur0.',
        'Les paiements sont saisis et justifiés séparément dans les deux sociétés ; aucune compensation ou consolidation fiscale présumée. Les variantes utilisent d’autres dossiers.']
    for t in ts:
        l.append('## '+t['id']+' — '+t['objectif'])
        for k,label in CHAMPS:
            if k=='id':continue
            l.append(label+' : '+(t[k] or 'À renseigner par le testeur.'))
    l+=['## Limites non exécutables et décisions','Les deux limites ci-dessous sont séparées des20cas humains ; ne pas les compter comme des tests réussis.']
    for v in d['limites']:l.append(v['id']+' — '+v['statut']+' — '+v['objet']+' : '+v['action'])
    return lisible('\n\n'.join(l)+'\n')


def documents(out,md):
    spec=importlib.util.spec_from_file_location('guide_ooxml639',ROOT/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=md;g.STEM=out/NOM;items=g.blocs();g.docx(items)
    p=out/(NOM+'.docx')
    with ZipFile(p) as z:fs={n:z.read(n) for n in z.namelist()}
    fs['word/header1.xml']=fs['word/header1.xml'].replace('Guide utilisateur — Démonstration et vérification'.encode(),'Recette des sociétés liées — Annexe 633/635'.encode())
    fs['docProps/core.xml']=fs['docProps/core.xml'].replace('HisabPro — Mode d’emploi et vérification des avancées'.encode(),TITRE.encode())
    with ZipFile(p,'w',ZIP_DEFLATED) as z:
        for n,b in fs.items():z.writestr(n,b)
    for n,f in [('Recette639','arial.ttf'),('Recette639Bold','arialbd.ttf')]:
        if n not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
    st={'title':ParagraphStyle('title',fontName='Recette639Bold',fontSize=21,leading=27,spaceAfter=20,textColor=colors.HexColor('#183D35')),
        'h1':ParagraphStyle('h1',fontName='Recette639Bold',fontSize=15,leading=20,spaceAfter=14,keepWithNext=True),
        'h2':ParagraphStyle('h2',fontName='Recette639Bold',fontSize=12,leading=16,spaceAfter=10,keepWithNext=True),
        'body':ParagraphStyle('body',fontName='Recette639',fontSize=10,leading=14,spaceAfter=8),
        'cell':ParagraphStyle('cell',fontName='Recette639',fontSize=9,leading=12)}
    story=[Spacer(1,15)]
    for kind,v in items:
        if kind=='table':
            tb=Table([[Paragraph(escape(c),st['cell']) for c in row] for row in v],colWidths=[65,140,145,150],repeatRows=1)
            tb.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CAD5D0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F1EC'))]));story += [tb,Spacer(1,12)]
        else:
            if kind=='h1':story.append(PageBreak())
            # Préserver la lisibilité des données JSON sur lignes distinctes.
            for ligne in v.splitlines():story.append(Paragraph(escape(ligne),st[kind]))
    def pied(c,d):
        c.setFont('Recette639',8);c.drawString(45,818,'HISABPRO · Sociétés liées · Annexe 633/635')
        c.drawString(45,22,'Sociétés fictives · Recette humaine à effectuer · Page '+str(d.page))
    SimpleDocTemplate(str(out/(NOM+'.pdf')),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=45,bottomMargin=42,title=TITRE,author='HisabPro').build(story,onFirstPage=pied,onLaterPages=pied)


def classeur(out,d,ts):
    w=Workbook();s=w.active;s.title='Synthèse';w.calculation=CalcProperties(fullCalcOnLoad=True)
    s.append([TITRE]);s.append(['Recette utilisateur à effectuer — aucune réussite préremplie']);s.append(['Domaine','Non testé','Réussi','Échoué','Bloqué','Total','Progression'])
    for i,n in enumerate(DOMAINES,4):
        xs=[t for t in ts if t['module']==n];sh=w.create_sheet(n);sh.append([label for _,label in CHAMPS])
        for t in xs:sh.append([t[k] for k,_ in CHAMPS])
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');sh.add_data_validation(dv);dv.add(f'K2:K{len(xs)+1}')
        s.append([n]+[f'=COUNTIF(\'{n}\'!K2:K{len(xs)+1},"{st}")' for st in ('Non testé','Réussi','Échoué','Bloqué')]+[f'=SUM(B{i}:E{i})',f'=IF(F{i}=0,0,C{i}/F{i})'])
    s.append(['TOTAL']+[f'=SUM({c}4:{c}9)' for c in 'BCDEF']+['=IF(F10=0,0,C10/F10)'])
    for row in range(4,11):s.cell(row,7).number_format='0%'
    s.append(['Les limites non exécutables sont séparées ; renseigner résultats réels, anomalies et preuves.'])
    ch=BarChart();ch.title='Progression de la recette';ch.add_data(Reference(s,min_col=2,max_col=5,min_row=3,max_row=9),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=9));s.add_chart(ch,'A14')
    ws=w.create_sheet('Données');ws.append(['Clé','Valeur exacte'])
    def plat(prefix,val):
        if isinstance(val,dict):
            for k,v in val.items():plat(prefix+'.'+k if prefix else k,v)
        elif isinstance(val,list):
            for i,v in enumerate(val):plat(prefix+f'[{i}]',v)
        else:ws.append([prefix,str(val)])
    plat('',{k:v for k,v in d.items() if k not in ('cas','oracle','limites')})
    ws=w.create_sheet('Oracle');ws.append(['Société','Contrôle','Attendu exact'])
    for soc,v in d['oracle']['societes'].items():
        for k,z in v.items():
            if k!='soldes_cents':ws.append([soc,k,z])
    j=w.create_sheet('Journal attendu');j.append(['Société','Référence','Date','Journal','Compte','Débit MAD','Crédit MAD'])
    for p in d['oracle']['pieces']:
        for l in p['lignes']:j.append([p['societe'],p['reference'],p['date'],p['journal'],l['compte'],l['debit_cents']/100,l['credit_cents']/100])
    b=w.create_sheet('Soldes attendus');b.append(['Société','Compte','Solde débiteur MAD','Solde créditeur MAD'])
    for soc,v in d['oracle']['societes'].items():
        for c,z in sorted(v['soldes_cents'].items()):b.append([soc,c,max(z,0)/100,max(-z,0)/100])
    lim=w.create_sheet('Limites');lim.append(['ID','Statut séparé','Objet non exécutable','Action'])
    for l in d['limites']:lim.append([l['id'],l['statut'],l['objet'],l['action']])
    for sh in w:
        sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
        for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='183D35')
        for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=65 if sh.title in DOMAINES else 40
        for row in sh:
            for c in row:
                c.alignment=Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value,str) and not c.value.startswith(('=COUNTIF','=SUM','=IF')):c.data_type='s'
        for r in range(2,sh.max_row+1):sh.row_dimensions[r].height=280 if sh.title in DOMAINES else 65
    for c in 'BCDEFG':s.column_dimensions[c].width=15
    s.column_dimensions['A'].width=32;s.merge_cells('A1:G1');s.merge_cells('A2:G2');s.merge_cells('A11:G11');s.freeze_panes='B4';s.auto_filter.ref='A3:G9';s.row_dimensions[1].height=45
    w.save(out/(NOM+'.xlsx'))


def generer(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);d=jeu();ts=cas();d['cas']=ts
    (out/JSON_NOM).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    md=out/(NOM+'.md');md.write_text(markdown(d,ts),encoding='utf8');documents(out,md);classeur(out,d,ts)
    return d


if __name__=='__main__':
    d=generer();print(NOM,len(d['cas']),'cas humains Non testé ; Word/PDF/Excel et données générés.')
