"""Vérifie les livrables, sans prévalider une recette utilisateur."""
import json
from decimal import Decimal

from generer_annexe_recette_commerciale import NOM, cas, generer, oracle


def test_cas_complets_et_oracle_independant():
    items = cas()
    assert [c['id'] for c in items] == [f'COM-{i:03}' for i in range(1, 6)]
    assert sum(c['statut'] == 'Non testé' for c in items) == 4
    assert sum(c['statut'] == 'Bloqué' for c in items) == 1
    assert all(not c['resultat_reel'] and not c['anomalies'] and not c['observations'] for c in items)
    assert all(c[k] for c in items for k in ('prerequis', 'donnees', 'actions', 'attendu', 'ecritures', 'fiscal', 'controles', 'preuves'))
    for quantites, ht, tva, ttc in (((3, 3, 1), '70.00', '14.00', '84.00'),
                                  ((1, 1, 1), '30.00', '6.00', '36.00'),
                                  ((1,), '10.00', '2.00', '12.00')):
        calcul = oracle(quantites)
        assert calcul == {'ht': ht, 'tva': tva, 'ttc': ttc}
        assert Decimal(calcul['ht']) + Decimal(calcul['tva']) == Decimal(calcul['ttc'])
    assert all('aucune' in c['ecritures'].lower() for c in items)
    assert 'Aucun champ UI' in items[-1]['prerequis']


def test_artefacts_pdf_excel_md_reellement_ouverts(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader

    generer(tmp_path)
    wb = load_workbook(tmp_path / (NOM + '.xlsx'))
    assert wb.sheetnames == ['Synthèse', 'Devis', 'Documents client', 'Permissions', 'Stock inconnu', 'Jeu de données']
    assert wb['Synthèse']['C4'].value.startswith('=COUNTIF(')
    assert wb['Synthèse']['B8'].value == '=SUM(B4:B7)'
    domaines = [ws for ws in wb if ws.title not in ('Synthèse', 'Jeu de données')]
    assert all(ws.data_validations.count == 1 and ws.freeze_panes == 'A2' for ws in domaines)
    rows = [row for ws in domaines for row in ws.iter_rows(min_row=2, values_only=True)]
    assert len(rows) == 5
    assert {r[0] for r in rows} == {c['id'] for c in cas()}
    assert all(r[11] is None and r[12] is None and r[14] is None and r[13] for r in rows)
    assert sum(r[10] == 'Bloqué' for r in rows) == 1
    jeu = dict(wb['Jeu de données'].iter_rows(min_row=2, values_only=True))
    assert json.loads(jeu['COM-001 oracle indépendant'])['ttc'] == '84.00'
    assert json.loads(jeu['COM-002 oracle indépendant'])['ttc'] == '36.00'
    pdf = PdfReader(tmp_path / (NOM + '.pdf'))
    texte = ' '.join(' '.join(p.extract_text() for p in pdf.pages).split())
    assert all(c['id'] in texte for c in cas())
    assert 'Aucun résultat utilisateur prévalidé' in texte
    assert '84,00' in texte and '36,00' in texte
    assert 'Aucun champ UI' in texte and 'sans réservation' in texte
    md = (tmp_path / (NOM + '.md')).read_text(encoding='utf-8')
    assert all(c['id'] in md for c in cas())
    assert 'Aucun résultat utilisateur prévalidé' in md
    assert 'SANS SIGNATURE AUTHENTIQUE' in md
