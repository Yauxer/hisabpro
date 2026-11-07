"""Cahier intégré733 : oracles indépendants, Word/PDF et suivi humain Excel."""
from pathlib import Path
from decimal import Decimal as D,ROUND_HALF_UP
import csv,importlib.util,json,re
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import DoughnutChart,Reference
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE/'CAHIER_INTEGRE_BALANCES_733.md';STEM=SOURCE.with_suffix('')


def donnees():
 def rows(v):return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in v]
 n=rows([('1111','0','10000'),('1161','0','3000'),('2111','2000','0'),('28111','0','500'),
  ('5141','17820','0'),('7111','0','10000'),('6132','3000','0'),('7581','0','1000'),
  ('6701','1580','0'),('6171','400','0'),('4455','0','1000'),('34552','500','0'),('34551','200','0')])
 n1=rows([('1111','0','10000'),('1161','0','1000'),('2111','1000','0'),('28111','0','200'),
  ('5141','13350','0'),('7111','0','5000'),('6132','2000','0'),('4455','0','300'),('34552','100','0'),('34551','50','0')])
 n2=rows([('1111','0','10000'),('5141','11000','0'),('7111','0','2000'),('6132','1000','0')])
 for r,t in [(n,'25500'),(n1,'16500'),(n2,'12000')]:assert sum(D(x['debit']) for x in r)==sum(D(x['credit']) for x in r)==D(t)
 net=D('10000')-D('3000')-D('400')+D('1000')-D('1580');avant=net+D('1580')
 fiscal=avant+D('500')-D('200');impot=(fiscal*D('.20')).quantize(D('.01'),rounding=ROUND_HALF_UP)
 assert net==D('6020') and avant==D('7600') and fiscal==D('7900') and impot==D('1580')
 assert D('1000')+D('3000')-D('1000')==D('3000') # RAN N :RAN N-1 + bénéfice N-1 − distribution payée enN.
 assert D('10000')+D('3000')+net-D('2000')+D('500')==D('17520')
 assert D('10000')+D('1000')+D('3000')-D('1000')+D('200')==D('13200')
 assert D('10000')+D('1000')==D('11000')
 courant=D('10000')-D('3000')-D('400');assert courant==D('6600')
 assert courant+D('500')-D('200')==D('6900') and courant-D('1380')==D('5220')
 assert D('300')+D('2000')-D('1300')==D('1000')
 assert D('100')+D('800')-D('400')==D('500') and D('50')+D('300')-D('150')==D('200')
 b12={'nature':'Passage intégré733 N','reintegrations':'500','deductions':'200','deficit_disponible':'0','taux_is':'20',
  'regime_avantages':'Hypothèse documentaire fictive, régime à justifier','reference_source':'SOURCE INTEGREE733 B12'}
 b13=[{'code':'B13-N','nature':'Courant intégré733 N','reintegrations':'500','deductions':'200','impot_theorique':'1380',
  'regime_avantages':'Hypothèse courante fictive','reference_source':'SOURCE INTEGREE733 B13 N'},
  {'code':'B13-N1','nature':'Courant partiel intégré733 N1','reintegrations':'0','deductions':'0','impot_theorique':None,
   'regime_avantages':'Impôt théorique N1 non fourni','reference_source':'SOURCE INTEGREE733 B13 N1'}]
 b14=[{'nature':f,'solde_debut':d,'operations':o,'declarations':t,'references_declarations':'DECL FICTIVE733 '+f,
  'reference_source':'SOURCE INTEGREE733 B14 '+f} for f,d,o,t in [('4455','300','2000','1300'),('34552','100','800','400'),('34551','50','300','150')]]
 extra=[{'code':code,'nature':'Synthèse intégrée733 '+code,'effectif_moyen':e,'benefices_distribues':b,
  'resultat_par_titre':r,'distribution_par_titre':d,'affectations_justifiees':pv,
  'reference_source':'SOURCE INTEGREE733 EXTRA '+code} for code,e,b,r,d,pv in [
  ('C3-N','3.50','2000','60.20','20','PV FICTIF2027 pour2026,100titres ; décision à qualifier'),
  ('C3-N1','3','1000','30','10','PV FICTIF2026 pour2025,100titres ;1000payés en2026'),
  ('C3-N2','2','0','10','0','PV FICTIF2025 pour2024,100titres ; bénéfice1000reporté')]]
 for benef,x in zip(['6020','3000','1000'],extra):
  assert D(benef)/100==D(x['resultat_par_titre']) and D(x['benefices_distribues'])/100==D(x['distribution_par_titre'])
 return {'societe_fictive':'Atlas Recette733 SARL — simulation documentaire MAD','exercice':2026,
  'n':n,'n1':n1,'n2':n2,'b12':b12,'b13':b13,'b14':b14,'extra':extra,
  'reference_n2':'SOURCE INTEGREE733 N2','attendus':{'net_n':'6020.00','net_n1':'3000.00','net_n2':'1000.00',
   'situation_n':'17520.00','situation_n1':'13200.00','situation_n2':'11000.00','avant_impots_n':'7600.00',
   'fiscal_avant_deficit':'7900.00','benefice_fiscal':'7900.00','is_theorique':'1580.00',
   'courant_n':'6600.00','base_courante':'6900.00','courant_apres_declare':'5220.00','tva_collectee_fin':'1000.00',
   'tva_charges_fin':'500.00','tva_immo_fin':'200.00','tva_recuperable_fin':'700.00','tva_nette_documentaire':'300.00'},
  'limites':['CM/CSS/crédits/acomptes/solde inconnus, aucune liquidation ou dépôt confirmé',
   'B13 N1 impôt théorique non fourni reste inconnu','Effectifs et titres explicitement déclarés, aucun scénario de paie',
   'Import de balances indépendant du Journal, de la clôture et de l’archivage annuel']}


def cas(d):
 commun='Société fictive MAD2026, exercices2024/2025/2026, plan existant avec1161, droits administrateur/comptable, aucune base réelle.'
 c=[('I733-01','Préparation','Importer les trois sources','CSV N2 en2024 puis N/N1 en2026 ; en-têtes compte,debit,credit.',
 'Importer puis Contrôler et préparer et Conserver une nouvelle version ; noter versions/empreintes, sans inventer un ID.',
 'Totaux N25500,N1 16500,N2 12000 ; nets6020/3000/1000 ; sources conservées séparément par exercice.'),
 ('I733-02','Comparatif N2','Rattacher explicitement N-2','Préparation2024 et référence SOURCE INTEGREE733 N2.',
 'En2026 choisir la source2024 dans Rattacher une source N-2 aux indicateurs C3 ; confirmer, conserver puis conserver les indicateurs C3.',
 'N2 situation11000/net1000 ; provenance2024/version/SHA ; anciennes versions sans N2 inchangées.'),
 ('I733-03','B12','Passage fiscal documenté','RI500,déductions200,déficit disponible0,taux déclaré20, référence SOURCE INTEGREE733 B12.',
 'Choisir B12-N, saisir tous les champs du jeu JSON, confirmer et conserver. Vider ensuite le déficit dans une version de test :ne pas saisir0 implicitement.',
 'Net6020+impôt67 à1580=7600 ; avant déficit7900, bénéfice7900, IS théorique1580. Déficit vide :bénéfice/IS inconnus ; rétablir0 explicitement.'),
 ('I733-04','B13','Distinguer courant et impôt comptabilisé','N RI500/déductions200/impôt courant déclaré1380 ; N1 RI0/déductions0/impôt inconnu ; références du JSON.',
 'Remplir B13-N et B13-N1, conserver ; comparer au CPC figé sans copier automatiquement67 dans l’impôt courant.',
 'Courant6600/base6900/après impôt déclaré5220 ;67 à1580 distinct de1380. N1 courant/base3000, après impôt inconnu.'),
 ('I733-05','B14','Rapprocher les flux TVA justifiés','4455 :300+2000−1300 ;34552 :100+800−400 ;34551 :50+300−150, références du JSON.',
 'Saisir trois familles B14, conserver ; comparer fins aux soldes sources. Modifier opérations4455 en1999,99, conserver et relever l’écart puis rétablir2000 et conserver à nouveau.',
 'Fins1000/500/200, récupérable700, net documentaire300, écarts0. Variante fin999,99/écart−0,01 visible, aucun solde source corrigé.'),
 ('I733-06','C3','Intégrer les déclarations et conserver C3','N :3,50personnes/2000MAD/60,20MAD par titre/20MAD par titre ; N1 :3/1000/30/10 ; N2 :2/0/10/0 ; PV/références du JSON.',
 'Saisir les trois synthèses extra-comptables, conserver ; constater C3 ancien inchangé et message d’actualisation. Conserver les indicateurs C3 puis choisir chaque période.',
 'Situations17520/13200/11000, nets6020/3000/1000 ; déclarations avec bonnes unités, provenance et PV ; aucune lecture RH ou calcul par titre inféré.'),
 ('I733-07','Exports','Vérifier dossier et logo','Logo fictif PNG/JPEG ; préparation contenant N2,B12,B13,B14,C3 et extra.',
 'Télécharger le dossier ZIP ; ouvrir PDF/Excel/JSON et troisCSV ; vérifier manifestes SHA256, logo, références et inconnus ; comparer Journal avant/après.',
 'Même version et mêmes valeurs dans chaque format, N2 traçable, logo présent, CRC/SHA exacts ; aucune écriture, liquidation ou pièce déplacée.'),
 ('I733-08','Droits','Refus et isolement','Profils comptable/lecture et deuxième société fictive ; NaN, référence vide, empreinte incorrecte.',
 'Tester saisie/export sur1440/390, lecteur sans conservation, autre société invisible ; rejets sans version ; brouillon conservé, anciennes versions inchangées.',
 'Écriture403 pour lecteur, préparation404 autre société, refus422 ou conflit409 adaptés ; aucune mutation des écritures validées.')]
 return [{'id':i,'module':m,'objectif':o,'prerequis':commun,'donnees':v,'actions':a,'attendu':r,
  'ecritures':'Aucune :préparations documentaires uniquement.','fiscal':'IS théorique1580 au taux déclaré ; CM/CSS/crédits/acomptes/solde inconnus. Aucune validation de dépôt ou de conformité.',
  'controles':'Anciennes versions/empreintes et Journal inchangés ; sources explicites, inconnus distincts de0.',
  'statut':'Non testé','resultat_reel':'','anomalies':'','preuve':'Capture du formulaire/contrôle et export de la version, avec date et rôle.','preuve_reelle':'','observations':''} for i,m,o,v,a,r in c]


def generer():
 d=donnees();tests=cas(d)
 (HERE/'DONNEES_INTEGREES733.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (HERE/'CAS_INTEGRES733.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for p,nom in [('n','N'),('n1','N1'),('n2','N2')]:
  with (HERE/f'BALANCE_FICTIVE_INTEGREE733_{nom}.csv').open('w',encoding='utf8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n');w.writeheader();w.writerows(d[p])
 intro='''# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

Version 1 du 22 octobre 2026. Complément intégré : préparations depuis balances externes.

## Portée et organisation

Ce cahier complète le CAHIER_RECETTE_HISABPRO.pdf/.xlsx existant ; il ne le remplace pas et ne modifie aucun résultat humain déjà saisi. Il couvre les compléments B12/B13/B14/C3/N-2/extra livrés en725–731. Pour le parcours global depuis société vierge jusqu’au Journal, clôture et dossier annuel, suivre d’abord le cahier global ; les imports décrits ici restent indépendants du Journal et ne créent aucune archive annuelle.

Aucune recette humaine, conformité réglementaire ou production n’est validée automatiquement. Les huit cas ci-dessous restent Non testé. Les rapports techniques indiquent séparément les tests locaux réellement exécutés. RH/paie etpoint6 humain restent différés.

## Préparer la société fictive et les sources

Créer une société séparée nommée Atlas Recette733 SARL — simulation documentaire, deviseMAD, administrateur, comptable et lecteur. Ajouter un logo fictif PNG/JPEG. Créer explicitement les exercices2024,2025,2026 avec dates01/01–31/12 si absents. Vérifier le plan existant, notamment1161 Report à nouveau (solde créditeur). Aucun champ légal supplémentaire n’est imposé par ce scénario.

Utiliser uniquement les troisCSV BALANCE_FICTIVE_INTEGREE733_N2.csv (comme Balance N en2024), _N.csv et _N1.csv (comme N/N-1 en2026). Un compte par ligne, en-têtes compte,debit,credit, valeurs exactes dans DONNEES_INTEGREES733.json. N2 :4comptes/12000MAD ; N1 :10comptes/16500MAD ; N :13comptes/25500MAD. Chaque côté non mouvementé présent vaut explicitement0.

Les fichiers et références sont fictifs. Le scénario vérifie les projections et leur cohérence arithmétique, pas un exercice réel complet ou une paie. Les décisions et effectifs déclarés ne constituent aucune validation juridique/sociale. Les pièces restent à leur version d’origine.

## Calculs indépendants et rapprochement des années

N2 :capital10000, ventes2000, charges1000 →net1000 et situation11000. Le bénéfice2024 est reporté en2025 :RAN1000. N1 :capital10000+RAN1000+net3000−non-valeurs1000+amortissements200=situation13200. Le bénéfice2025 est3000 ; hypothèse déclarée de distribution1000 payée en2026 :RAN N=1000+3000−1000=3000.

N :ventes10000−charges3000−rémunérations6171 à400+produit non courant1000−impôt67 comptabilisé1580=net6020. Capitaux10000+RAN3000+net6020−non-valeurs2000+amortissements500=situation17520. Total actif/passif20020, contre14300 enN1 et11000 enN2. Les valeurs6171 et effectifs sont des hypothèses documentaires distinctes, aucun bulletin n’est supposé.

B12 :net6020+67 à1580=avant impôts7600 ; autres réintégrations500−déductions200 →7900. Déficit disponible0 explicitement déclaré →bénéfice7900 ; taux fictif déclaré20 →IS théorique1580. Ce résultat n’est pas l’IS exigible ou le solde à payer :CM/CSS/crédits/acomptes restent inconnus. Aucun régime ou avantage n’est déduit.

B13 :courant10000−3000−400=6600 ; base documentaire6600+500−200=6900 ; impôt théorique courant déclaré1380 ; courant après impôt déclaré6600−1380=5220. Le67 comptabilisé1580 ne remplace pas1380. Pour N1, courant3000, réintégrations/déductions0 explicites et impôt courant non fourni :après impôt reste inconnu.

B14 :4455 début300+opérations2000−déclarations1300=fin1000 ;34552 :100+800−400=500 ;34551 :50+300−150=200. Récupérable totale700 ; net documentaire300 ; écarts0. Les soldes N1 pour mémoire300/100/50 ne prouvent pas les flux ; ceux-ci sont déclarés avec leurs références.

Extra C3 :hypothèse explicitement documentée100titres. N :net6020/100=60,20 et distribution2000/100=20 ; N1 :3000/100=30 et1000/100=10 ; N2 :1000/100=10 et0/100=0. Ces divisions sont l’oracle du jeu ; l’application reçoit les valeurs par titre déclarées. Effectifs déclarés3,50/3/2personnes. PV fictifs2027 pour2026,2026 pour2025,2025 pour2024 :qualification à revoir, jamais dates inférées.

## Saisie exacte des compléments

Les données de DONNEES_INTEGREES733.json sont reprises dans la feuille Déclarations Excel. Pour chaque tableau, choisir Saisie documentée — à revoir, justification Synthèse intégrée fictive733, ajouter une seule ligne sauf B14 troisfamilles, puis saisir tous les champs fournis. Aucun identifiant de base ne doit être inventé :noter celui de la préparation source2024 effectivement conservée.

Pour N2, référence SOURCE INTEGREE733 N2. Pour B12, désignation Passage intégré733 N, référence SOURCE INTEGREE733 B12, autres réintégrations500, déductions200, déficit disponible0, taux20. Pour B13 N et N1, utiliser exactement les deux synthèses du JSON ; laisser l’impôt N1 vide. Pour B14, copier les troisflux et les références DECL FICTIVE733 suivies de4455/34552/34551. Pour extra C3, copier les trois périodes, les PV et SOURCE INTEGREE733 EXTRA suivie du code.

Après chaque conservation, la nouvelle version doit être sélectionnée sans F5. Les contrôles figés ne changent pas pendant un brouillon. Après rattachement N2 ou modification extra, conserver explicitement une nouvelle version des indicateurs C3 pour les inclure ; les anciens contrôles restent inchangés.

## Cas détaillés de recette
'''
 morceaux=[intro]
 for t in tests:
  morceaux += ['\n### '+t['id']+' — '+t['objectif']+'\n']
  for cle,label in [('module','Module'),('prerequis','Prérequis'),('donnees','Données exactes'),('actions','Actions dans l’interface'),('attendu','Résultat attendu'),('ecritures','Écritures attendues'),('fiscal','Impacts fiscaux attendus'),('controles','Contrôles'),('statut','Statut humain'),('preuve','Preuve attendue')]:morceaux.append(label+' : '+t[cle]+'\n')
 morceaux.append('''
## Limites et documents complémentaires

Les exports ne prouvent ni dépôt, ni paiement, ni conformité. Les références justificatives et les qualifications fiscales/sociales restent humaines. Les données historiques FEC/ETIC incomplètes ne sont pas réparées. Le nouveau calcul automatique CM/CSS/crédits du mode externe reste conditionné à ses sources officielles applicables ; accès intégral CGI2026 MEF/DGI en échec pendant cette session. Aucun taux ou schéma EDI inventé.

Développement des quatre compléments livré ; validations automatisées détaillées dans les rapports725/727/729/731/733. Recette utilisateur à effectuer. Installation cible et prêt pour production nonvalidés. Les autres limites du cahier global et de REGISTRE_LIMITES_RECETTE.md restent applicables. Les guides détaillés par lot sont dans l’index de livraison733.
''')
 texte='\n'.join(morceaux)
 for a,b in [('troisfamilles','trois familles'),('en2024','en 2024'),('en2025','en 2025'),('en2026','en 2026'),('4comptes','4 comptes'),('10comptes','10 comptes'),('13comptes','13 comptes'),('100titres','100 titres'),('PV fictifs2027','PV fictifs 2027'),('taux20','taux 20'),('déficit disponible0','déficit disponible 0'),('rémunérations6171','rémunérations 6171')]:texte=texte.replace(a,b)
 SOURCE.write_text(texte,encoding='utf8')
 spec=importlib.util.spec_from_file_location('guide733',ROOT/'docs/guide/generer_guide.py');guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs();guide.docx(blocs);guide.pdf(blocs)
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True);ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre de cas'])
 domaines=[t['module'] for t in tests]
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):
  ws.append([statut,'=SUM('+','.join("COUNTIF('"+dom+"'!K2:K2,A"+str(i)+')' for dom in domaines)+')'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 ws.append(['Périmètre','Complément de8cas, distinct du cahier global ; aucune recette humaine effectuée.'])
 chart=DoughnutChart();chart.title='Progression de la recette';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 headers=['ID','Module','Objectif','Prérequis','Données exactes','Actions détaillées','Résultat attendu','Écritures attendues','Impacts fiscaux','Contrôles','Statut humain','Résultat réel','Anomalies','Preuve attendue','Preuves réelles / captures','Observations']
 keys=['id','module','objectif','prerequis','donnees','actions','attendu','ecritures','fiscal','controles','statut','resultat_reel','anomalies','preuve','preuve_reelle','observations']
 for t in tests:
  ws=wb.create_sheet(t['module']);ws.append(headers);ws.append([t[k] for k in keys]);ws.row_dimensions[2].height=240
  v=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(v);v.add('K2')
 for p,nom in [('n','Balance N'),('n1','Balance N1'),('n2','Balance N2')]:
  ws=wb.create_sheet(nom);ws.append(['compte','debit','credit'])
  for r in d[p]:ws.append([r[k] for k in ('compte','debit','credit')])
 ws=wb.create_sheet('Déclarations');ws.append(['Information','Valeur exacte'])
 for k,v in d['attendus'].items():ws.append([k,v])
 for bloc in ('b12','b13','b14','extra'):
  for i,row in enumerate(d[bloc] if isinstance(d[bloc],list) else [d[bloc]],1):
   for k,v in row.items():ws.append([bloc+' '+str(i)+' '+k,'Inconnu' if v is None else v])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;ws.sheet_view.zoomScale=85
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=36
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  ws.print_options.horizontalCentered=True;ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A4;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
 wb.save(STEM.with_suffix('.xlsx'))


if __name__=='__main__':generer();print('Cahier intégré733 Word/PDF/Excel,8cas humains Non testé et3CSV, oracles indépendants vérifiés.')
