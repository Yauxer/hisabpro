from test_patch09_3_liasse_fiscale import _dummy_liasse
from test_patch120_liasse_exports_ventilations import section
from exports09a import verifier_exports
from test_patch125_etic_requetes_orm import db


def test_exports_memoires_preservent_la_source_et_toutes_les_ventilations():
    data = _dummy_liasse()
    data['etic']['sections'] = [section('B6'), section('B7')]
    stats = verifier_exports(data)
    assert stats['pdf_pages'] > 0
    assert stats['feuilles'] >= 9
    assert stats['ventilations'] == 2


def test_rapport_02_002_conserve_les_sources_distinctes(db):
    from datetime import date
    from test_patch125_etic_requetes_orm import facture_source
    from recette09a_lecture_seule import rapport_references_exactes
    f02, e02 = facture_source(db, type_='achat', numero='02')
    f002, e002 = facture_source(db, type_='achat', numero='002')
    contenu = rapport_references_exactes(db, 3, 2026, date(2026, 12, 31))
    assert f'| achat | {f02.id} | 02 | {e02.id} |' in contenu
    assert f'| achat | {f002.id} | 002 | {e002.id} |' in contenu
