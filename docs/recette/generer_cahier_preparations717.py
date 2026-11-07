"""Cahier717 : compléments707–715, trente cas humains et neuf feuilles de suivi."""
from pathlib import Path
import importlib.util,json,re,hashlib
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.workbook.properties import CalcProperties
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STEM=HERE/'CAHIER_PREPARATIONS_BALANCES_717'
REGISTRE=[(707,'PARTICIPATIONS','Participations','P707'),(709,'EMETTEURS','Émetteurs','E709'),
 (711,'CESSIONS','Cessions','C711'),(713,'MOUVEMENTS','Mouvements','M713'),(715,'RACCORDS','Rattachements','R715')]


def source(lot,nom):return ROOT/f'docs/LIASSE_BALANCES_{nom}_{lot}.md'


def cas(lot,nom,prefixe):
 rows=[[c.strip() for c in line.strip('|').split('|')] for line in source(lot,nom).read_text(encoding='utf-8-sig').splitlines() if line.startswith('|'+prefixe+'-')]
 assert len(rows)==6 and all(len(r)==4 and r[3]=='Non testé' for r in rows)
 return rows


def charger_guide():
 spec=importlib.util.spec_from_file_location('guide717',ROOT/'docs/guide/generer_guide.py')
 g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);return g


def rendus(md,stem):
 g=charger_guide();g.SOURCE=md;g.STEM=stem;blocs=g.blocs();original=g.word_table
 largeurs={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 g.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+largeurs[m[1]]+'"',original(rows))
 g.docx(blocs);table=g.Table
 g.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*g.mm,64*g.mm,63*g.mm,19*g.mm]})
 g.pdf(blocs)


def generer():
 intro='''# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 21 octobre 2026. Annexe : préparations depuis balances, compléments707–715.

## Objet et ordre de lecture

Ce document rassemble les modes d’emploi et trente cas de recette des titres de participation,
déclarations d’émetteurs, cessions/retraits, mouvements d’immobilisations/amortissements/provisions
et rattachements de leurs clôtures aux comptes sources. Il complète le cahier général HisabPro.
Il ne remplace pas la recette annuelle complète depuis une base vierge jusqu’à l’archivage.

Accès commun : Comptabilité → Liasse fiscale → Préparer depuis des balances externes.
Installer les fichiers différentiels autorisés, redémarrer le backend et reconstruire le frontend.
Les migrations existantes du module doivent être présentes ; aucune migration nouvelle dans ces lots.
Utiliser exclusivement une société fictive séparée, en MAD, exercice2026 et profils autorisés.
Aucun essai de ce cahier ne doit modifier la comptabilité réelle. Les préparations présentées ne
créent ni écriture ni liquidation fiscale ; noter le Journal avant et après chaque parcours.

## Trois jeux de recette distincts

Jeu A : participations707 et émetteurs709, dans une préparation partagée avec les CSV707.
N titres2510=4000MAD ; N-1=3000MAD ; brut financier entier6000/4000MAD.
Les déclarations de deux émetteurs N2500+1500 et d’un émetteur N-1 3000 sont sourcées séparément.
Le total24/25 ne doit pas être comparé au seul251. Les pourcentages ne sont pas inférés du capital.

Jeu B : cessions/retraits711, dans une préparation distincte avec le contexte CSV707.
Le registre fictif de sorties est un autre exemple : prix5000−VNA6000=−1000MAD, puis variante−0,01.
Ses sorties ne sont pas à additionner aux mouvements du jeu C. Aucun rapprochement de ces deux
registres fictifs distincts n’est revendiqué et aucun résultat fiscal n’est déduit de leur différence.

Jeu C : mouvements713 puis rattachements715, dans une préparation partagée avec les CSV713.
Clôtures11000/4500/700MAD ; rattachements explicites2340/2834/1511, écarts0.
Après clôture déclarée B2 à10999,99, l’ancien contrôle reste signalé À refaire ; le nouveau donne−0,01.
Les ouvertures et flux viennent de pièces fictives, jamais d’une déduction des seules balances.

Les trois préparations sont distinctes. Elles peuvent être conservées dans la même société fictive,
sans écriture créée. Noter pour chacune son numéro, sa version et son empreinte afin de choisir
la bonne préparation dans le sélecteur. Les numéros de version réels peuvent varier.

## Utiliser le classeur de suivi

Ouvrir CAHIER_PREPARATIONS_BALANCES_717.xlsx. La feuille Synthèse compte les statuts humains
et donne accès aux guides de chaque partie. Participations, Émetteurs, Cessions, Mouvements et
Rattachements contiennent six cas chacune : actions/données, résultats attendus, statut, résultat
réel, anomalies et preuves. Les trente statuts commencent à Non testé. Remplir le résultat réel
et ajouter les captures/exports après vos essais. Preuves et Anomalies sont les registres communs.
Conserver un modèle vierge et utiliser une copie pour les résultats de travail.
Les formules du tableau de bord se recalculent à l’ouverture dans Excel.

Distinguer quatre états : développement du complément terminé ; tests automatisés du lot validés ;
recette utilisateur à effectuer ; production nonvalidée. Les réussites automatisées consignées
aux rapports ne remplissent pas les résultats humains. Un contrôle actuel ou un écart0 ne prouve
pas la complétude d’un registre ou une conformité réglementaire. Les sources fiscales autonomes,
spécifications officielles et limites du cahier général restent des sujets distincts.
RH/paie et point6 humain restent différés. Aucun modèle DGI ou dépôt officiel n’est certifié.

'''
 sections=[intro]
 for lot,nom,titre,prefixe in REGISTRE:
  texte=source(lot,nom).read_text(encoding='utf-8-sig').splitlines()
  sections.append(f'## Partie {titre} — complément{lot}\n\nGuide séparé : MODE_EMPLOI_{nom}_{lot}.docx/.pdf/.xlsx. Données : DONNEES_{nom}{lot}.json.\n\n')
  for line in texte[1:]:
   if line.startswith('## '):line='### '+line[3:]
   sections.append(line+'\n')
 STEM.with_suffix('.md').write_text(''.join(sections),encoding='utf8')
 rendus(STEM.with_suffix('.md'),STEM)
 # Ne régénérer que les Word/PDF dont le premier titre a été traité comme du corps.
 # Aucun classeur individuel n’est réécrit, y compris ses résultats humains éventuels.
 repaires=[];w_ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 excels={f'MODE_EMPLOI_{nom}_{lot}.xlsx':hashlib.sha256((HERE/f'MODE_EMPLOI_{nom}_{lot}.xlsx').read_bytes()).hexdigest() for lot,nom,_,_ in REGISTRE}
 for lot,nom,_,_ in REGISTRE:
  st=HERE/f'MODE_EMPLOI_{nom}_{lot}'
  with ZipFile(st.with_suffix('.docx')) as z:
   premier=ET.fromstring(z.read('word/document.xml')).find('w:body/w:p',w_ns)
   style=premier.find('w:pPr/w:pStyle',w_ns).attrib.get('{'+w_ns['w']+'}val')
  if style!='Title':
   rendus(source(lot,nom),st);repaires.append({'lot':lot,'ancien_style':style,'nouveau_style':'Title'})
 assert all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h for f,h in excels.items())
 trace={'titres_repares':repaires,'classeurs_individuels_sha256_preserves':excels}
 if (ROOT/'.codex-tests').is_dir():(ROOT/'.codex-tests/reparations717_preuve.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf8')
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 synth=wb.active;synth.title='Synthèse'
 synth.append(['Recette humaine','Total cas','Réussis','Échoués','Bloqués','Non testé','Progression','Guide PDF','Guide Word'])
 preuves=[]
 for no,(lot,nom,titre,prefixe) in enumerate(REGISTRE,2):
  ws=wb.create_sheet(titre)
  ws.append(['ID','Actions / données exactes','Résultat / preuve attendus','Statut humain','Résultat réel','Anomalies','Preuves réelles','Écritures / impacts fiscaux attendus'])
  for ident,actions,attendus,statut in cas(lot,nom,prefixe):
   ws.append([ident,actions,attendus,statut,'','','','Aucune écriture ni liquidation fiscale créée par la préparation.']);preuves.append(ident)
  validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('D2:D7')
  for statut,couleur in [('Réussi','D8F0DD'),('Échoué','F9DCDC'),('Bloqué','FFF0C2')]:
   ws.conditional_formatting.add('D2:D7',CellIsRule(operator='equal',formula=['"'+statut+'"'],fill=PatternFill('solid',fgColor=couleur)))
  ref="'"+titre.replace("'","''")+"'!"
  synth.append([titre,f'=COUNTA({ref}A2:A7)',f'=COUNTIF({ref}D2:D7,"Réussi")',f'=COUNTIF({ref}D2:D7,"Échoué")',
   f'=COUNTIF({ref}D2:D7,"Bloqué")',f'=COUNTIF({ref}D2:D7,"Non testé")',f'=IF(B{no}=0,0,C{no}/B{no})','Ouvrir PDF','Ouvrir Word'])
  synth.cell(no,8).hyperlink=f'MODE_EMPLOI_{nom}_{lot}.pdf';synth.cell(no,9).hyperlink=f'MODE_EMPLOI_{nom}_{lot}.docx'
  synth.cell(no,7).number_format='0%'
  for i in range(2,8):ws.row_dimensions[i].height=170
 synth.append(['GLOBAL',*[f'=SUM({col}2:{col}6)' for col in 'BCDEF'],'=IF(B7=0,0,C7/B7)']);synth['G7'].number_format='0%'
 synth.append(['Les tests automatisés restent distincts de cette recette humaine.'])
 ws=wb.create_sheet('Données');ws.append(['Jeu / complément','Information','Valeur déclarée ou attendue'])
 for lot,nom,titre,prefixe in REGISTRE:
  d=json.loads((HERE/f'DONNEES_{nom}{lot}.json').read_text(encoding='utf8'))
  ws.append([str(lot),'Source',f'DONNEES_{nom}{lot}.json'])
  ws.append([str(lot),'Contexte',d.get('contexte','Données fictives')])
  for cle,valeur in d.items():
   if cle!='contexte':ws.append([str(lot),cle,json.dumps(valeur,ensure_ascii=False)])
 ws=wb.create_sheet('Preuves');ws.append(['ID','Fichier / capture réelle','Observations'])
 for ident in preuves:ws.append([ident,'',''])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=45
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
 wb['Données'].column_dimensions['C'].width=110
 for col in 'BCDEFG':synth.column_dimensions[col].width=15
 for i in range(2,7):
  for c in (8,9):synth.cell(i,c).font=Font(color='185FA5',underline='single')
 wb.save(STEM.with_suffix('.xlsx'))
 print('Cahier717 généré : cinq domaines,30cas humains Non testé, neuf feuilles. Classeurs séparés préservés.')

if __name__=='__main__':generer()
