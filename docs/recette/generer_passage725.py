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
SOURCE=ROOT/'docs/LIASSE_BALANCES_PASSAGE_FISCAL_725.md'
STEM=HERE/'MODE_EMPLOI_PASSAGE_FISCAL_725'


def donnees():
    def rows(valeurs):
        return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    n=rows([('1111','0','10000'),('5141','16400','0'),('7111','0','10000'),
            ('6132','3000','0'),('7581','0','1000'),('6701','1600','0')])
    declarations=[{'code':'B12-N','reintegrations':'500','deductions':'200','deficit_disponible':'1000',
        'taux_is':'20','reference_source':'NOTE FICTIVE725, déficit éligible explicitement déclaré'}]
    assert sum(D(r['debit']) for r in n)==sum(D(r['credit']) for r in n)==D('21000')
    net=D('10000')-D('3000')+D('1000')-D('1600');avant=net+D('1600')
    avant_def=avant+D('500')-D('200');impute=min(D('1000'),max(avant_def,D(0)))
    benefice=max(D(0),avant_def-impute)
    from decimal import ROUND_HALF_UP
    impot=(benefice*D('20')/100).quantize(D('.01'),rounding=ROUND_HALF_UP)
    variante=(benefice*D('19.999')/100).quantize(D('.01'),rounding=ROUND_HALF_UP)
    assert (net,avant,avant_def,benefice,impot,variante)==tuple(map(D,['6400','8000','8300','7300','1460','1459.93']))
    return {'contexte':'Société fictive725 MAD2026, hypothèses fiscales déclarées pour test arithmétique uniquement.',
        'n':n,'declarations':declarations,'attendus':{'net':'6400.00','impots_67':'1600.00','avant_impots':'8000.00',
        'reintegrations_depuis_net':'2100.00','avant_deficit':'8300.00','impute':'1000.00','restant':'0.00',
        'benefice':'7300.00','is_theorique':'1460.00','variante_taux':'1459.93'},
        'inconnus':['Déficit absent : imputation/bénéfice/IS inconnus','Taux absent : IS inconnu',
        'CM/CSS/crédits/acomptes/solde final inconnus ; IS théorique distinct du montant à payer'],
        'impacts':'Aucune écriture, liquidation, imputation confirmée ou donnée fiscale réelle créée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_PASSAGE725.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n',):
        nom=HERE/f'BALANCE_FICTIVE_PASSAGE725_{"N" if p=="n" else "N1"}.csv'
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide725',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|F725-')]
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
    for periode in ('n',):
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
    generer();print('Word/PDF/Excel725 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
