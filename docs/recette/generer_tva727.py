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
SOURCE=ROOT/'docs/LIASSE_BALANCES_TVA_727.md'
STEM=HERE/'MODE_EMPLOI_TVA_727'


def donnees():
    def rows(valeurs):
        return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    n=rows([('1111','0','10000'),('5141','10300','0'),('4455','0','1000'),('34552','500','0'),('34551','200','0')])
    n1=rows([('1111','0','10000'),('5141','10150','0'),('4455','0','300'),('34552','100','0'),('34551','50','0')])
    declarations=[{'code':'4455','debut':'300','operations':'2000','declarations':'1300','reference':'DECL FICTIVE727 4455'},
      {'code':'34552','debut':'100','operations':'800','declarations':'400','reference':'DECL FICTIVE727 34552'},
      {'code':'34551','debut':'50','operations':'300','declarations':'150','reference':'DECL FICTIVE727 34551'}]
    assert sum(D(r['debit']) for r in n)==sum(D(r['credit']) for r in n)==D('11000')
    assert sum(D(r['debit']) for r in n1)==sum(D(r['credit']) for r in n1)==D('10300')
    fins=[D(r['debut'])+D(r['operations'])-D(r['declarations']) for r in declarations]
    assert fins==list(map(D,['1000','500','200'])) and fins[0]-sum(fins[1:])==D('300')
    assert D('300')+D('1999.99')-D('1300')-D('1000')==D('-.01')
    return {'contexte':'Société fictive727 MAD2026, flux explicitement justifiés ; aucun dépôt confirmé.',
      'n':n,'n1':n1,'declarations':declarations,'attendus':{'fin_collectee':'1000.00','fin_charges':'500.00',
      'fin_immo':'200.00','recuperable_totale':'700.00','net_documentaire':'300.00','variante_fin':'999.99',
      'variante_ecart':'-0.01','variante_net':'299.99'},
      'inconnus':['N-1 ne prouve pas le début N','Déclaration absente : fin reconstituée et écart inconnus',
      'Aucun dépôt, liquidation ou montant à payer déduit'],
      'impacts':'Aucune écriture, déclaration, liquidation ou donnée TVA réelle créée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_TVA727.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n','n1'):
        nom=HERE/f'BALANCE_FICTIVE_TVA727_{"N" if p=="n" else "N1"}.csv'
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide727',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|V727-')]
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
    for periode in ('n','n1'):
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
    generer();print('Word/PDF/Excel727 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
