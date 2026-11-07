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
SOURCE=ROOT/'docs/LIASSE_BALANCES_C3_EXTRA_731.md'
STEM=HERE/'MODE_EMPLOI_C3_EXTRA_731'


def donnees():
    def rows(valeurs):
        return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
    ancien=json.loads((HERE/'DONNEES_COMPARATIF729.json').read_text(encoding='utf8'))
    n,n1,n2=ancien['n'],ancien['n1'],ancien['n2']
    perte=rows([('1111','0','10000'),('5141','8999','0'),('6132','1001','0')])
    declarations=[{'code':code,'effectif_moyen':e,'benefices_distribues':b,'resultat_par_titre':r,
      'distribution_par_titre':d,'reference_source':'NOTE EXTRA FICTIVE731 '+code}
      for code,e,b,r,d in [('C3-N','3.50','2000','60','20'),('C3-N1','3','1000','30','10'),('C3-N2','2','0','10','0')]]
    for r,total in [(n,'21500'),(n1,'15200'),(n2,'12000'),(perte,'10000')]:
        assert sum(D(x['debit']) for x in r)==sum(D(x['credit']) for x in r)==D(total)
    for net,d in zip(['6000','3000','1000'],declarations):
        assert D(net)/100==D(d['resultat_par_titre'])
        assert D(d['benefices_distribues'])/100==D(d['distribution_par_titre'])
    assert -D('1001')/100==D('-10.01') and D('10000')-D('1001')==D('8999')
    return {'contexte':'Société fictive731 MAD2026, données extra-comptables déclarées, aucun scénario de paie déduit.',
      'n':n,'n1':n1,'n2':n2,'perte':perte,'declarations':declarations,
      'attendus':{'effectif_n':'3.50','effectif_n1':'3.00','effectif_n2':'2.00','variante_effectif_n':'141.25',
      'resultat_par_titre_n':'60.00','resultat_par_titre_n1':'30.00','resultat_par_titre_n2':'10.00',
      'distribution_par_titre_n':'20.00','distribution_par_titre_n1':'10.00','distribution_par_titre_n2':'0.00',
      'perte_net_n2':'-1001.00','perte_situation_n2':'8999.00','perte_resultat_par_titre_n2':'-10.01'},
      'inconnus':['Une case vide ne vaut pas0, même si bénéfices distribués0','Sans balance, comptabilité comparative inconnue',
      'Valeurs déclarées sans qualification juridique/sociale automatique'],
      'impacts':'Aucune écriture, salarié, bulletin, liquidation ou donnée réelle créée ou modifiée.'}


def generer():
    d=donnees()
    (HERE/'DONNEES_EXTRA731.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for p in ('n','n1','n2','perte'):
        noms={'n':'N','n1':'N1','n2':'N2','perte':'PERTE'}
        nom=HERE/f'BALANCE_FICTIVE_EXTRA731_{noms[p]}.csv'
        with nom.open('w',encoding='utf8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
            w.writeheader();w.writerows(d[p])
    spec=importlib.util.spec_from_file_location('guide731',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM;blocs=guide.blocs()
    orig=guide.word_table
    widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|X731-')]
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
    for periode in ('n','n1','n2','perte'):
        for row in d[periode]:ws.append([periode+' '+row['compte'],'Débit '+row['debit']+' ; crédit '+row['credit']+' MAD'])
    for row in d['declarations']:
        for k,v in row.items():ws.append([row['code']+' '+k,v])
    for k,v in d['attendus'].items():ws.append([k,v+(' personnes' if 'effectif' in k else ' MAD / titre' if 'par_titre' in k else ' MAD')])
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
    generer();print('Word/PDF/Excel731 générés, six cas humains Non testé ; données/CSV vérifiés indépendamment.')
