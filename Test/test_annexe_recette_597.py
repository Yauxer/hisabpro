"""Contrôles du livrable humain ; aucune recette utilisateur prévalidée."""
import json
from datetime import date
from decimal import Decimal

import fitz
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from generer_annexe_recette_597 import COLONNES, JSON_NOM, NOM, TITRE, cas, generer, limites, oracle


def test_oracle_independant_equilibre_et_prorata():
    o = oracle()
    assert sum(map(Decimal, o['soldes_tva_finaux'].values())) == 0
    assert Decimal(o['prorata']['reporte']) + Decimal(o['prorata']['non_reporte']) == 12000
    assert o['prorata']['reporte'] == '5934.07'
    assert o['decale']['reporte'] == '6032.79'
    assert (date(2025, 9, 30) - date(2025, 4, 1)).days + 1 == o['decale']['jours']
    assert (date(2025, 9, 30) - date(2025, 7, 1)).days + 1 == o['decale']['jours_futurs']
    assert Decimal(o['decale']['reporte']) + Decimal(o['decale']['non_reporte']) == 12000
    assert o['decale']['resultat_cca_apres_cm'] == '-8967.21'
    assert o['decale']['resultat_pca_apres_cm'] == '2967.21'
    assert o['prorata']['jours'] == 182 and o['prorata']['jours_futurs'] == 90
    assert o['journal_tva'] == dict(ecritures=14, lignes=31, debit='166000.00', credit='166000.00')
    assert 1 + 3 + 4 + 4 + 2 == 14
    assert 2 + 3 * 3 + 4 * 2 + 4 * 2 + 2 * 2 == 31
    for name in ('cca', 'pca'):
        assert o[name]['actif'] == o[name]['passif']


def test_recette_humaine_vierge_et_limites_exclues():
    cases = cas()
    assert len(cases) == 30
    assert len({c['id'] for c in cases}) == len(cases)
    assert [c['ordre'] for c in cases] == list(range(1, 31))
    for c in cases:
        assert c['statut'] == 'Non testé'
        for k in ('reel', 'anomalies', 'preuves'):
            assert c[k] == ''
        for k, _ in COLONNES:
            if k not in ('reel', 'anomalies', 'preuves'):
                assert str(c[k]).strip(), (c['id'], k)
    assert len(limites()) == 2
    assert all(l['statut'] == 'Bloqué' for l in limites())


@pytest.fixture(scope='module')
def livrable(tmp_path_factory):
    return generer(tmp_path_factory.mktemp('recette597'))


def test_excel_suivi_formules_liens_et_statuts(livrable):
    dossier, payload = livrable
    w = load_workbook(dossier / (NOM + '.xlsx'))
    assert w.sheetnames == ['Synthèse', 'RAS TVA', 'Inventaire', 'Négatifs', 'Chronologie', 'Données', 'Calculs', 'Limites']
    assert w['Synthèse']['B4'].value == 30
    assert w['Synthèse']['B9'].value == 2
    assert w['Synthèse']['B10'].value == '=IFERROR((B5+B6)/B4,0)'
    assert len(w['Synthèse']._charts) == 1
    assert w['Calculs']['B5'].value == '=12000-B4'
    assert w['Calculs']['B13'].value == '=ROUND(12000*92/183,2)'
    assert w['Calculs']['B14'].value == '=12000-B13'
    assert w.calculation.fullCalcOnLoad
    assert not w._external_links
    for domaine in ('RAS TVA', 'Inventaire', 'Négatifs'):
        ws = w[domaine]
        assert ws.freeze_panes == 'D2'
        assert ws.auto_filter.ref == ws.dimensions
        assert len(ws.data_validations.dataValidation) == 1
        assert ws.data_validations.dataValidation[0].errorStyle == 'stop'
        assert all(ws.cell(r, 12).value == 'Non testé' for r in range(2, ws.max_row + 1))
        assert all(ws.cell(r, col).value is None for r in range(2, ws.max_row + 1) for col in (13, 14, 16))
    for r in range(2, 32):
        assert w['Chronologie'].cell(r, 6).hyperlink.target.startswith("#'")
        assert w['Chronologie'].cell(r, 5).value.startswith("='")
    assert json.loads((dossier / JSON_NOM).read_text(encoding='utf8')) == payload
    assert (dossier / payload['donnees']['societes']['S1']['logo']).read_bytes().startswith(b'\x89PNG')


def test_pdf_fiches_completes_images_et_limites_de_page(livrable):
    dossier, payload = livrable
    path = dossier / (NOM + '.pdf')
    reader = PdfReader(path)
    texte = ' '.join(('\n'.join(p.extract_text() for p in reader.pages)).split())
    assert TITRE in texte
    for c in payload['cas']:
        assert c['id'] in texte
        assert c['objectif'] in texte
    assert '5934.07' in texte
    assert 'Non testé' in texte and 'Limites non exécutables' in texte
    assert sum(len(p.images) for p in reader.pages) >= 2
    with fitz.open(path) as doc:
        for p in doc:
            for block in p.get_text('blocks'):
                if block[4].strip():
                    assert block[0] >= 30 and block[1] >= 20
                    assert block[2] <= p.rect.width - 25
                    assert block[3] <= p.rect.height - 12
