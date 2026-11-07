"""Annexe humaine615/617 : oracle en centimes, sans import d'un service métier."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.sax.saxutils import escape
import importlib.util
import json
import re
from math import ceil
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

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/'docs/recette'
NOM='ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019'
JSON_NOM='donnees_recette_reprises_20261019.json'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
CHAMPS=[('id','Identifiant'),('module','Module'),('objectif','Objectif'),('prerequis','Prérequis'),
 ('donnees','Données exactes'),('actions','Actions dans l’interface'),('attendu','Résultat attendu'),
 ('ecritures','Écritures attendues'),('fiscal','Impacts fiscaux'),('controles','Contrôles'),
 ('statut','Statut humain'),('reel','Résultat réel'),('anomalies','Anomalies constatées'),
 ('preuve_attendue','Preuve attendue'),('preuves','Preuves réelles'),('observations','Observations')]


def argent(c):
    signe='-' if c<0 else '';q,r=divmod(abs(c),100)
    return f'{signe}{q}.{r:02d}'


def nettoyer(texte):
    mots='exercice|exercices|calendrier|calendriers|période|périodes|disponible|réservation|réservations|capacité|capital|dotation|reprise|reprises|inverse|montant|date|datée|pièce|pièces|ligne|lignes|Journal|Clôture|CPC|FEC|BQ|OD|de|au|en|après|compte|comptes|débit|crédit|banque|justificatif|référence|phase|rapports|Annexe'
    texte=re.sub(r'\b('+mots+r')(?=\d)',r'\1 ',texte,flags=re.I)
    texte=re.sub(r'(\d)(MAD|pièces?|lignes?|jours?|à\b|de\b|libellée\b|ouvert\b|présent\b|civil\b)',r'\1 \2',texte)
    texte=re.sub(r'\s*;\s*',' ; ',texte)
    for a,b in [('sansF5','sans F5'),('dejuin','de juin'),('enmars','en mars'),('enjuillet','en juillet'),
        ('rôlelecture','rôle lecture'),('noterBloqué','noter Bloqué'),('journalBQ','journal BQ'),
        ('référenceCAP','référence CAP'),('libelléeDOSSIER','libellée DOSSIER'),('motifAnnulation','motif Annulation'),
        ('code métier','code métier')]:texte=texte.replace(a,b)
    return texte


def oracle():
    # Comptes et montants fixés par le scénario, calculés en entiers uniquement.
    pieces=[{'reference':'CAP-PV01','date':'2025-01-02','journal':'BQ','lignes':[('5141',2000000,0),('1111',0,2000000)]},
        {'reference':'INV générée pour DOSSIER-PV01','date':'2025-12-31','journal':'OD','lignes':[('6195',100000,0),('1518',0,100000)]},
        {'reference':'REP-PV01','date':'2025-12-31','journal':'OD','lignes':[('1518',40000,0),('7195',0,40000)]},
        {'reference':'REP-PV02','date':'2025-12-31','journal':'OD','lignes':[('1518',20000,0),('7195',0,20000)]},
        {'reference':'ANN-REPRISE générée pour REP-PV01','date':'2025-12-31','journal':'OD','lignes':[('7195',40000,0),('1518',0,40000)]}]
    soldes={};debit=credit=0
    for p in pieces:
        for c,d,k in p['lignes']:soldes[c]=soldes.get(c,0)+d-k;debit+=d;credit+=k
    resultat=-sum(v for c,v in soldes.items() if c.startswith(('6','7')))
    passif=-soldes['1111']-soldes['1518']+resultat
    return {'pieces':pieces,'soldes_cents':soldes,'resultat_avant_impot':argent(resultat),
        'actif':argent(soldes['5141']),'passif':argent(passif),'provision_finale':argent(-soldes['1518']),
        'reprises_actives':argent(40000+20000-40000),'disponible_final':argent(100000-40000-20000+40000),
        'apres_deux_reprises':{'resultat_avant_impot':argent(-100000+40000+20000),'provision':argent(100000-40000-20000)},
        'journal':{'pieces':len(pieces),'lignes':sum(len(p['lignes']) for p in pieces),'debit':argent(debit),'credit':argent(credit)},
        'capacites':{'source':'1000.00','premier_brouillon':'600.00','deux_reprises':'400.00','inverse_brouillon':'400.00','inverse_valide':'800.00'},
        'chronologie':{'date_reprise':'2026-02-01','date_inverse':'2026-06-01','date_refusee':'2026-03-01',
            'demande':'600.00','capacite_mars':'0.00','date_acceptee':'2026-07-01','capacite_juillet':'1000.00'}}


def jeu():
    return {'date':'2026-10-19','perimetre':'Complément615/617 ; base fictive isolée uniquement. Recette humaine non exécutée.',
        'societe':{'nom':'RECETTE PROVISIONS615 SARL','ville':'Casablanca','devise':'MAD','forme':'SARL',
            'regime_fiscal':'IS déclaré, aucune liquidation ni déductibilité qualifiée par cette annexe',
            'identifiants_fiscaux':'Laisser vides ; aucun identifiant réel ni dépôt.',
            'administrateur':'Admin Recette Provisions','email':'recette.provisions615@example.com','mot_de_passe':'RecetteProvisions615!',
            'lecteur':'lecture.provisions615@example.com','mot_de_passe_lecteur':'LectureProvisions615!'},
        'autres_societes':{'S2':'RECETTE PROVISIONS CONTROLES615','S3':'RECETTE PROVISIONS CHRONO615'},
        'calendriers':{'2025':['2025-01-01','2025-12-31'],'2026':['2026-01-01','2026-12-31']},
        'logo':'docs/recette/images/LOGO_RECETTE_FICTIF.png',
        'comptes':{'5141':'Banques (solde débiteur)','1111':'Capital social','6195':"Dotations d'exploitation aux provisions pour risques et charges",
            '1518':'Autres provisions pour risques','7195':'Reprises sur provisions pour risques et charges'},
        'dotation':{'type':'provision_risque','libelle':'DOSSIER-PV01 — risque fictif de recette','montant':'1000.00','compte_activite':'6195','compte_contrepartie':'1518'},
        'reprises':[{'reference':'REP-PV01','montant':'400.00','justification':'Diminution fictive du risque — phase 1'},
                    {'reference':'REP-PV02','montant':'200.00','justification':'Diminution fictive du risque — phase 2'}],
        'annulation':{'date':'2025-12-31','motif':'Correction fictive de la reprise phase 1'},
        'oracle':oracle(), 'limites':[
            {'id':'LIM-RP01','statut':'Bloqué','objet':'Attribution des mouvements manuels historiques sans lien fiable','action':'Analyse humaine distincte ; aucun rapprochement par libellé supposé.'},
            {'id':'LIM-RP02','statut':'Bloqué','objet':'Déductibilité et qualification fiscale du risque réel','action':'Justificatifs et décision comptable/fiscale à obtenir, aucune attestation automatique.'}]}


def cas():
    res=[]
    def c(id,module,objectif,prerequis,donnees,actions,attendu,ecritures='Aucune nouvelle écriture.',
          controles='Contrôler société/exercice, nombres et absence de doublon.',preuve='Capture de l’écran et références générées.',fiscal='Aucune TVA ni déductibilité présumée ; résultat fiscal non qualifié.'):
        res.append(dict(id=id,module=module,objectif=objectif,prerequis=prerequis,donnees=donnees,actions=actions,
            attendu=attendu,ecritures=ecritures,fiscal=fiscal,controles=controles,statut='Non testé',reel='',anomalies='',preuves='',
            preuve_attendue=preuve,observations='Recette humaine à effectuer ; preuves automatisées distinctes dans les rapports615/617.'))
    c('RP-01','Préparation','Créer le dossier vierge et ses calendriers','Application de recette isolée ; migration100 installée séparément par l’administrateur. Aucune société réelle sélectionnée.',
      'Admin Recette Provisions ; RECETTE PROVISIONS615 SARL ; Casablanca ; recette.provisions615@example.com ; RecetteProvisions615! ; premier exercice2025 ; calendriers civils2025/2026.',
      'Déconnexion si nécessaire. Créer un compte → renseigner les cinq champs du jeu → créer. Paramètres : choisir SARL/MAD et Premier exercice (année de clôture)2025, enregistrer. Clôture : sélectionner2025, vérifier01/01–31/12 et périodes ouvertes ; conserver2026 civil. Si2025 n’a pas été préparé, Créer un exercice → année2025, début01/01/2025, clôture31/12/2025 → Créer cet exercice.',
      'Société fictive active, administrateur identifié, exercices2025/2026 présents sans chevauchement. Aucun identifiant fiscal inventé.',preuve='Écrans société et Gestion des exercices.')
    c('RP-02','Préparation','Préparer les comptes et le logo','RP-01 réussi.',
      'Comptes5141,1111,6195,1518,7195 ; logo docs/recette/images/LOGO_RECETTE_FICTIF.png.',
      'Plan comptable de la société → Compléter le plan CGNC. Rechercher les cinq comptes et vérifier leurs libellés. Paramètres → Logo de la société → choisir le PNG fictif → enregistrer. Ne pas utiliser un logo ou un dossier réel.',
      'Comptes disponibles et logo fictif visible, aucun mouvement comptable.',preuve='Plan filtré et aperçu du logo.')
    c('RP-03','Inventaire','Enregistrer le capital fictif et la dotation','RP-02 réussi ; exercice2025 actif.',
      'CAP-PV01 ;02/01/2025 ; BQ ;20000MAD. Dotation DOSSIER-PV01 — risque fictif de recette ;1000MAD ;6195/1518.',
      'Journal → Nouvelle écriture : date comptable et justificatif02/01/2025, journalBQ, libellé Apport bancaire fictif PV01, référenceCAP-PV01. Deux lignes5141 débit20000 et1111 crédit20000 → enregistrer, puis Valider. Clôture2025 → Ajouter un ajustement → Provision pour risques et charges, libellé/montant/comptes du jeu → Vérifier l’écriture → Créer l’écriture. Journal2025 : valider uniquement cette nouvelle OD.',
      'Deux pièces validées et équilibrées. Source datée31/12/2025 ; aucune contrepassation automatique. Résultat comptable avant impôt−1000 ; banque20000 ; provision1000.',
      'BQ D5141/C1111 20000 ; OD D6195/C1518 1000.',preuve='Deux pièces du Journal avec numéros et dotation de Clôture.')
    c('RP-04','Inventaire','Vérifier un aperçu sans mutation','RP-03 réussi.',
      'Source DOSSIER-PV01 ; date31/12/2025 ; montant400 ; REP-PV01 ; date pièce31/12/2025 ; Diminution fictive du risque — phase1.',
      'Clôture2025 → Reprises partielles de provisions → sélectionner DOSSIER-PV01. Saisir les cinq champs du jeu. Cliquer Vérifier la reprise, sans créer. Relever dotation1000, disponible1000, comptes/libellés et capacité pour cette date.',
      'Aperçu OD2025 : débit1518 et crédit7195 pour400. Aucun brouillon supplémentaire au Journal. Créer reste désactivé avant confirmation.',controles='Comparer le nombre de pièces avant/après aperçu ; contrôler1000de capacité.',preuve='Aperçu et nombre de pièces du Journal.')
    c('RP-05','Inventaire','Créer la réservation de400','RP-04 réussi ; ne pas changer les données après l’aperçu.',
      'Même demande REP-PV01,400MAD.',
      'Contrôler les mouvements et justificatifs fictifs. Cocher J’ai vérifié les mouvements du compte et les justificatifs de la reprise. Cliquer Créer le brouillon de reprise une fois. Rester sur le suivi puis ouvrir le Journal2025.',
      'Suivi mis à jour sansF5 : dotation1000 ; reprises validées0 ; réservation400 ; disponible600. Un seul nouveau brouillon, sans modifier la dotation.',
      'Brouillon OD D1518/C7195 400.',preuve='Suivi1000/0/400/600 et brouillon REP-PV01.')
    c('RP-06','Inventaire','Valider la première reprise','RP-05 réussi ; exercice2025 actif.',
      'REP-PV01 de400MAD.',
      'Journal : ouvrir la pièce REP-PV01, contrôler les deux lignes puis Valider. Revenir dans Clôture → reprises, sélectionner DOSSIER-PV01 et Actualiser les provisions si nécessaire.',
      'Reprise validée400 ; réservation0 ; disponible600. Montants et source inchangés, numéro définitif conservé.',
      'OD définitive D1518/C7195 400.',preuve='Pièce définitive et suivi actualisé.')
    c('RP-07','Inventaire','Ajouter200 et contrôler le premier résultat','RP-06 réussi.',
      '31/12/2025 ;200MAD ; REP-PV02 ; date pièce31/12/2025 ; Diminution fictive du risque — phase2.',
      'Même source : renseigner les données, Vérifier la reprise, confirmer puis créer. Vérifier réservation200 et disponible400. Journal2025 : valider REP-PV02. Liasse fiscale2025 : ouvrir CPC et Bilan.',
      'Reprises validées600, disponible400. CPC avant impôt−400 ; provision au bilan400 ; banque20000 ; actif=passif20000. Aucun impôt ou retraitement fiscal n’est ajouté dans ce scénario.',
      'OD D1518/C7195 200.',preuve='Suivi, CPC et bilan2025.')
    c('RP-08','Inventaire','Préparer l’annulation sans libération anticipée','RP-07 réussi.',
      'Annuler REP-PV01 ; date31/12/2025 ; motif Correction fictive de la reprise phase1.',
      'Suivi → repérer la ligne REP-PV01 de400 → Annuler la reprise → saisir date/motif → Créer l’inverse de reprise. Ne pas valider l’inverse immédiatement. Consulter le Journal.',
      'Original de400 conservé ; inverse400 en brouillon. Le disponible reste400, pas800. Le suivi explique la capacité maintenue jusqu’à validation des deux pièces.',
      'Inverse brouillon D7195/C1518 400.',preuve='Original et inverse présents, suivi avec capacité400.')
    c('RP-09','Inventaire','Valider l’inverse et contrôler le résultat final','RP-08 réussi ; seul l’inverse reste en brouillon.',
      'Inverse ANN-REPRISE de REP-PV01 ;400MAD ;31/12/2025.',
      'Journal2025 : contrôler puis valider l’inverse. Revenir au suivi, actualiser et sélectionner DOSSIER-PV01. Ouvrir Bilan/CPC depuis Liasse fiscale2025.',
      'Reprise active200, réservation0, disponible800. REP-PV01 et son inverse restent visibles. Provision finale800 ; CPC avant impôt−800 ; banque20000 ; actif=passif20000.',
      'Inverse définitif D7195/C1518 400. Aucun effacement de l’original.',preuve='Deux pièces400, suivi final1000/200/0/800 et états2025.')
    c('RP-10','Exports','Télécharger le suivi avec logo','RP-09 réussi ; logo fictif enregistré.',
      'Source DOSSIER-PV01 ; PDF et Excel de suivi.',
      'Dans le suivi, cliquer Télécharger le suivi PDF puis Télécharger le suivi Excel. Ouvrir les fichiers. Excel : feuilles Synthèse, Reprises, Logo société ; vérifier les deux reprises, référence déclarée, inverse et statut.',
      'Identité/logo fictifs dans les deux formats ; dotation1000, active200, réservations0, disponible800. Reprise400 annulée par inverse validé ;200 active. Empreinte présente, aucune attestation de déductibilité.',controles='Comparer écran/fichiers ; consigner les noms téléchargés et conserver les fichiers.',preuve='PDF, Excel et captures des cellules/du logo.')
    c('RP-11','Exports','Contrôler le Journal et le FEC final','RP-09 réussi ; cinq pièces toutes validées ; aucune autre opération dans S1.',
      'Exercice2025 ; référencesCAP-PV01,INV du dossier,REP-PV01,REP-PV02,ANN-REPRISE.',
      'Journal : filtrer2025, contrôler cinq pièces et leurs lignes. Exporter le FEC2025 depuis le module FEC. Ouvrir le fichier sans modifier les montants, comparer les comptes et références au tableau de l’oracle.',
      '5pièces,10lignes ; débit=crédit22000MAD. Soldes D5141=20000 ; C1111=20000 ; D6195=1000 ; C1518=800 ; C7195=200. Aucun brouillon.',controles='Sommes en centimes, unicité des pièces, références et numéros définitifs.',preuve='FEC et contrôle indépendant des10lignes.')
    c('RP-12','Permissions','Consulter sans commandes de mutation','RP-10 réussi ; administrateur S1.',
      'Nom Lecteur Provisions ; lecture.provisions615@example.com ; LectureProvisions615! ; rôlelecture.',
      'Paramètres → Utilisateurs → Ajouter un utilisateur : saisir nom, adresse et mot de passe du jeu, rôlelecture, Créer le compte. Déconnexion, connexion du lecteur. Clôture2025 → même source → lire et télécharger PDF/Excel.',
      'Suivi800 disponible et exports accessibles. Aucun formulaire Vérifier la reprise ni bouton Annuler la reprise. Source et pièces intactes.',preuve='Écran lecteur sans mutations, fichiers téléchargés et contrôle du Journal.')
    c('RP-13','Permissions','Séparer les sociétés','Administrateur reconnecté à S1 ; conserver ses fichiers finaux.',
      'Nouvelle société RECETTE PROVISIONS CONTROLES615 (S2).',
      'Sélecteur de société → Nouvelle société → saisir le nomS2 → Créer. Clôture → ouvrir les reprises. Vérifier l’absence du DOSSIER-PV01 deS1. Revenir à S1 et retrouver son suivi800.',
      'Aucune source deS1 visible dans S2 ; suivi deS1 inchangé.',controles='Vérifier les noms de sociétés en haut de page et dans les exports.',preuve='Deux écrans distincts S1/S2.')
    c('NEG-RP01','Négatifs','Refuser un dépassement ou une saisie invalide','Administrateur S1, aprèsRP-09.',
      'Source DOSSIER-PV01 ;31/12/2025 ; montant800.01 puis0,-1,0.001 ; justificationEssai négatif fictif.',
      'Essayer successivement ces montants dans Montant de reprise, cliquer Vérifier la reprise lorsque le navigateur le permet. Ne pas forcer les contrôles HTML. Revenir au suivi après chaque essai.',
      '800.01 refusé par capacité ; valeurs nulles/négatives/précision excessive empêchées par formulaire ou API. Disponible800, aucun nouveau brouillon.',preuve='Messages ou contrôle de saisie, nombre de pièces toujours5.')
    c('NEG-RP02','Négatifs','Refuser une reprise antérieure à la source','S1 aprèsRP-09.',
      'Date30/12/2025 ;100MAD ; justificationEssai de date fictif.',
      'Saisir les données dans le même panneau, Vérifier la reprise. Relever le refus puis remettre31/12/2025, sans créer.',
      'Refus : reprise antérieure à la dotation du31/12/2025 ; disponible800 et Journal inchangés.',preuve='Message de date et suivi800.')
    c('NEG-RP03','Négatifs','Bloquer une période fermée puis la rouvrir','S1 aprèsRP-11 ; administrateur ; aucune pièce brouillon.',
      'Période Décembre2025 ; demande100MAD au31/12/2025.',
      'Clôture2025 → Périodes comptables → cliquer la période dont l’action est Fermer Décembre, confirmer. Essayer un aperçu de reprise100 au31/12/2025 : relever le refus. Revenir aux périodes et Ouvrir Décembre, confirmer. Réessayer l’aperçu, sans créer.',
      'Fermeture bloque l’aperçu ; réouverture administrative rétablit l’aperçu. Aucune reprise ajoutée ni clôture annuelle exécutée ; trace de période conservée.',preuve='Période fermée/refus puis période ouverte ; Journal toujours5pièces.')
    c('NEG-RP04','Négatifs','Imposer original avant inverse','S2 vierge ; initialiser son plan,2025 et capital commeRP-01 à03. Dotation1000libelléeDOSSIER-CONTROLE-S2 validée.',
      'Reprise100 au31/12/2025 référenceREP-S2 ; annulation même date, motifAnnulation brouillon fictif.',
      'Créer REP-S2 en brouillon, ne pas valider. Depuis le suivi, créer son inverse. Journal2025 : essayer de valider uniquement l’inverse ; relever le refus. Puis Valider les brouillons pour les deux pièces, après contrôle.',
      'Inverse seul refusé ; original et inverse validés ensemble dans le bon ordre. Capacité1000 libérée uniquement après les deux validations.',
      'Brouillon D1518/C7195 100 et inverse D7195/C1518 100 ; effet net0.',preuve='Refus de validation isolée, deux numéros définitifs et disponible1000.')
    c('NEG-RP05','Négatifs','Respecter la date d’une annulation future','Créer S3 et initialiser plan/capital/dotation1000commeRP-01 à03, libelléDOSSIER-CHRONO-S3. Calendrier2026 ouvert.',
      'Reprise1000 le01/02/2026, référenceREP-CHRONO ; inverse01/06/2026, motifRisque fictif rétabli en juin ; aperçus600au01/03 puis01/07/2026.',
      'Dans S3, créer puis valider la reprise1000. Créer puis valider son inverse dejuin. Suivi : disponible final1000. Essayer un aperçu600 enmars : relever le refus ; essayer600 enjuillet : contrôler l’aperçu, sans créer. Cette branche ne simule aucune clôture ni à-nouveaux annuels.',
      'Mars refusé, capacité0à cette date ; juillet autorisé en aperçu avec capacité1000. Aucun nouveau mouvement600.',
      'Reprise2026 D1518/C7195 1000 ; inversejuin D7195/C1518 1000. Effet net2026nul.',preuve='Deux pièces1000 et les deux résultats d’aperçu.')
    c('NEG-RP06','Négatifs','Conserver les pièces liées et leurs justificatifs','S1 aprèsRP-11 ; administrateur.',
      'Source DOSSIER-PV01 ; REP-PV01 ; son inverse ; REP-PV02.',
      'Journal2025 : consulter chaque pièce, vérifier qu’une pièce définitive ne peut être supprimée ou réécrite. Les corrections liées se font depuis le suivi, pas par contrepassation générique. Ne pas tenter de modifier directement la base. Relever les messages de protection lorsque la commande est proposée.',
      'Source/originaux/inverse conservés,5pièces/10lignes22000. Les compléments justificatifs éventuels utilisent le flux append-only existant, sans réécrire les lignes.',preuve='Pièces conservées et contrôles/message de protection.')
    c('TECH-RP01','Technique','Rejouer les protections financières et concurrentes','Développeur sur copie locale isolée ; environnement Python et binaires PostgreSQL de recette disponibles. Jamais la base utilisateur.',
      "Depuis la racine : $env:PYTHON_DOTENV_DISABLED='1' ; .\\hisabpro-backend\\.venv\\Scripts\\python.exe -X utf8 Test/run_unit_tests.py Test/test_reprises_provisions.py Test/test_reprises_provisions615_isole.py Test/test_reprises_chronologie615_isole.py -q",
      'Exécuter exactement la commande dans PowerShell. Conserver la sortie et le code retour. Le banc prépare ses propres clusters nonce. Si les binaires/dépendances manquent, noterBloqué avec la cause ; ne pas substituer un PostgreSQL réel.',
      'NaN/infini/booléen refusés, idempotence et concurrence sans double consommation, sociétés/rôles protégés, périodes/clôture gardées, source antérieure intacte. Aucun succès déduit si commande échouée/ignorée.',preuve='Commande, sortie complète, code retour et chemins des preuves du banc.')
    for t in res:
        for k in ('objectif','prerequis','donnees','actions','attendu','ecritures','controles','preuve_attendue','observations'):t[k]=nettoyer(t[k])
    return res


def markdown(data,tests):
    o=data['oracle'];s=data['societe']
    lignes=[f'# {TITRE}','Annexe — reprises de provisions615/617',
        'Version 1 du 19 octobre 2026. Recette humaine à effectuer ; résultats automatisés distincts.',
        '## Périmètre et précautions de recette',
        'Cette annexe complète le cahier général existant. Elle couvre les reprises liées à une dotation, leurs contrôles et leurs exports. RH/paie restent différées. Utiliser uniquement une base vierge de recette ; aucun dossier réel.',
        'Développement du périmètre615/617 livré. Tests automatisés : rapports615/617. Recette utilisateur : Non testé. Mise en production : non validée. Ne pas clôturer l’exercice2025 deS1 dans ce scénario ; aucun impôt n’est calculé ou comptabilisé.',
        'Les montants de risque sont des hypothèses de test, pas des estimations comptables réelles. Référence et date de pièce sont fournies ici pour la preuve ; elles ne deviennent pas obligatoires pour la validation des écritures.',
        '## Jeu de données exact',
        f"S1 : {s['nom']} ; {s['ville']} ; {s['devise']} ; {s['forme']}. Email : {s['email']} ; mot de passe fictif : {s['mot_de_passe']}. Lecteur : {s['lecteur']} / {s['mot_de_passe_lecteur']}.",
        'Identifiants fiscaux laissés vides. Premier exercice2025 ; calendriers2025 et2026 civils, périodes ouvertes. Logo fictif : '+data['logo']+'.',
        'S2 : '+data['autres_societes']['S2']+' ; S3 : '+data['autres_societes']['S3']+'. Initialisation de chaque société : Compléter le plan CGNC,2025 civil, capitalBQ20000 au02/01/2025 puis dotation1000 au31/12/2025 commeRP-03. Ne pas importer les pièces deS1.',
        'Comptes5141/1111/6195/1518/7195. Dotation DOSSIER-PV01 — risque fictif de recette,1000. REP-PV01 :400, phase1 ; REP-PV02 :200, phase2. Reprises et inverse deS1 tous au31/12/2025. Motif inverse : Correction fictive de la reprise phase1.',
        'Le logiciel génère les identifiants/numéros définitifs et les référencesINV/ANN-REPRISE : les relever, sans les inventer ni forcer leur valeur.',
        '## Calcul indépendant des résultats attendus',
        'Calcul en centimes entiers, indépendant du code métier de l’application. Après les deux reprises : résultat avant impôt−400, provision400. Après inverse de400 : résultat avant impôt−800, provision800, reprise active200, disponible800.',
        f"Journal final :{o['journal']['pieces']}pièces/{o['journal']['lignes']}lignes, débit=crédit{o['journal']['debit']}MAD. Actif{o['actif']}=passif{o['passif']}. Aucun paiement, TVA ou impôt ajouté.",
        '| Compte | Libellé de contrôle | Débit net MAD | Crédit net MAD |','|---|---|---|---|']
    for compte,solde in sorted(o['soldes_cents'].items()):lignes.append(f'| {compte} | {data["comptes"][compte]} | {argent(max(solde,0))} | {argent(max(-solde,0))} |')
    for t in tests:
        lignes += [f"## {t['id']} — {t['objectif']}"]
        for cle,label in CHAMPS:
            if cle not in ('id','objectif'):lignes += [label+' : '+(t[cle] or 'À renseigner pendant la recette.')]
    lignes+=['## Limites non exécutables et validation humaine']
    for l in data['limites']:lignes.append(f"{l['id']} — {l['statut']} : {l['objet']}. {l['action']}")
    lignes += ['Une empreinte exportée identifie les données courantes, pas une signature ni une preuve de conformité fiscale. Les mouvements manuels historiques non liés ne sont pas attribués automatiquement.',
        'Excel : renseigner Statut humain, Résultat réel, Anomalies et Preuves. La synthèse se calcule à l’ouverture dans Excel ; son recalcul interactif et la mise en page Word du partenaire restent à vérifier.']
    return '\n\n'.join(nettoyer(ligne) for ligne in lignes)+'\n'


def fichiers_word_pdf(out,md):
    spec=importlib.util.spec_from_file_location('guide_ooxml619',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=md;guide.STEM=out/NOM;items=guide.blocs();guide.docx(items)
    cible=out/(NOM+'.docx')
    with ZipFile(cible) as z:fichiers={n:z.read(n) for n in z.namelist()}
    fichiers['word/header1.xml']=fichiers['word/header1.xml'].replace('Guide utilisateur — Démonstration et vérification'.encode(),'Recette des reprises de provisions — Annexe 615/617'.encode())
    fichiers['docProps/core.xml']=fichiers['docProps/core.xml'].replace('HisabPro — Mode d’emploi et vérification des avancées'.encode(),TITRE.encode())
    with ZipFile(cible,'w',ZIP_DEFLATED) as z:
        for n,b in fichiers.items():z.writestr(n,b)
    fonts=Path('C:/Windows/Fonts')
    for nom,f in [('Recette619','arial.ttf'),('Recette619Bold','arialbd.ttf')]:
        if nom not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(nom,str(fonts/f)))
    styles={'title':ParagraphStyle('title',fontName='Recette619Bold',fontSize=21,leading=27,spaceAfter=20,textColor=colors.HexColor('#183D35')),
        'h1':ParagraphStyle('h1',fontName='Recette619Bold',fontSize=15,leading=20,spaceAfter=14,keepWithNext=True,textColor=colors.HexColor('#183D35')),
        'h2':ParagraphStyle('h2',fontName='Recette619Bold',fontSize=12,leading=16,spaceAfter=10,keepWithNext=True),
        'body':ParagraphStyle('body',fontName='Recette619',fontSize=10,leading=14,spaceAfter=8),
        'cell':ParagraphStyle('cell',fontName='Recette619',fontSize=8,leading=11)}
    story=[Image(str(DOSSIER/'images/LOGO_RECETTE_FICTIF.png'),width=70,height=42),Spacer(1,15)]
    for kind,value in items:
        if kind=='table':
            table=Table([[Paragraph(escape(c),styles['cell']) for c in row] for row in value],colWidths=[45,275,90,90],repeatRows=1)
            table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CAD5D0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F1EC'))]))
            story += [table,Spacer(1,12)]
        else:
            if kind=='h1':story.append(PageBreak())
            story.append(Paragraph(escape(value),styles[kind]))
    def pied(c,d):
        c.setFont('Recette619',8);c.drawString(45,818,'HISABPRO · Recette des reprises de provisions · Annexe 615/617')
        c.drawString(45,22,'Sociétés fictives uniquement · Recette humaine à effectuer · Page '+str(d.page))
    SimpleDocTemplate(str(out/(NOM+'.pdf')),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=45,bottomMargin=42,
        title=TITRE,author='HisabPro').build(story,onFirstPage=pied,onLaterPages=pied)


def classeur(out,data,tests):
    w=Workbook();s=w.active;s.title='Synthèse';w.calculation=CalcProperties(fullCalcOnLoad=True)
    domaines=['Préparation','Inventaire','Exports','Permissions','Négatifs','Technique']
    s.append([TITRE]);s.append(['Annexe615/617 — résultats humains à renseigner'])
    s.append(['Domaine','Non testé','Réussi','Échoué','Bloqué','Total','Progression'])
    for i,nom in enumerate(domaines,4):
        ws=w.create_sheet(nom);ws.append([label for _,label in CHAMPS])
        ts=[t for t in tests if t['module']==nom]
        for t in ts:ws.append([t[k] for k,_ in CHAMPS])
        validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"',allow_blank=False)
        validation.errorTitle='Statut attendu';validation.error='Choisir un des quatre statuts.';validation.showErrorMessage=True;validation.errorStyle='stop'
        ws.add_data_validation(validation);validation.add(f'K2:K{len(ts)+1}')
        s.cell(i,1,nom)
        for j,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):s.cell(i,j,f'=COUNTIF(\'{nom}\'!K2:K{len(ts)+1},"{statut}")')
        s.cell(i,6,f'=SUM(B{i}:E{i})');s.cell(i,7,f'=IF(F{i}=0,0,C{i}/F{i})').number_format='0%'
    s.append(['Total','=SUM(B4:B9)','=SUM(C4:C9)','=SUM(D4:D9)','=SUM(E4:E9)','=SUM(F4:F9)','=IF(F10=0,0,C10/F10)']);s['G10'].number_format='0%'
    s.append(['Statuts : humains seulement. Les limites non exécutables sont séparées.'])
    s.append(['Automatisés615 :139regroupés +5compatibilité avec recouvrement +restauration77tables.617 :15ciblés +40connexes avec recouvrement +restauration.'])
    graphique=BarChart();graphique.title='Résultats de recette à renseigner';graphique.add_data(Reference(s,min_col=2,max_col=5,min_row=3,max_row=9),titles_from_data=True)
    graphique.set_categories(Reference(s,min_col=1,min_row=4,max_row=9));s.add_chart(graphique,'A15')
    def aplatir(cle,v):
        if isinstance(v,dict):
            for k,x in v.items():yield from aplatir(cle+' / '+str(k),x)
        elif isinstance(v,list):
            for i,x in enumerate(v,1):yield from aplatir(cle+' / '+str(i),x)
        else:yield [cle,v]
    j=w.create_sheet('Données');j.append(['Clé','Valeur exacte'])
    for cle,v in [('Société',data['societe']),('Calendriers',data['calendriers']),('Dotation',data['dotation']),('Reprises',data['reprises']),('Annulation',data['annulation']),('Autres sociétés',data['autres_societes'])]:
        for ligne in aplatir(cle,v):j.append(ligne)
    o=w.create_sheet('Oracle');o.append(['Contrôle indépendant','Valeur exacte'])
    for cle,v in data['oracle'].items():
        if cle not in ('pieces','soldes_cents'):
            for ligne in aplatir(cle,v):o.append(ligne)
    journal=w.create_sheet('Journal attendu');journal.append(['Pièce','Référence déclarée / générée','Date','Journal','Compte','Débit MAD','Crédit MAD'])
    for i,p in enumerate(data['oracle']['pieces'],1):
        for c,d,k in p['lignes']:
            journal.append([i,p['reference'],p['date'],p['journal'],c,d/100,k/100])
            journal.cell(journal.max_row,6).number_format=journal.cell(journal.max_row,7).number_format='0.00'
    journal.append(['Total indépendant','','','','',int(data['oracle']['journal']['debit'].split('.')[0]),int(data['oracle']['journal']['credit'].split('.')[0])])
    balances=w.create_sheet('Balance attendue');balances.append(['Compte','Libellé','Débit net MAD','Crédit net MAD'])
    for c,v in sorted(data['oracle']['soldes_cents'].items()):balances.append([c,data['comptes'][c],max(v,0)/100,max(-v,0)/100])
    l=w.create_sheet('Limites');l.append(['ID','Statut séparé','Objet non exécutable','Action'])
    for v in data['limites']:l.append([v['id'],v['statut'],v['objet'],v['action']])
    for ws in w:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='183D35')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42 if ws.title not in domaines else 36
        for row in ws:
            for c in row:
                c.alignment=Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value,str) and not c.value.startswith(('=COUNTIF','=SUM','=IF')):c.data_type='s'
        for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=160 if ws.title in domaines else 65
    for nom in domaines:
        ws=w[nom]
        for col in ['C','D','E','F','G','H','I','J','O']:ws.column_dimensions[col].width=65
        for row in range(2,ws.max_row+1):ws.row_dimensions[row].height=260
    s.column_dimensions['A'].width=29
    for c in 'BCDEFG':s.column_dimensions[c].width=15
    s.row_dimensions[12].height=70
    for plage in ['A1:G1','A2:G2','A11:G11','A12:G13']:s.merge_cells(plage)
    s.row_dimensions[1].height=45;s.row_dimensions[2].height=34
    s.freeze_panes='B4';s.auto_filter.ref='A3:G9'
    for c in s[3]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='183D35')
    j.column_dimensions['B'].width=110;o.column_dimensions['B'].width=110
    for ws in [j,o,journal,balances,l]:
        for row in ws:
            hauteur=max(sum(max(1,ceil(len(t)/max(1,int(ws.column_dimensions[c.column_letter].width)-3))) for t in str(c.value or '').split('\n')) for c in row)
            ws.row_dimensions[row[0].row].height=min(409,max(28,hauteur*14+10))
    w.save(out/(NOM+'.xlsx'))


def generer(out=DOSSIER):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    data=jeu();tests=cas();data['cas']=tests
    (out/JSON_NOM).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    md=out/(NOM+'.md');md.write_text(markdown(data,tests),encoding='utf8')
    fichiers_word_pdf(out,md);classeur(out,data,tests)
    return data


if __name__=='__main__':
    d=generer();print(NOM,len(d['cas']),'cas humains Non testé ; Word/PDF/Excel/JSON générés.')
