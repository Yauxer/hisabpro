"""Annexe utilisateur autonome ; oracles Decimal, aucune connexion applicative."""
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

DEST = Path(__file__).resolve().parents[1] / 'docs/recette'
NOM = 'ANNEXE_RECETTE_ACHATS_PARTIELS_20261009'
TITRE = 'CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
INTRO = ('Annexe autonome : achats reçus en deux parties, facturation, règlements et lettrage. '
         'Deux cas utilisateur Non testé, même si des tests développeur existent. '
         'Exécuter exclusivement dans une installation de recette isolée et une société fictive neuve, '
         'sans ajouter ces mouvements au scénario annuel. Aucun dépôt, droit fiscal, certification '
         'ou conformité réglementaire ne sont validés automatiquement.')
SOURCES = ['src/pages/Commercial.jsx', 'src/pages/Factures.jsx', 'src/pages/Lettrage.jsx',
           'src/pages/Parametres.jsx', 'Test/test_e2e_cycle_achat_reception_partielle_isole.py']
JEU = {
    'Installation': 'Administrateur dans une installation de recette isolée contenant les lots 275, 280 et 283. Si un champ ou une action requis manque, noter Bloqué et la version. Ne pas utiliser la société réelle ni son compte bancaire réel.',
    'Société et exercice': 'Créer ANNEXE ACHATS PARTIELS FICTIVE suivant Administration → Sociétés du cahier principal. Exercice 2026 ouvert, 01/01/2026–31/12/2026. Aucun ICE/IF ou justificatif réel à inventer. Activer Facturation et Comptabilité si nécessaire. Sélectionner cette société et cet exercice.',
    'Stock': 'Paramètres → Fiche société → Gestion du stock : Achats — entrée de stock = À la réception — BR passé en « livré ». Enregistrer. Ne pas conserver le réglage À la facturation pour ce scénario.',
    'Fournisseur': 'Clients / Fournisseurs → Nouveau tiers : nom FOURNISSEUR PARTIEL 284, type Fournisseur, délai de paiement 30 jours ; paramétrage comptable compte fournisseur 4411. Laisser identifiants et taux RAS non renseignés ; pas de retenue dans ce laboratoire. Enregistrer.',
    'Article': 'Articles → Nouvel article : code REC284-STOCK, désignation Marchandise partielle fictive, unité unité, article stockable, stock initial 0, prix achat HT 500, prix vente HT 700, TVA proposée 20 %, compte achat 6111. Emballage, transport, remises et autres frais zéro. Enregistrer.',
    'Dates et références': 'BC 15/03/2026 ; BR1 16/03/2026, BR2 18/03/2026 ; factures fournisseur FR284-001 du 16/03/2026 et FR284-002 du 18/03/2026 ; règlements par virement 20/03/2026 et 21/03/2026, références VIR284-001/VIR284-002. Noter les numéros internes réellement attribués, sans les deviner.',
    'Qualification choisie': 'TVA 20 %, qualification de ligne Taxable ; qualification TVA de l’achat Charge / achat courant, déductible 100 %. Ce sont des données explicites de laboratoire, sans nouvelle affirmation légale du droit à déduction. Pas de RAS, avoir, remise, escompte ou acompte dans ce scénario.',
    'Banque': 'Le parcours Payer le fournisseur propose Mode et Banque, sans champ de compte comptable ni option de comptabilisation. Dans cette société vierge, laisser Banque vide et utiliser le virement proposé ; vérifier ensuite que l’écriture automatique utilise 5141. Si un autre compte apparaît, noter Bloqué et son paramétrage au lieu de modifier l’oracle. Aucun apport initial prévu : solde comptable final crédit 2 400, soit −2 400. Ce solde fictif ne représente pas une banque réelle ni une trésorerie financée.',
    'Traçabilité': 'Consigner numéros BC, BR1, BR2, factures et quatre écritures dans les observations. Conserver captures et exports avant/après. Ne pas modifier une écriture validée. Les photos techniques DB des tests développeur ne sont pas exigées d’un utilisateur non développeur.',
}
COLONNES = dict(zip(
    ['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','statut','resultat_reel','anomalies','preuves','observations','sources'],
    ['Identifiant','Module','Objectif','Prérequis','Données à saisir','Actions détaillées','Résultat attendu','Écritures attendues','Impacts fiscaux','Contrôles','Statut','Résultat réel','Anomalies','Preuves/captures','Observations','Sources']))


def oracle():
    pu, taux = Decimal('500'), Decimal('20')/100
    quantites = [Decimal('1'), Decimal('3')]
    ht = [q*pu for q in quantites]; tva = [h*taux for h in ht]
    ttc = [h+v for h,v in zip(ht,tva)]
    return {'quantite_br1':quantites[0], 'quantite_br2':quantites[1],
            'ht_facture1':ht[0], 'ht_facture2':ht[1], 'tva_facture1':tva[0], 'tva_facture2':tva[1],
            'ttc_facture1':ttc[0], 'ttc_facture2':ttc[1], 'stock_final':sum(quantites),
            'solde_6111':sum(ht), 'solde_34552':sum(tva),
            'solde_4411':sum(ttc)-sum(ttc), 'solde_5141':-sum(ttc),
            'total_debit':sum(ttc)+sum(ttc), 'total_credit':sum(ttc)+sum(ttc)}


def cas():
    base = dict(module='Achats', fiscal='TVA documentaire totale 400, choisie déductible 100 % pour ce laboratoire. Aucun dépôt TVA ni validation réglementaire.',
        statut='Non testé', resultat_reel='', anomalies='', observations='', sources=' ; '.join(SOURCES))
    return [dict(base, id='ACH-284-01', objectif='Recevoir en deux parties, payer et lettrer le même fournisseur',
        prerequis='Installation isolée ; réaliser toutes les préparations du Jeu de données ci-dessus. Société neuve sans autre facture, règlement ou écriture. Exercice 2026 ouvert.',
        donnees='Une commande de 4 unités à 500 HT, TVA 20 %. BR1 : 1 unité ; BR2 : 3 unités. FR284-001 : 600 TTC ; FR284-002 : 1 800 TTC. VIR284-001 : 600 ; VIR284-002 : 1 800. Dates et comptes : voir Jeu de données.',
        actions=[
            'Cycle commercial → Achat → Bons de commande → Nouveau BC. Type Achat ; date 15/03/2026 ; sélectionner FOURNISSEUR PARTIEL 284 depuis les propositions, pas seulement son texte. Ajouter REC284-STOCK depuis les articles proposés, quantité 4, prix HT 500, TVA 20 %, Taxable. Créer la commande. Noter son numéro ; HT 2 000 / TVA 400 / TTC 2 400 ; stock 0.',
            'Sur le BC, Réceptionner (infobulle Créer un bon de réception sur le reliquat). Nouveau bon de réception : date 16/03/2026 ; quantité proposée 4, remplacer par 1 ; Créer le bon de réception. Noter BR1. Bons de réception : ligne BR1, Marquer en cours puis Marquer réceptionné. Vérifier article stock 1, une seule entrée 1 et BC reste 3. Un BR seulement préparé ne doit pas déjà augmenter le stock.',
            'Sur BR1 réceptionné, Facturer. Quantité 1 ; Créer la facture en brouillon. Dans Factures → Achats, ouvrir Modifier le brouillon correspondant. N° facture fournisseur FR284-001, date 16/03/2026. Qualification TVA de l’achat Charge / achat courant ; TVA déductible (%) 100 ; enregistrer puis rouvrir pour vérifier. Valider définitivement, puis Générer l’écriture comptable de cette facture. Journal : contrôler et Valider son écriture. Noter numéros facture/écriture ; stock reste 1.',
            'Revenir au même BC et Réceptionner. Quantité proposée 3 ; date 18/03/2026 ; recevoir 3. Sur BR2, Marquer en cours puis Marquer réceptionné. Stock 4 ; exactement deux entrées 1 et 3 ; BC reste 0. Facturer BR2, quantité 3. Modifier ce nouveau brouillon : FR284-002, date 18/03/2026, Charge / achat courant et déductible 100. Enregistrer, vérifier, Valider définitivement, Générer son écriture et la Valider dans Journal. Stock reste 4 ; première facture/écriture inchangée.',
            'Factures → Achats : FR284-001, Payer le fournisseur. Date 20/03/2026, montant 600, mode Virement, référence VIR284-001 ; laisser Banque vide dans ce laboratoire. Enregistrer : le règlement génère son écriture automatiquement. Répéter sur FR284-002 : date 21/03/2026, montant 1 800, Virement, référence VIR284-002, Banque vide. Vérifier chacune Payée et reste 0. Journal : contrôler les deux nouvelles écritures, notamment contrepartie 5141, puis Valider les brouillons de règlement uniquement (deux si aucun autre brouillon).',
            'Comptabilité → Lettrage. Exercice 2026, Compte Fournisseurs (4411), Tiers FOURNISSEUR PARTIEL 284. Cocher les quatre lignes : crédits 600 et 1 800 des factures, débits 600 et 1 800 des virements. Total sélection débit = crédit 2 400 ; Lettrer 4 lignes. Noter le code commun de trois lettres attribué (AAA attendu si aucun lettrage antérieur dans la société neuve). Vérifier le compteur 4 lettrée(s), solde 0. Recharger puis sélectionner à nouveau compte/tiers : code et lignes conservés.',
            'Comparer Journal, Grand livre comptes 6111/34552/4411/5141 et Stocks. Cycle commercial → Achat → Factures contient les deux factures ; BR1 etBR2 gardent leur lien à chacune. Exporter Journal CSV ou balances Excel/PDF et conserver les preuves. Aucun troisième mouvement stock ni nouvelle facture après rechargement.'
        ],
        attendu='Un BC, deux BR de 1/3, deux factures payées 600/1 800, deux virements 600/1 800 ; quatre écritures définitives, dix lignes. Exactement deux entrées de stock, stock final 4. Fournisseur soldé et quatre lignes 4411 lettrées sous un code commun. Chaque document conserve son lien source ; pas de double entrée à la validation facture.',
        ecritures='Facture 1 : D6111=500, D34552=100, C4411=600. Facture 2 : D6111=1 500, D34552=300, C4411=1 800. Règlement 1 : D4411=600, C5141=600. Règlement 2 : D4411=1 800, C5141=1 800. Chaque écriture équilibrée ; cumul D = C 4 800. Soldes D − C : 6111 = 2 000, 34552 = 400, 4411 = 0, 5141 = −2 400. Quatre lignes fournisseur rattachées au vrai tiers/auxiliaire.',
        controles='Comparer les montants à l’oracle indépendant, les numéros, quantités et sources. Vérifier toutes les écritures validées, quatre lignes lettrées et aucune troisième entrée. Aucun apport initial fictif à ajouter pour changer le solde banque attendu.',
        preuves='Captures réglage stock, BC/reliquats 3 puis 0, BR1/BR2, stock 0/1/4, qualification 100 %, deux factures Payées, deux virements, quatre écritures, lettrage quatre lignes et exports ouverts.'),
        dict(base,id='ACH-284-02', objectif='Empêcher la reconversion et préserver les pièces définitives',
        prerequis='ACH-284-01 effectué dans la même société ; conserver ses captures/exports avant essai. Ne pas créer un autre dossier pour ce cas négatif.',
        donnees='Même BC épuisé, BR1 etBR2 déjà facturés ; FR284-001/002 déjà validées, comptabilisées et payées ; mêmes dix lignes et deux mouvements stock.',
        actions=[
            'Cycle commercial → Achat → Bons de commande : sur le même BC tenter Réceptionner si disponible. Constater reliquat 0 et impossibilité de créer un nouveau BR ; si action indisponible, conserver la capture. Ne pas saisir une autre commande.',
            'Bons de réception : sur chacun des BR déjà facturés, tenter Facturer si disponible. Une quantité restante 0 ou un refus clair empêche une nouvelle facture. Si l’action est masquée/désactivée, noter ce comportement et capturer ; ne pas utiliser API/SQL ou outils développeur pour forcer une conversion.',
            'Factures → Achats : ouvrir les deux pièces. Vérifier absence de Modifier le brouillon et de Générer l’écriture déjà produite, ou refus explicite si une action reste proposée. Ne pas annuler, contrepasser, délettrer ou faire appel à une intervention admin sur une pièce définitive.',
            'Recharger Cycle commercial, Factures, Stocks et Lettrage ; rouvrir les exports. Comparer au cas 01 : un BC/deux BR/deux factures/deux règlements/quatre écritures/dix lignes, stock 4, deux entrées et code commun des quatre lignes inchangés. Une action empêchée est un résultat attendu ; une pièce créée/modifiée est une anomalie à consigner.'
        ],
        attendu='Aucune reconversion ni édition de brouillon définitif. Bouton indisponible ou refus compréhensible selon l’état de l’interface. Tous les totaux, documents, dates, montants, liens et code de lettrage du cas 01 sont conservés.',
        ecritures='Aucune écriture supplémentaire ou réécriture. Les quatre écritures/dix lignes du cas 01 restent identiques : cumul D = C 4 800, fournisseur 0, banque −2 400.',
        controles='Avant/après : nombres de pièces et mouvements, stock 4, auxiliaire fournisseur, montants et code. Les refus HTTP409/400 sont contrôlés par les tests développeur, sans les exiger du lecteur utilisateur.',
        preuves='Captures boutons absents/désactivés ou message de refus, liste des pièces et stock ; exports et lettrage avant/après.')]


def generer(destination=DEST):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    items=cas(); wb=Workbook(); synth=wb.active; synth.title='Synthèse'
    synth.append([TITRE]); synth.append([INTRO]); synth.append(['Domaine','Cas','Réussis','Échoués','Bloqués','Non testé','Progression'])
    synth.append(['Achats',len(items),*[f'=COUNTIF(Achats!K2:K3,"{s}")' for s in ('Réussi','Échoué','Bloqué','Non testé')],'=IF(B4=0,0,(C4+D4)/B4)'])
    synth['G4'].number_format='0%'
    ws=wb.create_sheet('Achats'); ws.append(list(COLONNES.values()))
    for item in items: ws.append(['\n'.join(item[k]) if isinstance(item[k],list) else item[k] for k in COLONNES])
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"'); ws.add_data_validation(dv); dv.add('K2:K3')
    jeu=wb.create_sheet('Jeu de données'); jeu.append(['Champ','Valeur fictive exacte'])
    for k,v in JEU.items(): jeu.append([k,v])
    for k,v in oracle().items(): jeu.append(['Oracle '+k,v])
    for sheet in wb:
        for cell in sheet[1]: cell.font=Font(bold=True,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='183D35')
        for row in sheet:
            for cell in row: cell.alignment=Alignment(vertical='top',wrap_text=True)
        for col in sheet.columns: sheet.column_dimensions[col[0].column_letter].width=36
    ws.column_dimensions['F'].width=95; ws.column_dimensions['H'].width=75
    wb.save(destination/(NOM+'.xlsx'))
    styles=getSampleStyleSheet(); styles['Heading3'].keepWithNext=True
    styles['BodyText'].fontSize=10; styles['BodyText'].leading=14
    story=[Paragraph(escape(TITRE),styles['Title']),Paragraph('Achats en deux réceptions',styles['Heading1']),Paragraph(escape(INTRO),styles['BodyText'])]
    for k,v in JEU.items(): story.extend([Paragraph(escape(k),styles['Heading3']),Paragraph(escape(v),styles['BodyText'])])
    story.append(Paragraph('Oracle indépendant — résultats attendus',styles['Heading2']))
    for k,v in oracle().items(): story.append(Paragraph(escape(k)+' : '+str(v),styles['BodyText']))
    for item in items:
        story.extend([PageBreak(),Paragraph(item['id']+' — '+escape(item['objectif']),styles['Heading1'])])
        for k,v in item.items():
            if k in ('id','objectif'): continue
            story.append(Paragraph(escape(COLONNES[k]),styles['Heading3']))
            if isinstance(v,list):
                for n,action in enumerate(v,1): story.extend([Paragraph(f'{n}. '+escape(action),styles['BodyText']),Spacer(1,7)])
            else: story.append(Paragraph(escape(v or 'À renseigner pendant la recette.'),styles['BodyText']))
    def pied(canvas,doc):
        canvas.saveState(); canvas.setFont('Helvetica',8)
        canvas.drawString(42,28,'HisabPro — Recette utilisateur à effectuer — ACH284')
        canvas.drawRightString(A4[0]-42,28,str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(destination/(NOM+'.pdf')),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=42,title=TITRE+' — Achats partiels').build(story,onFirstPage=pied,onLaterPages=pied)
    md=['# '+TITRE,'','## Achats en deux réceptions','',INTRO,'','## Jeu de données','']
    md.extend(f'- **{k}** : {v}' for k,v in JEU.items()); md.extend(['','## Oracle indépendant',''])
    md.extend(f'- `{k}` : {v}' for k,v in oracle().items())
    for item in items:
        md.extend(['','## '+item['id']+' — '+item['objectif'],''])
        for k,v in item.items():
            if k in ('id','objectif','sources'): continue
            md.append('**'+COLONNES[k]+'** :')
            if isinstance(v,list): md.extend(['']+[f'{i}. {a}' for i,a in enumerate(v,1)]+[''])
            else: md.extend([v or 'À renseigner pendant la recette.',''])
        md.append('**Sources de mise en œuvre** : '+', '.join(f'[{p}](../../{p})' for p in SOURCES))
    (destination/(NOM+'.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')
    return items


if __name__=='__main__':
    generer(); print('Deux cas Non testé générés PDF/XLSX/MD ; aucune base utilisée.')
