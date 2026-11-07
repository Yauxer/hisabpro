"""Documents de recette ouverts réellement ; aucun statut prévalidé."""
from decimal import Decimal

from generer_annexe_recette_bilan import COMPTES, NOM, cas, generer, oracle


def test_oracle_et_cas_complets():
    items = cas()
    assert [c['id'] for c in items] == [f'BILAN-DET-{i:02}' for i in range(1, 5)]
    assert all(c['statut'] == 'Non testé' for c in items)
    assert all(not c[k] for c in items for k in ('resultat_reel', 'anomalies', 'observations'))
    assert all(c[k] for c in items for k in ('prerequis', 'donnees', 'actions', 'attendu', 'ecritures', 'fiscal', 'controles', 'preuves'))
    assert sum(Decimal(v) for _, v in COMPTES) == Decimal(45000)
    assert oracle() == {'brut': '45000', 'amort': '300', 'net': '44700',
                        'immobilisations_brut': '21000', 'immobilisations_net': '20700', 'n1_net': '75'}
    assert Decimal(8925) + Decimal(75) == Decimal(9000)
    assert Decimal(44625) + Decimal(75) == Decimal(44700)
    assert 'Bloqué' in items[-1]['actions']
    assert 'snapshot' in items[-1]['prerequis']


def test_pdf_xlsx_md_reellement_ouverts(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader
    generer(tmp_path)
    wb = load_workbook(tmp_path / (NOM + '.xlsx'))
    assert wb.sheetnames == ['Synthèse', 'Bilan', 'Comparatif', 'Exports', 'Archives', 'Jeu de données']
    assert wb['Synthèse']['C4'].value == '=COUNTIF(\'Bilan\'!K2,"Réussi")'
    assert wb['Synthèse']['B8'].value == '=SUM(B4:B7)'
    for ws in list(wb)[1:5]:
        assert ws['K2'].value == 'Non testé'
        assert ws['L2'].value is None and ws['M2'].value is None and ws['O2'].value is None
        assert ws['N2'].value
        assert ws.data_validations.count == 1 and ws.freeze_panes == 'A2'
    jeu = dict(wb['Jeu de données'].iter_rows(min_row=2, values_only=True))
    assert jeu['Oracle net'] == '44700' and jeu['Oracle n1_net'] == '75'
    pdf = PdfReader(tmp_path / (NOM + '.pdf'))
    texte = ' '.join(' '.join(p.extract_text() or '' for p in pdf.pages).split())
    assert all(c['id'] in texte for c in cas())
    assert 'Aucun résultat utilisateur prévalidé' in texte
    assert '45 000,00' in texte and '44 700,00' in texte and '75,00' in texte
    md = (tmp_path / (NOM + '.md')).read_text(encoding='utf-8')
    assert all(c['id'] in md for c in cas())
    assert md.count('**statut** : Non testé') == 4
