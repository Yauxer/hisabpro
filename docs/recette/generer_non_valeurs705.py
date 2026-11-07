"""Mode d'emploi et suivi humain705 reproductibles, sans accès à la base."""
from pathlib import Path
import importlib.util
import re
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STEM=HERE/'MODE_EMPLOI_NON_VALEURS_705'
SOURCE=ROOT/'docs/LIASSE_BALANCES_NON_VALEURS_705.md'


def generer():
    spec=importlib.util.spec_from_file_location('guide705',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=SOURCE;guide.STEM=STEM
    blocs=guide.blocs()
    table_word_orig=guide.word_table
    largeurs={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',
        lambda m:'w:w="'+({'650':'3500','3000':'1100','1250':'1100','3400':'2600'} if rows[0][0]=='Flux' else largeurs)[m[1]]+'"',table_word_orig(rows))
    guide.docx(blocs)
    table_orig=guide.Table
    # La grille du guide historique réserve13mm au code et27mm au résultat.
    # Adapter seulement ce nouveau document, pour garder les ID lisibles.
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':([75*guide.mm,20*guide.mm,20*guide.mm,55*guide.mm] if rows[0][0].getPlainText()=='Flux' else [24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm])})
    guide.pdf(blocs)
    cas=[[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines() if line.startswith('|NV705-')]
    assert len(cas)==6 and all(len(r)==4 and r[3]=='Non testé' for r in cas)
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
    ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):
        ws.append([statut,f'=COUNTIF(Recette!D2:D7,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Recette')
    ws.append(['ID','Actions / données exactes','Résultat / preuve attendus','Statut humain',
               'Résultat réel','Anomalies','Preuves réelles','Écritures / impacts fiscaux attendus'])
    for ident,actions,result,statut in cas:
        ws.append([ident,actions,result,statut,'','','','Aucune écriture ni liquidation fiscale créée par cette préparation.'])
    validation=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"')
    ws.add_data_validation(validation);validation.add('D2:D7')
    import json
    d=json.loads((HERE/'DONNEES_NON_VALEURS705.json').read_text(encoding='utf8'))
    from decimal import Decimal as D
    for periode in ('n','n1'):
        assert sum(D(r['debit']) for r in d[periode]) == sum(D(r['credit']) for r in d[periode])
    for p in ('n','n1'):
        brut=sum((D(r['debit'])-D(r['credit']) for r in d[p] if r['compte'].startswith('21')),D(0))
        amort=sum((D(r['credit'])-D(r['debit']) for r in d[p] if r['compte'].startswith('281')),D(0))
        assert brut-amort==D(d['attendus_'+p]['net'])
    ws=wb.create_sheet('Données');ws.append(['Information','Valeur exacte'])
    ws.append(['Contexte',d['contexte']])
    for periode in ('n','n1'):
        for ligne in d[periode]:
            ws.append([periode.upper()+' '+ligne['compte'], 'Débit '+ligne['debit']+' ; crédit '+ligne['credit']+' MAD'])
    for periode in ('attendus_n','attendus_n1'):
        for cle,valeur in d[periode].items():ws.append([periode+' '+cle,valeur+' MAD'])
    ws.append(['Écritures et impacts fiscaux','Aucun'])
    ws=wb.create_sheet('Preuves');ws.append(['ID','Fichier / capture réelle','Observations'])
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
    generer();print('Word/PDF/Excel705 générés, six cas humains Non testé.')
