"""Word/PDF et suivi Excel du complément ventes ; aucune connexion à une base."""
from pathlib import Path
from decimal import Decimal
from zipfile import ZipFile
import importlib.util
import math
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guide_commun',HERE/'generer_guide.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
g.SOURCE=HERE/'GUIDE_PREPARATION_VENTES.md';g.STEM=g.SOURCE.with_suffix('')
g.docx(g.blocs());g.pdf(g.blocs())
wb=Workbook();s=wb.active;s.title='Synthèse';c=wb.create_sheet('Ventes');d=wb.create_sheet('Données exactes')
c.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu',
          'Écritures attendues','Impact fiscal','Contrôles','Statut','Résultat réel','Anomalies','Preuves / captures','Observations'])
cas=[
 ('VP-001','Préparation et exclusions','Profil fictif du guide ;trois pièces définitives,non comptabilisées.',
  'F1 15/01/2026 HT100/TVA20/TTC120 ;F2 HT200/TVA40/TTC240 ;avoirF1 15/03/2026 quantité0,30 HT30/TVA6/TTC36.',
  'Liasse→Préparation ventes→Préparer ;contrôler trois sources et exclusions dans une variante brouillon/proforma/annulée.',
  'HT270/TVA54/TTC324 ;avoir signé à sa date ;achats,brouillons,proformas,annulés exclus.'),
 ('VP-002','Exports de la préparation et refus des sources modifiées','VP001 exécuté ;préparation disponible. Variante dans dossier séparé.',
  'VENTES_PREPARATION_INTERNE_2026.csv/.xlsx/.pdf ;CSV UTF-8,point-virgule ;ICE/IF comme texte. Variante :quatrième facture100/20/120.',
  'ExporterCSV,Excel,PDF ;comparer société,sources,période,empreinte ettotaux. Variante :créer quatrième facture après aperçu ;exportExcel/PDF refusé ;Actualiser puis exporter.',
  'Trois pièces ettotaux270/54/324 ;empreinte identique. Ancien aperçu refusé après ajout ;actualisation quatre pièces370/74/444 ;aucune mutation par export.'),
 ('VP-003','Identité historique figée','Les trois pièces existent avant changement de fiche tiers.',
  'ICE initial001234567890123 ;nouvelICE de fiche009876543210987.',
  'Modifier uniquement ICE du client puisActualiser les ventes ;comparer les trois pièces etCSV.',
  'ICE historique reste001234567890123 ;numéros,montants et pièces inchangés.'),
 ('VP-004','Changement d’exercice','Exercice2025 vide créé dans le même dossier de recette.',
  '2025 du01/01/2025 au31/12/2025 ;sources duprofil toutes2026.',
  'Sélectionner2025 ;Préparer ;revenir2026 ;Préparer.',
  'Aucune source2026 dans2025 ;trois sources dans2026 ;réponse tardive ancienne non retenue.'),
 ('VP-005','Isolation société','Autre société fictive vierge et son exercice2026.',
  'Première sociétéRECETTE VENTES418SARL ;autre sociétéRECETTE VENTES418B.',
  'Changer société ;Préparer ;revenir dans première société.',
  'Aucune fuite des trois sources vers autre société ;retour au dossier de la première.'),
 ('VP-006','Consultation autorisée','UtilisateurLecture fictif créé dans première société.',
  'Comptelecture.ventes418@example.com ;mot de passe fictifLectureVentes2026! ;rôleLecture.',
  'Se connecter ;Liasse→Préparation ventes ;Préparer etExporter ;comparer les pièces etJournal.',
  'Lecture/CSV/Excel/PDF disponibles ;aucune mutation ou nouvelle écriture par ce flux.'),
 ('VP-007','Montants historiques inconnus','Jeu synthétique préparé par technicien en environnement isolé ;hors parcours manuel principal.',
  'Profil100+200−30 connu ;pièce historique supplémentaire au montant source inconnu.',
  'Technicien utilise les tests isolés livrés ;consulter préparation ;comparer sources avant/après.',
  'Pièce visibleÀ vérifier,total complet inconnu,partie connue270/54/324 ;source non réparée.'),
]
for ident,obj,pre,donnees,actions,attendu in cas:
 c.append([ident,'Liasse / préparation ventes',obj,pre,donnees,actions,attendu,
  'Aucune nouvelle écriture lors lecture/export ;pièces etJournal conservés.',
  'Totaux documentaires ;aucune déclaration fiscale ni calcul fiscal nouveau.',
  'Numéros,dates,identités,périmètre,signes etconservation des sources.','Non testé','','','','FormatDGI non qualifié ;recette humaine distincte.'])
d.append(['Référence','Date','HT','TVA','TTC','Quantité / description'])
for row in [('F1','15/01/2026',100,20,120,'1 × 100'),('F2','15/01/2026',200,40,240,'1 × 200'),('A1','15/03/2026',-30,-6,-36,'0,30 de F1'),('NET','2026',270,54,324,'100+200−30')]:d.append(row)
d.append(['Client','CLIENT RECETTE VENTES 418','','','','ICE001234567890123 / IF12345678'])
s.append(['HISABPRO — Suivi de recette de la préparation ventes','Valeur'])
s.append(['Date du guide','12/10/2026']);s.append(['Total des cas',len(cas)])
for statut in ['Non testé','Réussi','Échoué','Bloqué']:
 s.append([statut,f'=COUNTIF(Ventes!K2:K8,"{statut}")'])
s.append(['Progression','=COUNTIF(Ventes!K2:K8,"Réussi")/B3']);s.cell(8,2).number_format='0%'
s.append(['Note','Les résultats humains restent vierges ;formatDGI et production non validés.'])
dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');dv.errorTitle='Statut invalide';dv.error='Choisir une valeur de la liste.';dv.showErrorMessage=True;dv.errorStyle='stop';c.add_data_validation(dv);dv.add('K2:K8')
wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
for feuille in wb:
 feuille.freeze_panes='A2';feuille.auto_filter.ref=feuille.dimensions
 for cellule in feuille[1]:cellule.font=Font(bold=True,color='FFFFFF');cellule.fill=PatternFill('solid',fgColor='185FA5')
 for row in feuille:
  for cellule in row:cellule.alignment=Alignment(vertical='top',wrap_text=True)
 for colonne in feuille.columns:
  lettre=colonne[0].column_letter;feuille.column_dimensions[lettre].width=14 if lettre in ('A','K') else 36
 for n in range(2,feuille.max_row+1):
  lignes=max(math.ceil(len(str(cellule.value or ''))/max(10,feuille.column_dimensions[cellule.column_letter].width-2)) for cellule in feuille[n])
  feuille.row_dimensions[n].height=max(120 if feuille==c else 30,18*lignes+8)
dest=HERE.parent/'recette/ANNEXE_RECETTE_VENTES.xlsx';wb.save(dest)
with ZipFile(dest) as z:assert z.testzip() is None
r=load_workbook(dest);assert r.sheetnames==['Synthèse','Ventes','Données exactes']
assert len({r['Ventes'].cell(i,1).value for i in range(2,9)})==7
assert all(r['Ventes'].cell(i,11).value=='Non testé' for i in range(2,9))
assert all(r['Ventes'].cell(i,j).value is None for i in range(2,9) for j in (12,13,14))
assert Decimal(100)+Decimal(200)-Decimal(30)==270
assert Decimal(20)+Decimal(40)-Decimal(6)==54
assert Decimal(120)+Decimal(240)-Decimal(36)==324
print('Word/PDF générés ;Excel3feuilles7NonTeste,CRC etoracle indépendant vérifiés.')
