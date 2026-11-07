"""Consolidation540/541, proformas et rôles, sur le socle PostgreSQL nonce098."""
from pathlib import Path
import hashlib, importlib, json
import pytest
from test_consolidation_factures538_isole import (
    application as application538, application536, application534, application532,
    application530, application528, application526, application524, application522,
    application520, application518, application514, application512, application510,
    application508, application506, application503, application501, application499,
    application497, application495, application493, application490, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
for nom,prefixe in (
    ('test_consolidation_factures538_isole','test_'),
    ('test_e2e_factures_lecture_isole','test_lecture540_'),
    ('test_factures_proforma_lecture_isole','test_proforma541_'),
):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            nom_test=prefixe+k[5:]
            assert nom_test not in globals()
            globals()[nom_test]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application538):
    chemins=[ROOT/'src/pages/Factures.jsx',ROOT/'hisabpro-backend/schemas.py',Path(__file__),
        ROOT/'Test/test_e2e_factures_lecture_isole.py',
        ROOT/'Test/test_factures_proforma_lecture_isole.py']
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'erreur':None,'sources':avant}
    try:
        yield application538
        assert sources()==avant
        preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/factures540_preuve.json').write_text(
            json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
