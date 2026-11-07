"""Recette capture RAS déclarative ; Decimal autonome, sans connexion applicative."""
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

DEST=Path(__file__).resolve().parents[1]/'docs/recette'
NOM='ANNEXE_RECETTE_RAS_CAPTURE_20261010'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
INTRO=('Annexe autonome : capture explicite, validation, lettrage et annulation d’une retenue déclarée. '
       'Deux cas utilisateur Non testé, dans deux sociétés fictives neuves et indépendantes. '
       'Installation de recette isolée exclusivement. TVA 20 %, RAS estimée 10 %, montants 30/70 et comptes 3453/4457 '
       'sont des choix de laboratoire : aucune obligation ni qualification fiscale automatique, attestation ou crédit IS certifié.')
SOURCES=['docs/MISE_A_JOUR_RAS_20261009.md','hisabpro-backend/083_ras_reglements.sql',
    'src/pages/Commercial.jsx','src/pages/Factures.jsx','src/pages/Lettrage.jsx',
    'Test/test_e2e_ras_capture_isole.py','Test/test_ras_capture_reglement_postgres.py',
    'Test/test_sauvegarde_ras_reglements_isole.py','Test/rapport_sources_ras_20261009.md']
JEU={
    'Activation préalable': 'Administrateur d’une copie isolée : suivre le guide MISE_A_JOUR_RAS_20261009.md. Migration 083 manuelle avec le rôle de migration, jamais sur une base réelle dans cette recette. Le lecteur utilisateur n’a pas à exécuter SQL : demander une installation de recette prête. Sans 083, message d’indisponibilité attendu, noter Bloqué sans contourner ni forcer une capture.',
    'Date exacte du parcours': 'D = date réelle du jour d’exécution de la recette, à noter dans les observations avant de commencer ; exemple 10/10/2026. E = année de D, exemple 2026. Saisir D pour la facture, chacun des deux virements et chacune des deux captures. L’annulation par bouton utilise également le jour courant. Réaliser tout le cas le même jour ; sinon noter Bloqué et préparer des dates cohérentes avant de reprendre, sans réécrire de pièce définitive.',
    'Société vente': 'Créer ANNEXE CAPTURE VENTE FICTIVE 306 suivant Administration → Sociétés du cahier principal. Exercice E ouvert, du 01/01/E au 31/12/E, aucun autre mouvement ni lettrage. Créer CLIENT CAPTURE 306, compte client 3421. Aucun identifiant fiscal officiel à inventer.',
    'Société achat': 'Créer séparément ANNEXE CAPTURE ACHAT FICTIVE 306, même exercice E ouvert et vierge. Créer FOURNISSEUR CAPTURE 306, compte fournisseur 4411. Ne pas réutiliser la société vente.',
    'Facture': 'Date D ; une ligne Service laboratoire capture 306, quantité 1, prix unitaire HT 1 000, TVA 20 %, Taxable. Vente : compte produit 7111. Achat : N° facture fournisseur ACH-CAP306-001, compte 6111, qualification Charge / achat courant, TVA déductible (%) 100. RAS (sur HT) 10 % explicite : estimation 100, net estimé 1 100. Remises, emballage, transport et acomptes zéro.',
    'Premier virement et capture': 'Virement 400, date D, référence VIR-CAP306-400, Banque vide. Capture : Montant RAS * 30, Date de l’opération RAS * D, Référence RAS * PIECE-CAP306-30, Compte destination RAS * 3453 en vente / 4457 en achat. Aucune valeur de montant, référence ou compte préremplie ne doit être inventée.',
    'Second virement et capture': 'Virement 700, date D, référence VIR-CAP306-700, Banque vide. Capture 70, date D, référence PIECE-CAP306-70, même compte destination. Les montants déclarés sont saisis indépendamment : ni taux ni prorata automatique.',
    'Comptes et trésorerie': 'Virement comptabilisé automatiquement en 5141 dans ces sociétés neuves. Vérifier ce compte ; sinon Bloqué et noter la configuration plutôt que changer l’oracle. Aucun apport initial : après annulation, banque +400 en vente ou −400 en achat. Comptes 3453/4457 actifs choisis uniquement pour le laboratoire, pas imposés fiscalement.',
    'Limites et sécurité': 'Flux actuel limité aux virements et espèces immédiats déjà comptabilisés, sur facture validée non proforma et non annulée. Pas de mélange avec un historique déjà marqué RAS comptabilisée. Aucune attestation fiscale ni transfert automatique vers crédits IS. Si À vérifier apparaît, conserver le diagnostic et noter Bloqué ; aucun SQL, NaN, réparation de données ou modification d’écriture définitive n’est demandé au lecteur.',
    'Preuves et comparaison': 'Noter numéros des factures, règlements, OD et contrepassations réellement attribués, et D/E. Exporter le Journal avant/après. Le délettrage change volontairement le code de lettrage ; il ne change pas les montants, comptes, dates, références ou numéros des écritures originales. Ne pas comparer le maintien de AAA après avoir demandé son délettrage.',
}
COLONNES=dict(zip(
    ['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','statut','resultat_reel','anomalies','preuves','observations','sources','preuves_attendues'],
    ['Identifiant','Module','Objectif','Prérequis','Données à saisir','Actions détaillées','Résultat attendu','Écritures attendues','Impacts fiscaux','Contrôles','Statut','Résultat réel','Anomalies','Preuves/captures','Observations','Sources','Preuves attendues']))


def oracle():
    ht=Decimal('1000'); tva=ht*Decimal('20')/100; ttc=ht+tva
    cash1=Decimal('400'); ras1=Decimal('30'); cash2=Decimal('700'); ras2=Decimal('70')
    base=ttc+cash1+ras1+cash2+ras2; final=base+cash2+ras2
    return {'ht':ht,'tva':tva,'ttc':ttc,'ras_estimee':ht*Decimal('10')/100,
        'cash1':cash1,'reste_apres_cash1':ttc-cash1,'ras1':ras1,'reste_apres_capture1':ttc-cash1-ras1,
        'cash2':cash2,'reste_apres_cash2':ttc-cash1-ras1-cash2,'ras2':ras2,
        'reste_solde':ttc-cash1-ras1-cash2-ras2,'total_debit_solde':base,'total_credit_solde':base,
        'reste_apres_annulation':ttc-cash1-ras1,'ras_active':ras1,
        'total_debit_final':final,'total_credit_final':final,
        'banque_vente':cash1,'banque_achat':-cash1,'retenue_vente':ras1,'retenue_achat':-ras1,
        'collectif_vente':ttc-cash1-ras1,'collectif_achat':-(ttc-cash1-ras1)}


ORACLE_LABELS=dict(zip(
    list(oracle()), ['Montant HT','TVA documentaire','Total TTC','RAS estimée','Premier virement','Reste après premier virement','Première capture déclarée','Reste après première capture','Deuxième virement','Reste après deuxième virement','Deuxième capture déclarée','Reste soldé','Total débit avant annulation','Total crédit avant annulation','Reste après annulation','Retenue active après annulation','Total débit final','Total crédit final','Banque — vente','Banque — achat','Retenue — vente','Retenue — achat','Client final','Fournisseur final']))


def cas():
    items=[]
    for sens in ('vente','achat'):
        vente=sens=='vente'; tiers='CLIENT CAPTURE 306' if vente else 'FOURNISSEUR CAPTURE 306'
        collectif='3421' if vente else '4411'; destination='3453' if vente else '4457'
        payer='Encaisser le client' if vente else 'Payer le fournisseur'
        invoice='D3421=1 200, C7111=1 000, C4455=200' if vente else 'D6111=1 000, D34552=200, C4411=1 200'
        cash='D5141/C3421' if vente else 'D4411/C5141'
        ras='D3453/C3421' if vente else 'D4411/C4457'
        inverse='D3421/C5141=700 et D3421/C3453=70' if vente else 'D5141/C4411=700 et D4457/C4411=70'
        items.append(dict(id='CAP-306-01' if vente else 'CAP-306-02',module='Recouvrement',objectif='Capture déclarative et annulation traçable — '+sens,
            prerequis='Installation isolée activée 083 ; société '+sens+' vierge du Jeu, exercice E ouvert, tiers '+tiers+' créé, comptes actifs. Même jour D pendant tout le cas.',
            donnees='Facture 1 000 HT +200 TVA =1 200 TTC ; virements 400/700 ; captures déclarées 30/70, références et comptes explicites du Jeu. Compte destination '+destination+'.',
            actions=[
                'Sélectionner ANNEXE CAPTURE '+sens.upper()+' FICTIVE 306 et E. Factures → '+('Ventes' if vente else 'Achats')+' → Nouvelle facture. Sélectionner '+tiers+' dans les propositions ; saisir D et la ligne du Jeu. '+('' if vente else 'N° facture fournisseur ACH-CAP306-001, compte 6111, Charge / achat courant et déductible 100 %. ')+'Choisir RAS (sur HT) 10 %. Enregistrer en brouillon, vérifier HT 1 000/TVA 200/TTC 1 200, puis Valider définitivement et Générer l’écriture comptable. Journal : contrôler et Valider cette première écriture uniquement. Noter son numéro ; reste dû 1 200, estimation seule non imputée.',
                'Facture : '+payer+'. Date D, Montant * 400, Mode Virement, référence VIR-CAP306-400, Banque vide. Enregistrer : une écriture de trésorerie en brouillon est produite. Avant capture, reste dû 800. Ne pas valider d’autres écritures à ce stade.',
                'Cycle commercial → '+('Vente' if vente else 'Achat')+' → Règlements. Sur la ligne du virement 400, bouton avec infobulle Consulter ou déclarer la RAS. Vérifier montant/référence/compte vides ; saisir Montant RAS * 30, confirmer Date de l’opération RAS * D, Référence RAS * PIECE-CAP306-30, sélectionner Compte destination RAS * '+destination+'. Cliquer Préparer la RAS déclarée. Vérifier reste dû 770. Rouvrir ce bouton : capture visible, À contrôler et à valider, aucun nouveau bouton de préparation pour ce même règlement ; Fermer. La référence de laboratoire n’est pas une attestation fiscale.',
                'Revenir à la même facture : '+payer+'. Date D, Montant * 700, Virement, référence VIR-CAP306-700, Banque vide ; Enregistrer. Reste avant capture 70. Cycle commercial → Règlements : sur la ligne 700, Consulter ou déclarer la RAS ; saisir montant 70, date D, référence PIECE-CAP306-70, compte '+destination+' ; Préparer la RAS déclarée. Vérifier facture soldée, reste 0, RAS déclarée totale 100. Ce total vient des deux saisies, pas d’une certification du taux estimé.',
                'Journal : quatre brouillons nouveaux attendus, deux virements et deux OD déclaratives. Contrôler chacun, notamment les comptes, références, auxiliaires et montants 400/30/700/70. Cliquer Valider les brouillons et confirmer les quatre seulement dans cette société vierge. Cinq écritures définitives, onze lignes, total débit = crédit 2 400. Exporter CSV et conserver comme comparaison avant annulation.',
                'Comptabilité → Lettrage : Compte '+('Clients (3421)' if vente else 'Fournisseurs (4411)')+', Tiers '+tiers+', exercice E. Cocher cinq lignes : '+('débit facture 1 200, crédits 400/30/700/70' if vente else 'crédit facture 1 200, débits 400/30/700/70')+'. Débit = crédit 1 200 ; Lettrer 5 lignes. Vérifier 5 lettrée(s) et AAA dans cette société neuve. Noter le code réellement attribué ; si l’action manque ou les lignes ne concordent pas, Bloqué et capture sans forcer.',
                'Avant l’annulation, utiliser le bouton infobulle Délettrer le code AAA (ou le code réellement attribué), puis accepter la confirmation native du navigateur. Vérifier les cinq lignes délettrées. Cette action est volontaire et tracée ; conserver les preuves. Ne pas essayer de supprimer ou réécrire les écritures originales pour annuler un règlement.',
                'Cycle commercial → '+('Vente' if vente else 'Achat')+' → Règlements : sur le virement 700 uniquement, cliquer Annuler par contrepassation et accepter la confirmation native. Vérifier règlement annulé. Consulter ou déclarer la RAS de cette ligne : Annulée par contrepassation et capture originale conservée. Fermer. Le virement 400 et sa capture 30 restent actifs. Facture : reste dû 770, RAS déclarée active 30 ; aucune nouvelle capture automatique.',
                'Journal : deux contrepassations nouvelles en brouillon, trésorerie 700 et RAS 70. Contrôler puis Valider ces deux écritures. Comparer exports et Grand livre : sept écritures, quinze lignes, total débit = crédit 3 170. Banque '+('+400' if vente else '−400')+', compte '+destination+' '+('+30' if vente else '−30')+', collectif '+collectif+' '+('+770' if vente else '−770')+'. Vérifier les cinq écritures originales identiques en montants/comptes/dates/références/numéros ; seul le lettrage a été volontairement retiré. Aucun nouveau lettrage à inventer après l’annulation.'
            ],
            attendu='400+30 → reste 770 ; 700+70 → reste 0 ; cinq écritures/onze lignes D=C 2 400 ; cinq lignes lettrées AAA puis délettrées volontairement. Annulation du second règlement et de sa capture → reste 770, capture active 30 ; sept écritures/quinze lignes D=C 3 170. Originaux conservés.',
            ecritures='Facture : '+invoice+'. Virements : '+cash+' pour 400 puis 700. OD déclaratives : '+ras+' pour 30 puis 70. Annulation : '+inverse+'. Après annulation : banque '+('+400' if vente else '−400')+', retenue '+('+30' if vente else '−30')+', collectif '+('+770' if vente else '−770')+'. Avant/après : D=C 2 400 puis 3 170.',
            fiscal='Saisies explicites de laboratoire, comptes et TVA sans qualification obligatoire. RAS estimée distincte des captures. Aucune attestation fiscale authentifiée, déclaration, prorata légal automatique ni crédit IS généré.',
            controles='Mode immédiat comptabilisé, date D explicite et période ouverte ; vrais liens règlement/facture/OD, compte choisi, cinq puis sept écritures équilibrées, auxiliaire tiers, validation, AAA et délettrage. Capture annulée conservée avec son inverse ; aucun montant inconnu remplacé par zéro.',
            statut='Non testé',resultat_reel='',anomalies='',preuves='',observations='',sources=' ; '.join(SOURCES),
            preuves_attendues='Installation isolée/activation, données D/E, facture, deux virements, captures avec montant/date/référence/compte, solde 770/0/770, OD brouillon puis définitive, cinq lignes AAA puis délettrées, confirmation annulation, deux inverses, CSV avant/après et Grand livre. Inscrire les preuves réellement produites dans Preuves/captures.'))
    return items


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
    synth.append(['Recouvrement',len(items),*[f'=COUNTIF(Recouvrement!K2:K3,"{s}")' for s in ('Réussi','Échoué','Bloqué','Non testé')],'=IF(B4=0,0,(C4+D4)/B4)'])
    synth['G4'].number_format='0%'
    ws=wb.create_sheet('Recouvrement'); ws.append(list(COLONNES.values()))
    for item in items: ws.append(['\n'.join(item[k]) if isinstance(item[k],list) else item[k] for k in COLONNES])
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"'); ws.add_data_validation(dv); dv.add('K2:K3')
    jeu=wb.create_sheet('Jeu de données'); jeu.append(['Champ','Valeur fictive exacte'])
    for k,v in JEU.items(): jeu.append([k,v])
    for k,v in oracle().items(): jeu.append(['Oracle '+ORACLE_LABELS[k],v])
    for sheet in wb:
        for cell in sheet[1]: cell.font=Font(bold=True,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='183D35')
        for row in sheet:
            for cell in row: cell.alignment=Alignment(vertical='top',wrap_text=True)
        for col in sheet.columns: sheet.column_dimensions[col[0].column_letter].width=36
    ws.column_dimensions['F'].width=95; ws.column_dimensions['H'].width=75
    wb.save(destination/(NOM+'.xlsx'))
    styles=getSampleStyleSheet(); styles['Heading3'].keepWithNext=True
    styles['BodyText'].fontSize=10; styles['BodyText'].leading=14
    styles['BodyText'].allowWidows=False
    story=[Paragraph(escape(TITRE),styles['Title']),Paragraph('Capture déclarative et annulation traçable',styles['Heading1']),Paragraph(escape(INTRO),styles['BodyText'])]
    for k,v in JEU.items(): story.extend([Paragraph(escape(k),styles['Heading3']),Paragraph(escape(v),styles['BodyText'])])
    story.append(Paragraph('Oracle indépendant — résultats attendus',styles['Heading2']))
    for k,v in oracle().items(): story.append(Paragraph(escape(ORACLE_LABELS[k])+' : '+str(v)+' MAD',styles['BodyText']))
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
        canvas.drawString(42,28,'HisabPro — Recette utilisateur à effectuer — CAP306')
        canvas.drawRightString(A4[0]-42,28,str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(destination/(NOM+'.pdf')),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=42,title=TITRE+' — Capture déclarative et annulation traçable').build(story,onFirstPage=pied,onLaterPages=pied)
    md=['# '+TITRE,'','## Capture déclarative et annulation traçable','',INTRO,'','## Jeu de données','']
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
    generer(); print('Deux cas capture Non testé générés PDF/XLSX/MD ; aucune base utilisée.')
