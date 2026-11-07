"""Ancien cycle complet sous SQL100, registre témoin non vide et inchangé."""
from contextlib import closing
import importlib
import pytest
from test_reprises_provisions615_isole import (
    application as application100,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,dotation,creer,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_prorata_inventaire_isole import photo


@pytest.fixture(scope='module')
def application(application100):
    app=application100
    with closing(client(app)[0]) as api:
        a=dotation(api);s=creer(api,a['id'])
        ids=[a['ecriture_id'],s['reprises'][0]['ecriture_id']]
        avant=photo(app,ids)
        yield app
        assert ok(api.get(f"{PATH}/{a['id']}"))==s
        assert photo(app,ids)==avant


for prefixe,module in [('facturation','test_e2e_facturation_isole'),
    ('annuel','test_e2e_annee_connectee_isole'),('decale','test_e2e_cloture_decalee605_isole'),
    ('ras','test_ras_tva_capture_isole')]:
    for nom,fonction in vars(importlib.import_module(module)).items():
        if nom.startswith('test_') and callable(fonction):globals()[f'test_{prefixe}_{nom[5:]}']=fonction
