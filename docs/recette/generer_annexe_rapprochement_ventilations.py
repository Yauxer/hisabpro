"""Classeur de recette humaine : aucune base, aucun résultat prévalidé."""
from pathlib import Path
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
wb=Workbook();synthese=wb.active;synthese.title='Synthèse'
cas=wb.create_sheet('Banque et ventilations');donnees=wb.create_sheet('Données exactes')
titres=['ID','Module','Objectif','Prérequis','Données exactes','Actions dans l’interface',
    'Résultat attendu','Écritures attendues','Impact fiscal','Contrôles',
    'Statut','Résultat réel','Anomalies','Preuves / captures','Observations']
cas.append(titres)
ecritures='Pointage seul : aucune nouvelle écriture. Deux factures HT100/200, TVA20/40, TTC120/240 et règlements120/120 : quatre pièces,10lignes,D=C600 ; tiers reste120, banque240.'
fiscal='Aucun impact fiscal nouveau du pointage. Les pièces, déclarations et contrôles sources restent inchangés.'
faits=[
('RVT-001','Pointage vente240','Copie isolée ;2026 ouvert ; quatre écritures validées ; lot natif.',
 'Client RAPPROCHEMENT DÉMO ;11/10/2026 ;facturesBQ-VENT-1 TTC120 etBQ-VENT-2 TTC240 ;virementBQ-VIR-240 affecté120/120 ;banque5141.',
 'Ajouter relevéCrédit240,BQ-VIR-240 ;choisir Ventilation 2règlements240 ;initial0/final240 ;recharger.',
 'Une ligne de relevé et deux lignes comptables pointées ;solde banque240 ;choix conservé.',
 'Journal identique ;photos avant/après ;débit relevé inversé en comptabilité.'),
('RVT-002','Pointage achat240','Autre société de recette ;fournisseur ;quatre écritures validées ;même banque.',
 'Même structure120/240,références fournisseur propres ;paiement240 affecté120/120.',
 'Ajouter relevéDébit240 ;choisir lot ;initial0/final−240 ;recharger.',
 'Une ligne de relevé,deux lignes crédit banque rapprochées ;dette restante120 ;solde−240.',
 'Sens achat conservé ;aucun compte client inventé ;journal D=C600.'),
('RVT-003','Dérapprochement et repointage','RVT-001 ou002 réussi dans son dossier propre.',
 'Même relevé240 et mêmes deux règlements.',
 'Choisir Non rapprochée ;recharger ;choisir de nouveau le lot.',
 'Deux lignes libérées puis repointées ;relevé présent ;aucune écriture modifiée.',
 'Nombre de lignes du relevé constant1 ;originaux identiques.'),
('RVT-004','Refus montant/sens/compte','Dossier de recette distinct ;lot natif complet non pointé.',
 'Relevé240,01 au lieu de240 ;autre essaiDébit au lieu deCrédit ;autre compte5142.',
 'Tenter de choisir le lot ;ne pas corriger les écritures pour rendre le choix disponible.',
 'Lot non proposé ou refus explicite ;aucun pointage ni écriture créé.',
 'Montant total exact au centime ;sens et banque explicites.'),
('RVT-005','Anti-double pointage','Deux lignes bancaires fictives distinctes ;un seul lot240.',
 'BQ-VIR-240 etBQ-VIR-240-ESSAI,total240 chacune ;ou relevé120 pointant un paiement seul.',
 'Pointer la première ;tenter le même lot sur la seconde ou réutiliser une ligne individuellement.',
 'Seule la première utilise les deux lignes ;deuxième tentative indisponible/refusée.',
 'Dérapprocher avant changement ;aucune double affectation.'),
('RVT-006','Lot non définitif ou annulé','Dossier négatif distinct ;pièces uniquement fictives.',
 'Deux règlements120 ;laisser leurs écritures en brouillon ou annuler une seule ligne.',
 'Consulter les propositions et tenter le pointage collectif.',
 'Lot non proposé/refusé ;aucune comptabilisation ou réparation automatique.',
 'Messages conservés ;aucune validation automatique d’un brouillon.'),
('RVT-007','Annuel et archive2025/2026','Jeu annuel380/393 préparé par le technicien ;aucun mélange avec les autres dossiers.',
 '2025 :capital1000,vente240 etachat240 ;2026 :compléments120/120 ;voir feuille Données exactes.',
 'Pointer les3lignes2025 ;clôturer selon le parcours annuel ;vérifier liens en lecture seule ;pointer les2lignes2026.',
 '2025 :5lignes comptables pointées,total brut1480,solde1000 ;2026 :2lignes,total brut240,initial=final1000 ;FEC et balance inchangés.',
 'Dérapprochement2025 interdit après clôture ;AN4180 ;balance2026 nette4060.'),
('RVT-008','Permissions et sociétés','Utilisateur Lecture et autre société de recette ;dossiers administrateur déjà préparés.',
 'Un compte Lecture du même dossier ;autre société avec son propre lot,éventuellement mêmeUUID dans le banc technique.',
 'Se connecter comme lecteur ;consulter ;tenter pointage/dépointage ;changer de société et vérifier ses seules lignes.',
 'Lecture autorisée ;mutations refusées ;aucun accès aux lignes de l’autre société.',
 'Capturer refus et liste ;références libres identiques ne fusionnent aucun dossier.'),
]
for ident,objectif,pre,data,actions,attendu,controles in faits:
    attendu_compta=ecritures
    if ident=='RVT-002':
        attendu_compta='Achats6111 débit300,TVA34552 débit60,fournisseur4411 crédit360 ;paiements4411 débit240,banque5141 crédit240 ;quatre pièces10lignes,D=C600 ;reste fournisseur120.'
    elif ident=='RVT-007':
        attendu_compta='Oracle380 :9pièces22lignes,D=C2200 avant impôt ;clôture etAN2026 équilibrés4180 ;compléments120/120 ;balance2026 nette4060. Le pointage ne modifie aucune écriture.'
    cas.append([ident,'Banque / comptabilité',objectif,pre,data,actions,attendu,attendu_compta,fiscal,controles,'Non testé','','','',''])
dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"',allow_blank=False)
dv.errorTitle='Statut de recette';dv.error='Choisir un statut de la liste.';dv.showErrorMessage=True
cas.add_data_validation(dv);dv.add(f'K2:K{cas.max_row}')
cas.auto_filter.ref=cas.dimensions;cas.freeze_panes='D2'
synthese.append(['HISABPRO — RECETTE DES VENTILATIONS BANCAIRES','11/10/2026'])
synthese.append(['Portée','Annexe de suivi humain,8cas ;point6 en attente utilisateur.'])
synthese.append(['État','Aucun résultat partenaire prévalidé. Essais sur copie isolée uniquement.'])
synthese.append(['Statut','Nombre'])
for statut in ['Non testé','Réussi','Échoué','Bloqué']:
    synthese.append([statut,f'=COUNTIF(\'Banque et ventilations\'!K2:K9,A{synthese.max_row+1})'])
synthese.append(['Total','=SUM(B5:B8)'])
synthese.append(['Progression réussie','=IFERROR(B6/B9,0)']);synthese['B10'].number_format='0%'
synthese.append(['Preuves automatisées','Consulter rapports392/393 ;elles ne remplacent pas les résultats humains.'])
donnees.append(['Dossier','Date','Opération','Montant / sens','Écritures / contrôles attendus'])
for row in [
 ['Vente autonome','11/10/2026','Deux factures HT100 et200','TVA20 et40,TTC120 et240','3421débit360 ;7111crédit300 ;4455crédit60'],
 ['Vente autonome','11/10/2026','Paiement par tiers240,affectations120/120','RelevéCrédit240,un seul mouvement','5141débit240 ;3421crédit240 ;resteclient120'],
 ['Achat autonome','11/10/2026','Structure identique fournisseur','RelevéDébit240,un seul mouvement','5141crédit240 ;4411débit240 ;restedette120'],
 ['Annuel distinct','01/01/2025','Apport bancaire','Créditrelevé1000','5141débit1000 ;1111crédit1000'],
 ['Annuel distinct','01et02/06/2025','Deux factures achat et deux vente,HT100/200 par sens','TTC120/240 par sens','TVA factures60/60 ;qualification laboratoire uniquement'],
 ['Annuel distinct','15/06/2025','Deux paiementsnatifs240 affectés120/120','RelevéCrédit240 puisDébit240','3lignes relevé aveccapital ;5lignes banque ;brut1480 ;solde1000'],
 ['Annuel distinct','31/12/2025','Clôture profil fiscal du laboratoire380','Impôt3000 ;AN2026 équilibrés4180','Pointages2025 conservés ;aucune nouvelle règle fiscale'],
 ['Annuel distinct','15/02/2026','Deux compléments120','RelevéCrédit120 etDébit120','Initial1000/final1000 ;totalbrut240 ;lettrage AN ;balance nette4060'],
]:donnees.append(row)
for ws in wb:
    ws.freeze_panes=ws.freeze_panes or 'A2'
    for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='17365D')
    for row in ws.iter_rows(min_row=2):
        for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
    ws.sheet_view.showGridLines=False
    for col in ws.columns:
        lettre=col[0].column_letter;ws.column_dimensions[lettre].width=25 if ws==cas else 38
cas.column_dimensions['A'].width=14;cas.column_dimensions['K'].width=14
for i in range(2,cas.max_row+1):cas.row_dimensions[i].height=140
wb.calculation=CalcProperties(fullCalcOnLoad=True)
target=HERE/'ANNEXE_RECETTE_RAPPROCHEMENT_VENTILATIONS.xlsx';wb.save(target)
with ZipFile(target) as z:assert z.testzip() is None
check=load_workbook(target,data_only=False)
assert check.sheetnames==['Synthèse','Banque et ventilations','Données exactes']
assert all(check['Banque et ventilations'].cell(i,11).value=='Non testé' for i in range(2,10))
assert all(check['Banque et ventilations'].cell(i,j).value is None for i in range(2,10) for j in range(12,16))
assert len({check['Banque et ventilations'].cell(i,1).value for i in range(2,10)})==8
assert check['Synthèse']['B10'].data_type=='f'
assert 1000+240-240==1000 and 1000+120-120==1000 and 1000+240+240==1480
print('Classeur3feuilles,8casNonTeste,IDsuniques,preuves/resultatsvides,formules/validation etCRC contrôlés.')
