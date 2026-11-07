"""Recette documentaire B13 : génération reproductible, aucune connexion DB."""
from pathlib import Path
from decimal import Decimal as D
import csv,importlib.util,json,re
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'docs/LIASSE_BALANCES_RESULTAT_COURANT_721.md'
STEM=HERE/'MODE_EMPLOI_RESULTAT_COURANT_721'


def donnees():
    def rows(valeurs):
        return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    n=rows([('1111','0','10000'),('5141','16400','0'),('7111','0','10000'),
            ('6132','3000','0'),('7581','0','1000'),('6701','1600','0')])
    n1=rows([('1111','0','10000'),('5141','13000','0'),('7111','0','5000'),('6132','2000','0')])
    declarations=[{'code':'B13-N','reintegrations':'500','deductions':'200','impot_theorique':'1200',
                   'reference_source':'NOTE FICTIVE721 N, postes courants seulement'},
                  {'code':'B13-N1','reintegrations':'0','deductions':'0','impot_theorique':'0',
                   'reference_source':'NOTE FICTIVE721 N-1, zéros déclarés'}]
    # Oracle arithmétique indépendant : aucune importation du moteur applicatif.
    assert sum(D(r['debit']) for r in n)==sum(D(r['credit']) for r in n)==D('21000')
    assert sum(D(r['debit']) for r in n1)==sum(D(r['credit']) for r in n1)==D('15000')
    courant=D('10000')-D('3000');courant1=D('5000')-D('2000')
    net=courant+D('1000')-D('1600')
    assert net==D('6400') and D('16400')==D('10000')+net
    assert courant==D('7000') and courant1==D('3000')
    assert courant+D('500')-D('200')==D('7300')
    assert courant-D('1200')==D('5800')
    assert courant-D('1199.99')==D('5800.01')
    return {'contexte':'Société fictive721 MAD, exercice2026. Déclarations arithmétiques sans taux fiscal calculé.',
        'n':n,'n1':n1,'declarations':declarations,
        'attendus':{'courant_n':'7000.00','non_courant_n':'1000.00','impots_comptabilises_n':'1600.00',
            'net_n':'6400.00','base_documentaire_n':'7300.00','courant_apres_declare_n':'5800.00',
            'courant_n1':'3000.00','variante_apres_n':'5800.01'},
        'inconnus':['Impôt théorique vide ne vaut pas1600 ou0','Régime/avantages N-1 non fournis',
                    'Après clôture119 le courant ne vaut pas0 déduit'],
        'impacts':'Aucune écriture, liquidation ou opération fiscale réelle créée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_COURANT721.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n','n1'):
        nom=HERE/f'BALANCE_FICTIVE_COURANT721_{"N" if p=="n" else "N1"}.csv'
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide721',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|B721-')]
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
    generer();print('Word/PDF/Excel721 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
