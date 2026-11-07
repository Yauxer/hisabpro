"""Scénario annuel fiscal755 : calculs indépendants, aucun accès DB ou moteur HisabPro."""
from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
import ast,csv,json
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def f(v):return format(D(v),'.2f')
def mouvement(id,date,libelle,debits,credits):
 assert sum(D(str(v)) for v in debits.values())==sum(D(str(v)) for v in credits.values()),id
 return {'id':id,'date':date,'libelle':libelle,'debits':{k:f(v) for k,v in debits.items()},'credits':{k:f(v) for k,v in credits.items()}}
def balance(operations,ouverture=None):
 soldes=defaultdict(lambda:D('0'),ouverture or {})
 for op in operations:
  for k,v in op['debits'].items():soldes[k]+=D(v)
  for k,v in op['credits'].items():soldes[k]-=D(v)
 assert sum(soldes.values())==0
 return {k:v for k,v in sorted(soldes.items()) if v!=0}
def resultat(soldes):return -sum(v for k,v in soldes.items() if k.startswith(('6','7')))
def colonnes(soldes):return [{'compte':k,'debit':f(max(D(0),v)),'credit':f(max(D(0),-v))} for k,v in soldes.items()]


def donnees():
 n1=[mouvement('N1-01','2025-01-01','Capital fictif',{'5141':10000},{'1111':10000}),
  mouvement('N1-02','2025-06-15','Prestations2025 HT100000 TVA20000',{'3421':120000},{'7124':100000,'4455':20000}),
  mouvement('N1-03','2025-06-20','Encaissement client2025',{'5141':120000},{'3421':120000}),
  mouvement('N1-04','2025-07-15','TVA2025 réglée',{'4455':20000},{'5141':20000}),
  mouvement('N1-05','2025-12-31','Acomptes2025 cumulés, détail à sourcer dans un vrai dossier',{'3453':17600},{'5141':17600}),
  mouvement('N1-06','2025-12-31','Impôt2025 sur bénéfice100000 à17,5%',{'6701':17500},{'4453':17500})]
 bn1=balance(n1);rn1=resultat(bn1);assert rn1==82500
 ouverture={k:v for k,v in bn1.items() if not k.startswith(('6','7'))};ouverture['1181']=-rn1
 assert sum(ouverture.values())==0
 ventes=D('140000');charges=D('21500');interets=D('1500');tva_ventes=ventes*D('.20');tva_achats=charges*D('.20')
 pprf=interets*D('.20');ras_tiers=D('4000')*D('.05')
 n=[mouvement('N-AG','2026-03-15','PV fictif AGO : report à nouveau du résultat2025',{'1181':rn1},{'1161':rn1}),
  mouvement('N-01','2026-03-15','Liquidation2025 :17500 imputés, excédent100 restant',{'4453':17500},{'3453':17500}),
  mouvement('N-02','2026-06-15','Conseil à organisme public, HT4000 et TVA800',{'3421':4800},{'7124':4000,'4455':800}),
  mouvement('N-03','2026-06-20','Client public :cash4600 et retenueIS200',{'5141':4600,'3453':ras_tiers},{'3421':4800}),
  mouvement('N-04','2026-04-15','Autres prestations privées HT136000 TVA27200',{'3421':163200},{'7124':136000,'4455':27200}),
  mouvement('N-05','2026-04-30','Encaissement autres clients privés',{'5141':163200},{'3421':163200}),
  mouvement('N-06','2026-02-28','Honoraires société fournisseur HT21500 TVA4300',{'6136':charges,'34552':tva_achats},{'4411':25800}),
  mouvement('N-07','2026-03-10','Paiement fournisseur personne morale',{'4411':25800},{'5141':25800}),
  mouvement('N-08','2026-03-20','Intérêts1500 brut, PPRF300 et cash1200',{'5141':interets-pprf,'3453':pprf},{'7381':interets}),
  mouvement('N-09','2026-07-15','TVA Q2 soldée après imputation crédit TVA Q1',{'4455':tva_ventes},{'34552':tva_achats,'5141':tva_ventes-tva_achats})]
 ap=[{'numero':'1','date_mouvement':'2026-03-31','verse':'4800','credit_anterieur':'100','retenue':'100','reference_credit':'CR755-A','reference_source':'AP755-Q1'},
     {'numero':'2','date_mouvement':'2026-06-30','verse':'4950','credit_anterieur':'0','retenue':'50','reference_credit':'CR755-B','reference_source':'AP755-Q2'},
     {'numero':'3','date_mouvement':'2026-09-30','verse':'5000','credit_anterieur':'0','retenue':'0','reference_credit':'','reference_source':'AP755-Q3'},
     {'numero':'4','date_mouvement':'2026-12-31','verse':'5000','credit_anterieur':'0','retenue':'0','reference_credit':'','reference_source':'AP755-Q4'}]
 for a in ap:n.append(mouvement('N-AP'+a['numero'],a['date_mouvement'],'Versement effectif acompte'+a['numero'],{'3453':D(a['verse'])},{'5141':D(a['verse'])}))
 benefice=ventes+interets-charges;is_n=benefice*D('.20');n.append(mouvement('N-IS','2026-12-31','Provision IS principal, aucun paiement de solde',{'6701':is_n},{'4453':is_n}))
 n.sort(key=lambda o:o['date']);n1.sort(key=lambda o:o['date'])
 bn=balance(n,ouverture);rn=resultat(bn)
 cash=sum(D(a['verse']) for a in ap);ant=sum(D(a['credit_anterieur']) for a in ap);retenues=sum(D(a['retenue']) for a in ap)
 credits=pprf+ras_tiers;dispo=credits-retenues;acomptes=cash+ant+retenues;cm_calc=(ventes+interets)*D('.0025');cm=max(D('3000'),cm_calc)
 du=max(is_n,cm);solde=du-dispo-acomptes
 assert benefice==120000 and is_n==24000 and rn==96000 and cash==19750 and credits==500 and dispo==350 and acomptes==20000 and solde==3650
 assert bn['5141']==192150 and bn['3453']==20350 and bn['4453']==-24000
 assert bn['3453']==cash+ant+credits and -bn['4453']-bn['3453']==solde
 assert sum(max(D(0),v) for v in bn.values())==258000 and sum(max(D(0),v) for v in bn1.values())==127500
 assert D('100000')*D('.175')==17500 and D('17600')-D('17500')==ant and D('100000')*D('.20')==20000
 for a in ap:assert sum(D(a[k]) for k in ('verse','credit_anterieur','retenue'))==5000
 return {'schema_version':1,'societe_fictive':'ATLAS CONSEIL RECETTE755 SARL','ville':'Casablanca','devise':'MAD','exercice':2026,
  'periode':{'debut':'2026-01-01','fin':'2026-12-31'},'date_controle':'2027-03-15','date_controle_fictive':True,
  'hypotheses':['Société IS droit commun, bénéfices sous300000 en2025 et sous100millions en2026, aucun régime spécifique','TVA20% sur prestations et honoraires fictifs','Client public et rémunération de conseil éligible déclarés ; autres clients privés hors nouvelle obligation RAS2026','Aucun déficit, retraitement ou autre crédit fiscal','CM sans exonération et entièrement au taux standard ; CSS sur dernier clos2025 de100000','Hypothèse explicite d’ouverture : résultat2025 en instance1181 puis PV AGO15/03/2026 en report1161 ; aucune écriture de clôture générée par ces fichiers'],
  'balance_n':colonnes(bn),'balance_n1':colonnes(bn1),'ouverture_n':colonnes(ouverture),'operations_n':n,'operations_n1':n1,'acomptes':ap,
  'credits':[{'nature':'PPRF bancaire fictif755','type_credit':'PPRF — CGI159','exercice_rattachement':'2026','date_retenue':'2026-03-20','date_allocation':'','categorie_payeur':'','eligibilite_confirmee':'oui','montant':'300','deja_impute_acomptes':'100','autres_utilisations':'0','reference_source':'CR755-A'},
             {'nature':'Conseil organisme public fictif755','type_credit':'Rémunérations de tiers — CGI157','exercice_rattachement':'2026','date_retenue':'2026-06-20','date_allocation':'2026-06-20','categorie_payeur':'Public ou filiale publique','eligibilite_confirmee':'oui','montant':'200','deja_impute_acomptes':'50','autres_utilisations':'0','reference_source':'CR755-B'}],
  'attendus':{k:f(v) for k,v in {'debit_credit_n':258000,'debit_credit_n1':127500,'actif_passif_n':212500,'actif_passif_n1':110000,
   'resultat_net_n':rn,'resultat_net_n1':rn1,'resultat_avant_is':benefice,'benefice_fiscal':benefice,'is_theorique':is_n,'cm_base':ventes+interets,'cm_calculee':cm_calc,'cm_exigible':cm,
   'maximum_is_cm':du,'credits_total':credits,'credits_deja_utilises':retenues,'credits_disponibles':dispo,'acomptes_cash':cash,'ancien_impute':ant,'acomptes_imputables':acomptes,
   'ancien_restant':0,'solde_is_propose':solde,'excedent_arithmetique':0,'css_proposee':0,'tva_collectee':tva_ventes,'tva_recuperable':tva_achats,'tva_versee':tva_ventes-tva_achats}.items()},
  'statut_humain':'Non testé','limites':['Jeu exclusivement fictif, aucune donnée réelle','Import et préparation ne créent aucune écriture','Aucun paiement ou liquidation confirmé','Aucune liasse complète prête à déposer ni XML/EDI officiel','Calendrier CSS et éligibilité réelle à revoir sur pièces']}


def generer_donnees():
 data=donnees();(HERE/'DONNEES_FISCALES755.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 tree=ast.parse((ROOT/'hisabpro-backend/services/plan_comptable.py').read_text(encoding='utf-8'))
 plan=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='PLAN_COMPTABLE' for a in n.targets))
 for k,s in [('balance_n','N'),('balance_n1','N1')]:
  with (HERE/f'BALANCE_FICTIVE_FISCALE755_{s}.csv').open('w',encoding='utf-8-sig',newline='') as fcsv:
   w=csv.DictWriter(fcsv,fieldnames=['compte','intitule','debit','credit'],delimiter=';',lineterminator='\n');w.writeheader()
   w.writerows({**x,'intitule':plan[x['compte']]} for x in data[k])
 Image.new('RGB',(20,12),'#185FA5').save(HERE/'LOGO_FICTIF755.png')
 from reportlab.pdfgen import canvas
 pdf=canvas.Canvas(str(HERE/'JUSTIFICATIFS_FICTIFS755.pdf'),invariant=1)
 def titre(s):
  pdf.setFont('Helvetica-Bold',13);pdf.drawString(38,800,'HISABPRO — DOSSIER FICTIF DE RECETTE755')
  pdf.setFont('Helvetica-Bold',10);pdf.drawString(38,780,'AUCUNE VALEUR FISCALE OU COMPTABLE REELLE')
  pdf.setFont('Helvetica',10);pdf.drawString(38,755,s)
 titre('ATLAS CONSEIL RECETTE755 SARL — Sources du scenario uniquement')
 lignes=['NOTE755-B12 : benefice2026 120000, IS20%=24000 ; aucun retraitement/deficit.',
  'NOTE755-CM : base141500 ;0,25%=353,75 ;minimum3000 ;maximumIS/CM24000.',
  'NOTE755-REF : dernierclos2025,benefice100000,IS17,5%=17500,acomptes17600.',
  'Excedent2025 100 ;reference2026 adaptee100000 x20%=20000,4quarts5000.',
  'NOTE755-CSS : contribution2026 sur dernierclos2025 de100000 ;CSS0.',
  'PV AGO FICTIF15/03/2026 : resultat2025 82500 affecte au report1161.',
  'CR755-A : interets20/03/2026,brut1500,PPRF20%=300 ;100deja suracompte1.',
  'CR755-B : conseil public alloue/retenu20/06/2026,HT4000,RAS5%=200.',
  'CR755-B :50deja suracompte2 ;autresutilisations0 pourlesdeuxcredits.',
  'Disponiblecredits :500-150=350. Pas de piece fiscale reelle attestee.']
 y=725
 for line in lignes:pdf.drawString(38,y,line);y-=24
 pdf.showPage();titre('Quittances et affectations fictives ;aucun paiement effectue par cette preparation')
 y=720
 for a in data['acomptes']:
  for line in [a['reference_source']+' — '+a['date_mouvement'],
   'Cash '+a['verse']+' MAD ;ancien '+a['credit_anterieur']+' ;retenue '+a['retenue']+' '+a['reference_credit'],
   'Couverture declaree5000MAD,aucune double ecriture de retenue.']:
   pdf.drawString(38,y,line);y-=22
  y-=18
 pdf.drawString(38,y-10,'REVUE755 :24000-350-20000=3650MAD de solde simule ;CSS0 separee.')
 pdf.drawString(38,y-40,'Ces notes ne prouvent ni eligibilite reelle,ni declaration,ni paiement fiscal.')
 pdf.save()
 return data


def generer_documents():
 """Documents de recette humaine ; aucune preuve humaine préremplie."""
 import importlib.util,re,shutil
 from openpyxl import Workbook
 from openpyxl.styles import Alignment,Font,PatternFill
 from openpyxl.worksheet.datavalidation import DataValidation
 from openpyxl.workbook.properties import CalcProperties
 from openpyxl.chart import DoughnutChart,Reference
 source=ROOT/'docs/RECETTE_FISCALE_INTEGREE_755.md'
 stem=HERE/'CAHIER_RECETTE_FISCALE_755'
 texte=source.read_text(encoding='utf8')
 spec=importlib.util.spec_from_file_location('guide755',ROOT/'docs/guide/generer_guide.py')
 guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
 guide.SOURCE=source;guide.STEM=stem;blocs=guide.blocs();orig=guide.word_table
 widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
 guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
 guide.docx(blocs);table=guide.Table
 guide.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
 guide.pdf(blocs)
 cas=[[c.strip() for c in line.strip('|').split('|')] for line in texte.splitlines() if line.startswith('|F755-')]
 assert len(cas)==14 and all(len(c)==4 and c[3]=='Non testé' for c in cas)
 data=json.loads((HERE/'DONNEES_FISCALES755.json').read_text(encoding='utf8'))
 # Recalcul indépendant sans moteur financier, SQL ou application.
 assert donnees()==data
 wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
 ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
 for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K15,A{i})'])
 ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
 ws.append(['Périmètre','Complément annuel Liasse seule ; ne remplace pas la recette intégrale du produit'])
 ws.append(['Société fictive',data['societe_fictive']]);ws.append(['Attention','Aucune déclaration, paiement ou liquidation confirmée. Qualifications fictives à vérifier sur pièces réelles.'])
 chart=DoughnutChart();chart.title='Recette utilisateur';chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=5),titles_from_data=True);chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=5));ws.add_chart(chart,'D2')
 sections={};titre=None
 for line in texte.splitlines():
  if line.startswith('## '):titre=line[3:];sections[titre]=[]
  elif titre:sections[titre].append(line)
 etapes=[k for k in sections if k.startswith('Étape')]
 choix=[etapes[0],etapes[1],etapes[2],etapes[3],etapes[3],etapes[4],etapes[5],etapes[6],etapes[7],None,None,None,None,None]
 ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
 for idx,(ident,action,result,statut) in enumerate(cas):
  details='\n'.join(sections[choix[idx]]).strip() if choix[idx] else '\n'.join(sections['Contrôles négatifs']).strip()
  if idx==9:details='Rôle comptable puis lecture ; largeur390px. Créer les utilisateurs fictifs depuis administration ; appliquer les permissions du rôle. Voir guide étape1 pour identité et étapes2–8 pour données.'
  ws.append([ident,'Liasse seule / scénario annuel755',action,'Environnement isolé ; société neuve pour01 puis cas précédents réussis. Utiliser une copie pour les négatifs.',details,action+'\n'+details,result,'Aucune écriture créée par import ou formulaires. Opérations N/N-1 : calculs indépendants expliquant les CSV ; ne pas les saisir en Journal dans ce parcours.','Bénéfice120000 ; IS24000 ; crédits disponibles350 ; acomptes20000 ; solde proposé3650 ; CSS0 séparée. Pas de confirmation fiscale.',result,statut,'','','','','Captures et fichiers explicitement décrits dans le résultat attendu ; preuve à renseigner après exécution humaine'])
 validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(validation);validation.add('K2:K15')
 # Les libellés sont ceux du plan comptable du dépôt, pas des intitulés inventés.
 noms={}
 for tag in ('N','N1'):
  with (HERE/f'BALANCE_FICTIVE_FISCALE755_{tag}.csv').open(encoding='utf-8-sig',newline='') as fi:
   noms.update({row['compte']:row['intitule'] for row in csv.DictReader(fi,delimiter=';')})
 for titre,key in [('Balance N','balance_n'),('Balance N-1','balance_n1')]:
  ws=wb.create_sheet(titre);ws.append(['Compte','Intitulé exact','Débit MAD','Crédit MAD'])
  for a in data[key]:ws.append([a['compte'],noms[a['compte']],float(a['debit']),float(a['credit'])])
  fin=ws.max_row;ws.append(['TOTAL','',f'=SUM(C2:C{fin})',f'=SUM(D2:D{fin})']);ws.append(['Équilibre','',f'=C{fin+1}-D{fin+1}'])
 for titre,key in [('Opérations N','operations_n'),('Opérations N-1','operations_n1')]:
  ws=wb.create_sheet(titre);ws.append(['ID','Date','Opération fictive','Compte','Débit MAD','Crédit MAD'])
  if key=='operations_n':
   for a in data['ouverture_n']:ws.append(['OUVERTURE','2026-01-01','Soldes N-1 classes1–5 et résultat en instance1181',a['compte'],float(a['debit']),float(a['credit'])])
  for op in data[key]:
   for compte in sorted(set(op['debits'])|set(op['credits'])):ws.append([op['id'],op['date'],op['libelle'],compte,float(op['debits'].get(compte,0)),float(op['credits'].get(compte,0))])
  fin=ws.max_row;ws.append(['TOTAL','','','',f'=SUM(E2:E{fin})',f'=SUM(F2:F{fin})'])
 ws=wb.create_sheet('Paramètres');ws.append(['Bloc','Champ ou rubrique','Valeur exacte / instruction'])
 for k in ('societe_fictive','ville','devise','exercice','periode','date_controle'):ws.append(['Identité',k,json.dumps(data[k],ensure_ascii=False)])
 for h in data['hypotheses']:ws.append(['Hypothèse explicite','Fictif',h])
 for titre in etapes:
  for line in sections[titre]:
   if line.strip():ws.append([titre,'Saisie exacte',line])
 for groupe in ('acomptes','credits'):
  for row in data[groupe]:
   for k,v in row.items():ws.append([groupe+' '+row['reference_source'],k,str(v)])
 ws=wb.create_sheet('Calculs indépendants');ws.append(['Contrôle','Oracle exact MAD','Formule Excel indépendante','Portée'])
 calculs=[('Résultat N-1','82500.00','=100000-17500'),('Ancien excédent','100.00','=17600-17500'),('Avant IS N','120000.00','=140000+1500-21500'),('IS N','24000.00','=120000*20%'),('Résultat net N','96000.00','=120000-24000'),('CM calculée','353.75','=141500*0.25%'),('CM exigible','3000.00','=MAX(353.75,3000)'),('Maximum IS/CM','24000.00','=MAX(24000,3000)'),('Crédits disponibles','350.00','=300+200-100-50'),('Cash acomptes','19750.00','=4800+4950+5000+5000'),('Acomptes imputables','20000.00','=19750+100+150'),('Solde proposé','3650.00','=24000-350-20000'),('Actif N','212500.00','=192150+20350'),('Passif N','212500.00','=10000+82500+96000+24000'),('CSS séparée','0.00','=0')]
 for a,b,c in calculs:ws.append([a,float(b),c,'Oracle calculé en Decimal par Python ; formules Office à recalculer lors de la recette humaine'])
 for k,v in data['attendus'].items():ws.append([k,str(v),'','Valeur indépendante exacte issue du jeu fictif'])
 ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
 for c in cas:ws.append([c[0],'',''])
 ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
 for ws in wb:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
  for row in ws:
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
 for i in range(2,16):wb['Fiscalité'].row_dimensions[i].height=180
 wb.save(stem.with_suffix('.xlsx'))
 preuve=ROOT/'.codex-tests/fiscal755-comptable-390.png'
 if preuve.exists():shutil.copyfile(preuve,HERE/'PREUVE_FISCALE755_MOBILE.png')
 return {'cas_humains_non_testes':14,'feuilles':wb.sheetnames}


if __name__=='__main__':
 print(generer_donnees()['attendus'])
 print(generer_documents())
