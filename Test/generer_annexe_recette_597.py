"""Annexe humaine593/595 : oracle en centimes indépendant du code métier."""
from pathlib import Path
import json
import math
import re
import shutil
from xml.sax.saxutils import escape
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table

ROOT=Path(__file__).resolve().parents[1]
NOM='ANNEXE_RECETTE_RAS_TVA_CCA_PCA_20261019'
JSON_NOM='donnees_recette_593_595_20261019.json'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
COLONNES=[('id','ID'),('ordre','Ordre'),('module','Module'),('objectif','Objectif'),('prerequis','Prérequis'),
 ('donnees','Données exactes'),('actions','Actions dans l’interface'),('attendu','Résultat attendu'),
 ('ecritures','Écritures attendues'),('fiscal','Impacts fiscaux'),('controles','Contrôles'),('statut','Statut humain'),
 ('reel','Résultat réel'),('anomalies','Anomalies'),('preuve_attendue','Preuve attendue'),('preuves','Preuves réelles'),
 ('observations','Observations'),('auto','Couverture technique')]


def argent(cents):
    signe='-' if cents<0 else '';q,r=divmod(abs(cents),100)
    return f'{signe}{q}.{r:02d}'


def oracle():
    # Calcul en entiers, sans Decimal ni import des services de l'application.
    q,r=divmod(1200000*90,182);report=q+int(2*r>=182)
    qd,rd=divmod(1200000*92,183);decale=qd+int(2*rd>=183)
    return {'quote_ttc':'6000.00','quote_tva':'1000.00','ras':'750.00','cash':'5250.00',
        'registre_avant_r4':{'saisies':'2250.00','actives':'1500.00','validees_avant_r3':'750.00','annulees':'750.00'},
        'registre_apres_r4':{'saisies':'3000.00','actives':'2250.00','validees':'2250.00','annulees':'750.00'},
        'soldes_tva_finaux':{'5141':'84250.00','3421':'12000.00','34552':'4000.00','4411':'-6000.00',
            '4457':'-2250.00','4455':'-2000.00','1111':'-100000.00','6133':'20000.00','7124':'-10000.00'},
        'journal_tva':{'ecritures':14,'lignes':31,'debit':'166000.00','credit':'166000.00'},
        'prorata':{'base':'12000.00','jours':182,'jours_futurs':90,'reporte':argent(report),'non_reporte':argent(1200000-report)},
        'cca':{'resultat_2025':'-6065.93','actif':'13934.07','passif':'13934.07'},
        'pca':{'resultat_2025':'6065.93','actif':'32000.00','passif':'32000.00'},
        'cloture_civile':{'cm_profil_laboratoire':'3000.00','resultat_cca':'-9065.93','resultat_pca':'3065.93','an_cca':'23000.00','an_pca':'32000.00'},
        'decale':{'jours':183,'jours_futurs':92,'reporte':argent(decale),'non_reporte':argent(1200000-decale),
            'resultat_cca_apres_cm':argent(-(1200000-decale)-300000),'resultat_pca_apres_cm':argent(1200000-decale-300000),
            'date_an_cp':'2025-07-01','exercice_an_cp':2026}}


def jeu():
    return {'publication':'2026-10-19','environnement':'Base de recette isolée uniquement, jamais une société réelle.',
        'statut':'Recette humaine à effectuer ; aucune fiche prévalidée.',
        'societes':{
            'S1':{'nom':'RECETTE TVA593','devise':'MAD','forme':'SARL','regime_tva':'encaissement','exercice':'2026-01-01 au 2026-12-31',
                'identifiants_fiscaux':'Laisser vides ; aucune utilisation pour un dépôt.','logo':'images/LOGO_RECETTE_FICTIF.png'},
            'S2':{'nom':'RECETTE CCA595','devise':'MAD','exercice':'2025-01-01 au 2025-12-31 ; calendrier2026 civil présent'},
            'S3':{'nom':'RECETTE PCA595','devise':'MAD','exercice':'2025-01-01 au 2025-12-31 ; calendrier2026 civil présent'},
            'S4':{'nom':'RECETTE CCA605 DECALEE','devise':'MAD','exercice':'2025 :2024-07-01 au2025-06-30 ;2026 :2025-07-01 au2026-06-30'},
            'S5':{'nom':'RECETTE PCA605 DECALEE','devise':'MAD','exercice':'Mêmes calendriers que S4, société indépendante'},
            'S6':{'nom':'RECETTE CONTROLES603','devise':'MAD','exercice':'2025 civil ouvert ; aperçus seulement, aucune provision à comptabiliser'}},
        'profil_cloture':'Laboratoire seulement : SARL, IS droit commun, hypothèse explicite hors démarrage (exploitation depuis2020), aucune exonération CM/minimum, bases exclue et taux réduit0, pas de taux forcé. Cette hypothèse consignée ici n’est pas qualifiée par le premier calendrier de l’application. Les cas ne valident pas les acomptes ni une liquidation fiscale.',
        'operations_decalees':'S4/S5 : CAPITAL-605 au02/01/2025 BQ D5141/C1111 20000 ; BASE-605 au01/04/2025, S4 D6125/C5141 12000, S5 D5141/C7124 12000. Calcul CONTRAT-605, base Autre,12000, du01/04/2025 au30/09/2025. Pas de TVA inférée.',
        'article':{'code':'SERV-RT01','nom':'Maintenance fictive RT01','stockable':False,'prix_ht':'10000.00','tva_pct':20,'compte_achat':'6133','compte_vente':'7124'},
        'tiers':{'fournisseur':'PRESTATAIRE FICTIF RT01 — personne physique assujettie','client':'CLIENT FICTIF RT01'},
        'qualification_ras':{'payeur':'Personne morale privée assujettie','prestataire':'Personne physique assujettie',
            'service':'Liste B explicitement qualifiée dans ce scénario fictif','exclusion':'Aucune après contrôle des pièces fictives',
            'attestation':'Présentée, date2026-09-01, référence ATTEST-FICTIVE-RT01','taux_ht':'0',
            'quote_ttc':'6000.00','quote_tva':'1000.00','compte_destination':'4457 (choix du laboratoire, pas affectation imposée)'},
        'documents':{
            'A1':'Facture achat, référence fournisseur ACH-RT01, date2026-10-01, article SERV-RT01, quantité1 : HT10000 / TVA2000 / TTC12000.',
            'A2':'Facture achat, référence fournisseur ACH-RT02, date2026-10-02, mêmes article/quantité/montants.',
            'V1':'Facture vente, référence VENTE-RT01, date2026-10-03, mêmes article/quantité/montants ; aucun règlement ni capture subie.',
            'R1':'A1, virement5250 le2026-10-18, référence VIR-RT01 ; capture RAS-RT01 de750.',
            'R2':'A1, virement5250 le2026-10-18, référence VIR-RT02 ; capture RAS-RT02 de750, puis annulation.',
            'R3':'A2, virement5250 le2026-10-18, référence VIR-RT03 ; capture RAS-RT03 de750.',
            'R4':'A1, virement5250 le2026-10-18, référence VIR-RT04 ; capture RAS-RT04 de750 remplaçant le paiement annulé.',
            'CCA':'S2 : capital20000 (BQ,2025-01-02), charge12000 (BQ,2025-10-01). Calcul référence CONTRAT-CCA595, base Autre, du2025-10-01 au2026-03-31.',
            'PCA':'S3 : capital20000 (BQ,2025-01-02), produit12000 (BQ,2025-10-01). Calcul référence CONTRAT-PCA595, base Autre, mêmes période/montant.'},
        'consignes':'Utiliser les dates fixes et les références du jeu. Noter les numéros techniques réellement attribués ; ne pas les forcer. Remises, transport, emballage, avoirs, acomptes et RAS HT : zéro/aucun. Les hypothèses de TVA20% et déduction100% valent uniquement pour le laboratoire ; elles ne qualifient pas un dossier réel.'}


def cas():
    resultat=[]
    def c(id,module,objectif,prerequis,donnees,actions,attendu,ecritures='Aucune écriture créée par cette consultation.',fiscal='Aucun calcul fiscal nouveau attendu.',controles='Comparer les valeurs et conserver la preuve avant de poursuivre.',preuve='Capture de l’écran avec société/exercice et résultat ; référence des pièces concernées.'):
        resultat.append(dict(id=id,ordre=len(resultat)+1,module=module,objectif=objectif,prerequis=prerequis,donnees=donnees,
            actions=actions,attendu=attendu,ecritures=ecritures,fiscal=fiscal,controles=controles,preuve_attendue=preuve,
            statut='Non testé',reel='',anomalies='',preuves='',observations='À renseigner après exécution humaine.',
            auto='Parcours technique : voir les rapports des lots593 à605, avec des jeux distincts ; cette fiche humaine reste à exécuter.'))
    c('RT-01','RAS TVA','Préparer une société de recette et son paramétrage','Installation isolée ; administrateur ; chaîne jusqu’à099 qualifiée par le responsable technique.','S1, article SERV-RT01, fournisseur/client du jeu. Identifiants fiscaux vides.',
      'Créer S1 via le sélecteur Société. Dans Paramètres, vérifier MAD et TVA encaissement ; garder le calendrier2026 civil. Charger le logo fictif fourni. Dans Articles, créer SERV-RT01 non stockable, TVA20%, comptes achat6133/vente7124. Créer les deux tiers.',
      'Société et exercice visibles ; article non stockable et comptes explicites conservés. Aucun stock créé.','Aucune écriture ; les paramètres ne doivent pas générer de comptabilité.')
    c('RT-02','RAS TVA','Constituer les pièces commerciales du jeu','RT-01 réussi ; rôle administrateur/comptable.','Capital100000 au2026-10-01 ; A1, A2 et V1 du jeu.',
      'Dans Journal, saisir BQ : débit5141 / crédit1111 de100000, pièce CAP-RT01, date2026-10-01 ; valider. Dans Factures, créer A1/A2 achats et V1 vente avec l’article du jeu. RAS HT0, déduction TVA100% en achats pour ce scénario. Valider les factures, les comptabiliser puis valider leurs écritures dans Journal.',
      'Trois factures TTC12000, chacune comptabilisée une seule fois ; V1 non payée.',
      'Capital : D5141/C1111 100000. Chaque achat : D6133 10000 + D34552 2000 / C4411 12000. Vente : D3421 12000 / C7124 10000 + C4455 2000.',
      'TVA comptabilisée selon les hypothèses fictives ; aucune qualification réelle de déduction n’est présumée.')
    c('RT-03','RAS TVA','Créer la trésorerie réelle du premier paiement','RT-02 réussi.','R1 : VIR-RT01,2026-10-18,5250, virement.','Cycle commercial → Achat → Règlements : enregistrer R1 sur A1, en cochant la comptabilisation. Vérifier le compte banque5141. Valider l’écriture de trésorerie dans Journal.',
      'Un paiement5250 visible immédiatement ; la facture ne doit pas être artificiellement soldée.', 'D4411/C5141 5250, avec le vrai tiers de A1.')
    c('NEG-01','Négatifs','Refuser une ventilation dont le net ne correspond pas au règlement','R1 existe, aucune capture encore créée.','Quote-partTTC5000 / TVA1000, attestation du jeu ; net simulé4250 au lieu de5250.',
      'Sur R1, ouvrir Consulter ou déclarer la RAS → RAS TVA guidée. Renseigner les faits du jeu, mais la quote-partTTC5000. Simuler puis Vérifier le règlement et afficher l’aperçu.',
      'Refus du rapprochement ; aucune capture/OD enregistrée. Ne pas modifier le règlement pour rendre ce contrôle vert.',
      'L’écriture bancaire5250 reste intacte ; aucune écriture RAS.', 'Aucune retenue ou imputation nouvelle enregistrée.')
    c('RT-04','RAS TVA','Capturer puis valider la retenue guidée','NEG-01 exécuté ; R1 inchangé.','Faits de qualification du jeu ; quoteTTC6000 / TVA1000 ; RAS-RT01 ; compte4457 ; justification VENTILATION-RT01.',
      'Dans le même assistant, corriger la quote-partTTC6000. Simuler :750 de RAS et5250 de net. Saisir justification/référence/compte, vérifier l’aperçu, confirmer les pièces puis Préparer la capture RAS TVA et son OD. Dans Journal, vérifier et valider cette OD.',
      'Capture immuable liée à R1 ; la banque n’est pas comptabilisée une seconde fois. A1 garde6000 à régler.', 'OD D4411/C4457 750, tiers de A1 ; banque5250 inchangée.',
      'Calcul fictif75% de la TVA déclarée de1000. Aucun versement au Trésor ni crédit imputable prouvé.')
    c('RT-05','RAS TVA','Conserver une annulation traçable','RT-04 réussi.','R2 du jeu, puis annulation au2026-10-18, motif ANNULATION-FICTIVE-RT02.',
      'Enregistrer R2 sur A1, préparer sa capture guidée750 avec VENTILATION-RT02 et valider ses écritures. Dans Règlements, annuler R2 avec le motif et la date du jeu. Contrôler les contrepassations dans Journal, sans supprimer d’original ; valider les pièces encore en brouillon avant les comparaisons finales.',
      'A1 redevient partiellement réglée, reste6000. R2 et sa capture restent consultables comme annulés.',
      'Originaux D4411/C5141 5250 et D4411/C4457 750 conservés ; inverses D5141/C4411 5250 et D4457/C4411 750.',
      'Une annulation n’est pas une déduction automatique d’un bordereau fiscal antérieur.')
    c('RT-06','RAS TVA','Préparer le mois avec une OD restant à valider','RT-05 réussi.','R3 et capture RAS-RT03 ; VENTILATION-RT03 ; mêmes faits et montants.',
      'Enregistrer R3 sur A2 et valider la trésorerie5250. Préparer sa capture750 mais laisser cette OD en brouillon. Ouvrir Comptabilité → Déclaration TVA → Préparation mensuelle des retenues opérées ; choisir2026-11.',
      'Paiements2026-10, trois captures opérées : saisies2250, actives1500, actives OD validées750, annulées750. V1 sans capture n’entre pas dans cette préparation.',
      'R3 : D4411/C5141 5250 validée ; D4411/C4457 750 encore en brouillon.', 'Ces montants sont capturés, pas un reste fiscal à payer.')
    c('RT-07','RAS TVA','Actualiser après validation et exporter avec logo','RT-06 réussi.','OD de R3 ; période2026-11.','Valider l’OD RAS de R3 dans Journal. Revenir à la préparation et cliquer Actualiser la préparation. Télécharger CSV, Excel et PDF.',
      'Actives OD validées1500 ; autres totaux2250/1500/750 inchangés. Les trois formats portent la même empreinte ; logo dans PDF/Excel.',
      'Validation de l’OD existante750, sans nouvelle OD.', preuve='Trois fichiers téléchargés et capture des quatre totaux ; comparer leurs empreintes.')
    c('RT-08','RAS TVA','Conserver le panneau lors du recalcul TVA','RT-07 réussi.','Préparation2026-11 ouverte.','Dans Déclaration TVA, changer la vue de calcul vers Trimestrielle. Laisser la préparation mensuelle ouverte pendant le recalcul ; vérifier son mois et ses lignes.',
      'La préparation reste ouverte sur2026-11 avec ses trois captures. L’impression de déclaration reste indisponible si son calcul n’est pas exploitable.',fiscal='Avec les captures guidées, l’alerte de déclaration non qualifiée doit rester visible ; aucun faux zéro.')
    c('RT-09','RAS TVA','Refuser un export périmé après changement d’identité','RT-07 réussi ; ongletA gardé ouvert sans rechargement.','Nouvelle raison sociale : RECETTE TVA593 VARIANTE.','Dans un second ongletB Paramètres, changer la raison sociale. Revenir à A sans F5 et demander le PDF de l’ancienne préparation. Après le refus, cliquer Actualiser puis télécharger de nouveau.',
      'Ancien export refusé avec demande d’actualisation. Nouveau PDF porte la nouvelle identité et une nouvelle empreinte ; montants inchangés.')
    c('RT-10','RAS TVA','Consulter depuis la liasse et vérifier le calendrier','RT-07 réussi.','Année civile2026 ; préparation2026-11.','Ouvrir Liasse fiscale → Retenues TVA. Ouvrir le registre annuel et la préparation mensuelle. Choisir2026-12 dans la préparation puis revenir à2026-11.',
      'Décembre ne trouve aucune capture du mois de paiement novembre. Novembre retrouve les trois captures. Les tableaux T1… restent une numérotation interne ; cette préparation n’est pas incorporée à une archive définitive.')
    c('RT-11','RAS TVA','Solder A1 et effectuer un lettrage équilibré','RT-07 réussi ; R2 annulé, R1/R3 actifs et validés.','R4 : VIR-RT04, RAS-RT04, VENTILATION-RT04 ; code de lettrage AAA.',
      'Sur A1, enregistrer R4 et sa capture guidée avec les montants du jeu. Valider banque et OD. Dans Lettrage, sélectionner le fournisseur réel puis les cinq lignes actives : facture A1 crédit12000, R1/R4 débits5250 chacun et leurs deux captures débits750 chacune. Lettrer avec AAA ; ne pas sélectionner R2 annulé.',
      'A1 soldée ; A2 reste6000. Cinq lignes actives équilibrées lettrées AAA. Préparation : saisies3000, actives2250, actives validées2250, annulées750.',
      'R4 : D4411/C5141 5250 et D4411/C4457 750 ; le lettrage ne modifie pas les montants, dates ou numéros.')
    c('RT-12','RAS TVA','Recouper les soldes et le journal','RT-11 réussi ; toutes les pièces2026 du jeu validées, y compris contrepassations.','Oracle JSON : soldes_tva_finaux et journal_tva.','Exporter le Journal et la Balance2026. Comparer les comptes et totaux avec la feuille Calculs. Contrôler le CPC et le bilan sans déclencher de dépôt.',
      'Journal14écritures/31lignes, débit=crédit166000. Banque84250, clients12000, TVA récupérable4000 ; dettes6000, RAS2250, TVA facturée2000. CPC−10000, bilan actif/passif100250.',
      'Soldes exacts dans le JSON ; aucune correction arbitraire si une différence apparaît.',fiscal='La cohérence comptable ne valide pas une déclaration fiscale ou un reversement. Noter les limites visibles.')
    c('INV-01','Inventaire','Préparer le dossier CCA indépendant','Société S2 neuve et distincte de S1 ; administrateur.','Calendriers2025/2026 civils ; CAP-CCA595 et BASE-CCA595.',
      'Créer S2. Créer2025 du01/01 au31/12 ; conserver2026 civil. Journal : au02/01/2025, BQ D5141/C1111 20000 ; au01/10/2025, BQ D6125/C5141 12000. Saisir ces références et dates de pièces, puis valider.',
      'Deux écritures validées, banque8000 et charge12000. Aucun ajustement.',
      'D5141/C1111 20000 ; D6125/C5141 12000.',fiscal='Base comptable de laboratoire hors qualification TVA/fiscale.')
    c('INV-02','Inventaire','Calculer une CCA avec une convention explicite','INV-01 réussi, S2/exercice2025.','CCA ; CONTRAT-CCA595 ;12000,00 ; Base Autre ;01/10/2025 au31/03/2026.',
      'Clôture → exercice2025 → Calcul documentaire facultatif CCA/PCA. Saisir les valeurs du jeu et cliquer Calculer en jours calendaires.',
      'Clôture31/12/2025 ;90/182jours ; part à reporter5934,07 et complément6065,93. Aucune écriture créée.',fiscal='Ni TVA ni déductibilité déduites du prorata.')
    c('INV-03','Inventaire','Conserver la feuille de calcul','INV-02 réussi.','Résultat courant5934,07.','Cliquer Télécharger la feuille PDF. Vérifier référence, dates, base, jours, montants et empreinte ; conserver le PDF avec le contrat fictif.',
      'PDF lisible avec identité/logo s’il est paramétré. Empreinte des données, pas signature ni hash du PDF. Aucun archivage fiscal automatique.',preuve='PDF calcul_prorata_2025_cca.pdf ; référence du contrat et capture du résultat.')
    c('NEG-02','Négatifs','Invalider le calcul après changement de saisie','INV-02 réussi, résultat affiché.','Remplacer12000 par10000, puis rétablir12000.',
      'Modifier le montant sans cliquer Calculer. Vérifier la disparition du résultat et de la reprise. Rétablir12000 puis recalculer.',
      'Aucune reprise de l’ancien résultat possible. Après nouveau calcul,5934,07 revient ; aucune écriture n’a été créée.')
    c('INV-04','Inventaire','Reprendre explicitement le montant sans comptabiliser','INV-02 réussi, période de fin2025 ouverte.','Résultat5934,07 et libellé proposé.',
      'Cliquer Utiliser le montant et le libellé. Vérifier le formulaire d’ajustement CCA, son montant et la justification90/182. Vérifier les comptes3491/6125 du jeu.',
      'Formulaire rempli ; Créer l’écriture reste désactivé avant l’aperçu. Toujours deux écritures initiales seulement.')
    c('INV-05','Inventaire','Créer l’ajustement et vérifier la contrepassation','INV-04 réussi.','CCA5934,07, comptes3491/6125.','Cliquer Vérifier l’écriture ; contrôler31/12/2025 et01/01/2026. Cliquer Créer l’écriture. Consulter Journal2025 puis2026 sans valider la contrepassation2026.',
      'Ajustement en brouillon2025, contrepassation en brouillon2026 ; originaux conservés.',
      '2025 D3491/C6125 5934,07 ;2026 inverse D6125/C3491 5934,07.')
    c('INV-06','Inventaire','Valider et comparer CPC/bilan','INV-05 réussi.','Valider uniquement l’ajustement2025.','Dans Journal2025, valider l’OD de l’ajustement. Contrôler la Balance, puis Liasse fiscale → CPC et Bilan. Garder la contrepassation2026 en brouillon.',
      'Charge nette6065,93 ; CPC−6065,93. Banque8000 + CCA5934,07 = actif13934,07 ; passif13934,07. Aucun original bancaire modifié.',
      'Une validation, pas une seconde écriture ; capital20000 inchangé.',fiscal='Le résultat comptable est contrôlé ; résultat fiscal et impôt ne sont pas validés par ce test.')
    c('INV-07','Inventaire','Tester le PCA dans une troisième société','S3 neuve, indépendante ; ne pas modifier S2.','CAP-PCA595 : D5141/C1111 20000 au02/01/2025 ; BASE-PCA595 : D5141/C7124 12000 au01/10/2025.',
      'Créer S3 et les calendriers2025/2026 civils. Saisir et valider les deux écritures du jeu. Ouvrir le calcul2025 en choisissant PCA, CONTRAT-PCA595, montant12000, base Autre et même période. Calculer, télécharger, reprendre, vérifier puis créer et valider l’ajustement2025 ; laisser2026 en brouillon.',
      'Report5934,07 ; produit net6065,93. CPC+6065,93 ; actif/passif32000, dont banque32000 et PCA5934,07 au passif.',
      '2025 D7124/C4491 5934,07 ;2026 inverse D4491/C7124 5934,07.',fiscal='Aucune qualification fiscale du produit ou de sa TVA par le calcul.')
    c('INV-08','Inventaire','Contrôler un report nul','S2/exercice2025, sans modifier les écritures existantes.','Calcul seul : montant12000, base Autre, période01/01/2025 au31/12/2025, référence NUL-CCA595.',
      'Dans le calcul facultatif, saisir ces valeurs et calculer. Ne créer aucun nouvel ajustement.',
      '0jour après clôture, report0,00, complément12000,00 ; reprise désactivée. Les écritures existantes restent inchangées.')
    c('NEG-03','Négatifs','Refuser une période inversée ou un montant invalide','Outil de calcul ouvert dans S2, rôle autorisé à lire.','Fin01/01/2025 avant début01/10/2025 ; puis montantabc, puis0,001.',
      'Tester séparément chaque saisie, cliquer Calculer et relever le message. Après chaque refus, rétablir les valeurs du jeu avant le cas suivant.',
      'Erreur lisible ; aucun NaN, faux0, écriture ou ancien résultat réutilisable.')
    c('NEG-04','Négatifs','Respecter la consultation seule','Administrateur : créer un utilisateur lecture sur S1/S2 ; se reconnecter avec ce rôle.','Nom LECTEUR RECETTE, email lecteur.recette@example.com, mot de passe RecetteLocale2026! (compte fictif isolé).',
      'Dans S1, consulter registre/préparation et télécharger leurs exports. Dans S2, calculer et télécharger le PDF. Observer les commandes de reprise/création et de validation.',
      'Lecture/export disponibles ; reprise du calcul et écritures interdites. Aucun changement de montants, comptes ou pièces.',preuve='Captures du rôle et des commandes désactivées ; exports ; comparaison du Journal avant/après.')
    c('INV-09','Inventaire','Retrouver la contrepassation dans son exercice','Se reconnecter administrateur ; INV-06/07 réussis ; S2 puis S3.','Exercice2026 ; CP5934,07 encore en brouillon, source2025 validée.',
      'Ouvrir Clôture2026, bloc Contrepassations d’ouverture. Vérifier source, dates et débits/crédits. Revenir à2025 : la liste de destination doit être vide. Revenir à2026, ouvrir le Journal via le bouton puis revenir sans valider. Cliquer Actualiser les contrepassations.',
      'Dans chaque société :1liée,1à valider,0validée ; date01/01/2026, source31/12/2025. Aucune modification comptable par la consultation.',controles='Comparer source et contrepassation ; ne pas confondre cette liste avec toutes les écritures manuelles.')
    c('NEG-05','Négatifs','Refuser le croisement des comptes de provision','Administrateur ; créer S6 indépendante, exercice2025 civil ouvert.','Montant123,45 ; libellé TEST-COMPTES603 ; Stock/3942, Client/3911, Risque/3942.',
      'Clôture → Ajouter un ajustement. Pour chacun des trois couples, choisir le type, saisir montant/libellé et mauvaise contrepartie puis Vérifier l’écriture. Ne pas cliquer Créer ; réinitialiser le formulaire entre les essais.',
      'Message de famille attendue (391,3942 ou15/45). Création bloquée, aucune OD ni CP. Les sociétés S2/S3 conservent leurs écritures.',controles='Vérifier trois refus et Journal S6 inchangé.')
    c('INV-10','Inventaire','Contrôler les trois aperçus valables sans comptabiliser','NEG-05 réussi ; rester dans S6.','Stock :61961/3915 ; Client :61964/3942 ; Risque :6195/4508 ;123,45 ; TEST-APERCU603.',
      'Pour chaque type, vérifier les suggestions, saisir le compte de dotation et la contrepartie du jeu, montant/libellé puis Vérifier l’écriture. Comparer les lignes, cliquer Annuler et passer au type suivant. Ne créer aucune provision, faute de risque réel dans ce jeu.',
      'Aperçu : débit du compte de dotation, crédit de la contrepartie,123,45 ; aucune CP automatique ; suggestions propres au type, aucun mouvement comptable.',ecritures='Aucune écriture enregistrée ; trois aperçus seulement.',fiscal='Aucun montant provisionné ni déductibilité validés.')
    c('INV-11','Inventaire','Clôturer les deux sociétés civiles puis valider les CP','Administrateur ; S2/S3, seules les deux sources et AD2025 sont validées ;2026 ouvert.','Profil de clôture du jeu ; CM3000 pour ce laboratoire.',
      'Pour S2 puis S3, Paramètres → vérifier SARL/IS. Résultat fiscal/IS2025 → Catégorie fiscale droit commun, taux forcé vide, bases CM0, exonération totale et minimum non applicable décochés ; enregistrer. Clôture2025 → vérifier l’impôt annoncé3000 puis Clôturer. Journal2026 → vérifier et valider uniquement la CP. Revenir au suivi ; télécharger FEC2025 et2026 ; consulter CPC/Bilan2026.',
      'Résultats nets2025 : S2−9065,93 ; S3+3065,93. AN23000/32000 équilibrés. CP5934,07 validée ; compte3491/4491 soldé, CPC2026−5934,07/+5934,07 avant impôt2026. Sources intactes.',
      'Clôture : D6705/C4453 3000 ; AN2026 avec résultat1199/1191 et dette4453. CP inverse de l’AD, sans duplication.',fiscal='Résultat du profil fictif explicite ; pas de qualification fiscale réelle, ni validation d’acomptes ou de liquidation.',preuve='Écran de clôture, AN/CP du Journal, FEC des deux années et états2026 pour chaque société.')
    c('INV-12','Inventaire','Préparer un calcul sur calendrier décalé','Créer S4/S5 neuves ; aucune opération avant configuration des deux calendriers.','Calendriers et opérations_decalees du jeu ; base12000 du01/04 au30/09/2025.',
      'Clôture → créer/régler2025 du01/07/2024 au30/06/2025 et2026 du01/07/2025 au30/06/2026 ; le calendrier2026 doit être changé avant toute écriture. Saisir et valider CAPITAL-605 et BASE-605 dans chacune des sociétés. Calcul2025 → CCA pour S4, PCA pour S5, CONTRAT-605 et période du jeu ; calculer, conserver le PDF, reprendre, vérifier et créer l’AD puis valider uniquement l’AD2025.',
      '92/183jours, report6032,79 et complément5967,21. AD30/06/2025 ; CP01/07/2025 en exercice2026, encore en brouillon.',
      'S4 D3491/C6125 6032,79 ; S5 D7124/C4491 6032,79 ; CP inverses datées01/07/2025.',fiscal='Aucune TVA/déductibilité déduite. Calendrier comptable distinct de l’année civile.')
    c('INV-13','Inventaire','Clôturer au 30 juin et ouvrir au 1er juillet','INV-12 réussi ; administrateur, S4 puis S5.','Même profil de clôture que INV-11 ; CM3000.',
      'Appliquer les paramètres IS du cas INV-11 à S4/S5. Clôturer2025. Sélectionner2026, vérifier AN et CP au01/07/2025 puis valider la CP au Journal. Contrôler suivi, CPC/Bilan et télécharger FEC2025/2026. Ne déplacer aucune date vers2026 pour faire correspondre la référence d’exercice.',
      'Résultat2025 : S4−8967,21 ; S5+2967,21. AN23000/32000 équilibrés. CPC2026 avant impôt−6032,79/+6032,79 ; bilan équilibré. Le FEC2026 contient les dates20250701. Sources et AD inchangées.',
      'CM D6705/C4453 3000 ; AN et CP datés01/07/2025, référence2026. CP solde3491/4491.',fiscal='Profil fictif seulement ; aucune déclaration déposée.',preuve='FEC2025/2026, AN/CP et écrans société/calendrier/états pour S4/S5.')
    # Espacer les mots usuels et leurs montants sans changer les références,
    # comptes ou identifiants (CONTRAT-CCA595, SERV-RT01, D3491, etc.).
    mots='exercice|Clôture|Journal|CPC|Bilan|FEC|CM|AN|CP|TVA|capital|banque|report|complément|montant|contrepartie|période|référence|saisies|actives|validées|annulées'
    for item in resultat:
        for k in ('objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','preuve_attendue','auto'):
            item[k]=re.sub(r'\b('+mots+r')(?=\d)',r'\1 ',item[k])
            item[k]=re.sub(r'(\d)(juin|juillet|jours?|MAD|liée|validée)',r'\1 \2',item[k])
    return resultat


def limites():
    return [{'id':'LIM-01','statut':'Bloqué','objet':'Déclaration TVA complète, imputation et justificatifs de reversement',
        'motif':'La préparation interne n’est pas un bordereau administratif et ne prouve aucun versement. Les modèles et règles complémentaires restent à qualifier. Aucune procédure de dépôt à exécuter ici.'},
        {'id':'LIM-02','statut':'Bloqué','objet':'XML/EDI officiel, recette humaine annuelle et production',
        'motif':'Aucun schéma officiel applicable inventé. Cette annexe ne remplace ni le cahier annuel existant ni sa recette utilisateur, et ne qualifie pas la production. RH/paie différées.'}]


def classeur(data,cases,lim,cible):
    w=Workbook();s=w.active;s.title='Synthèse'
    s.append([TITRE]);s.merge_cells('A1:H1');s.append(['Lots593 à605 — données fictives — statuts humains à renseigner'])
    groupes=['RAS TVA','Inventaire','Négatifs'];emplacements={}
    for groupe in groupes:
        ws=w.create_sheet(groupe);ws.append([titre for _,titre in COLONNES]);rows=[c for c in cases if c['module']==groupe]
        for r,c in enumerate(rows,2):
            ws.append([c[k] for k,_ in COLONNES]);emplacements[c['id']]=(groupe,r)
            ws.row_dimensions[r].height=min(409,max(140,math.ceil(max(len(str(c[k]))/(70 if k in ('actions','attendu') else 45) for k,_ in COLONNES))*14+20))
        for col,width in {'A':15,'B':9,'C':16,'D':40,'E':48,'F':60,'G':85,'H':80,'I':65,'J':60,'K':50,'L':18,'M':50,'N':50,'O':60,'P':50,'Q':55,'R':55}.items():ws.column_dimensions[col].width=width
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');dv.errorTitle='Statut de recette';dv.error='Choisir un statut de la liste.';dv.showErrorMessage=True;dv.errorStyle='stop'
        ws.add_data_validation(dv);dv.add(f'L2:L{len(rows)+1}');ws.freeze_panes='D2';ws.auto_filter.ref=ws.dimensions
    s['A4']='Cas exécutables';s['B4']=len(cases)
    for r,statut in enumerate(['Réussi','Échoué','Non testé','Bloqué'],5):
        s.cell(r,1,statut);s.cell(r,2,'='+ '+'.join(f'COUNTIF(\'{g}\'!L2:L{1+len([c for c in cases if c["module"]==g])},"{statut}")' for g in groupes))
    s['A9']='Limites non exécutables';s['B9']=len(lim);s['A10']='Taux d’exécution';s['B10']='=IFERROR((B5+B6)/B4,0)';s['B10'].number_format='0.0%'
    s['A23']='Suivre Chronologie. Renseigner Statut humain, Résultat réel, Anomalies et Preuves dans la feuille du domaine.';s.merge_cells('A23:H24')
    s['A26']='Aucun succès humain prérempli. Les preuves automatisées des lots ne remplacent pas cette recette.';s.merge_cells('A26:H27')
    for col in 'ABCDEFGH':s.column_dimensions[col].width=23
    chart=BarChart();chart.title='Progression de la recette humaine';chart.add_data(Reference(s,min_col=2,min_row=5,max_row=8));chart.set_categories(Reference(s,min_col=1,min_row=5,max_row=8));chart.height=8;chart.width=17;s.add_chart(chart,'D4')
    ch=w.create_sheet('Chronologie');ch.append(['Ordre','ID','Domaine','Objectif','Statut (lié)','Lien vers la fiche'])
    for c in cases:
        groupe,r=emplacements[c['id']];ch.append([c['ordre'],c['id'],groupe,c['objectif'],f"='{groupe}'!L{r}",'Ouvrir la fiche'])
        cellule=ch.cell(ch.max_row,6);cellule.hyperlink=f"#'{groupe}'!A{r}";cellule.style='Hyperlink'
    ch.freeze_panes='D2';ch.auto_filter.ref=ch.dimensions
    for col,width in {'A':10,'B':15,'C':18,'D':65,'E':20,'F':24}.items():ch.column_dimensions[col].width=width
    d=w.create_sheet('Données');d.append(['Rubrique','Données exactes'])
    for k,v in data.items():d.append([k,json.dumps(v,ensure_ascii=False,indent=2) if isinstance(v,(dict,list)) else v])
    d.column_dimensions['A'].width=28;d.column_dimensions['B'].width=125
    for r in range(2,d.max_row+1):d.row_dimensions[r].height=min(409,max(45,str(d.cell(r,2).value).count('\n')*14+25))
    o=w.create_sheet('Calculs');o.append(['Contrôle indépendant','Formule Excel à recalculer','Attendu indépendant'])
    for row in [('RAS sur TVA', '=1000*75/100',750),('Trésorerie de la quote-part','=6000-750',5250),
        ('Prorata90/182','=ROUND(12000*90/182,2)',5934.07),('Complément','=12000-B4',6065.93),
        ('Banque S1 finale','=100000-3*5250',84250),('Débit = crédit Journal S1','=100000+3*12000+4*5250+4*750+5250+750',166000),
        ('Actif S1','=84250+12000+4000',100250),('Passif S1','=100000-10000+6000+2250+2000',100250),
        ('Actif S2 CCA','=8000+5934.07',13934.07),('CPC S2','=-(12000-5934.07)',-6065.93),
        ('CPC S3','=12000-5934.07',6065.93),
        ('Prorata décalé92/183','=ROUND(12000*92/183,2)',6032.79),('Complément décalé','=12000-B13',5967.21),
        ('CCA décalée après CM du profil','=-(12000-B13)-3000',-8967.21),('PCA décalée après CM du profil','=12000-B13-3000',2967.21),
        ('CCA civile après CM du profil','=-(12000-B4)-3000',-9065.93),('PCA civile après CM du profil','=12000-B4-3000',3065.93)]:o.append(row)
    for col,width in {'A':38,'B':70,'C':28}.items():o.column_dimensions[col].width=width
    l=w.create_sheet('Limites');l.append(['ID','Statut','Hors recette exécutable','Motif'])
    for item in lim:l.append([item['id'],item['statut'],item['objet'],item['motif']])
    for col,width in {'A':15,'B':18,'C':60,'D':115}.items():l.column_dimensions[col].width=width
    for ws in w:
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='183D35')
        for row in ws:
            for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
        ws.row_dimensions[1].height=38
        ws.print_title_rows='1:1'
        if ws.title not in groupes:ws.freeze_panes='A2'
    w.calculation.fullCalcOnLoad=True;w.save(cible)


def pdf(data,cases,lim,cible,images):
    st=getSampleStyleSheet();st['BodyText'].fontSize=9;st['BodyText'].leading=11;st['BodyText'].spaceAfter=4
    st['Heading2'].fontSize=10;st['Heading2'].leading=12;st['Heading2'].spaceBefore=5;st['Heading2'].spaceAfter=2
    st['Heading1'].textColor=colors.HexColor('#183D35');font=Path('C:/Windows/Fonts/arial.ttf')
    if font.is_file():
        if 'Recette597' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('Recette597',str(font)))
        for nom in ('BodyText','Heading1','Heading2','Title'):st[nom].fontName='Recette597'
    p=lambda x:Paragraph(escape(str(x)).replace('\n','<br/>'),st['BodyText'])
    story=[Paragraph(escape(TITRE),st['Title']),Paragraph('Lots593 à605 — RAS TVA, inventaire et suivi de clôture',st['Heading1']),
        p('Publication :19octobre2026. '+data['environnement']),p(data['statut']),
        p('Ne remplace pas le cahier annuel existant. Les cas ci-dessous sont exécutables ; les deux limites finales ne sont pas des fonctionnalités présentées comme testables.'),
        p('Suivre les identifiants dans l’ordre de la chronologie. Dans Excel, remplir les colonnes de résultat réel, anomalies et preuves dans la feuille du domaine. Les formules et graphiques se recalculent à l’ouverture dans Excel ; leur exécution dans Excel n’est pas revendiquée ici.'),
        Paragraph('Jeu de données fixe',st['Heading1'])]
    for k,v in data.items():
        if k in ('publication','environnement','statut'):continue
        story += [Paragraph(escape(k),st['Heading2']),p(json.dumps(v,ensure_ascii=False,indent=2) if isinstance(v,(dict,list)) else v)]
    story += [Paragraph('Oracle indépendant',st['Heading1']),p(json.dumps(oracle(),ensure_ascii=False,indent=2)),
        p('Les soldes sont signés débit−crédit. Les comptes de ce jeu sont explicites, pas des affectations obligatoires nouvelles. Si une configuration diffère, noter Bloqué et conserver l’écart ; ne jamais modifier une écriture définitive pour faire passer une fiche.')]
    for c in cases:
        story += [PageBreak(),Paragraph(c['id']+' · '+c['objectif'],st['Heading1'])]
        for k,label in COLONNES:
            if k in ('id','objectif'):continue
            story += [Paragraph(escape(label),st['Heading2']),p(c[k] if c[k]!='' else 'À renseigner par le testeur.')]
    story += [PageBreak(),Paragraph('Limites non exécutables',st['Heading1'])]
    for item in lim:story += [Paragraph(item['id']+' · '+item['statut'],st['Heading2']),p(item['objet']),p(item['motif'])]
    story += [p('Développement global : partiel. Tests automatisés locaux des lots : qualifiés selon leurs rapports. Recette utilisateur : à effectuer. Production et conformité réglementaire : non validées automatiquement.')]
    story += [PageBreak(),Paragraph('Illustrations de laboratoire',st['Heading1']),p('Captures réelles d’Edge, sociétés fictives et PostgreSQL jetable. Illustrations techniques, pas preuves de votre recette humaine.')]
    story.append(Table([[Image(str(images/'RAS_TVA_593_FICTIF.png'),width=220,height=564),Image(str(images/'CALCUL_CCA_PCA_595_FICTIF.png'),width=220,height=564)]],colWidths=[235,235]))
    def pied(c,doc):c.setFont('Helvetica',8);c.drawString(40,22,'HisabPro · Annexe de recette593 à605 · 19/10/2026');c.drawRightString(A4[0]-40,22,str(doc.page))
    SimpleDocTemplate(str(cible),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=40,title=TITRE).build(story,onFirstPage=pied,onLaterPages=pied)


def generer(dossier=None):
    dossier=Path(dossier) if dossier else ROOT/'docs/recette';dossier.mkdir(parents=True,exist_ok=True)
    images=dossier/'images';images.mkdir(exist_ok=True)
    for nom in ('RAS_TVA_593_FICTIF.png','CALCUL_CCA_PCA_595_FICTIF.png','LOGO_RECETTE_FICTIF.png'):
        source=ROOT/'docs/recette/images'/nom;dest=images/nom
        if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
    data,cases,lim=jeu(),cas(),limites()
    payload={'titre':TITRE,'donnees':data,'oracle':oracle(),'cas':cases,'limites_non_executables':lim}
    (dossier/JSON_NOM).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    classeur(data,cases,lim,dossier/(NOM+'.xlsx'));pdf(data,cases,lim,dossier/(NOM+'.pdf'),images)
    return dossier,payload


if __name__=='__main__':
    dossier,payload=generer();print(dossier);print(len(payload['cas']),'cas humains Non testé ;',len(payload['limites_non_executables']),'limites Bloqué')
