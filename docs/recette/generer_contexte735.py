"""Complément de recette735 reproductible, oracles Decimal indépendants."""
from decimal import Decimal as D
from pathlib import Path
from xml.sax.saxutils import escape
import csv
import importlib.util
import json

from openpyxl import Workbook
from openpyxl.chart import DoughnutChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'docs/LIASSE_BALANCES_CONTEXTE_FISCAL_735.md'
STEM = HERE / 'MODE_EMPLOI_CONTEXTE_FISCAL_735'


def donnees():
    n = json.loads((HERE / 'DONNEES_PASSAGE725.json').read_text(encoding='utf8'))['n']
    credits = [('Crédit A fictif', 'CERT-A735', '300', '100'),
               ('Crédit B fictif', 'CERT-B735', '200', '50'),
               ('Crédit C fictif', 'CERT-C735', '100', '0')]
    assert sum(D(r['debit']) for r in n) == sum(D(r['credit']) for r in n) == D('21000')
    total = sum(D(r[2]) for r in credits)
    impute = sum(D(r[3]) for r in credits)
    assert total == D('600') and impute == D('150') and total - impute == D('450')
    assert D('150') - impute == D('0') and D('149.99') - impute == D('-0.01')
    assert (D('8000') + 500 - 200 - 1000) * D('.20') == D('1460')
    assert (D('8000') + 500 - 200 - 1000) * D('.10') == D('730')
    return {'contexte': 'Société fictive735 MAD2026 ; montants fiscaux documentaires, aucune éligibilité déduite.',
            'n': n, 'cm': '3000', 'css': '0', 'credits': credits,
            'acompte': {'reference': 'QUITTANCE735', 'verse': '1000', 'credit_anterieur': '100', 'credits_deja_imputes': '150'},
            'attendus': {'credits_total': '600.00', 'credits_deja_imputes': '150.00',
                         'credits_restants': '450.00', 'ecart_imputations': '0.00',
                         'variante_ecart': '-0.01', 'is_memoire_initial': '1460.00', 'is_memoire_apres_revue': '730.00'},
            'impot_du': None, 'solde_final': None,
            'impacts': 'Aucune écriture ou liquidation créée ; aucun paiement ni droit fiscal confirmé.'}


def generer():
    d = donnees()
    (HERE / 'DONNEES_CONTEXTE735.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    with (HERE / 'BALANCE_FICTIVE_CONTEXTE735_N.csv').open('w', encoding='utf8', newline='') as out:
        w = csv.DictWriter(out, fieldnames=['compte', 'debit', 'credit'], delimiter=';', lineterminator='\n')
        w.writeheader(); w.writerows(d['n'])
    spec = importlib.util.spec_from_file_location('guide735', ROOT / 'docs/guide/generer_guide.py')
    guide = importlib.util.module_from_spec(spec); spec.loader.exec_module(guide)
    guide.SOURCE = SOURCE; guide.STEM = STEM

    def word_table(rows):
        widths = [1800, 3200, 3300] if len(rows[0]) == 3 else [1200, 3050, 3050, 1000]
        content = '<w:tbl><w:tblPr><w:tblStyle w:val="GuideTable"/><w:tblW w:w="8300" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr>'
        content += '<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{v}"/>' for v in widths) + '</w:tblGrid>'
        for i, row in enumerate(rows):
            content += '<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if i == 0 else '') + '</w:trPr>'
            for width, cell in zip(widths, row):
                content += f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>' + guide.para(cell, 'TableText') + '</w:tc>'
            content += '</w:tr>'
        return content + '</w:tbl>'

    guide.word_table = word_table
    table_orig = guide.Table
    guide.Table = lambda rows, **kw: table_orig(rows, **{**kw, 'colWidths': [v * guide.mm for v in
        ([35, 65, 70] if len(rows[0]) == 3 else [24, 64, 63, 19])]})
    blocs = guide.blocs(); guide.docx(blocs); guide.pdf(blocs)
    cas = [[c.strip() for c in line.strip('|').split('|')] for line in SOURCE.read_text(encoding='utf8').splitlines()
           if line.startswith('|CF735-')]
    assert len(cas) == 8 and all(len(r) == 4 and r[3] == 'Non testé' for r in cas)
    wb = Workbook(); wb.calculation = CalcProperties(fullCalcOnLoad=True)
    ws = wb.active; ws.title = 'Synthèse'; ws.append(['Statut humain', 'Nombre'])
    for i, statut in enumerate(['Non testé', 'Réussi', 'Échoué', 'Bloqué'], 2):
        ws.append([statut, f'=COUNTIF(\'Contexte fiscal\'!K2:K9,A{i})'])
    ws.append(['Progression', '=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']); ws['B6'].number_format = '0%'
    chart = DoughnutChart(); chart.title = 'Recette utilisateur'
    chart.add_data(Reference(ws, min_col=2, min_row=1, max_row=5), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=5)); ws.add_chart(chart, 'D2')
    ws = wb.create_sheet('Contexte fiscal')
    ws.append(['ID', 'Module', 'Objectif', 'Prérequis', 'Données exactes', 'Actions interface', 'Résultat attendu',
               'Écritures attendues', 'Impact fiscal attendu', 'Contrôles', 'Statut humain', 'Résultat réel',
               'Anomalies', 'Preuves réelles', 'Observations', 'Justificatif attendu'])
    for ident, actions, resultat, statut in cas:
        ws.append([ident, 'Liasse / balances externes', actions, 'Société fictive MAD2026 ; voir mode d’emploi735',
                   'CSV735 et DONNEES_CONTEXTE735.json ; valeurs détaillées dans le mode d’emploi', actions,
                   resultat, 'Aucune écriture créée ou modifiée', d['impacts'], resultat, statut,
                   '', '', '', '', 'Captures et exports indiqués dans le résultat attendu'])
    validation = DataValidation(type='list', formula1='"Non testé,Réussi,Échoué,Bloqué"')
    ws.add_data_validation(validation); validation.add('K2:K9')
    ws = wb.create_sheet('Données'); ws.append(['Information', 'Valeur exacte'])
    for r in d['n']: ws.append(['Compte ' + r['compte'], 'Débit ' + r['debit'] + ' ; crédit ' + r['credit']])
    for nature, ref, total, impute in d['credits']: ws.append([nature, ref + ' ; total ' + total + ' ; déjà imputé ' + impute])
    for k in ('cm', 'css'): ws.append([k, d[k]])
    for k, v in d['acompte'].items(): ws.append(['acompte ' + k, v])
    for k, v in d['attendus'].items(): ws.append([k, v])
    ws.append(['Impôt dû / solde final', 'Indisponibles'])
    ws = wb.create_sheet('Preuves'); ws.append(['ID', 'Preuve réelle', 'Observations'])
    for row in cas: ws.append([row[0], '', ''])
    ws = wb.create_sheet('Anomalies'); ws.append(['ID', 'Cas', 'Constat', 'Décision', 'Statut'])
    for ws in wb:
        ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
        for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='185FA5')
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 42
        for row in ws:
            for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
    for i in range(2, 10): wb['Contexte fiscal'].row_dimensions[i].height = 150
    wb.save(STEM.with_suffix('.xlsx'))
    return {'cas_humains_non_testes': len(cas), 'feuilles': wb.sheetnames}


if __name__ == '__main__':
    print(generer())
