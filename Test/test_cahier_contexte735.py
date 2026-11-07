"""Vérification du complément de recette, sans assimiler recette humaine et tests."""
from decimal import Decimal as D
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/recette'
STEM = HERE / 'MODE_EMPLOI_CONTEXTE_FISCAL_735'


def test_735_donnees_et_oracles_independants():
    d = json.loads((HERE / 'DONNEES_CONTEXTE735.json').read_text(encoding='utf8'))
    with (HERE / 'BALANCE_FICTIVE_CONTEXTE735_N.csv').open(encoding='utf8', newline='') as f:
        lignes = list(csv.DictReader(f, delimiter=';'))
    assert lignes == d['n']
    assert sum(D(r['debit']) for r in lignes) == sum(D(r['credit']) for r in lignes) == D('21000')
    total = sum(D(r[2]) for r in d['credits']); impute = sum(D(r[3]) for r in d['credits'])
    assert total == D('600') and impute == D('150') and total - impute == D(d['attendus']['credits_restants']) == D('450')
    assert d['impot_du'] is d['solde_final'] is None
    assert D(d['acompte']['credits_deja_imputes']) - impute == D('0')
    assert D('149.99') - impute == D(d['attendus']['variante_ecart']) == D('-0.01')


def test_735_word_pdf_et_consigne_sans_fausse_liquidation():
    with ZipFile(STEM.with_suffix('.docx')) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        word = ' '.join(root.itertext())
    pdf = PdfReader(STEM.with_suffix('.pdf'))
    texte = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    md = (ROOT / 'docs/LIASSE_BALANCES_CONTEXTE_FISCAL_735.md').read_text(encoding='utf8')
    assert len(pdf.pages) >= 6
    for s in (word, texte, md):
        for i in range(1, 9): assert f'CF735-0{i}' in s
        assert 'Ne pas inscrire 1250' in s
        assert 'aucun taux' in s.lower() and '450' in s and '149,99' in s
    assert len([r for r in md.splitlines() if r.startswith('|CF735-') and r.endswith('|Non testé|')]) == 8


def test_735_excel_suivi_humain_vierge_et_validation():
    w = load_workbook(STEM.with_suffix('.xlsx'))
    assert w.sheetnames == ['Synthèse', 'Contexte fiscal', 'Données', 'Preuves', 'Anomalies']
    ws = w['Contexte fiscal']
    assert ws.max_row == 9 and len(w['Synthèse']._charts) == 1
    for i in range(2, 10):
        assert ws[f'K{i}'].value == 'Non testé'
        assert all(ws[f'{c}{i}'].value is None for c in 'LMNO')
        assert ws[f'H{i}'].value == 'Aucune écriture créée ou modifiée'
    assert any('K2:K9' in str(v.sqref) for v in ws.data_validations.dataValidation)
    assert w.calculation.fullCalcOnLoad
    assert w['Synthèse']['B2'].value == "=COUNTIF('Contexte fiscal'!K2:K9,A2)"
