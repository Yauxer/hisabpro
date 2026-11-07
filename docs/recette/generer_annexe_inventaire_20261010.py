"""Annexe de recette : génération locale déterministe, aucune connexion DB."""
from pathlib import Path
from decimal import Decimal
from xml.sax.saxutils import escape
import json

from openpyxl import Workbook
from openpyxl.chart import PieChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

DIR = Path(__file__).resolve().parent
BASE = 'ANNEXE_RECETTE_INVENTAIRE_20261010'
D = Decimal
NAVY, TEAL = '17243A', '167D8D'

DONNEES = [
    ('Société', 'RECETTE INVENTAIRE 313 SARL — fictive, société distincte du dossier annuel'),
    ('Utilisateur', 'Administrateur recette ; email inventaire313@example.com ; mot de passe choisi par le testeur'),
    ('Exercice', '2025 ; début01/01/2025, fin31/12/2025 ; ouvert, sélectionné avant toute opération'),
    ('Devise', 'MAD ; régime fiscal/TVA à qualifier pour le laboratoire, aucun identifiant légal inventé'),
    ('Fournisseur', 'FOURNISSEUR FICTIF INV313 ; délai30jours ; compte collectif4411'),
    ('Article principal', 'INV313-M ; Marchandise recette ; stockable ; unitéunité ; stock initial0 ; achatHT20 ; venteHT30 ; TVA20 ; frais0 ; seuil0'),
    ('Article zéro', 'INV313-Z ; Zéro connu ; stockable ; stock initial0 ; achatHT0 ; venteHT0 ; TVA0 ; frais0 ; seuil0'),
    ('Comptes', '1111 capital ; 5141 banque ; 6111 achat ; 34552 TVA récupérable sur charges ; 4411 fournisseur ; 3111 stock ; 6114 variation. Choisir les libellés exacts du plan chargé.'),
    ('Hypothèse TVA', 'Taux20% et récupération100% explicitement choisis uniquement pour cet oracle fictif ; aucune qualification fiscale réelle'),
    ('Dates/références', 'Capital02/01/2025 CAP-INV313 ; achat10/01/2025 ACH-INV313 ; paiement20/01/2025 REG-INV313 ; inventaire31/12/2025 INV-STOCK-2025'),
    ('Achat et paiement', '10unités ×20HT =200HT +40TVA =240TTC ; paiement unique240 ; aucun avoir/acompte/RAS'),
    ('Comptage', 'ArticleINV313-M :8unités ; articleINV313-Z :0 ; écart principal−2 ; CMUP20 ; perte40 ; valeur160'),
]

def cas(n, module, objectif, pre, donnees, actions, attendu, ecritures='Aucune écriture nouvelle.', fiscal='Aucun impact fiscal supplémentaire calculé.', controles='', preuve='', statut='Non testé'):
    return {'id':f'INV313-{n:02d}', 'module':module, 'objectif':objectif,
            'prerequis':pre, 'donnees':donnees, 'actions':actions,
            'attendu':attendu, 'ecritures':ecritures, 'fiscal':fiscal,
            'controles':controles, 'statut':statut, 'resultat_reel':'', 'anomalies':'', 'preuves':preuve}

CAS = [
cas(1,'Administration','Créer le dossier fictif et son exercice passé.',
    'Base de recette isolée vierge préparée par le technicien ; aucune connexion au dossier réel.',
    'Société et administrateur ci-dessus ; exercice2025,01/01–31/12.',
    "S'inscrire ; ouvrir la gestion des exercices ; créer2025 explicitement ; choisir2025 dans Exercice actif ; vérifier les dates et le statut ouvert.",
    'Société distincte, plan chargé, exercice2025 ouvert et actif. Ne pas saisir un capital2025 avant cette création.',
    controles='Identité du dossier de test et exercice affichés avant chaque opération.', preuve='Capture société/exercice et URL du dossier isolé.'),
cas(2,'Administration','Financer la banque fictive.', 'INV313-01 réussi.',
    '02/01/2025 ; CAP-INV313 ; capital1000MAD.',
    'Journal : créer une écriture bancaire, débit5141=1000/crédit1111=1000 ; enregistrer puis valider.',
    'Une écriture définitive équilibrée ; banque1000, capital1000.',
    '5141D1000 /1111C1000.', controles='Référence et deux lignes ; validation effective, aucune duplication.', preuve='Écriture et grand livre5141.'),
cas(3,'Articles','Créer les deux articles sans stock initial.', 'INV313-01 réussi.',
    'INV313-M et INV313-Z ; valeurs exactes du tableau de données.',
    'Articles : créer les deux fiches ; cocher Stockable ; saisir prix, TVA et frais explicitement ; stock initial0 ; enregistrer et rouvrir.',
    'Deux articles distincts ; stock0 et coût0 connus, aucun zéro utilisé pour masquer une donnée inconnue.',
    controles='Codes, prix, TVA, stockable et absence de mouvement initial non nul.', preuve='Fiches et liste articles.'),
cas(4,'Facturation','Acheter10unités et alimenter le stock.', 'INV313-01/03 réussis ; fournisseur fictif créé avec compte4411.',
    'Facture fournisseur10/01/2025 ; ACH-INV313 ; INV313-M quantité10, prixHT20, TVA20%, récupération100%.',
    'Factures : Nouvelle facture, type achat ; choisir le fournisseur ; saisir référence externeACH-INV313 et article ; enregistrer puis valider ; générer son écriture comptable. Ne pas créer de BR dans cette variante directe.',
    'Facture200HT/40TVA/240TTC ; stock10 et CMUP20, une seule entrée ; écriture brouillon conforme.',
    '6111D200 /34552D40 /4411C240.',
    'TVA laboratoire40 récupérable sous hypothèse explicite ; dette fournisseur240.',
    'Comparer les trois montants et le mouvement10×20 ; stopper et noter anomalie si la TVA ou le stock diffère.',
    'Facture, historique article et écriture liée.'),
cas(5,'Règlements','Payer le fournisseur intégralement.', 'INV313-02/04 réussis.',
    '20/01/2025 ;240MAD ; banque5141 ; virement ; REG-INV313.',
    'Depuis la facture, Payer le fournisseur ; saisir240, date20/01 et compte banque5141 ; enregistrer ; générer le règlement comptable si demandé par le flux.',
    'Facture payée, reste0 ; banque760 ; paiement et écriture liés.',
    '4411D240 /5141C240.',
    'Pas de seconde TVA ni de retenue fictive.',
    'Comparer montant enregistré, statut payé, dette et banque ; aucune seconde sortie.', 'Facture et règlement lié.'),
cas(6,'Journal','Valider et lettrer achat/règlement.', 'INV313-04/05 réussis.',
    'Deux brouillons achat/paiement ; tiers fournisseur ; codeAAA.',
    'Journal : valider les brouillons ; Lettrage : choisir Fournisseurs puis le fournisseur ; sélectionner240crédit de facture et240débit du règlement ; lettrerAAA.',
    'Trois écritures définitives en comptant le capital ; fournisseur soldé ; deux lignes lettréesAAA.',
    'Aucune écriture de lettrage nouvelle ; écritures sources conservées.',
    controles='Solde auxiliaire et collectif0 ; banque760 ; total débits=crédits1480 avant inventaire.', preuve='Journal validé et lettrageAAA.'),
cas(7,'Inventaire','Vérifier les sources avant comptage.', 'INV313-03/04 réussis.',
    'INV313-M : stock10, CMUP20, valeur200 ; INV313-Z :0/0/0.',
    'Inventaire : ouvrir Comptage physique puis Valeur du stock ; rechercher chaque article ; vérifier les quantités préremplies et les montants.',
    'Total200 ; réel proposé10 et0 ; aucun diagnostic de source inconnue.',
    controles='Le zéro connu reste0 ; ne pas confondre préremplissage et comptage physique réel.', preuve='Feuille et valorisation200.'),
cas(8,'Inventaire','Simuler un comptage complet de fin2025.', 'INV313-07 réussi.',
    '31/12/2025 ; INV-STOCK-2025 ; M=8 ; Z=0 ; note Comptage fictif313.',
    'Comptage physique : conserver la date31/12/2025 ; saisir8 sur M et0 sur Z ; cliquer Vérifier ; lire aperçu et perte.',
    'ÉcartM−2, perte40, excédent0, impact−40, stock compté160. Simulation sans mutation.',
    controles='Rouvrir Valeur du stock avant validation : stock toujours10, valeur200 ; aucun mouvement ni snapshot ajouté.', preuve='Aperçu et historique avant validation.'),
cas(9,'Inventaire','Valider le comptage et sa photographie.', 'INV313-08 réussi.',
    'Même date, référence et quantités ; confirmation explicite.',
    "Cliquer Valider l’inventaire ; confirmer ; rouvrir les deux articles et l'historique sans F5.",
    'M stock8/CMUP20/valeur160 ; Z0 ; photographie2lignes, total160/perte40 ; une correction supplémentaire de2unités en sortie.',
    'Pas encore de nouvelle écriture comptable tant que la génération stock n’a pas été demandée.',
    controles='Deux mouvements au total pour M : achat10 puis correction2 ; aucune nouvelle entrée après validation.', preuve='Confirmation, historique et photographie.'),
cas(10,'Inventaire','Comptabiliser le stock final.', 'INV313-06/09 réussis ; aucun autre stock ou stock initial comptable dans cette société.',
    'Exercice2025 ; photographie160 ; comptes3111/6114.',
    'Inventaire : Rapprochement comptable ; cliquer Générer l’écriture de stock ; ouvrir le brouillon créé.',
    'Brouillon160/160 lié à2025 ; stock comptable devient160 après validation. Ne pas créer en plus une OD de perte40 : elle compterait deux fois la charge.',
    '3111D160 /6114C160.',
    'Achat200 et variation crédit160 donnent charge nette40 avant impôt ; aucune TVA supplémentaire.',
    'Deux lignes exactes, date31/12/2025, référenceSTOCK-CLOTURE-2025.', 'Brouillon stock.'),
cas(11,'Journal','Valider et rapprocher le stock.', 'INV313-10 réussi.',
    'Le seul nouveau brouillon stock160/160.',
    'Journal : valider le brouillon ; retour Inventaire/Rapprochement comptable ; vérifier la mention Stock rapproché.',
    'Physique160 =comptable brut160 ; dépréciation0 ; écart0 ; écriture stock validée ; quantité8inchangée.',
    controles='Quatre écritures définitives ; neuf lignes ; D=C1640 ; fournisseur0, banque760, stock160, TVA40.', preuve='Écriture définitive et rapprochement.'),
cas(12,'États','Comparer les états aux calculs indépendants.', 'INV313-11 réussi ; aucune autre opération et aucun impôt ajouté.',
    'Banque760 ; stock160 ; TVA40 ; capital1000 ; résultat avant impôt−40.',
    'Lire balance/grand livre ; ouvrir bilan et CPC dans Liasse fiscale ; comparer les comptes aux feuilles Oracle et Écritures attendues.',
    'Actif960 =passif960 ; charges nettes40 ; résultat−40 avant toute écriture fiscale ; aucune créance/dette fournisseur.',
    fiscal='Aucune liquidation IS/CM/CSS revendiquée. Hypothèses fiscales à qualifier dans le cahier annuel.',
    controles='Actif :760+160+40 ; passif :1000−40. Total mouvements1640dechaque côté.', preuve='Balance, bilan et CPC.'),
cas(13,'Exports','Contrôler CSV et PDF du livre.', 'INV313-11 réussi, exercice2025 encore ouvert.',
    'ArticleM8/20/160, articleZ0/0/0 ; total160.',
    'Inventaire/Valeur du stock : Exporter ; ouvrir CSV ; Livre d’inventaire : choisir2025 et Exporter PDF ; lire toutes les lignes stock.',
    'Valeurs160 et0 lisibles dans fichiers ; PDF ouvrable ; stock rapproché. Archive définitive reste indisponible puisque l’exercice est ouvert.',
    controles='Présence des deux articles, dates, montants et quantités ; aucun NaN/Infinity ; ne pas déclarer dossier prêt à déposer.', preuve='CSV/PDF téléchargés et captures.'),
cas(14,'Sécurité','Vérifier le lecteur.', 'Créer un utilisateur Lecture sur la société fictive ; INV313-11 réussi.',
    'lecture-inv313@example.com ; rôleLecture.',
    'Se connecter avec le lecteur ; consulter inventaire/livre ; vérifier que validation et génération ne sont pas accessibles ; revenir comme administrateur.',
    'Lecture autorisée ; aucune mutation autorisée, aucune nouvelle écriture ni photographie.',
    controles='Technique :tentativesPOST avec jeton lecteur403 ; contrôle complémentaire réservé au technicien.', preuve='Écrans lecteur et journal inchangé.'),
cas(15,'Inventaire négatif','Refuser une quantité négative ou non numérique.', 'Copie isolée de la société ; aucun comptage à valider pour ce cas.',
    'Quantité−1 puis texteabc ; aucune valeur finale valide envoyée.',
    'Comptage : tenter−1 puisabc ; Vérifier ; relever le refus ; remettre8 uniquement pour quitter sans valider.',
    'Saisie invalide refusée ; aucune mutation ; stock conserve8. API booléen/NULL/texte refusés422 par tests techniques.',
    controles='Stock, mouvement et photographie identiques avant/après.', preuve='Message de refus et historique.'),
cas(16,'Inventaire négatif','Refuser une photographie annuelle incomplète.', 'Copie isolée ; feuille avec les deux articles stockables.',
    '31/12/2025 ; M=8 ; caseZvide.',
    'Vider la quantité de Z ; tenter Vérifier/Valider ; lire erreur sans confirmer une mutation.',
    'Comptage de clôture incomplet explicitement refusé ; la case vide ne devient pas0.',
    controles='Renseigner0 rend la ligne connue, mais ne valider aucun nouveau comptage pour terminer ce cas.', preuve='Refus articleZ et photographie inchangée.'),
cas(17,'Inventaire historique','Rendre visibles les nombres historiques inconnus.',
    'Technicien : société fictive distincte et cluster nonce vérifié ; préparer article stockNULL, coûtNULL/NaN/Inf/négatif et valeur débordante. Jamais dans le dossier utilisateur.',
    'Jeu technique313 fourni par les tests isolés ; aucun NaN saisi dans un formulaire normal.',
    'Après préparation technique : Inventaire/Comptage puis Valeur du stock ; rechercher les articles signalés ; lire les diagnostics ; exporterCSV.',
    'Sources inconnues et total affichés À vérifier ; quantitéNULL vide ; coût invalide ne devient pas0 ; CSV contient diagnostic et valeur inconnue.',
    controles='Aucun changement de prix/quantité historique ; garder ces anomalies visibles.', preuve='Captures, CSV et photographie technique avant/après.', statut='Bloqué'),
cas(18,'Inventaire historique','Refuser sans mutation comptage/clôture/archivage.',
    'INV313-17 préparé ; exercice2025 ouvert ; capital validé1000 dans la variante technique.',
    'Compter toutes les lignes à0 ; conserver un article source inconnu.',
    'Comptage : observer Vérifier et Valider désactivés ; Rapprochement : génération désactivée ; Clôture : sélection2025, clôture désactivée ; livre/PDF : lire diagnostics et absence d’archivage définitif.',
    'Refus avant mutation ; capital1000 inchangé ; stock total inconnu, rapprochementfalse ; PDF lisible.',
    controles='Technique :simulation400, validation/génération409, clôture400, archivage409 ; archives et écritures définitives inchangées.', preuve='Captures PDF et preuves techniques313.', statut='Bloqué'),
cas(19,'Inventaire historique','Préserver un brouillon en présence d’un ancien snapshotNaN.',
    'Technicien : cluster nonce et photographie historique avec total/CMUPNaN réellement stockable ; brouillon existant.',
    'Ancien stock snapshot incohérent ; aucune réparation autorisée.',
    'Lire Rapprochement et livre ; tenter de générer via contrôle technique authentifié ; comparer le brouillon et ses lignes avant/après.',
    'Lecture diagnostiquée, génération409 ; brouillon conservé ; valeurs figées et archives non réécrites.',
    controles='Comparaison des IDs/lignes et empreintes ; ne pas supprimer pour obtenir un test vert.', preuve='JSON et photographie technique avant/après.', statut='Bloqué'),
]

ENTREES = [
    ('CAP-INV313','2025-01-02','5141','Banque',D('1000'),D('0')),
    ('CAP-INV313','2025-01-02','1111','Capital',D('0'),D('1000')),
    ('ACH-INV313','2025-01-10','6111','Achats de marchandises',D('200'),D('0')),
    ('ACH-INV313','2025-01-10','34552','TVA récupérable sur charges',D('40'),D('0')),
    ('ACH-INV313','2025-01-10','4411','Fournisseur',D('0'),D('240')),
    ('REG-INV313','2025-01-20','4411','Fournisseur',D('240'),D('0')),
    ('REG-INV313','2025-01-20','5141','Banque',D('0'),D('240')),
    ('STOCK-CLOTURE-2025','2025-12-31','3111','Stock de marchandises',D('160'),D('0')),
    ('STOCK-CLOTURE-2025','2025-12-31','6114','Variation des stocks',D('0'),D('160')),
]

def oracle():
    achat=D('10')*D('20'); tva=achat*D('.20'); ttc=achat+tva
    stock=D('8')*D('20'); perte=(D('10')-D('8'))*D('20')
    banque=D('1000')-ttc; resultat=stock-achat
    total_d=sum(e[4] for e in ENTREES); total_c=sum(e[5] for e in ENTREES)
    actif=banque+stock+tva; passif=D('1000')+resultat
    assert actif==passif==D('960') and perte==D('40') and total_d==total_c==D('1640')
    assert len(ENTREES)==9  # Capital2 + achat3 + règlement2 + stock2.
    return {k:str(v) for k,v in {'achat_ht':achat,'tva_laboratoire':tva,'achat_ttc':ttc,
        'stock_avant':achat,'stock_final':stock,'perte_physique':perte,'banque':banque,
        'solde_fournisseur':D('0'),'resultat_avant_impot':resultat,
        'actif':actif,'passif':passif,'total_debits':total_d,'total_credits':total_c}.items()}

LIMITES = ('Cette annexe complète le cahier annuel218cas. Elle ne remplace ni sa recette de clôture '
           'ni une liquidation fiscale. Les19cas utilisateur commencent Non testé (16) ou Bloqué (3), '
           'jamais Réussi. Les148tests et4Edge313 ont été exécutés sur leurs propres fixtures ; '
           'le scénario entier achat→paiement→inventaire de cette annexe n’a pas été exécuté ici. '
           'Aucune conformité réglementaire, recette humaine ou production automatiquement validée. '
           'Ne jamais modifier une écriture définitive pour masquer un écart ; préparer les historiques '
           'inconnus uniquement dans un cluster isolé vérifié. Le technicien ouvre la base de recette, '
           'le testeur suit les actions interface. Ne jamais saisir les valeurs NaN/Inf via SQL réel.')

def construire():
    attendu=oracle()
    texte = ['# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO',
        '', '## Annexe inventaire — 10 octobre2026 — lot317', '', LIMITES, '',
        '## Données exactes', '', *[f'- **{k}** : {v}' for k,v in DONNEES], '',
        '## Oracle indépendant (MAD)', '', *[f'- {k} : {v}' for k,v in attendu.items()], '',
        'Quatre écritures, neuf lignes. Les40MAD de perte physique ne créent pas une OD supplémentaire : achat200 et variation crédit160 produisent déjà la charge nette40.', '']
    for c in CAS:
        texte += [f"## {c['id']} — {c['objectif']}", '']
        for champ,label in [('module','Module'),('prerequis','Prérequis'),('donnees','Données exactes'),
            ('actions','Actions interface'),('attendu','Résultat attendu'),('ecritures','Écritures attendues'),
            ('fiscal','Impact fiscal'),('controles','Contrôles'),('statut','Statut utilisateur'),
            ('resultat_reel','Résultat réel'),('anomalies','Anomalies/observations'),('preuves','Preuves attendues')]:
            texte.append(f"- **{label}** : {c[champ] or 'À renseigner'}")
        texte.append('')
    (DIR/(BASE+'.md')).write_text('\n'.join(texte),encoding='utf-8')
    (DIR/'oracle_inventaire_20261010.json').write_text(json.dumps({
        'societe_fictive':DONNEES[0][1], 'hypotheses':LIMITES,'oracle':attendu,
        'ecritures':[{'reference':r,'date':dt,'compte':co,'libelle':li,'debit':str(d),'credit':str(cr)} for r,dt,co,li,d,cr in ENTREES],
        'cas':CAS},ensure_ascii=False,indent=2),encoding='utf-8')
    excel(attendu)
    pdf(attendu)
    print('Annexe créée :19cas (16Non testé/3Bloqué),4écritures9lignes,oracle1640/1640 et bilan960/960.')

def styliser(ws, largeurs):
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    for c in ws[1]:
        c.fill=PatternFill('solid',fgColor=NAVY); c.font=Font(color='FFFFFF',bold=True)
        c.alignment=Alignment(wrap_text=True,vertical='center')
    ws.row_dimensions[1].height=32
    for i,w in enumerate(largeurs,1): ws.column_dimensions[chr(64+i)].width=w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
        ws.row_dimensions[row[0].row].height=125 if ws.title.startswith('Cas') else 48
    ws.sheet_view.zoomScale=80
    ws.page_setup.orientation='landscape'; ws.page_setup.paperSize=ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0
    ws.sheet_properties.pageSetUpPr.fitToPage=True
    ws.print_title_rows='1:1'

def excel(attendu):
    wb=Workbook(); wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
    syn=wb.active; syn.title='Synthèse'
    syn.append(['Indicateur','Valeur'])
    syn.append(['Cas utilisateur',len(CAS)])
    syn.append(['Réussi','=COUNTIF(\'Cas principal\'!K2:K17,"Réussi")+COUNTIF(\'Cas historiques\'!K2:K4,"Réussi")'])
    syn.append(['Échoué','=COUNTIF(\'Cas principal\'!K2:K17,"Échoué")+COUNTIF(\'Cas historiques\'!K2:K4,"Échoué")'])
    syn.append(['Bloqué','=COUNTIF(\'Cas principal\'!K2:K17,"Bloqué")+COUNTIF(\'Cas historiques\'!K2:K4,"Bloqué")'])
    syn.append(['Non testé','=COUNTIF(\'Cas principal\'!K2:K17,"Non testé")+COUNTIF(\'Cas historiques\'!K2:K4,"Non testé")'])
    syn.append(['Progression réussite','=B3/B2']); syn['B7'].number_format='0.0%'
    syn.append(['Recette humaine','À effectuer ; formules recalculées lors de l’ouverture dans Excel.'])
    syn.append(['Tests313 exécutés','148tests ciblés +4Edge ; source de preuves distincte des statuts utilisateur.'])
    syn.append(['Périmètre',LIMITES]); styliser(syn,[28,100]); syn.row_dimensions[10].height=130
    chart=PieChart(); chart.title='Progression de la recette'
    chart.add_data(Reference(syn,min_col=2,min_row=3,max_row=6),titles_from_data=False)
    chart.set_categories(Reference(syn,min_col=1,min_row=3,max_row=6)); syn.add_chart(chart,'D2')
    headers=['ID','Module','Objectif','Prérequis','Données exactes','Actions détaillées','Résultat attendu',
             'Écritures attendues','Impact fiscal','Contrôles','Statut','Résultat réel','Anomalies / observations','Preuves / captures']
    keys=['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','statut','resultat_reel','anomalies','preuves']
    for nom,cases in [('Cas principal',CAS[:16]),('Cas historiques',CAS[16:])]:
        ws=wb.create_sheet(nom); ws.append(headers)
        for c in cases: ws.append([c[k] for k in keys])
        styliser(ws,[16,20,38,42,45,65,60,40,38,48,16,45,45,40])
        val=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"',allow_blank=False)
        val.errorTitle='Statut de recette'; val.error='Choisir un des quatre statuts.'; val.showErrorMessage=True
        ws.add_data_validation(val); val.add(f'K2:K{ws.max_row}')
    ws=wb.create_sheet('Données'); ws.append(['Champ','Donnée exacte'])
    for row in DONNEES: ws.append(row)
    styliser(ws,[28,110])
    ws=wb.create_sheet('Écritures attendues'); ws.append(['Référence','Date','Compte','Libellé indicatif','Débit','Crédit'])
    for r,dt,co,li,d,cr in ENTREES: ws.append([r,dt,co,li,float(d),float(cr)])
    ws.append(['TOTAL','','','', '=SUM(E2:E10)','=SUM(F2:F10)']); styliser(ws,[26,16,14,38,20,20])
    for row in ws.iter_rows(min_row=2,min_col=5,max_col=6):
        for cell in row: cell.number_format='#,##0.00'
    ws=wb.create_sheet('Oracle'); ws.append(['Contrôle','Valeur attendue indépendante','Valeur réelle','Écart'])
    for k,v in attendu.items():
        ws.append([k,float(D(v)),None,f'=IF(C{ws.max_row+1}="","",C{ws.max_row+1}-B{ws.max_row+1})'])
    styliser(ws,[35,32,30,30]); wb.save(DIR/(BASE+'.xlsx'))

def pdf(attendu):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('Titre',parent=styles['Title'],fontSize=20,leading=26,textColor=colors.HexColor('#'+NAVY)))
    styles.add(ParagraphStyle('Accent',parent=styles['Heading2'],textColor=colors.HexColor('#'+TEAL),spaceAfter=10))
    styles['BodyText'].fontSize=10; styles['BodyText'].leading=14
    doc=SimpleDocTemplate(str(DIR/(BASE+'.pdf')),pagesize=(210*mm,297*mm),
        leftMargin=19*mm,rightMargin=19*mm,topMargin=22*mm,bottomMargin=20*mm,
        title='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO — Annexe inventaire',author='HisabPro')
    flow=[]
    def p(txt,style='BodyText'): return Paragraph(escape(txt),styles[style])
    flow += [Spacer(1,20*mm),p('HISABPRO','Titre'),p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE','Titre'),
        p('Annexe inventaire, clôture et livre','Accent'),p('10 octobre2026 — lot317 — scénario2025 / MAD'),Spacer(1,12*mm),
        p(LIMITES),Spacer(1,10*mm),p('Le parcours commence par un exercice explicitement créé. Chaque test produit une preuve et un résultat réel ; les inconnus ne sont jamais remplacés par zéro.'),PageBreak(),
        p('Données exactes du laboratoire','Titre')]
    for k,v in DONNEES: flow += [p(k,'Accent'),p(v),Spacer(1,3*mm)]
    flow += [PageBreak(),p('Oracle financier indépendant','Titre')]
    for k,v in attendu.items(): flow += [p(k.replace('_',' ')+' : '+v+' MAD'),Spacer(1,2*mm)]
    flow += [Spacer(1,5*mm),p('Quatre écritures / neuf lignes. Achat200 et variation crédit160 donnent charge nette40 : ne pas ajouter une seconde OD de perte40.'),
             Spacer(1,5*mm),p('Le bilan attendu avant impôt est960/960 : banque760 + stock160 + TVA40 = capital1000 − résultat déficitaire40.')]
    rows=[[p('Référence'),p('Compte'),p('Débit'),p('Crédit')]]
    for r,dt,co,li,d,cr in ENTREES: rows.append([p(r),p(co),p(str(d)),p(str(cr))])
    t=Table(rows,colWidths=[78*mm,26*mm,32*mm,32*mm],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCECEF')),
        ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#B5C4CF')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    flow += [Spacer(1,5*mm),t]
    for c in CAS:
        flow += [PageBreak(),p(c['id']+' — '+c['module'],'Accent'),p(c['objectif'],'Titre')]
        for key,label in [('prerequis','Prérequis'),('donnees','Données exactes'),('actions','Actions détaillées'),
                          ('attendu','Résultat attendu'),('ecritures','Écritures attendues'),('fiscal','Impact fiscal'),
                          ('controles','Contrôles'),('preuves','Preuves attendues'),('statut','Statut utilisateur')]:
            flow += [p(label,'Accent'),p(c[key] or 'À renseigner'),Spacer(1,2*mm)]
        flow += [p('Résultat réel / anomalies / preuves : à renseigner dans le classeur.')]
    def pied(canvas,doc):
        canvas.saveState(); canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#'+NAVY))
        canvas.drawString(19*mm,12*mm,'HisabPro • Recette fictive isolée • 10 octobre2026')
        canvas.drawRightString(191*mm,12*mm,f'Page{doc.page}'); canvas.restoreState()
    doc.build(flow,onFirstPage=pied,onLaterPages=pied)

if __name__=='__main__': construire()
