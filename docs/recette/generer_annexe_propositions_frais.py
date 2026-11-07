"""Recette humaine complémentaire ; aucune connexion, aucun résultat prévalidé."""
from pathlib import Path
from zipfile import ZipFile
from decimal import Decimal
import math,re
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
wb=Workbook();s=wb.active;s.title='Synthèse'
cas=wb.create_sheet('Propositions et frais');d=wb.create_sheet('Données exactes')
cas.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu',
    'Écritures attendues','Impact fiscal','Contrôles','Statut','Résultat réel','Anomalies','Preuves / captures','Observations'])
infos=[
 ('RPF-001','Proposition collective240','Dossier RVT vente distinct ;084 active ;lot120/120 validé.',
  '11/10/2026 ;banque5141 ;lotBQ-VIR-240 ;relevéCrédit240 même référence.',
  'Proposer ;vérifier date/sens/référence/montant ;confirmer ;recharger.',
  'Une proposition ;une ligne relevé,deux lignes comptables pointées.',
  'Aucune nouvelle écriture ;quatre pièces10lignes,D=C600 ;client reste120,banque240.'),
 ('RPF-002','Proposition simple60 et sélection','Dossier séparé ;paiement simple validé.',
  '11/10/2026 ;paiement60 sur facture120 ;référenceSIMPLE-RPF ;relevéCrédit60.',
  'Proposer ;décocher puis recocher ;confirmer ;recharger.',
  'Une proposition exacte ;une ligne bancaire pointée ;aucun pointage quand décochée.',
  'Facture3421D120,7111C100,4455C20 ;règlement5141D60,3421C60 ;D=C180.'),
 ('RPF-003','Ambiguïtés et refus non exacts','Dossier négatif distinct ;une écriture banque validée60.',
  'Deux relevés identiquesCrédit60,SIMPLE-RPF,11/10/2026 ;puis variante60,01 ou référence avec texte ajouté.',
  'Proposer ;consulter ambiguïtés ;ne pas choisir arbitrairement ;traiter avec justificatifs.',
  'Aucune proposition ambiguë ;montant/référence différents restent sans correspondance exacte.',
  'Aucune nouvelle écriture ou mutation du Journal.'),
 ('RPF-004','Aperçu obsolète et contexte','Compte écriture du même dossier ;aperçu ouvert.',
  'Modifier le libellé d’un relevé non pointé depuis une seconde fenêtre ;ou changer compte5142.',
  'Confirmer ancien aperçu ;puis fermer et recalculer ;changer compte/période.',
  'Refus si situation changée,aucun pointage partiel ;ancien contexte fermé.',
  'Pièces validées intactes ;aucun montant absorbé automatiquement.'),
 ('RPF-005','Chèque120 frais10,01','Société ENCAISSEMENT FRAIS DÉMO distincte,2026 ouvert,client natif.',
  '11/10/2026 ;factureHT100/TVA20/TTC120 ;référenceENCAISSE-FRAIS-FICTIF ;banque5141.',
  'Valider/comptabiliser facture ;encaisser modeChèque120 ;remettre ;confirmer encaissement frais10,01 ;valider3brouillons ;relevéCrédit109,99 ;proposer/confirmer ;lettrer2lignes ;exportFEC.',
  'Facture soldée120 ;netbanque109,99 ;frais10,01 ;une ligne pointée ;lettrageAAA dossier vierge ;FEC10lignes.',
  'Facture3421D120,7111C100,4455C20 ;portefeuille51111D120,3421C120 ;remise51112D120,51111C120 ;encaissement5141D109,99,61472D10,01,51112C120 ;4pièces10lignes,D=C480.'),
 ('RPF-006','Effet120 frais10,01','Autre société de recette ;même structure queRPF005.',
  'Échéance11/10/2026 ;avis11/10/2026 ;référenceENCAISSE-FRAIS-FICTIF ;frais10,01.',
  'RépéterRPF005 modeEffet et échéance11/10/2026 ;remettre ;encaisser ;pointer le net ;lettrer ;exportFEC.',
  'Même net et soldes ;effet encaissé à échéance ;aucun escompte simulé.',
  'Remplacer51111 par3425 et51112 par51132 dansRPF005 ;4pièces10lignes,D=C480 ;attente etclient0.'),
 ('RPF-007','Frais invalides et opérations non couvertes','Dossier négatif distinct,pièces uniquement fictives.',
  'Encaissement120 :frais10,005 puis−1 ;remise avecfrais1,01 ;paiement effetfournisseur avecfrais1,01 (testAPI technique).',
  'Tenter confirmation ;faire vérifier refusAPI au technicien pour cas non saisissables dansUI.',
  'Refus avant mutation ;aucun frais silencieusement ignoré ;statut et écritures inchangés.',
  'Aucune nouvelle écriture sur essais refusés ;comparer photos et statuts avant/après.'),
 ('RPF-008','Clôture et permissions','Dossier de test séparé ;utilisateurLecture ;exercice clôturé via parcours annuel existant.',
  'Même banque et lignes rapprochées du dossier ;autre société avec ses seules opérations.',
  'Consulter comme lecteur ;tenter confirmation ;consulter exercice clôturé ;changer de société.',
  'Mutations interdites ;consultation conservée ;aucun accès à autre société.',
  'Aucune altération de montants,validation ou liens d’un autre dossier.'),
 ('RPF-009','Année2025 et à-nouveaux2026 avec frais','Autre dossier isolé ;2025 et2026 ouverts,2026 vierge ;profil technique de laboratoireIS/TVAencaissement/MAD/exercice_debut2020 préparé par le technicien.',
  '15/06/2025 ;factureHT100/TVA20/TTC120 ;chèque120 ;frais10,01 ;relevéCrédit109,99 ;référenceENCAISSE-FRAIS-FICTIF ;impôt3000 attendu dans ce seul profil de test.',
  'RépéterRPF005 dans2025 ;valider/lettrer/pointer ;Clôture→Clôturer2025 ;contrôlerAN2026 ;exporterFEC2025/2026 ;revenir au rapprochement2025.',
  'Résultat avant impôt89,99 puis perte2910,01 ;AN2026 quatre lignes3020 équilibrés ;pointage conservé/lecture seule,dépointage refusé ;FEC équilibrés.',
  'AN5141D109,99+1199D2910,01 ;4455C20+4453C3000 ;D=C3020. Comptes attente/client0. Impôt de laboratoire,pas une qualification fiscale réelle.'),
]
for ident,obj,pre,data,actions,result,compta in infos:
    cas.append([ident,'Banque / effets',obj,pre,data,actions,result,compta,
        'Aucune règle fiscale nouvelle ;TVA20 de laboratoire uniquement ;pas de TVA bancaire inventée.',
        'Captures avant/après ;pièces et soldes identiques après pointage/lettrage ;référence complète et date réelle.',
        'Non testé','','','',''])
dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"',allow_blank=False)
dv.showErrorMessage=True;dv.error='Choisir un statut de la liste.';cas.add_data_validation(dv);dv.add('K2:K10')
cas.auto_filter.ref=cas.dimensions;cas.freeze_panes='D2'
s.append(['HISABPRO — PROPOSITIONS ET FRAIS','11/10/2026'])
s.append(['Portée','Annexe humaine9cas ;point6 en attente utilisateur.'])
s.append(['État','Résultats humains non prévalidés ;copie de recette isolée uniquement.'])
s.append(['Statut','Nombre'])
for statut in ['Non testé','Réussi','Échoué','Bloqué']:
    s.append([statut,f'=COUNTIF(\'Propositions et frais\'!K2:K10,A{s.max_row+1})'])
s.append(['Total','=SUM(B5:B8)']);s.append(['Progression réussie','=IFERROR(B6/B9,0)']);s['B10'].number_format='0%'
s.append(['Preuves automatisées','Rapports404/405/406 ;ne remplacent pas la recette humaine.'])
d.append(['Dossier','Date','Opération','Débit','Crédit','Attendu'])
for row in [
 ['Frais distinct','11/10/2026','Facture HT100/TVA20','3421:120','7111:100 ;4455:20','TTC120'],
 ['Chèque','11/10/2026','Portefeuille','51111:120','3421:120','Client soldé'],
 ['Chèque','11/10/2026','Remise','51112:120','51111:120','Portefeuille soldé'],
 ['Chèque','11/10/2026','Encaissement','5141:109,99 ;61472:10,01','51112:120','Net109,99 ;D=C120'],
 ['Effet distinct','11/10/2026','Même cycle à échéance','3425 puis51132','3421 puis3425 puis51132','4pièces10lignes,D=C480'],
 ['Pointage','11/10/2026','Une ligne relevéCrédit109,99','','','Même date/sens/référence/montant ;une ligne comptable pointée'],
 ['Lettrage','11/10/2026','Deux lignes3421/tiers120','','','D=C120 ;AAA dans dossier vierge'],
 ['FEC','2026','Export définitif','','','10lignes,D=C480 ;banque109,99/frais10,01/client0'],
]:d.append(row)
for ws in wb:
    ws.sheet_view.showGridLines=False;ws.freeze_panes=ws.freeze_panes or 'A2'
    for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='17365D')
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment=Alignment(vertical='top',wrap_text=True)
            if isinstance(c.value,str) and not c.value.startswith('='):
                c.value=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)|(?<=\d)(?=[A-Za-zÀ-ÿ])',' ',c.value)
    for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=25 if ws==cas else 38
for col,width in {'E':36,'F':48,'G':36,'H':48,'J':36,'N':30}.items():cas.column_dimensions[col].width=width
for i in range(2,11):
    lignes=max(math.ceil(len(str(c.value or ''))/(cas.column_dimensions[c.column_letter].width*.85)) for c in cas[i])
    cas.row_dimensions[i].height=max(130,lignes*14+12)
cas.column_dimensions['A'].width=14;cas.column_dimensions['K'].width=14
wb.calculation=CalcProperties(fullCalcOnLoad=True)
p=HERE/'ANNEXE_RECETTE_PROPOSITIONS_FRAIS.xlsx';wb.save(p)
with ZipFile(p) as z:assert z.testzip() is None
r=load_workbook(p,data_only=False);assert len(r.sheetnames)==3
assert len({r['Propositions et frais'].cell(i,1).value for i in range(2,11)})==9
assert all(r['Propositions et frais'].cell(i,11).value=='Non testé' for i in range(2,11))
assert all(r['Propositions et frais'].cell(i,j).value is None for i in range(2,11) for j in range(12,16))
assert r['Synthèse']['B10'].data_type=='f'
assert Decimal('109.99')+Decimal('10.01')==120 and 120*4==480
assert Decimal('109.99')+Decimal('2910.01')==3020 and Decimal('89.99')-3000==Decimal('-2910.01')
print('Excel3feuilles9NonTeste,formules/validation/CRC et oracle exact vérifiés.')
