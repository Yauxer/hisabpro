"""Annexe RAS documentaire : deux parcours utilisateurs, Decimal indépendant, sans DB."""
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

DEST = Path(__file__).resolve().parents[1] / 'docs/recette'
NOM = 'ANNEXE_RECETTE_RAS_ESTIMATION_20261009'
TITRE = 'CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
INTRO = ('Annexe autonome : distinguer RAS estimée et règlement réellement enregistré. Deux cas Non testé, '
         'dans deux sociétés fictives neuves et indépendantes, exclusivement sur une installation de recette isolée. '
         'Les choix TVA 20 % et RAS 10 % sont des données de laboratoire, sans affirmation de leur applicabilité légale. '
         'Aucune attestation, déclaration fiscale, certification ou recette utilisateur n’est validée automatiquement.')
SOURCES = ['src/pages/Factures.jsx', 'src/pages/Lettrage.jsx', 'src/pages/SituationFinanciere.jsx',
           'Test/test_e2e_ras_situation_isole.py', 'Test/test_ras_estimation_solde_postgres.py',
           'Test/test_e2e_ras_solde_lettrage_isole.py', 'Test/rapport_e2e_ras_solde_lettrage.md',
           'Test/rapport_sources_ras_20261009.md']
JEU = {
    'Installation': 'Administrateur, Facturation et Comptabilité disponibles, lots 291 et 292 intégrés. Si une action requise manque, noter Bloqué et la version ; ne pas utiliser une société ni une banque réelle.',
    'Société vente': 'Créer ANNEXE RAS VENTE FICTIVE 298, exercice 2026 ouvert du 01/01 au 31/12, suivant Administration → Sociétés du cahier principal. Créer client CLIENT RAS 298, compte client 3421 ; aucun autre mouvement. Ne pas inventer d’identifiants fiscaux officiels.',
    'Société achat': 'Créer séparément ANNEXE RAS ACHAT FICTIVE 298, même exercice ouvert. Créer fournisseur FOURNISSEUR RAS 298, compte fournisseur 4411 ; aucun autre mouvement. Ne pas réutiliser la société vente.',
    'Factures': 'Date 15/03/2026, une ligne Service laboratoire 298, quantité 1, prix unitaire HT 1 000, TVA 20 %, Taxable. Vente : compte produit 7111. Achat : compte achat 6111 ; référence fournisseur ACH-RAS298-001, qualification TVA Charge / achat courant, déductible 100 %. Remises, transport, emballage et acomptes zéro. Retenue à la source (sur HT) : 10 % explicitement choisie.',
    'Règlements': 'Premier virement réel de laboratoire : 20/03/2026, montant 1 100, référence VIR-RAS298-1100. Deuxième : 21/03/2026, montant 100, référence VIR-RAS298-100. Dans chaque société, laisser Banque vide : vérifier contrepartie automatique 5141, sinon Bloqué et noter le paramétrage. Aucun apport initial ; banque finale +1 200 en vente, −1 200 en achat.',
    'Sens de la preuve': 'La RAS estimée de 100 et le net estimé de 1 100 ne prouvent ni une retenue opérée ni un paiement. Ces scénarios règlent finalement les 1 200 en trésorerie et ne capturent aucune retenue. Ne pas comptabiliser une OD de RAS pour solder artificiellement les 100.',
    'Historiques inconnus': 'Si l’interface présente À vérifier ou un diagnostic historique, ne pas forcer un montant ni modifier une pièce définitive. Consigner Bloqué et conserver la capture pour une vérification contrôlée. La fabrication de NaN/SQL ou d’un ancien historique n’est pas demandée à l’utilisateur. Les autres écrans concernés par les lots 296/297 et la future capture explicite sont hors parcours de cette annexe.',
    'Traçabilité': 'Noter le numéro réellement attribué à chaque facture et ses trois écritures. Conserver captures et exports ouverts. Après validation, aucune réécriture des pièces : comparer avant/après par le Journal et le Grand livre.',
}
COLONNES = dict(zip(
    ['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','statut','resultat_reel','anomalies','preuves','observations','sources','preuves_attendues'],
    ['Identifiant','Module','Objectif','Prérequis','Données à saisir','Actions détaillées','Résultat attendu','Écritures attendues','Impacts fiscaux','Contrôles','Statut','Résultat réel','Anomalies','Preuves/captures','Observations','Sources','Preuves attendues']))
ORACLE_LABELS = dict(zip(
    ['ht','tva','ttc','ras_estimee','net_estime','solde_avant','cash1','reste_apres_cash1','cash2','solde_final','ras_imputee','banque_vente','banque_achat','total_debit','total_credit'],
    ['Montant HT','TVA documentaire','Total TTC','RAS estimée','Net estimé','Solde avant paiement','Premier virement','Reste après premier virement','Deuxième virement','Solde final du tiers','RAS imputée','Solde banque — vente','Solde banque — achat','Total débit','Total crédit']))


def oracle():
    ht=Decimal('1000'); tva=ht*Decimal('20')/100; ras=ht*Decimal('10')/100
    ttc=ht+tva; cash1=Decimal('1100'); cash2=Decimal('100')
    return {'ht':ht,'tva':tva,'ttc':ttc,'ras_estimee':ras,'net_estime':ttc-ras,
        'solde_avant':ttc,'cash1':cash1,'reste_apres_cash1':ttc-cash1,
        'cash2':cash2,'solde_final':ttc-cash1-cash2,'ras_imputee':Decimal('0'),
        'banque_vente':cash1+cash2,'banque_achat':-cash1-cash2,
        'total_debit':ttc+cash1+cash2,'total_credit':ttc+cash1+cash2}


def cas():
    items=[]
    for sens in ('vente','achat'):
        vente=sens=='vente'; nom='CLIENT RAS 298' if vente else 'FOURNISSEUR RAS 298'
        compte='3421' if vente else '4411'; bouton='Encaisser le client' if vente else 'Payer le fournisseur'
        facture='D3421=1 200, C7111=1 000, C4455=200' if vente else 'D6111=1 000, D34552=200, C4411=1 200'
        reglements='D5141=1 100/C3421=1 100 puis D5141=100/C3421=100' if vente else 'D4411=1 100/C5141=1 100 puis D4411=100/C5141=100'
        items.append(dict(id='RAS-298-01' if vente else 'RAS-298-02',module='Recouvrement',
            objectif='RAS estimée sans imputation — '+sens,
            prerequis='Société '+sens+' neuve et isolée, exercice 2026 ouvert, tiers '+nom+' préparé selon le Jeu. Aucun autre mouvement ni lettrage.',
            donnees='HT 1 000 / TVA 200 / TTC 1 200 ; taux RAS estimé 10 %, estimation 100, net estimé 1 100. Virements 1 100 puis 100, dates et références du Jeu.',
            actions=[
                'Sélectionner ANNEXE RAS '+sens.upper()+' FICTIVE 298 et exercice 2026. Factures → '+('Ventes' if vente else 'Achats')+' → Nouvelle facture. Sélectionner '+nom+' dans les propositions, date 15/03/2026 ; saisir la ligne et le compte du Jeu. '+('' if vente else 'N° facture fournisseur ACH-RAS298-001 ; Charge / achat courant, TVA déductible (%) 100. ')+'Choisir Retenue à la source (sur HT) 10 %. Enregistrer le brouillon, vérifier HT 1 000/TVA 200/TTC 1 200 et net estimé 1 100. Valider définitivement, puis Générer l’écriture comptable de cette facture. Dans Journal, contrôler et Valider cette écriture. Noter les numéros réellement attribués.',
                'Sur cette facture, '+bouton+'. Le formulaire affiche RAS estimée 100,00 MAD et propose Montant * 1 200,00 : le solde reste le TTC, sans imputation de l’estimation. Annuler sans enregistrer. Situation financière & recouvrement → Échéances & impayés → '+('Clients' if vente else 'Fournisseurs')+' : retrouver cette pièce, reste dû 1 200 et imputé 0. Conserver les preuves avant paiement.',
                'Revenir à la même facture, '+bouton+'. Date 20/03/2026, Montant * 1 100, Mode Virement, référence VIR-RAS298-1100 ; Banque vide. Enregistrer. Vérifier statut Part. payée, puis rouvrir ce formulaire : montant proposé 100,00, estimation toujours 100,00. Annuler. Journal : contrôler et Valider uniquement la nouvelle écriture de virement ; ne pas créer une retenue pour les 100 restants.',
                'Même facture, '+bouton+' : date 21/03/2026, Montant * 100, Virement, référence VIR-RAS298-100, Banque vide. Enregistrer puis contrôler et Valider sa nouvelle écriture dans Journal. Vérifier facture Payée, reste 0. Aucune OD de RAS ni mouvement 3453/4457 ; seuls les deux virements réels ont soldé le tiers.',
                'Comptabilité → Lettrage : exercice 2026, Compte '+('Clients (3421)' if vente else 'Fournisseurs (4411)')+', Tiers '+nom+'. Cocher les trois lignes : '+('débit facture 1 200, crédits virements 1 100/100' if vente else 'crédit facture 1 200, débits virements 1 100/100')+'. Total débit = crédit 1 200 ; Lettrer 3 lignes. Noter le code commun de trois lettres, AAA attendu dans cette société neuve sans lettrage antérieur. Si le lettrage ou les lignes requis manquent, noter Bloqué et conserver la preuve, sans forcer de ligne.',
                'Journal → Exporter CSV, ouvrir le fichier ; Grand livre : contrôler '+compte+' soldé et 5141 '+('+1 200' if vente else '−1 200')+'. Comparer trois écritures/sept lignes, total débit = crédit 2 400, aucune 3453/4457. Recharger et recontrôler facture Payée et code commun ; les écritures initiales restent inchangées.'
            ],
            attendu='RAS estimée 100 et net estimé 1 100 distincts des paiements : solde initial 1 200 ; après trésorerie 1 100 reste 100 et Part. payée ; après trésorerie 100 reste 0 et Payée. Trois écritures, sept lignes ; trois lignes du tiers lettrées sous un code commun.',
            ecritures='Facture : '+facture+'. Virements : '+reglements+'. Cumul D=C2 400 ; '+compte+'=0 ; banque '+('+1 200' if vente else '−1 200')+'. Aucun compte 3453/4457 ni OD de RAS. Sept lignes, toutes définitives après validation.',
            fiscal='TVA documentaire 200 et RAS estimée 100 proviennent des choix explicites du laboratoire. Aucune retenue imputée, attestation, déclaration ni qualification réglementaire automatique. Ne pas transposer les taux à un dossier réel.',
            controles='Solde, statut, proposition de montant et estimation à chacune des trois étapes ; comptes, sens des virements, nombres de lignes, équilibre, vrai tiers, code AAA ou code attribué consigné ; pas de réparation historique.',
            statut='Non testé',resultat_reel='',anomalies='',preuves='',observations='',sources=' ; '.join(SOURCES),
            preuves_attendues='Captures facture et trois étapes de solde, formulaire montant 1 200 puis 100, estimation 100 ; trois écritures validées, lettrage, Grand livre et CSV ouvert. Renseigner le chemin des preuves réellement obtenues dans la colonne Preuves/captures.'))
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
    story=[Paragraph(escape(TITRE),styles['Title']),Paragraph('RAS estimée et paiements réels',styles['Heading1']),Paragraph(escape(INTRO),styles['BodyText'])]
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
        canvas.drawString(42,28,'HisabPro — Recette utilisateur à effectuer — RAS298')
        canvas.drawRightString(A4[0]-42,28,str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(destination/(NOM+'.pdf')),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=42,title=TITRE+' — RAS estimée et paiements réels').build(story,onFirstPage=pied,onLaterPages=pied)
    md=['# '+TITRE,'','## RAS estimée et paiements réels','',INTRO,'','## Jeu de données','']
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
    generer(); print('Deux cas RAS Non testé générés PDF/XLSX/MD ; aucune base utilisée.')
