"""Recette documentaire B12 : génération reproductible, aucune connexion DB."""
from pathlib import Path
from decimal import Decimal as D
import csv,importlib.util,json,re
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_COMPARATIF_N2_729.md'
STEM=HERE/'MODE_EMPLOI_COMPARATIF_N2_729'


def donnees():
    def rows(valeurs):
        return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    ancien=json.loads((HERE/'DONNEES_INDICATEURS723.json').read_text(encoding='utf8'))
    n,n1=ancien['n'],ancien['n1']
    n2=rows([('1111','0','10000'),('5141','11000','0'),('7111','0','2000'),('6132','1000','0')])
    technique=rows([('1111','0','10000'),('5141','11000','0'),('1191','0','1000')])
    for r,total in [(n,'21500'),(n1,'15200'),(n2,'12000'),(technique,'11000')]:
        assert sum(D(x['debit']) for x in r)==sum(D(x['credit']) for x in r)==D(total)
    assert D('2000')-D('1000')==D('1000') and D('10000')+D('1000')==D('11000')
    return {'contexte':'Société fictive729 MAD2026, source N2 explicitement conservée en2024.',
      'n':n,'n1':n1,'n2':n2,'technique':technique,
      'declarations':[{'code':'SOURCE-N2','exercice':'2024','reference_source':'BALANCE FICTIVE729 N-2 explicitement choisie'}],
      'attendus':{'situation_n':'14500.00','net_n':'6000.00','situation_n1':'12200.00','net_n1':'3000.00',
      'situation_n2':'11000.00','ca_n2':'2000.00','avant_impots_n2':'1000.00','impots_n2':'0.00','net_n2':'1000.00'},
      'inconnus':['Sans rattachement explicite N2 reste inconnu','Après solde119, activité N2 inconnue',
      'Effectif moyen, distributions et données par titre inconnus'],
      'impacts':'Aucune écriture, salarié, liquidation ou pièce réelle créée ou déplacée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_COMPARATIF729.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n','n1','n2','technique'):
        noms={'n':'N','n1':'N1','n2':'N2','technique':'TECHNIQUE'}
        nom=HERE/f'BALANCE_FICTIVE_COMPARATIF729_{noms[p]}.csv'
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide729',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|N729-')]
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
    for periode in ('n','n1','n2','technique'):
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
    generer();print('Word/PDF/Excel729 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
