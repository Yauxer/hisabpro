"""Vérifie les oracles et ouvre effectivement les documents de recette."""
from decimal import Decimal
from pathlib import Path

from generer_annexe_recette_corrections_277 import JEU, NOM, SOURCES, cas, generer, oracle


def test_oracles_independants_et_perimetres():
    attendu = {'achat_ht': '1000', 'achat_tva': '200', 'achat_ttc': '1200',
               'charge_80': '1040', 'deductible_80': '160', 'charge_0': '1200',
               'banque_initial': '1000', 'banque_credit_mars': '200', 'banque_final': '800',
               'frais_initiaux_unite': '9.75', 'frais_modifies_unite': '12.25'}
    assert oracle() == {k: Decimal(v) for k, v in attendu.items()}
    assert oracle()['charge_80'] + oracle()['deductible_80'] == oracle()['achat_ttc']
    assert sum(k.startswith('Société ') for k in JEU) == 4
    assert 'pas demandé' in JEU['Limites']
    assert 'Bloqué' in JEU['Limites']


def test_cas_sources_et_statuts_non_prevalides():
    items = cas()
    assert [c['id'] for c in items] == [f'COR-277-{i:02}' for i in range(1, 9)]
    assert [c['module'] for c in items] == ['Articles']*3 + ['Paramètres'] + ['Achats']*2 + ['Comptabilité', 'Banques']
    assert all(c['statut'] == 'Non testé' for c in items)
    assert all(not c[k] for c in items for k in ('resultat_reel', 'anomalies', 'observations'))
    assert all(c[k] for c in items for k in ('prerequis', 'donnees', 'actions', 'attendu', 'ecritures', 'fiscal', 'controles', 'preuves', 'sources'))
    root = Path(__file__).resolve().parents[1]
    assert all((root / p).is_file() for chemins in SOURCES.values() for p in chemins)
    assert 'sans réservation' in items[3]['attendu']
    assert '1e309' in items[2]['donnees']
    assert 'distincte' in items[5]['prerequis']


def test_documents_pdf_xlsx_md_ouverts(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader
    generer(tmp_path)
    wb = load_workbook(tmp_path / (NOM + '.xlsx'))
    assert wb.sheetnames == ['Synthèse', *SOURCES, 'Jeu de données']
    assert wb['Synthèse']['B9'].value == '=SUM(B4:B8)'
    assert wb['Synthèse']['G9'].value == '=IF(B9=0,0,(C9+D9)/B9)'
    assert wb['Synthèse']['C4'].value == '=COUNTIF(\'Articles\'!K2:K4,"Réussi")'
    assert sum(wb['Synthèse'].cell(r, 2).value for r in range(4, 9)) == 8
    for module in SOURCES:
        ws = wb[module]
        assert ws['D1'].value == 'Prérequis'
        assert ws['E1'].value == 'Données à saisir'
        assert ws['L1'].value == 'Résultat réel'
        assert ws.freeze_panes == 'A2' and ws.data_validations.count == 1
        for r in range(2, ws.max_row+1):
            assert ws.cell(r, 11).value == 'Non testé'
            assert all(ws.cell(r, col).value is None for col in (12, 13, 15))
            assert ws.cell(r, 14).value and ws.cell(r, 16).value
    jeu = dict(wb['Jeu de données'].iter_rows(min_row=2, values_only=True))
    assert jeu['Oracle charge_80'] == 1040 and jeu['Oracle deductible_80'] == 160
    assert jeu['Oracle banque_final'] == 800
    assert wb['Jeu de données'].cell(12, 2).data_type == 'n'
    pdf = PdfReader(tmp_path / (NOM + '.pdf'))
    texte = ' '.join(' '.join(p.extract_text() or '' for p in pdf.pages).split())
    assert len(pdf.pages) >= 9
    assert all(c['id'] in texte for c in cas())
    assert 'aucun résultat utilisateur prévalidé' in texte.lower()
    assert '1 040' in texte and '160' in texte and '1e309' in texte
    assert 'Actions détaillées' in texte and 'Résultat réel' in texte
    md = (tmp_path / (NOM + '.md')).read_text(encoding='utf-8')
    assert md.count('**statut** : Non testé') == 8
    assert all(f'../../{p}' in md for chemins in SOURCES.values() for p in chemins)
    assert 'opérateur de laboratoire' in md
