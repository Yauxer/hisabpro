"""Reproduire le mode d'emploi Word/PDF et son suivi humain vierge, hors base."""
from pathlib import Path
import importlib.util
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STEM = HERE / 'MODE_EMPLOI_DOSSIER_PREPARATION_689'


def generer():
    spec = importlib.util.spec_from_file_location('guide689', ROOT/'docs/guide/generer_guide.py')
    guide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guide)
    guide.SOURCE = ROOT/'docs/LIASSE_BALANCES_DOSSIER_689.md'
    guide.STEM = STEM
    blocs = guide.blocs()
    guide.docx(blocs)
    guide.pdf(blocs)
    wb = Workbook()
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    ws = wb.active
    ws.title = 'Synthèse'
    ws.append(['Statut humain', 'Nombre'])
    for i, statut in enumerate(['Non testé', 'Réussi', 'Échoué', 'Bloqué'], 2):
        ws.append([statut, f'=COUNTIF(Recette!D2:D3,A{i})'])
    ws.append(['Progression', '=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))'])
    ws['B6'].number_format = '0%'
    ws = wb.create_sheet('Recette')
    ws.append(['Identifiant', 'Module', 'Objectif', 'Statut humain', 'Résultat réel', 'Anomalies', 'Preuves réelles', 'Observations'])
    ws.append(['BAL689-01', 'Liasse / balances', 'Vérifier le dossier de la version2/3 avec le cas01 du mode d’emploi', 'Non testé', '', '', '', ''])
    ws.append(['BAL689-02', 'Liasse / balances', 'Lecture/mobile et séparation des sociétés avec le cas02 du mode d’emploi', 'Non testé', '', '', '', ''])
    validation = DataValidation(type='list', formula1='"Non testé,Réussi,Échoué,Bloqué"')
    ws.add_data_validation(validation)
    validation.add('D2:D3')
    ws = wb.create_sheet('Preuves')
    ws.append(['Identifiant', 'ZIP / capture réelle', 'Observations'])
    for identifiant in ('BAL689-01', 'BAL689-02'):
        ws.append([identifiant, '', ''])
    ws = wb.create_sheet('Anomalies')
    ws.append(['ID', 'Cas', 'Constat', 'Décision', 'Statut'])
    for ws in wb:
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='185FA5')
        for colonne in ws.columns:
            ws.column_dimensions[colonne[0].column_letter].width = 48
        for ligne in ws:
            for cell in ligne:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
    wb.save(STEM.with_suffix('.xlsx'))


if __name__ == '__main__':
    generer()
    print('Word/PDF/Excel689 générés, deux cas humains Non testé.')
