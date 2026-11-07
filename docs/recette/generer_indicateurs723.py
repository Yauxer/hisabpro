"""Recette documentaire C3 : génération reproductible, aucune connexion DB."""
from pathlib import Path
from decimal import Decimal as D
import csv,importlib.util,json,re
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_INDICATEURS_723.md'
STEM=HERE/'MODE_EMPLOI_INDICATEURS_723'


def donnees():
    def rows(valeurs):return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    n=rows([('1111','0','10000'),('2111','2000','0'),('28111','0','500'),('5141','14500','0'),
            ('7111','0','10000'),('6132','3000','0'),('7581','0','1000'),('6701','1600','0'),('6171','400','0')])
    n1=rows([('1111','0','10000'),('2111','1000','0'),('28111','0','200'),('5141','12200','0'),
             ('7111','0','5000'),('6132','2000','0')])
    technique=rows([('1111','0','10000'),('2111','2000','0'),('28111','0','500'),('5141','14500','0'),('1191','0','6000')])
    for lignes,total in ((n,'21500'),(n1,'15200'),(technique,'16500')):
        assert sum(D(r['debit']) for r in lignes)==sum(D(r['credit']) for r in lignes)==D(total)
    courant=D('10000')-D('3000')-D('400');avant=courant+D('1000');net=avant-D('1600')
    situation=D('10000')+net-D('2000')+D('500')
    assert courant==D('6600') and avant==D('7600') and net==D('6000') and situation==D('14500')
    assert D('10000')+D('3000')-D('1000')+D('200')==D('12200')
    assert D('10000')+D('6000')-D('2000')+D('500')==situation
    return {'contexte':'Société fictive723 MAD, exercice2026. Jeu distinct du B13 fictif721, aucune donnée réelle.',
        'n':n,'n1':n1,'technique':technique,'declarations':[],
        'attendus':{'situation_n':'14500.00','ca_n':'10000.00','avant_impots_n':'7600.00','impots_n':'1600.00',
            'net_n':'6000.00','remunerations6171_n':'400.00','situation_n1':'12200.00','ca_n1':'5000.00',
            'net_n1':'3000.00','impots_n1':'0.00','remunerations6171_n1':'0.00','situation_apres119':'14500.00'},
        'inconnus':['N-2 non fourni','Effectif moyen et données par titre non fournis',
                    'Distributions et affectations non fournies','Activité après119 indisponible, pas zéro'],
        'impacts':'Aucune écriture, liquidation ou donnée RH créée ou modifiée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_INDICATEURS723.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n','n1','technique'):
        nom=HERE/('BALANCE_FICTIVE_INDICATEURS723_'+{'n':'N','n1':'N1','technique':'TECHNIQUE'}[p]+'.csv')
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide723',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|I723-')]
    assert len(cas)==6 and all(len(r)==4 and r[3]=='Non testé' for r in cas)
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
    ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Recette!D2:D7,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Recette');ws.append(['ID','Actions et données exactes','Résultat et preuve attendus',
        'Statut humain','Résultat réel','Anomalies','Preuves réelles','Écritures et impacts attendus'])
    for ident,actions,result,statut in cas:ws.append([ident,actions,result,statut,'','','',d['impacts']])
    validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"')
    ws.add_data_validation(validation);validation.add('D2:D7')
    ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
    ws.append(['Contexte',d['contexte']])
    for periode in ('n','n1','technique'):
        for row in d[periode]:ws.append([periode+' '+row['compte'],'Débit '+row['debit']+' ; crédit '+row['credit']+' MAD'])
    for row in d['declarations']:
        for k,v in row.items():ws.append([row['code']+' '+k,v])
    for k,v in d['attendus'].items():ws.append([k,v+' MAD'])
    for note in d['inconnus']:ws.append(['Limite',note])
    ws=wb.create_sheet('Preuves');ws.append(['ID','Fichier ou capture réelle','Observations'])
    for row in cas:ws.append([row[0],'',''])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    for ws in wb:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=48
        for row in ws:
            for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
    for i in range(2,8):wb['Recette'].row_dimensions[i].height=150
    wb.save(STEM.with_suffix('.xlsx'))


if __name__=='__main__':
    generer();print('Word/PDF/Excel723 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
