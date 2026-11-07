"""Annexe documentaire RAS : oracle entier indépendant, aucun service métier importé."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.sax.saxutils import escape
import importlib.util,json,re,xml.etree.ElementTree as E
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
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
from reportlab.pdfgen import canvas
from generer_annexe_reprises619 import CHAMPS,argent

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/recette'
NOM='ANNEXE_RECETTE_DOCUMENTS_RAS_20261019';JSON_NOM='donnees_recette_documents_ras_20261019.json'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
DOMAINES=['Préparation','Documents RAS','Contrôles']
PREUVE='DOCUMENT_FICTIF_649.pdf'


def lisible(s):
    mots='capital|quantité|prixHT|TVA|TTC|HT|compte|banque|fournisseur|facture|ouverte?|règlement|paiement|retenue|annulation|achat|quote-part|trésorerie|résultat|bilan|année|exercice|novembre|référence|préfixe|prorata|déduction|ouverture|laboratoire|créditeur|jeu|Registre|FEC|guides?|annexe|lot|de|du|au|en|et'
    s=re.sub(r'\b('+mots+r')(?=\d)',r'\1 ',s,flags=re.I)
    s=re.sub(r'(\d)(MAD|HT|TVA|TTC|pièces?|lignes?|soldé|créditeur|actifs|saisis|annulés|actif|OD|capital|banque|achat|fournisseur|compte|de\b|dont|est\b|sur\b)',r'\1 \2',s)
    s=re.sub(r'\bD=C(?=\d)','D = C = ',s)
    s=re.sub(r'\b([DC])(\d{4,5})=',r'\1 \2 = ',s)
    s=re.sub(r':(?=\S)',': ',s)
    return s.replace('enRDO','en RDO').replace('dontTVA','dont TVA').replace('ODvalidée','OD validée').replace('2026du','2026 du').replace('prixHT','prix HT').replace('listeB','liste B').replace('régimeIS','régime IS').replace('impôt−','impôt −').replace('CumulD','Cumul D')


def montants_revision653(s):
    """Réviser une fois les montants connus du texte, dates/repères/% conservés."""
    valeurs={10000:100000,1000:10000,200:2000,1200:12000,600:6000,500:5000,
        100:1000,75:750,525:5250,9475:94750,9675:96750,11800:118000,12400:124000,10200:102000}
    motif=r'(?<![\d.])(?:'+'|'.join(str(n) for n in sorted(valeurs,key=lambda n:-len(str(n))))+r')(?!\d|[.,]\d|\s*%)'
    return re.sub(motif,lambda m:str(valeurs[int(m[0])]),s)


def oracle():
    capital=10000000;ht=1000000;tva=ht*20//100;ttc=ht+tva
    quote=600000;quote_tva=100000;ras=quote_tva*75//100;cash=quote-ras
    pieces=[]
    def piece(phase,journal,ls):
        assert sum(x[1] for x in ls)==sum(x[2] for x in ls)
        pieces.append({'phase':phase,'journal':journal,'lignes':[{'compte':c,'debit_cents':d,'credit_cents':k} for c,d,k in ls]})
    piece('Capital','BQ',[('5141',capital,0),('1111',0,capital)])
    piece('Achat','AC',[('6111',ht,0),('34552',tva,0),('4411',0,ttc)])
    piece('Règlement','BQ',[('4411',cash,0),('5141',0,cash)])
    piece('Capture RAS','OD',[('4411',ras,0),('4457',0,ras)])
    def situation():
        soldes={}
        for p in pieces:
            for l in p['lignes']:soldes[l['compte']]=soldes.get(l['compte'],0)+l['debit_cents']-l['credit_cents']
        assert sum(soldes.values())==0
        actif=soldes['5141']+soldes['34552'];passif=capital-ht-soldes['4411']-soldes['4457']
        assert actif==passif
        return {'pieces':len(pieces),'lignes':sum(len(p['lignes']) for p in pieces),
            'debit':argent(sum(l['debit_cents'] for p in pieces for l in p['lignes'])),
            'credit':argent(sum(l['credit_cents'] for p in pieces for l in p['lignes'])),
            'soldes_cents':soldes,'banque':argent(soldes['5141']),'fournisseur':argent(-soldes['4411']),
            'compte_capture':argent(-soldes['4457']),'resultat_avant_impot':argent(-ht),
            'actif':argent(actif),'passif':argent(passif)}
    avant=situation()
    piece('Annulation règlement','BQ',[('5141',cash,0),('4411',0,cash)])
    piece('Annulation RAS','OD',[('4457',ras,0),('4411',0,ras)])
    apres=situation()
    return {'capital':argent(capital),'ht':argent(ht),'tva':argent(tva),'ttc':argent(ttc),
        'quote_part_ttc':argent(quote),'tva_quote_part':argent(quote_tva),'ras':argent(ras),'tresorerie':argent(cash),
        'avant_annulation':avant,'apres_annulation':apres,'pieces':pieces,
        'ajout_document':{'pieces':0,'lignes':0,'debit':'0.00','credit':'0.00'}}


def jeu():
    return {'version':'649-revision2-653-20261019','revision':{'lot':653,'version':2,'cumul_mensuel_externe_suppose':None,
            'raison':'Remplace le petit montant initial par une facture et une quote-part supérieures à5000MAD, sans supposer un cumul mensuel non renseigné. Les autres qualifications restent déclarées pour le laboratoire.'},
        'perimetre':'Complément aux guides RAS573/593 et documents647 ; pas un cahier annuel de remplacement.',
        'societe':{'nom':'SOCIETE FICTIVE DOC649 SARL','devise':'MAD','forme_juridique':'SARL','regime_fiscal':'is','regime_tva':'encaissement','capital_social':100000,'prefixe_facture':'DOC649'},
        'identifiants_legaux':'ICE, IF, RC non renseignés. Conserver les avertissements ; aucune identité officielle fictivement utilisable.',
        'administrateur':{'email':'docs649@example.com','mot_de_passe':'DocumentsRecette649!'},
        'comptable':{'email':'compta649@example.com','mot_de_passe':'DocumentsRecette649!'},
        'lecteur':{'email':'lecture649@example.com','mot_de_passe':'DocumentsRecette649!'},
        'exercice':{'annee':2026,'date_debut':'2026-01-01','date_fin':'2026-12-31'},
        'date_operation':'2026-10-19','fournisseur':'FOURNISSEUR FICTIF DOC649','article':'SERVICE DOC649',
        'comptes':{'capital':'1111','banque':'5141','achat':'6111','tva_achat':'34552','fournisseur':'4411','capture_choisie':'4457'},
        'references':{'capital':'CAP-DOC649','fournisseur':'FOURN-DOC649','virement':'VIR-DOC649','ras':'RAS-DOC649','complement':'COMP-DOC649'},
        'facture':{'date':'2026-10-19','type':'achat','reference':'FOURN-DOC649','lignes':[{'description':'SERVICE DOC649','quantite':1,'prix_unitaire':10000,'tva':20}],'nature_tva_achat':'charge','tva_deductible_pct':100},
        'simulation':{'date_paiement':'2026-10-19','payeur':'pm_privee_assujettie','prestataire':'pp_assujettie','prestation_liste_b':True,
            'exclusion':'aucune_apres_controle','attestation':'presentee','date_attestation':'2026-09-01','reference_attestation':'ATT-FICTIVE-DOC649',
            'montant_paiement_ttc':'6000.00','tva_paiement':'1000.00'},
        'justification_quote_part':'VENTILATION FICTIVE DOC649 : 5000 HT + 1000 TVA = 6000 TTC',
        'mois_preparation':'2026-11','motif_annulation':'ANNULATION FICTIVE DOC649 POUR RECETTE',
        'document_fictif':PREUVE,'qualification':'Reprise du cas de laboratoire déjà documenté573 : faits explicitement supposés pour tester le logiciel, à ne pas utiliser comme attestation ou qualification fiscale réelle. Compte4457 choisi pour le jeu, aucune affectation obligatoire imposée.',
        'oracle':oracle(),
        'limites':[{'id':'RDO-L01','statut':'Bloqué','objet':'Déclaration/justificatifs officiels, imputation et reversement','action':'Obtenir les spécifications applicables ; cet ajout documentaire ne les réalise pas.'},
            {'id':'RDO-L02','statut':'Non testé','objet':'Recette humaine et mise en production','action':'Attendre le retour utilisateur ; aucun résultat humain ou déploiement prévalidé.'}]}


def cas():
    ts=[]
    def t(n,module,obj,pre,donnees,actions,attendu,ecritures,controles,preuve):
        ts.append(dict(zip([k for k,_ in CHAMPS],[f'RDO-{n:03}',module,obj,pre,donnees,actions,attendu,ecritures,
            'Aucun dépôt, versement ou crédit fiscal validé par ce cas. Montants de laboratoire ; voir périmètre.',controles,'Non testé','','',preuve,'','Recette humaine à effectuer ; utiliser exclusivement la société fictive.'])))
    t(1,'Préparation','Créer le dossier fictif','Environnement de test isolé, migrations existantes dont083/099 appliquées par administrateur ; aucune base réelle.',
      'SOCIETE FICTIVE DOC649 SARL ; admin docs649@example.com / DocumentsRecette649! ; MAD ; SARL ; capital10000 ; IS ; TVA encaissement ; exercice2026 du01/01 au31/12 ; préfixeDOC649. ICE/IF/RC vides.',
      'Créer le compte et la société. Dans Paramètres, renseigner les valeurs ci-dessus. Dans Exercices sélectionner2026 ouvert. Créer les utilisateurs compta649@example.com (Comptable) et lecture649@example.com (Consultation seule), même mot de passe. Créer FOURNISSEUR FICTIF DOC649 de type Fournisseur. Vérifier le plan et les comptes du jeu.',
      'Société/exercice et rôles sélectionnables ; avertissements d’identifiants conservés ; aucun mouvement financier créé par ce paramétrage.',
      'Aucune écriture.', 'Société de test et année2026 visibles ; aucune identité légale inventée.', 'Capture Paramètres, exercice et rôles.')
    t(2,'Préparation','Comptabiliser capital et achat','RDO-001 ; comptes1111/5141/6111/34552/4411 disponibles.',
      'Capital02/01/2026 : CAP-DOC649,10000. Achat19/10/2026 : FOURN-DOC649, SERVICE DOC649, quantité1, prixHT1000, TVA20%, charge et déduction100%. Prorata laboratoire100%.',
      'Dans Déclaration TVA, régler Prorata annuel de déduction (%) à100 et crédit d’ouverture à0, puis Enregistrer. Dans Journal créer une écriture BQ : débit5141=10000, crédit1111=10000 ; référenceCAP-DOC649 et libellé Capital fictif DOC649. Valider. Dans Factures choisir Achat, le fournisseur du jeu et19/10/2026. Saisir la référence fournisseur et la ligne ci-dessus. Valider puis comptabiliser. Dans Journal contrôler et valider l’écriture d’achat.',
      'Achat1000HT+200TVA=1200TTC ; numéro attribué DOC649-2026-001 à noter ; référence fournisseur FOURN-DOC649 conservée.',
      'BQ : D5141=10000 / C1111=10000. AC : D6111=1000 + D34552=200 / C4411=1200.',
      'Deux pièces/cinq lignes ; D=C11200. Ne pas inventer un paiement à cette étape.', 'Facture, deux pièces du Journal et leurs références.')
    t(3,'Préparation','Préparer la capture partielle et son OD','RDO-002 ; faits de laboratoire explicitement supposés, ne représentent pas des pièces fiscales réelles.',
      '19/10/2026, virement VIR-DOC649=525. Quote-part TTC600, TVA100. Payeur personne morale privée assujettie ; prestataire personne physique assujettie ; listeB oui ; aucune exclusion après contrôle ; attestation présentée01/09/2026, ATT-FICTIVE-DOC649. RAS-DOC649, compte4457.',
      'Depuis Règlements enregistrer525 sur la facture, en cochant la comptabilisation. Ouvrir Consulter ou déclarer la RAS → RAS TVA guidée. Dans Assistant renseigner les faits ci-dessus et simuler. Renseigner VENTILATION FICTIVE DOC649 : 500 HT + 100 TVA = 600 TTC, référenceRAS-DOC649 et compte4457. Vérifier l’aperçu, confirmer les pièces supposées du jeu puis préparer la capture. Valider les écritures correspondantes dans Journal.',
      'Simulation du cas existant :75de retenue,525de trésorerie et mois prévu2026-11. Facture encore ouverte600. Quatre pièces/neuf lignes au total ; banque9475.',
      'BQ : D4411=525 / C5141=525. OD : D4411=75 / C4457=75. D=C11800 cumulés.',
      'Retenue75 distincte du virement525. Dossier et OD conservés ; aucun versement fiscal enregistré.', 'Aperçu, dossier RAS, deux écritures et reste600.')
    t(4,'Documents RAS','Joindre et relire le premier document','RDO-003. Utiliser DOCUMENT_FICTIF_649.pdf fourni, marqué essai uniquement.',
      'Registre année2026 ou préparation novembre2026 ; capture RAS-DOC649 ; OD de capture créée enRDO-003.',
      'Dans Déclaration TVA ouvrir le registre2026 et la capture, puis Documents liés aux OD. Dans Capture · OD, cliquer Joindre un fichier et choisir le PDF fourni. Attendre son apparition sans F5. Cliquer Télécharger et ouvrir le document reçu.',
      'Un fichier apparaît avec suffixe attribué. Sa référence documentaire et sa date sont visibles. Le PDF conserve la mention fictive. La référence d’attestation du dossier n’est pas remplacée par ce fichier.',
      'Aucune écriture nouvelle ;4pièces/9lignes et D=C11800 inchangés.',
      'Montants, OD et dossier099 d’origine inchangés. Fichier de la bonne société et bonne OD.', 'Capture avant/après et PDF téléchargé.')
    t(5,'Documents RAS','Conserver deux fichiers homonymes','RDO-004.',PREUVE+' envoyé une seconde fois sur la même OD.',
      'Cliquer à nouveau Joindre un fichier dans la même section et sélectionner le même PDF. Attendre l’envoi ; relire les deux noms puis télécharger chacun.',
      'Deux noms physiques distincts avec suffixes ; aucun écrasement. Deux compléments et deux fichiers sur l’OD de capture.',
      'Aucune écriture ; invariants RDO-003 conservés.', 'Deux fichiers, contenus égaux à l’original fictif ; aucun bouton de suppression dans cet écran RAS.', 'Liste des deux fichiers et deux téléchargements.')
    t(6,'Documents RAS','Ajouter une référence sans fichier','RDO-005. Administrateur ou comptable.',
      'RéférenceCOMP-DOC649 ; date19/10/2026 ; motif Complément documentaire fictif DOC649.',
      'Ouvrir Journal → Justificatifs sur l’OD de capture. Ajouter la référence, sa date et le motif. Revenir au registre et cliquer Actualiser le registre, puis Documents liés aux OD.',
      'Trois compléments sur l’OD : deux fichiers et une référence sans fichier. COMP-DOC649 n’est pas présenté comme un fichier ou un versement.',
      'Aucune nouvelle écriture. La priorité de référence FEC suit le fonctionnement existant du Journal.',
      'Référence sans fichier explicite, dates et référence d’origine conservées.', 'Historique Journal et section documentaire du registre.')
    t(7,'Documents RAS','Contrôler les trois exports actifs','RDO-006 ; logo de test facultatif dans Paramètres, jamais une marque réelle non autorisée.',
      'Registre2026 et préparation2026-11 ; deux fichiers et COMP-DOC649.',
      'Exporter CSV, Excel et PDF du registre. Ouvrir la préparation mensuelle novembre et exporter les mêmes formats. Lire Documents liés. Vérifier la phase Capture, l’OD, les dates et les deux noms. Si une vue ancienne est refusée après un ajout, utiliser son bouton Actualiser puis retélécharger.',
      'Trois lignes documentaires dans chaque export ; section/feuille distincte. Montants75actifs,75OD validée, aucun montant annulé. Logo présent dans PDF/Excel si configuré. Aucun fichier binaire embarqué.',
      'Toujours4pièces/9lignes, D=C11800 ; aucun export ne crée de mouvement.',
      'Le hash décrit les données/métadonnées, pas les octets des documents ; aucun bordereau officiel supposé.', 'Six exports et contrôle des trois lignes documentaires.')
    t(8,'Documents RAS','Annuler et documenter la contrepassation','RDO-007 ; même règlement525, aucun lettrage effectué.',
      'Annulation19/10/2026 ; motif ANNULATION FICTIVE DOC649 POUR RECETTE. PDF fictif fourni à joindre à l’OD de contrepassation.',
      'Dans Règlements annuler VIR-DOC649 avec date/motif ci-dessus. Valider les nouvelles écritures dans Journal. Actualiser le registre et déplier Documents liés aux OD : noter la nouvelle OD de contrepassation. Joindre le PDF dans cette section distincte. Exporter à nouveau. Dans Comptabilité → Liasse fiscale, exercice2026, contrôler Bilan et CPC ; exporter le FEC2026 depuis Journal.',
      'Capture annulée, données et documents d’origine conservés ; trois compléments côté Capture et un côté Contrepassation. Reste facture1200 ; banque10000 ; compte4457soldé. Registre :75saisis/75annulés,0actif. Six pièces/treize lignes ; bilan10200 ; résultat avant impôt−1000.',
      'BQ inverse : D5141=525 / C4411=525. OD inverse : D4457=75 / C4411=75. CumulD=C12400.',
      'Aucune suppression/remplacement des lignes initiales. FEC13lignes D=C12400 ; aucune déduction fiscale automatique due à l’annulation.', 'Deux contrepassations, documents par OD, soldes, FEC, bilan/CPC.')
    t(9,'Contrôles','Consulter avec le rôle lecture','RDO-008 et utilisateurlecture649 créé.',
      'lecture649@example.com / DocumentsRecette649!.',
      'Se déconnecter puis se connecter en consultation seule. Ouvrir registre2026 et préparationnovembre. Ouvrir la capture et les deux OD. Télécharger une pièce de chaque OD puis un export.',
      'Références et fichiers lisibles ; aucun bouton Joindre un fichier ni Supprimer ; montants et documents inchangés.',
      'Aucune écriture.', 'Ne pas confondre consultation avec permission d’écriture ; exporter ne qualifie pas les pièces.', 'Captures lecture et deux documents reçus.')
    t(10,'Contrôles','Vérifier la séparation des sociétés','RDO-009 ; revenir à l’administrateur. Société secondaire de test vide à créer.',
      'TEMOIN DOC649 SARL, aucun mouvement ni capture.',
      'Depuis Paramètres créer la seconde société. La sélectionner dans l’en-tête. Ouvrir le registre2026. Revenir à SOCIETE FICTIVE DOC649 SARL puis à son registre.',
      'Aucune capture/document de la première société dans le témoin. Au retour, les pièces du scénario sont retrouvées sans duplication.',
      'Aucune écriture créée par le changement de société.', 'Nom de société visible et aucune ancienne liste réaffichée dans le témoin.', 'Deux captures d’écran nom de société et registre.')
    t(11,'Contrôles','Refuser un règlement au sous-centime','RDO-010, première société active, administrateur.',
      'Montant0,005MAD sur la facture encore ouverte1200 ; référenceREFUS-DOC649.',
      'Tenter d’enregistrer un règlement de0,005. Lire le message, fermer le formulaire et vérifier facture, règlements et Journal. Ne pas remplacer la valeur pour forcer le passage.',
      'Montant refusé au centime. Aucun règlement, document ou mouvement créé ; soldes finaux RDO-008 conservés.',
      'Aucune écriture ;6pièces/13lignes D=C12400.', 'Pas d’arrondi implicite à0,01 ni modification de la facture.', 'Message de refus et contrôle du Journal.')
    t(12,'Contrôles','Afficher un refus de lecture sans faux vide','RDO-011 ; deux sessions distinctes en environnement de test.',
      'SessionA : compta649@example.com ; sessionB : administrateur docs649@example.com.',
      'Dans A, ouvrir les fichiers de la capture et attendre leur chargement. Dans B, désactiver seulement le compte compta649 fictif. Dans A, cliquer Actualiser les pièces jointes ; constater le refus. Dans B, réactiver le compte. Reconnecter A et relire les documents.',
      'Refus explicite, jamais Aucune pièce jointe à la place d’une erreur. Après reconnexion, tous les fichiers sont retrouvés ; aucun faux PDF téléchargé.',
      'Aucune écriture ni suppression documentaire.', 'Ne pas désactiver un compte réel. Vérifier la conservation des trois fichiers et des quatre compléments.', 'Message, réactivation et liste retrouvée.')
    return [{k:lisible(montants_revision653(lisible(v))) if k not in ('id','module','statut') else v for k,v in t.items()} for t in ts]


def markdown(d,ts):
    o=d['oracle'];l=['# '+TITRE,'Version 2 du 19 octobre 2026','Annexe649 — Documents des OD RAS TVA · Révision653',
        'Révision653 : le cas principal utilise une facture12000TTC et une quote-part6000TTC. Aucun cumul mensuel antérieur n’est supposé pour écarter une exclusion. Le cas initial649 reste une preuve arithmétique historique, à ne pas utiliser comme recette fiscale principale.',
        'Recette utilisateur à effectuer. Tous les cas sont Non testé ; résultats réels, anomalies et preuves restent vierges.',
        'Complément au cahier annuel et aux guides573/593. Ni bordereau officiel, ni attestation fiscale, ni preuve de versement. RH/paie et recette humaine restent différées.',
        '## Données du scénario', 'Utiliser exclusivement une base de test isolée. Ne pas lancer ce scénario dans une société réelle.',
        'Les codes de situations ci-dessous correspondent aux choix de l’assistant déjà documenté573. Le taux75% est celui de ce seul jeu existant ; aucun cas réel n’est qualifié par cette annexe.',
        'Société : SOCIETE FICTIVE DOC649 SARL. Devise MAD, forme SARL, capital10000, régimeIS, TVA sur encaissement. PréfixeDOC649. ICE/IF/RC non renseignés : conserver les avertissements.',
        'Exercice2026 ouvert, du01/01/2026 au31/12/2026. Opérations du19/10/2026 ; capital au02/01/2026. Crédit TVA d’ouverture0 ; prorata annuel du laboratoire100%.',
        'Administrateur : docs649@example.com. Comptable : compta649@example.com. Lecture : lecture649@example.com. Mot de passe de ces comptes fictifs : DocumentsRecette649!.',
        'Fournisseur : FOURNISSEUR FICTIF DOC649. Achat : référence fournisseur FOURN-DOC649 ; description SERVICE DOC649 ; quantité1 ; prixHT1000 ; TVA20% ; charge, déduction100%. Numéro attendu DOC649-2026-001.',
        'Références à saisir : CAP-DOC649 pour le capital ; VIR-DOC649 pour le virement525 ; RAS-DOC649 pour la capture ; COMP-DOC649 pour le complément documentaire.',
        'Comptes du jeu :1111capital,5141banque,6111achat,34552TVA sur achats,4411fournisseur et4457compte destination explicitement choisi pour la capture.',
        'Faits supposés du laboratoire : payeur personne morale privée assujettie ; prestataire personne physique assujettie ; prestation de listeB ; aucune exclusion après contrôle ; attestation présentée du01/09/2026, référence ATT-FICTIVE-DOC649. Aucun de ces faits ne constitue une pièce réelle.',
        'Quote-part :600TTC dont100TVA. Justification à saisir : VENTILATION FICTIVE DOC649 : 500 HT + 100 TVA = 600 TTC. Mois de versement prévu :2026-11, sans versement présumé.',
        'Document fourni : DOCUMENT_FICTIF_649.pdf, marqué essai uniquement. Motif d’annulation : ANNULATION FICTIVE DOC649 POUR RECETTE. Société témoin vide : TEMOIN DOC649 SARL.',
        'Le fichier donnees_recette_documents_ras_20261019.json fournit également toutes les données structurées et les calculs indépendants.',
        '## Calculs indépendants et Journal attendu',
        'Calculs entiers en centimes, sans import d’un calcul métier. Achat1000+200=1200 ; quote-part600dontTVA100 ; retenue du jeu75 ; trésorerie525. Le compte4457est une convention de recette, pas une affectation imposée.',
        'Avant annulation : banque9475, fournisseur600, compte4457créditeur75, résultat−1000, bilan9675 ;4pièces/9lignes D=C11800.',
        'Après annulation : banque10000, fournisseur1200, compte4457soldé, résultat−1000, bilan10200 ;6pièces/13lignes D=C12400. Chaque ajout documentaire crée0pièce/0ligne/0MAD.',
        '| Phase | Journal | Compte | Débit / crédit MAD |','|---|---|---|---|']
    for p in o['pieces']:
        for x in p['lignes']:l.append(f"| {p['phase']} | {p['journal']} | {x['compte']} | {argent(x['debit_cents'])} / {argent(x['credit_cents'])} |")
    # Le Journal contient déjà les décimaux recalculés ; réviser seulement les
    # montants entiers des paragraphes introductifs historiques.
    l=[lisible(montants_revision653(lisible(x))) if not x.startswith('|') else x for x in l]
    for t in ts:
        l+=['## '+t['id']+' — '+t['objectif']]
        for k,label in CHAMPS:
            if k not in ('id','objectif'):l.append(label+' : '+(t[k] or 'À renseigner par la personne chargée de la recette.'))
    l+=['## Limites et reprise','Développement de ce complément disponible ; tests automatisés qualifiés séparément ; recette utilisateur et production non validées.']
    l += [x['id']+' — '+x['statut']+' — '+x['objet']+' : '+x['action'] for x in d['limites']]
    l+=['Mode d’emploi : docs/RAS_DOCUMENTS_647.md. Rapports : Test/rapport_ras_documents647.md et Test/rapport_coherence_scenario653.md. Sources : docs/audit/SOURCES_SCENARIO_RAS_20261019_653.md. Ne pas réappliquer les lots645/647 ; utiliser cette révision des documents649.']
    # Conserver intégralement les données JSON et leurs identifiants exacts.
    return '\n\n'.join(x if x.startswith('{') else lisible(x) for x in l)+'\n'


def documents(out,md):
    spec=importlib.util.spec_from_file_location('guide_ooxml649',ROOT/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=md;g.STEM=out/NOM;items=g.blocs();g.docx(items)
    p=out/(NOM+'.docx')
    with ZipFile(p) as z:fs={n:z.read(n) for n in z.namelist()}
    ns={'w':g.W};doc=E.fromstring(fs['word/document.xml']);E.register_namespace('w',g.W)
    # La phase comptable doit rester lisible dans le tableau Word à quatre colonnes.
    for tbl in doc.findall('.//w:tbl',ns):
        widths=[2500,950,1200,3650]
        for col,largeur in zip(tbl.findall('w:tblGrid/w:gridCol',ns),widths):col.set('{'+g.W+'}w',str(largeur))
        for row in tbl.findall('w:tr',ns):
            for tc,largeur in zip(row.findall('w:tc',ns),widths):tc.find('w:tcPr/w:tcW',ns).set('{'+g.W+'}w',str(largeur))
    fs['word/document.xml']=E.tostring(doc,encoding='utf-8',xml_declaration=True)
    fs['word/header1.xml']=fs['word/header1.xml'].replace('Guide utilisateur — Démonstration et vérification'.encode(),'Documents des OD RAS — Annexe 649'.encode())
    fs['docProps/core.xml']=fs['docProps/core.xml'].replace('HisabPro — Mode d’emploi et vérification des avancées'.encode(),TITRE.encode())
    with ZipFile(p,'w',ZIP_DEFLATED) as z:
        for n,b in fs.items():z.writestr(n,b)
    for n,f in [('Recette649','arial.ttf'),('Recette649Bold','arialbd.ttf')]:
        if n not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
    st={k:ParagraphStyle(k,fontName='Recette649Bold' if k in ('title','h1','h2') else 'Recette649',fontSize=20 if k=='title' else 14 if k=='h1' else 10,leading=26 if k=='title' else 19 if k=='h1' else 14,spaceAfter=9,keepWithNext=k in ('h1','h2')) for k in ('title','h1','h2','body','cell')}
    story=[]
    for kind,v in items:
        if kind=='table':
            rows=[[Paragraph(escape(c),st['cell']) for c in row] for row in v]
            tb=Table(rows,colWidths=[150,55,80,220],repeatRows=1);tb.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CAD5D0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F1EC'))]));story += [tb,Spacer(1,10)]
        else:
            if kind=='h1':story.append(PageBreak())
            for ligne in v.splitlines():story.append(Paragraph(escape(ligne),st[kind]))
    def pied(c,d):
        c.setFont('Recette649',8);c.drawString(45,818,'HISABPRO · Documents des OD RAS · Annexe 649')
        c.drawString(45,22,'Données fictives · Recette humaine à effectuer · Page '+str(d.page))
    SimpleDocTemplate(str(out/(NOM+'.pdf')),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=45,bottomMargin=42,title=TITRE,author='HisabPro').build(story,onFirstPage=pied,onLaterPages=pied)


def classeur(out,d,ts):
    w=Workbook();s=w.active;s.title='Synthèse';w.calculation=CalcProperties(fullCalcOnLoad=True)
    s.append([TITRE]);s.append(['Recette utilisateur à effectuer — aucune réussite préremplie']);s.append(['Domaine','Non testé','Réussi','Échoué','Bloqué','Total','Progression'])
    for i,n in enumerate(DOMAINES,4):
        xs=[t for t in ts if t['module']==n];sh=w.create_sheet(n);sh.append([label for _,label in CHAMPS])
        for t in xs:sh.append([t[k] for k,_ in CHAMPS])
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');sh.add_data_validation(dv);dv.add(f'K2:K{len(xs)+1}')
        s.append([n]+[f'=COUNTIF(\'{n}\'!K2:K{len(xs)+1},"{st}")' for st in ('Non testé','Réussi','Échoué','Bloqué')]+[f'=SUM(B{i}:E{i})',f'=IF(F{i}=0,0,C{i}/F{i})'])
    s.append(['TOTAL']+[f'=SUM({c}4:{c}6)' for c in 'BCDEF']+['=IF(F7=0,0,C7/F7)'])
    for i in range(4,8):s.cell(i,7).number_format='0%'
    ch=BarChart();ch.title='Progression de la recette';ch.add_data(Reference(s,min_col=2,max_col=5,min_row=3,max_row=6),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=6));s.add_chart(ch,'A11')
    donnees=w.create_sheet('Données');donnees.append(['Clé','Valeur exacte'])
    for k,v in d.items():
        if k not in ('cas','oracle','limites'):donnees.append([k,json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v])
    j=w.create_sheet('Journal attendu');j.append(['Phase','Journal','Compte','Débit MAD','Crédit MAD'])
    for p in d['oracle']['pieces']:
        for x in p['lignes']:j.append([p['phase'],p['journal'],x['compte'],x['debit_cents']/100,x['credit_cents']/100])
    o=w.create_sheet('Soldes attendus');o.append(['Étape','Contrôle','Valeur exacte'])
    for phase in ('avant_annulation','apres_annulation'):
        for k,v in d['oracle'][phase].items():o.append([phase,k,json.dumps(v,ensure_ascii=False) if isinstance(v,dict) else v])
    l=w.create_sheet('Limites');l.append(['ID','Statut séparé','Objet non exécutable','Action'])
    for x in d['limites']:l.append([x['id'],x['statut'],x['objet'],x['action']])
    for sh in w:
        sh.freeze_panes='D2' if sh.title in DOMAINES else 'A2';sh.auto_filter.ref=sh.dimensions
        for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='183D35')
        for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=65 if sh.title in DOMAINES else 42
        for row in sh:
            for c in row:
                c.alignment=Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value,str) and not c.value.startswith(('=COUNTIF','=SUM','=IF')):c.data_type='s'
        for n in range(2,sh.max_row+1):sh.row_dimensions[n].height=280 if sh.title in DOMAINES else 90
    s.merge_cells('A1:G1');s.merge_cells('A2:G2');s.row_dimensions[1].height=45;s.row_dimensions[2].height=35
    for c in 'BCDEFG':s.column_dimensions[c].width=15
    s.column_dimensions['A'].width=32
    for n in range(3,8):s.row_dimensions[n].height=28
    w.save(out/(NOM+'.xlsx'))


def generer(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);d=jeu();ts=cas();d['cas']=ts
    (out/JSON_NOM).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    md=out/(NOM+'.md');md.write_text(markdown(d,ts),encoding='utf8');documents(out,md);classeur(out,d,ts)
    c=canvas.Canvas(str(out/PREUVE),invariant=True);c.setFont('Helvetica-Bold',16);c.drawString(45,780,'HISABPRO - DOCUMENT FICTIF649')
    c.setFont('Helvetica',11)
    for y,t in [(735,'ESSAI UNIQUEMENT - AUCUNE ATTESTATION FISCALE'),(710,'Ce PDF sert aux tests de pieces jointes.'),(685,'Il ne justifie aucune operation ou paiement reel.')]:c.drawString(45,y,t)
    c.save();return d


if __name__=='__main__':
    d=generer();print(NOM,len(d['cas']),'cas humains Non testé ; Word/PDF/Excel, oracle et PDF fictif générés.')
